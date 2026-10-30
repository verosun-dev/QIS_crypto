import unittest
from decimal import Decimal as D
from qis_spot_perp.data.orderbook import Book
from qis_spot_perp.execution.taker import sweep
from qis_spot_perp.core.instruments import matched_units
from tests.fixtures.market import event


class ExecutionTests(unittest.TestCase):
    def test_vwap_and_partial(self):
        b=Book();e=event(0,'99999','100000','.02');e['asks'].append(['100010','.03']);b.apply(e)
        fills,left=sweep(b,'buy','.05')
        self.assertEqual(sum(p*q for p,q in fills)/D('.05'),D(100006));self.assertEqual(left,0)
        fills,left=sweep(b,'buy','.01');self.assertEqual(left,D('.01'));self.assertFalse(fills)

    def test_contract_multiplier(self):
        s={'baseCcy':'BTC','quoteCcy':'USDT','minSz':'.00001','lotSz':'.00000001'}
        p={'ctType':'linear','ctValCcy':'BTC','settleCcy':'USDT','ctVal':'.01','ctMult':'1','minSz':'.01','lotSz':'.01'}
        self.assertEqual(matched_units('.01',s,p)[1],D(1))
        with self.assertRaises(ValueError):matched_units('.000001',s,p)
