"""Tests that saved experiments are complete, reproducible, and never overwritten."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from qis_spot_perp.reporting.artifacts import (
    ExperimentExistsError, save_run, source_fingerprint, write_csv)


def fake_engine(net='1'):
    """Replay stand-in with one trade; summary() returns a recognisable value."""
    return SimpleNamespace(
        features=[], orders=[], fills=[], equity=[], states=[],
        trades=[{'episode_id': 1, 'net_usdt': net}],
        summary=lambda: {'closed_net_usdt': net},
    )


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        # Every test works in a throwaway folder, never in the real outputs/.
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'src').mkdir()
        (self.root / 'src' / 'mod.py').write_text('x = 1\n')

    def tearDown(self):
        self.tmp.cleanup()

    def save(self, experiment_id, net='1'):
        out = self.root / 'outputs' / experiment_id
        config = {'experiment_id': experiment_id}
        return save_run(self.root, out, 'configs/x.json', config, fake_engine(net), {}, [])

    def register_ids(self):
        lines = (self.root / 'outputs' / 'experiment_register.jsonl').read_text().splitlines()
        return [json.loads(line)['experiment_id'] for line in lines]

    def test_first_save_writes_every_file(self):
        self.save('exp_a')
        out = self.root / 'outputs' / 'exp_a'
        for name in ['features', 'orders', 'fills', 'trades', 'equity', 'states', 'pressure']:
            self.assertTrue((out / f'{name}.csv').exists(), name)
        for name in ['summary', 'data_quality_report', 'config', 'experiment']:
            self.assertTrue((out / f'{name}.json').exists(), name)
        self.assertEqual(self.register_ids(), ['exp_a'])

    def test_second_save_with_same_id_is_refused_and_keeps_first_result(self):
        self.save('exp_a', net='1')
        with self.assertRaises(ExperimentExistsError):
            self.save('exp_a', net='999')
        summary = json.loads((self.root / 'outputs/exp_a/summary.json').read_text())
        self.assertEqual(summary['closed_net_usdt'], '1')     # original evidence intact
        self.assertEqual(self.register_ids(), ['exp_a'])      # no duplicate record

    def test_new_id_is_allowed(self):
        self.save('exp_a')
        self.save('exp_b')
        self.assertEqual(self.register_ids(), ['exp_a', 'exp_b'])

    def test_empty_folder_from_runner_is_allowed(self):
        # runner.py creates the output folder before replaying; that must not block saving.
        (self.root / 'outputs' / 'exp_a').mkdir(parents=True)
        (self.root / 'outputs' / 'exp_a' / '.DS_Store').write_text('')   # macOS clutter
        self.save('exp_a')
        self.assertEqual(self.register_ids(), ['exp_a'])

    def test_id_in_register_is_refused_even_if_folder_was_deleted(self):
        self.save('exp_a')
        for f in (self.root / 'outputs' / 'exp_a').iterdir():
            f.unlink()
        with self.assertRaises(ExperimentExistsError):
            self.save('exp_a')

    def test_experiment_record_contains_reproduction_details(self):
        self.save('exp_a')
        record = json.loads((self.root / 'outputs/exp_a/experiment.json').read_text())
        self.assertEqual(record['source_sha256'], source_fingerprint(self.root))
        self.assertIn('--config configs/x.json', record['command'])
        self.assertEqual(record['config'], {'experiment_id': 'exp_a'})

    def test_fingerprint_changes_when_code_changes(self):
        before = source_fingerprint(self.root)
        (self.root / 'src' / 'mod.py').write_text('x = 2\n')
        self.assertNotEqual(before, source_fingerprint(self.root))

    def test_empty_table_keeps_known_headers(self):
        self.save('exp_a')
        header = (self.root / 'outputs/exp_a/orders.csv').read_text().splitlines()[0]
        self.assertTrue(header.startswith('order_id,episode_id,leg,side'))

    def test_write_csv_without_rows_or_fields(self):
        path = self.root / 'empty.csv'
        write_csv(path, [])
        self.assertEqual(path.read_text().strip(), 'status')


if __name__ == '__main__':
    unittest.main()
