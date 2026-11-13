import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from scripts import fetch_sample
from qis_spot_perp.data.manifests import provenance


class FetchSampleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)

    def fake_curl(self, url, path, *limits):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if urlparse(url).hostname == 'static.okx.com':
            path.write_bytes(b'archive')
            return
        params = parse_qs(urlparse(url).query)
        data = []
        if 'module' in params:
            leg = 'spot' if params['instType'] == ['SPOT'] else 'swap'
            day = datetime.fromtimestamp(int(params['begin'][0])/1000, timezone.utc).date()
            kind = 'trades' if params['module'] == ['1'] else 'books'
            groups = []
            for offset in range(2 if kind == 'trades' else 1):
                date = (day+timedelta(days=offset)).isoformat()
                filename = f'{leg}-{kind}-{date}.zip'
                groups.append({'filename': filename, 'url': f'https://static.okx.com/{filename}', 'sizeMB': '0.001'})
            data = [{'details': [{'groupDetails': groups}]}]
        path.write_text(json.dumps({'code': '0', 'data': data}))

    def fetch(self, date='2020-01-01', download=False, side_effect=None):
        args = ['fetch_sample.py', '--date', date] + (['--download'] if download else [])
        with patch('sys.argv', args), patch.object(fetch_sample, 'curl', side_effect=side_effect or self.fake_curl) as request, patch.object(fetch_sample.time, 'sleep'), redirect_stdout(io.StringIO()):
            fetch_sample.main()
        return request

    def snapshot(self, directory):
        return {p.relative_to(directory).as_posix(): p.read_bytes() for p in directory.rglob('*') if p.is_file()}

    def test_two_dates_preserve_source_responses_and_legacy_metadata(self):
        legacy = self.root/'data/manifests'
        legacy.mkdir(parents=True)
        for name in ('okx-spot-spec.json', 'retrieval_requests.json', 'downloads.json'):
            (legacy/name).write_bytes(b'historical metadata')
        first = self.fetch()
        self.assertEqual(first.call_count, 7)
        directory = legacy/'2020-01-01'
        original = self.snapshot(directory)
        self.fetch('2020-01-02')
        self.assertEqual(self.snapshot(directory), original)
        for name in ('okx-spot-spec.json', 'retrieval_requests.json', 'downloads.json'):
            self.assertEqual((legacy/name).read_bytes(), b'historical metadata')
        requests = json.loads((directory/'retrieval_requests.json').read_text())
        self.assertEqual(len(requests), 7)
        for row in requests:
            self.assertEqual(Path(row['file']).parent, Path('data/manifests/2020-01-01'))
            self.assertIsNotNone(datetime.fromisoformat(row['retrieved_at_utc']).tzinfo)

    def test_repeated_listing_performs_no_requests_or_writes(self):
        self.fetch()
        directory = self.root/'data/manifests/2020-01-01'
        original = self.snapshot(directory)
        repeated = self.fetch()
        repeated.assert_not_called()
        self.assertEqual(self.snapshot(directory), original)

    def test_list_then_download_uses_cached_metadata(self):
        self.fetch()
        directory = self.root/'data/manifests/2020-01-01'
        original = self.snapshot(directory)
        downloaded = self.fetch(download=True)
        self.assertEqual(downloaded.call_count, 6)
        self.assertTrue(all(urlparse(call.args[0]).hostname == 'static.okx.com' for call in downloaded.call_args_list))
        self.assertEqual(len(list((self.root/'data/raw').iterdir())), 6)
        self.assertEqual(self.snapshot(directory), original)

    def test_existing_raw_archive_is_retained(self):
        self.fetch()
        raw = self.root/'data/raw/spot-books-2020-01-01.zip'
        raw.parent.mkdir(parents=True)
        raw.write_bytes(b'existing archive')
        downloaded = self.fetch(download=True)
        self.assertEqual(downloaded.call_count, 5)
        self.assertEqual(raw.read_bytes(), b'existing archive')

    def test_failed_metadata_does_not_publish_acquisition(self):
        def failure(url, path, *limits):
            Path(path).write_text(json.dumps({'code': '1', 'msg': 'simulated failure'}))

        with self.assertRaises(ValueError):
            self.fetch(side_effect=failure)
        self.assertFalse((self.root/'data/manifests/2020-01-01').exists())
        self.assertEqual(list((self.root/'data/manifests').iterdir()), [])
        self.assertEqual(self.fetch().call_count, 7)

    def test_missing_archive_listing_does_not_publish_acquisition(self):
        def missing(url, path, *limits):
            self.fake_curl(url, path, *limits)
            if Path(path).name == 'okx-spot-books.json':
                Path(path).write_text(json.dumps({'code': '0', 'data': []}))

        with self.assertRaisesRegex(ValueError, 'expected two books'):
            self.fetch(side_effect=missing)
        self.assertFalse((self.root/'data/manifests/2020-01-01').exists())

    def test_failed_raw_download_preserves_metadata_and_partial_file(self):
        self.fetch()
        directory = self.root/'data/manifests/2020-01-01'
        original = self.snapshot(directory)

        def failure(url, path, *limits):
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.with_name(path.name+'.part').write_bytes(b'partial archive')
            raise RuntimeError('simulated archive failure')

        with self.assertRaisesRegex(RuntimeError, 'simulated archive failure'):
            self.fetch(download=True, side_effect=failure)
        self.assertEqual(self.snapshot(directory), original)
        self.assertEqual(len(list((self.root/'data/raw').glob('*.part'))), 1)

    def test_incomplete_cached_acquisition_is_rejected_without_requests(self):
        self.fetch()
        (self.root/'data/manifests/2020-01-01/okx-spot-spec.json').unlink()
        with patch.object(fetch_sample, 'curl') as request, patch('sys.argv', ['fetch_sample.py', '--date', '2020-01-01']), self.assertRaises(FileNotFoundError):
            fetch_sample.main()
        request.assert_not_called()

    def test_finalized_source_changes_block_downloads_without_requests(self):
        self.fetch(download=True)
        provenance(self.root, '2020-01-01')
        directory = self.root/'data/manifests/2020-01-01'
        source = directory/'okx-spot-spec.json'
        source.write_text(source.read_text()+'\n')
        original = self.snapshot(directory)
        with patch.object(fetch_sample, 'curl') as request, patch('sys.argv', ['fetch_sample.py', '--date', '2020-01-01', '--download']), self.assertRaisesRegex(ValueError, 'source bytes changed'):
            fetch_sample.main()
        request.assert_not_called()
        self.assertEqual(self.snapshot(directory), original)

    def test_finalized_acquisition_can_restore_missing_raw_with_same_sources(self):
        self.fetch(download=True)
        saved = provenance(self.root, '2020-01-01')
        (self.root/saved['files'][0]['local_path']).unlink()
        restored = self.fetch(download=True)
        self.assertEqual(restored.call_count, 1)
        self.assertEqual(provenance(self.root, '2020-01-01'), saved)

    def test_date_must_be_canonical_before_requests(self):
        for date in ('2020-1-01', '20200101', '2020-01-01T00:00:00', '../2020-01-01'):
            with self.subTest(date=date), patch.object(fetch_sample, 'curl') as request, patch('sys.argv', ['fetch_sample.py', '--date', date]), self.assertRaises(ValueError):
                fetch_sample.main()
            request.assert_not_called()
