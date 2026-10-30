import unittest
from decimal import Decimal as D
from qis_spot_perp.data.archives import archive_dates, utc_ms


class ArchiveDateTests(unittest.TestCase):
    def test_utc8_file_boundary(self):
        s,e=utc_ms('2026-10-23'),utc_ms('2026-10-24')
        self.assertEqual(archive_dates(s,e,1),['2026-10-23','2026-10-24'])
        self.assertEqual(archive_dates(s,e,4),['2026-10-23'])
