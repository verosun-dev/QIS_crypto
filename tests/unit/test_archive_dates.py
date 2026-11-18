import unittest
from decimal import Decimal as D
from qis_spot_perp.data.archives import archive_dates, utc_ms


class ArchiveDateTests(unittest.TestCase):
    def test_iso_offsets_identify_the_same_instant(self):
        expected_ms = utc_ms('2026-10-23T16:00:00.125')
        for value in ('2026-10-24T00:00:00.125+08:00', '2026-10-23T12:00:00.125-04:00'):
            with self.subTest(value=value):
                self.assertEqual(utc_ms(value), expected_ms)

    def test_empty_or_reversed_interval_has_no_archive_dates(self):
        start = utc_ms('2026-10-23T12:00:00')
        for module in (1, 4):
            for end in (start, start - 1):
                with self.subTest(module=module, end=end):
                    self.assertEqual(archive_dates(start, end, module), [])

    def test_one_millisecond_at_trade_archive_midnight(self):
        midnight = utc_ms('2026-10-24T00:00:00+08:00')
        self.assertEqual(archive_dates(midnight - 1, midnight, 1), ['2026-10-23'])
        self.assertEqual(archive_dates(midnight, midnight + 1, 1), ['2026-10-24'])
        self.assertEqual(archive_dates(midnight, midnight + 1, 4), ['2026-10-23'])

    def test_utc8_file_boundary(self):
        s,e=utc_ms('2026-10-23'),utc_ms('2026-10-24')
        self.assertEqual(archive_dates(s,e,1),['2026-10-23','2026-10-24'])
        self.assertEqual(archive_dates(s,e,4),['2026-10-23'])
