import unittest
from decimal import Decimal as D
from qis_spot_perp.backtest.accounting import Account, paired_gross
from qis_spot_perp.risk.controls import funding_in_interval


class AccountingTests(unittest.TestCase):
    def test_teaching_pnl(self):
        self.assertEqual(paired_gross('.01','100000','100300','101000','101100'),D(2))
        self.assertEqual(paired_gross('.01','100000','100300','101000','101300'),0)

    def test_static_market_fees_not_double_spread(self):
        a=Account()
        for leg,side,px,fee in [('spot','buy','101','10'),('perp','sell','100','5'),
                                ('spot','sell','100','10'),('perp','buy','101','5')]:
            a.fill(leg,side,1,px,fee)
        self.assertEqual(a.cash_pnl,D('-2.3015'))
        self.assertFalse(any(a.positions.values()))

    def test_funding_sign_and_actual_quantity(self):
        a=Account();self.assertEqual(a.settle_funding('.01','100'),0)
        a.fill('perp','sell','.4','100',0)
        self.assertEqual(a.settle_funding('.01','120'),D('.48'))
        self.assertEqual(a.settle_funding('-.01','120'),D('-.48'))
        self.assertTrue(funding_in_interval(1,10,[{'fundingTime':'10'}]))
