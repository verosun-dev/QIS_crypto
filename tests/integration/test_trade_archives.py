import unittest
from decimal import Decimal as D
import tempfile
import zipfile
from pathlib import Path
from qis_spot_perp.data.archives import utc_ms
from qis_spot_perp.data.trades import read_trade_notionals


class TradeArchiveTests(unittest.TestCase):
    def test_distinct_trade_ids_at_same_timestamp_retained(self):
        start=utc_ms('2026-10-23');end=start+1000
        with tempfile.TemporaryDirectory() as directory:
            for instrument in ['BTC-USDT','BTC-USDT-SWAP']:
                header='instrument_name,trade_id,side,price,size,created_time,source\n'
                row=f'{instrument},1,buy,100,1,{start},0\n'
                other=f'{instrument},2,sell,100,1,{start},0\n'
                with zipfile.ZipFile(Path(directory)/f'{instrument}-trades-2026-10-23.zip','w') as z:
                    z.writestr('trades.csv',header+row+other+row)
            quality,_=read_trade_notionals(directory,start,end,'.01')
        self.assertEqual(quality['spot']['rows'],2)
        self.assertEqual(quality['spot']['duplicates'],1)
