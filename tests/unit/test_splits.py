import unittest
from copy import deepcopy

from qis_spot_perp.evaluation.splits import purged_split


class PurgedSplitTests(unittest.TestCase):
    def test_keeps_outcomes_completed_before_boundary(self):
        events = [
            {'id': 'early', 'decision_ms': 1, 'label_end_ms': 4},
            {'id': 'last_millisecond', 'decision_ms': 5, 'label_end_ms': 9},
        ]
        self.assertEqual(purged_split(events, 10), events)

    def test_excludes_outcomes_touching_or_crossing_boundary(self):
        events = [
            {'id': 'before', 'decision_ms': 5, 'label_end_ms': 9},
            {'id': 'touches', 'decision_ms': 5, 'label_end_ms': 10},
            {'id': 'crosses', 'decision_ms': 5, 'label_end_ms': 11},
        ]
        self.assertEqual([e['id'] for e in purged_split(events, 10)], ['before'])

    def test_excludes_decisions_at_or_after_boundary(self):
        events = [
            {'decision_ms': 10, 'label_end_ms': 10},
            {'decision_ms': 10, 'label_end_ms': 12},
            {'decision_ms': 11, 'label_end_ms': 12},
        ]
        self.assertEqual(purged_split(events, 10), [])

    def test_empty_input(self):
        self.assertEqual(purged_split([], 10), [])

    def test_accepts_generator(self):
        events = ({'decision_ms': t, 'label_end_ms': t + 2} for t in (1, 8, 11))
        self.assertEqual(purged_split(events, 10), [{'decision_ms': 1, 'label_end_ms': 3}])

    def test_preserves_input_order_and_records(self):
        events = [
            {'id': 'later', 'decision_ms': 6, 'label_end_ms': 8, 'details': {'value': 1}},
            {'id': 'crossing', 'decision_ms': 4, 'label_end_ms': 12},
            {'id': 'earlier', 'decision_ms': 1, 'label_end_ms': 3},
        ]
        original = deepcopy(events)
        selected = purged_split(events, 10)
        self.assertEqual([e['id'] for e in selected], ['later', 'earlier'])
        self.assertEqual(events, original)
        self.assertIs(selected[0], events[0])
        self.assertIs(selected[1], events[2])
