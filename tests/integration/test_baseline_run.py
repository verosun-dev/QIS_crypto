import unittest
from decimal import Decimal as D
from qis_spot_perp.backtest.engine import Replay
from tests.fixtures.market import config, market, event


class BaselineRunTests(unittest.TestCase):
    def test_latency_report_and_holding(self):
        r=Replay(config(),'1').run(market())
        self.assertEqual(len(r.trades),1)
        for f in r.fills:self.assertEqual(f['report_ms']-f['fill_ms'],300)
        self.assertEqual(r.orders[0]['arrival_ms']-r.orders[0]['send_ms'],150)
        entry_reports=[x for x in r.states if x['state']=='HEDGED']
        self.assertEqual(entry_reports[0]['ts'],r.orders[1]['report_ms'])
        self.assertFalse(any(r.actual.positions.values()))

    def test_arrival_uses_changed_quote(self):
        r=Replay(config(),'1')
        r.exchange['spot'].apply(event(0,'100','101'))
        r.send(0,'spot','buy',D('.01'),'test')
        r.exchange['spot'].apply(event(100,'110','111'))
        r.arrive(150,r.orders[0])
        self.assertEqual(r.fills[0]['price'],'111')
        self.assertEqual(r.known.positions['spot'],0)

    def test_partial_recovery_preserves_costs(self):
        c=config();c['order_latency_ms']=200
        r=Replay(c,'1').run(market(partial=True))
        self.assertTrue(any(o['status']=='PARTIAL_IOC' for o in r.orders))
        self.assertTrue(any(x['state']=='RECOVERY' for x in r.states))
        self.assertFalse(any(r.actual.positions.values()))
        self.assertGreater(r.actual.fees,0)
        ledger=sum(((-1 if x['side']=='buy' else 1)*D(x['quantity_btc'])*D(x['price'])-D(x['fee_usdt']) for x in r.fills),D(0))
        self.assertEqual(ledger,r.actual.cash_pnl)

    def test_end_position_is_reported(self):
        c=config();c['end_ms']=4000
        r=Replay(c,'1').run(x for x in market() if x[0]<4000)
        self.assertEqual(r.summary()['status'],'INCOMPLETE')
        self.assertNotEqual(r.summary()['end_positions']['spot'],'0')

    def test_funding_not_used_as_predictor(self):
        a=Replay(config(),'1',[{'fundingTime':'5000','realizedRate':'.1'}]).run(market())
        b=Replay(config(),'1',[{'fundingTime':'5000','realizedRate':'-.5'}]).run(market())
        self.assertEqual(a.orders,b.orders)
        self.assertEqual(a.summary()['orders'],0)
