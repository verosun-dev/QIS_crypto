import unittest

from qis_spot_perp.features.basis import Features


class BasisTests(unittest.TestCase):
    def test_basis_sign_and_units(self):
        for perp, expected in [(101, 100), (100, 0), (99, -100)]:
            with self.subTest(perp=perp):
                result=Features(3000).update(0,100,perp)
                self.assertAlmostEqual(result['basis_bps'],expected)

    def test_preceding_median_excludes_current_point(self):
        for previous, expected_median in [([100,102,104],200), ([100,102,104,106],300)]:
            with self.subTest(previous=previous):
                features=Features(len(previous)*1000)
                for i, perp in enumerate(previous):features.update(i*1000,100,perp)
                result=features.update(len(previous)*1000,100,150)
                self.assertTrue(result['warm'])
                self.assertAlmostEqual(result['excess_bps'],5000-expected_median)

    def test_first_warmup_boundary_and_rolling_expiration(self):
        features=Features(3000)
        for i, perp in enumerate([100,102,104]):
            result=features.update(i*1000,100,perp)
            self.assertFalse(result['warm'])
            self.assertIsNone(result['excess_bps'])
        result=features.update(3000,100,106)
        self.assertTrue(result['warm'])
        self.assertAlmostEqual(result['excess_bps'],400)
        result=features.update(4000,100,108)
        self.assertTrue(result['warm'])
        self.assertAlmostEqual(result['excess_bps'],400)

    def test_missing_grid_point_blocks_until_it_expires(self):
        features=Features(3000)
        for t in [0,1000,3000,4000,5000]:
            result=features.update(t,100,101)
            self.assertFalse(result['warm'])
            self.assertIsNone(result['excess_bps'])
        result=features.update(6000,100,101)
        self.assertTrue(result['warm'])
        self.assertAlmostEqual(result['excess_bps'],0)

    def test_momentum_requires_a_full_sixty_second_lag(self):
        features=Features(120000)
        for t in range(0,60000,1000):
            result=features.update(t,100,100+t/100000)
            self.assertIsNone(result['momentum_60s_bps'])
        result=features.update(60000,100,101)
        self.assertAlmostEqual(result['momentum_60s_bps'],100)

    def test_momentum_uses_exact_lag_and_preserves_sign(self):
        features=Features(120000)
        features.update(0,100,100)
        features.update(1000,100,103)
        result=features.update(60000,100,102)
        self.assertAlmostEqual(result['momentum_60s_bps'],200)
        result=features.update(61000,100,101)
        self.assertAlmostEqual(result['momentum_60s_bps'],-200)

    def test_missing_exact_lag_does_not_use_an_older_sample(self):
        features=Features(120000)
        features.update(0,100,100)
        features.update(1000,100,101)
        result=features.update(62000,100,103)
        self.assertIsNone(result['momentum_60s_bps'])

    def test_momentum_is_independent_of_short_median_window(self):
        features=Features(3000)
        for t in range(0,61000,1000):features.update(t,100,100+t/100000)
        result=features.update(61000,100,102)
        self.assertTrue(result['warm'])
        self.assertIsNotNone(result['momentum_60s_bps'])
        self.assertAlmostEqual(result['momentum_60s_bps'],199)

    def test_future_observations_do_not_change_prior_features(self):
        def calculate(future_perp):
            features=Features(3000)
            return [features.update(t,100,100 if t<62000 else future_perp)
                    for t in range(0,65000,1000)]
        self.assertEqual(calculate(101)[:62],calculate(110)[:62])

    def test_full_day_warmup_boundary(self):
        features=Features(86400000)
        for t in range(0,86400000,1000):
            result=features.update(t,100,101)
            self.assertFalse(result['warm'])
            self.assertIsNone(result['excess_bps'])
        result=features.update(86400000,100,101)
        self.assertTrue(result['warm'])
        self.assertAlmostEqual(result['excess_bps'],0)
