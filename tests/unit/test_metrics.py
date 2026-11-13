"""Hand-checked tests for evaluation.metrics.summarize.

Each test builds a tiny fake engine with made-up trades, works out the expected
answer by hand (shown in the comments), and checks the code agrees.
"""
import unittest
from decimal import Decimal as D
from types import SimpleNamespace

from qis_spot_perp.evaluation.metrics import summarize


def fake_engine(trades=(), equity=(), positions=None, pending=(), unknown_funding=False,
                fees='0', funding='0', initial_capital='1500'):
    """Smallest stand-in with every attribute summarize() reads.

    trades: (gross_fill_usdt, net_usdt) pairs.  equity: account values over time.
    """
    return SimpleNamespace(
        c={'initial_capital_usdt': initial_capital, 'data_kind': 'synthetic_test'},
        trades=[{'gross_fill_usdt': g, 'net_usdt': n} for g, n in trades],
        equity=[{'equity_usdt': e} for e in equity],
        pending=set(pending),
        actual=SimpleNamespace(positions=positions or {'spot': D(0), 'perp': D(0)},
                               fees=D(fees), funding=D(funding)),
        unknown_funding=unknown_funding,
        episode=len(trades), orders=[], fills=[],
        state='FLAT', rejects={}, book_health={},
    )


class MetricsTests(unittest.TestCase):
    def test_hand_calculated_three_trades(self):
        # Net +2, -1, +0.5 (gross 5, 1, 2). Equity 1500 -> 1502 -> 1501 -> 1501.5.
        s = summarize(fake_engine(trades=[('5', '2'), ('1', '-1'), ('2', '0.5')],
                                  equity=['1502', '1501', '1501.5'], fees='5.5'))
        self.assertEqual(s['status'], 'COMPLETED_DEBUG')
        self.assertEqual(s['incomplete_reasons'], [])
        self.assertEqual(s['closed_trades'], 3)
        self.assertEqual(D(s['gross_fill_usdt']), D('8'))              # 5 + 1 + 2
        self.assertEqual(D(s['fees_usdt']), D('5.5'))
        self.assertEqual(D(s['closed_net_usdt']), D('1.5'))            # 2 - 1 + 0.5
        self.assertEqual(D(s['return_on_total_capital']), D('0.001'))  # 1.5 / 1500
        self.assertAlmostEqual(s['win_rate'], 2 / 3)                   # 2 of 3 trades > 0
        self.assertEqual(D(s['worst_trade_usdt']), D('-1'))
        self.assertEqual(D(s['max_drawdown_usdt']), D('1'))            # peak 1502 - 1501

    def test_no_trades_does_not_crash(self):
        s = summarize(fake_engine())
        self.assertEqual(s['status'], 'COMPLETED_DEBUG')
        self.assertEqual(s['closed_trades'], 0)
        self.assertIsNone(s['win_rate'])          # no trades: undefined, not 0%
        self.assertIsNone(s['worst_trade_usdt'])
        self.assertEqual(D(s['closed_net_usdt']), D(0))
        self.assertEqual(D(s['max_drawdown_usdt']), D(0))

    def test_open_position_is_reported_incomplete(self):
        s = summarize(fake_engine(positions={'spot': D('0.01'), 'perp': D('-1')}))
        self.assertEqual(s['status'], 'INCOMPLETE')
        self.assertEqual(s['incomplete_reasons'], ['open position at end of data: perp, spot'])
        self.assertEqual(s['end_positions'], {'spot': '0.01', 'perp': '-1'})

    def test_one_open_leg_is_named(self):
        # Only the spot leg filled: the unhedged leg must be visible.
        s = summarize(fake_engine(positions={'spot': D('0.01'), 'perp': D(0)}))
        self.assertEqual(s['incomplete_reasons'], ['open position at end of data: spot'])

    def test_pending_order_is_reported_incomplete(self):
        s = summarize(fake_engine(pending=['order-7']))
        self.assertEqual(s['status'], 'INCOMPLETE')
        self.assertEqual(s['incomplete_reasons'], ['1 order(s) still pending at end of data'])
        self.assertEqual(s['pending_orders'], ['order-7'])

    def test_unknown_funding_hides_net_results(self):
        s = summarize(fake_engine(trades=[('3', '1')], unknown_funding=True))
        self.assertEqual(s['status'], 'INCOMPLETE')
        self.assertIn('a funding settlement could not be valued', s['incomplete_reasons'])
        self.assertIsNone(s['funding_usdt'])
        self.assertIsNone(s['closed_net_usdt'])
        self.assertIsNone(s['return_on_total_capital'])
        self.assertEqual(D(s['gross_fill_usdt']), D('3'))  # gross is still known

    def test_every_reason_is_listed(self):
        s = summarize(fake_engine(positions={'spot': D('0.01'), 'perp': D(0)},
                                  pending=['a', 'b'], unknown_funding=True))
        self.assertEqual(len(s['incomplete_reasons']), 3)

    def test_breakeven_trade_is_not_a_win(self):
        s = summarize(fake_engine(trades=[('1', '1'), ('0.5', '0')]))
        self.assertEqual(s['win_rate'], 0.5)

    def test_drawdown_measured_from_starting_capital(self):
        # Equity never rises above 1500, so the peak is the starting capital.
        s = summarize(fake_engine(equity=['1498', '1497', '1499']))
        self.assertEqual(D(s['max_drawdown_usdt']), D('3'))           # 1500 - 1497

    def test_drawdown_keeps_the_largest_drop(self):
        # Two drops: 1510 -> 1505 (5), then 1520 -> 1512 (8). The answer is the larger.
        s = summarize(fake_engine(equity=['1510', '1505', '1520', '1512', '1530']))
        self.assertEqual(D(s['max_drawdown_usdt']), D('8'))


if __name__ == '__main__':
    unittest.main()
