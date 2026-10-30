import unittest

from qis_spot_perp.strategies.basis_threshold import entry_rejection


class BasisThresholdTests(unittest.TestCase):
    def test_threshold_is_inclusive_but_basis_must_be_positive(self):
        self.assertIsNone(entry_rejection({'basis_bps': 3, 'excess_bps': 2}, 2, True))
        self.assertEqual(
            entry_rejection({'basis_bps': 0, 'excess_bps': 2}, 2, True),
            'nonpositive_basis',
        )
        self.assertEqual(
            entry_rejection({'basis_bps': 3, 'excess_bps': 1.99}, 2, True),
            'below_threshold',
        )

    def test_warmup_precedes_other_rejection_reasons(self):
        self.assertEqual(
            entry_rejection({'basis_bps': -1, 'excess_bps': None}, 2, False),
            'warmup_incomplete',
        )

    def test_eligible_signal_requires_a_reset_episode(self):
        self.assertEqual(
            entry_rejection({'basis_bps': 3, 'excess_bps': 2}, 2, False),
            'episode_not_reset',
        )
