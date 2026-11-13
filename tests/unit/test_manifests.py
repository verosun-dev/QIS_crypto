import hashlib
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from qis_spot_perp import cli
from qis_spot_perp.data.manifests import provenance, sha256


class ManifestTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.date = '2020-01-01'
        self.directory = self.make_inputs(self.date)

    def make_inputs(self, date, legacy=False):
        directory = self.root/'data/manifests'
        if not legacy:
            directory = directory/date
        directory.mkdir(parents=True, exist_ok=True)
        raw = self.root/'data/raw'
        raw.mkdir(parents=True, exist_ok=True)
        retrieval = []
        for leg in ('spot', 'swap'):
            for kind in ('spec', 'trades', 'books'):
                groups = []
                if kind != 'spec':
                    for number in range(2 if kind == 'trades' else 1):
                        filename = f'{leg}-{kind}-{date}-{number}.zip'
                        (raw/filename).write_bytes(b'abc')
                        groups.append({'filename': filename, 'url': f'https://static.okx.com/{filename}', 'sizeMB': '0.001'})
                name = f'okx-{leg}-{kind}.json'
                response = {'code': '0', 'data': [{'details': [{'groupDetails': groups}]}]}
                (directory/name).write_text(json.dumps(response))
                retrieval.append({'file': str((directory/name).relative_to(self.root)), 'url': f'https://www.okx.com/{name}', 'retrieved_at_utc': '2020-02-01T00:00:00+00:00'})
        (directory/'okx-funding.json').write_text(json.dumps({'code': '0', 'data': []}))
        retrieval.append({'file': str((directory/'okx-funding.json').relative_to(self.root)), 'url': 'https://www.okx.com/funding', 'retrieved_at_utc': '2020-02-01T00:00:00+00:00'})
        (directory/'retrieval_requests.json').write_text(json.dumps(retrieval))
        return directory

    def test_sha256_known_and_multichunk_inputs(self):
        target = self.root/'hash-input'
        for payload, expected in (
            (b'', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
            (b'abc', 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'),
            (b'x'*(1024*1024+37), hashlib.sha256(b'x'*(1024*1024+37)).hexdigest()),
        ):
            with self.subTest(size=len(payload)):
                target.write_bytes(payload)
                self.assertEqual(sha256(target), expected)

    def test_dated_summary_records_exact_inputs(self):
        result = provenance(self.root, self.date)
        self.assertEqual(result['research_date'], self.date)
        self.assertEqual(result['total_bytes'], 18)
        self.assertEqual(len(result['files']), 6)
        for row in result['files']:
            self.assertEqual(row['local_path'], f"data/raw/{row['filename']}")
            self.assertEqual(row['bytes'], 3)
            self.assertEqual(row['sha256'], 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
            self.assertTrue(row['retrieval_manifest'].startswith(f'data/manifests/{self.date}/'))
        self.assertEqual(len(result['source_manifests']), 8)
        for source in result['source_manifests']:
            self.assertEqual(source['sha256'], hashlib.sha256((self.root/source['path']).read_bytes()).hexdigest())
        checked = datetime.fromisoformat(result['checked_at_utc'])
        self.assertEqual(checked.utcoffset(), timedelta(0))
        self.assertEqual(result['checked_client_date'], checked.date().isoformat())
        self.assertEqual(json.loads((self.directory/'downloads.json').read_text()), result)

    def test_repeat_verifies_without_rewriting_even_after_mtime_change(self):
        saved = provenance(self.root, self.date)
        output = self.directory/'downloads.json'
        original, modified = output.read_bytes(), output.stat().st_mtime_ns
        raw = self.root/saved['files'][0]['local_path']
        os.utime(raw, (1, 1))
        self.assertEqual(provenance(self.root, self.date), saved)
        self.assertEqual(output.read_bytes(), original)
        self.assertEqual(output.stat().st_mtime_ns, modified)

    def test_changed_archive_is_rejected_without_replacing_summary(self):
        saved = provenance(self.root, self.date)
        output = self.directory/'downloads.json'
        original = output.read_bytes()
        (self.root/saved['files'][0]['local_path']).write_bytes(b'xyz')
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            provenance(self.root, self.date)
        self.assertEqual(output.read_bytes(), original)

    def test_changed_source_is_rejected_without_replacing_summary(self):
        provenance(self.root, self.date)
        output = self.directory/'downloads.json'
        original = output.read_bytes()
        source = self.directory/'okx-spot-spec.json'
        source.write_text(source.read_text()+'\n')
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            provenance(self.root, self.date)
        self.assertEqual(output.read_bytes(), original)

    def test_changed_saved_summary_is_not_reported_as_verified(self):
        provenance(self.root, self.date)
        output = self.directory/'downloads.json'
        original = output.read_text()
        for key, value in (('total_bytes', 999), ('url', 'https://wrong.example/archive'), ('dateTs', '999'), ('sizeMB', '999')):
            with self.subTest(key=key):
                saved = json.loads(original)
                if key == 'total_bytes':
                    saved[key] = value
                else:
                    saved['files'][0][key] = value
                output.write_text(json.dumps(saved))
                altered = output.read_bytes()
                with self.assertRaisesRegex(ValueError, 'inputs changed'):
                    provenance(self.root, self.date)
                self.assertEqual(output.read_bytes(), altered)

    def test_missing_archive_blocks_finalization(self):
        next((self.root/'data/raw').iterdir()).unlink()
        with self.assertRaisesRegex(ValueError, 'missing raw archives'):
            provenance(self.root, self.date)
        self.assertFalse((self.directory/'downloads.json').exists())

    def test_two_dates_preserve_each_other_and_legacy_metadata(self):
        legacy = self.root/'data/manifests/downloads.json'
        legacy.write_bytes(b'historical debug evidence')
        provenance(self.root, self.date)
        snapshot = {p.name: p.read_bytes() for p in self.directory.iterdir()}
        second = self.make_inputs('2020-01-02')
        provenance(self.root, '2020-01-02')
        self.assertTrue((second/'downloads.json').exists())
        self.assertEqual({p.name: p.read_bytes() for p in self.directory.iterdir()}, snapshot)
        self.assertEqual(legacy.read_bytes(), b'historical debug evidence')

    def test_legacy_inspection_does_not_replace_historical_summary(self):
        legacy = self.make_inputs(self.date, legacy=True)
        output = legacy/'downloads.json'
        output.write_bytes(b'historical debug evidence')
        result = provenance(self.root)
        self.assertEqual(len(result['files']), 6)
        self.assertEqual(result['total_bytes'], 18)
        self.assertEqual(output.read_bytes(), b'historical debug evidence')

    def test_legacy_inspection_keeps_missing_inputs_explicit(self):
        self.make_inputs(self.date, legacy=True)
        for path in (self.root/'data/raw').iterdir():
            path.unlink()
        result = provenance(self.root)
        self.assertEqual(result['total_bytes'], 0)
        self.assertTrue(all(row['sha256'] is None and row['bytes'] is None for row in result['files']))
        self.assertFalse((self.root/'data/manifests/downloads.json').exists())

    def test_date_must_be_canonical(self):
        for date in ('2020-1-01', '20200101', '2020-01-01T00:00:00', '../2020-01-01'):
            with self.subTest(date=date), self.assertRaises(ValueError):
                provenance(self.root, date)


class ManifestCliTests(unittest.TestCase):
    def test_manifest_dispatches_optional_date(self):
        for date in (None, '2020-01-01'):
            args = ['qis', 'manifest'] + (['--date', date] if date else [])
            with self.subTest(date=date), patch('sys.argv', args), patch.object(cli, 'provenance', return_value={'files': []}) as inspect, redirect_stdout(io.StringIO()) as output:
                cli.main()
                inspect.assert_called_once_with(Path.cwd(), date)
                self.assertEqual(json.loads(output.getvalue()), {'files': []})

    def test_run_rejects_manifest_only_date_option(self):
        with patch('sys.argv', ['qis', 'run', '--date', '2020-01-01']), patch.object(cli, 'run') as run, redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            cli.main()
        run.assert_not_called()
