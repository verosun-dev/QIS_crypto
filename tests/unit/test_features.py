import unittest
from decimal import Decimal as D
from qis_spot_perp.features.basis import Features
from qis_spot_perp.features.order_flow import trade_pressure, pressure_rows
from qis_spot_perp.evaluation.splits import purged_split


class FeatureTests(unittest.TestCase):
    def test_pressure_is_available_only_after_minute_closes(self):
        from collections import defaultdict

        buckets = defaultdict(lambda: [0., 0.])
        buckets['spot', 0] = [80., 20.]
        buckets['perp', 0] = [90., 10.]
        rows = pressure_rows(buckets, 0, 120000)
        self.assertEqual(rows[0]['available_exchange_ms'], 60000)
        self.assertAlmostEqual(rows[0]['relative_tp'], .2)
        self.assertEqual(rows[1]['available_exchange_ms'], 120000)
        self.assertIsNone(rows[1]['relative_tp'])
        self.assertIsNone(rows[1]['relative_decay'])

    def test_future_data_does_not_change_features(self):
        def calc(future):
            f=Features(3000)
            return [f.update(t*1000,100,100 if t<5 else future) for t in range(8)]
        self.assertEqual(calc(110)[:5],calc(200)[:5])
        self.assertFalse(calc(110)[2]['warm']);self.assertTrue(calc(110)[3]['warm'])

    def test_missing_feature_window_blocks_warmup(self):
        f=Features(3000)
        for t in [0,1000,3000]:r=f.update(t,100,101)
        self.assertFalse(r['warm'])

    def test_pressure_and_purge(self):
        self.assertEqual(trade_pressure(8,2),.6);self.assertIsNone(trade_pressure(0,0))
        self.assertEqual(purged_split([{'decision_ms':5,'label_end_ms':15}],10),[])
