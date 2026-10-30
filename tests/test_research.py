import copy
import json
import unittest
from decimal import Decimal as D
from pathlib import Path
import tempfile
import zipfile
from qis_spot_perp.accounting import Account, paired_gross, funding_in_interval
from qis_spot_perp.book import Book,matched_units
from qis_spot_perp.data import archive_dates,utc_ms,trades_summary
from qis_spot_perp.features import Features,trade_pressure,purged_split
from qis_spot_perp.replay import Replay


def event(ts,bid='100',ask='101',size='1',action='snapshot',seq=1,prev=-1):
    return dict(ts=str(ts),bids=[[bid,size]],asks=[[ask,size]],action=action,seqId=seq,prevSeqId=prev)


class ResearchTests(unittest.TestCase):
    def test_teaching_pnl(self):
        self.assertEqual(paired_gross('.01','100000','100300','101000','101100'),D(2))
        self.assertEqual(paired_gross('.01','100000','100300','101000','101300'),0)

    def test_book_absolute_delete_and_gap_recovery(self):
        b=Book();b.apply(event(0,size='2'))
        b.apply(event(1,size='3',action='update',seq=8,prev=1))
        self.assertEqual(b.bids[D(100)],3)
        b.apply(dict(ts='2',bids=[['100','0']],asks=[],action='update',seqId=9,prevSeqId=8))
        self.assertFalse(b.bids)
        self.assertEqual(b.apply(event(3,action='update',seq=11,prev=10)),'sequence_gap')
        self.assertFalse(b.valid)
        b.apply(event(4));self.assertTrue(b.valid)

    def test_heartbeat_duplicate_and_reset(self):
        b=Book();snap=event(0);b.apply(snap)
        self.assertEqual(b.apply(snap),'duplicate')
        b.apply(dict(ts='1',bids=[],asks=[],action='update',seqId=1,prevSeqId=1))
        b.apply(event(2,action='update',seq=0,prev=1))
        self.assertTrue(b.valid);self.assertEqual(b.seq,0)

    def test_missing_sequence_not_verified(self):
        e=event(0);e.pop('seqId');e.pop('prevSeqId')
        b=Book();b.apply(e);self.assertFalse(b.valid)
        b=Book(allow_unsequenced=True);b.apply(e)
        self.assertTrue(b.valid);self.assertFalse(b.sequence_verified)

    def test_vwap_and_partial(self):
        b=Book();e=event(0,'99999','100000','.02');e['asks'].append(['100010','.03']);b.apply(e)
        fills,left=b.sweep('buy','.05')
        self.assertEqual(sum(p*q for p,q in fills)/D('.05'),D(100006));self.assertEqual(left,0)
        fills,left=b.sweep('buy','.01');self.assertEqual(left,D('.01'));self.assertFalse(fills)

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

    def test_future_data_does_not_change_features(self):
        def calc(future):
            f=Features(3000)
            return [f.update(t*1000,100,100 if t<5 else future) for t in range(8)]
        self.assertEqual(calc(110)[:5],calc(200)[:5])
        self.assertFalse(calc(110)[2]['warm']);self.assertTrue(calc(110)[3]['warm'])

    def test_missing_feature_window_blocks_warmup(self):
        f=Features(3000)
        for t in [0,1000,3000]:r=f.update(t,100,101)
        self.assertFalse(r['warm'])

    def test_utc8_file_boundary(self):
        s,e=utc_ms('2026-10-23'),utc_ms('2026-10-24')
        self.assertEqual(archive_dates(s,e,1),['2026-10-23','2026-10-24'])
        self.assertEqual(archive_dates(s,e,4),['2026-10-23'])

    def test_pressure_and_purge(self):
        self.assertEqual(trade_pressure(8,2),.6);self.assertIsNone(trade_pressure(0,0))
        self.assertEqual(purged_split([{'decision_ms':5,'label_end_ms':15}],10),[])

    def test_distinct_trade_ids_at_same_timestamp_retained(self):
        start=utc_ms('2026-10-23');end=start+1000
        with tempfile.TemporaryDirectory() as directory:
            for instrument in ['BTC-USDT','BTC-USDT-SWAP']:
                header='instrument_name,trade_id,side,price,size,created_time,source\n'
                row=f'{instrument},1,buy,100,1,{start},0\n'
                other=f'{instrument},2,sell,100,1,{start},0\n'
                with zipfile.ZipFile(Path(directory)/f'{instrument}-trades-2026-10-23.zip','w') as z:
                    z.writestr('trades.csv',header+row+other+row)
            quality,_=trades_summary(directory,'2026-10-23',start,end,'.01')
        self.assertEqual(quality['spot']['rows'],2)
        self.assertEqual(quality['spot']['duplicates'],1)

    def test_contract_multiplier(self):
        s={'baseCcy':'BTC','quoteCcy':'USDT','minSz':'.00001','lotSz':'.00000001'}
        p={'ctType':'linear','ctValCcy':'BTC','settleCcy':'USDT','ctVal':'.01','ctMult':'1','minSz':'.01','lotSz':'.01'}
        self.assertEqual(matched_units('.01',s,p)[1],D(1))
        with self.assertRaises(ValueError):matched_units('.000001',s,p)

    def config(self):
        c=json.loads(Path('configs/debug.json').read_text())
        c.update(start_ms=0,end_ms=10000,entry_start_ms=2000,entry_end_ms=4000,
                 lookback_seconds=2,holding_ms=2000,q_btc='.01',threshold_bps=1,
                 max_stale_ms=2000,max_pair_loss_usdt='100',feed_latency_ms=100,
                 order_latency_ms=150,report_latency_ms=300,data_kind='SYNTHETIC_TEST_ONLY')
        return c

    def market(self,partial=False):
        for t in range(0,10000,100):
            yield t,'spot',event(t,'100','100.1',size='.006' if partial and t==3200 else '1')
            yield t,'perp',event(t,'100.1' if t<2500 or t>5500 else '101','101.1' if 2500<=t<=5500 else '100.2')

    def test_latency_report_and_holding(self):
        r=Replay(self.config(),'1').run(self.market())
        self.assertEqual(len(r.trades),1)
        for f in r.fills:self.assertEqual(f['report_ms']-f['fill_ms'],300)
        self.assertEqual(r.orders[0]['arrival_ms']-r.orders[0]['send_ms'],150)
        entry_reports=[x for x in r.states if x['state']=='HEDGED']
        self.assertEqual(entry_reports[0]['ts'],r.orders[1]['report_ms'])
        self.assertFalse(any(r.actual.positions.values()))

    def test_arrival_uses_changed_quote(self):
        r=Replay(self.config(),'1')
        r.exchange['spot'].apply(event(0,'100','101'))
        r.send(0,'spot','buy',D('.01'),'test')
        r.exchange['spot'].apply(event(100,'110','111'))
        r.arrive(150,r.orders[0])
        self.assertEqual(r.fills[0]['price'],'111')
        self.assertEqual(r.known.positions['spot'],0)

    def test_partial_recovery_preserves_costs(self):
        c=self.config();c['order_latency_ms']=200
        r=Replay(c,'1').run(self.market(partial=True))
        self.assertTrue(any(o['status']=='PARTIAL_IOC' for o in r.orders))
        self.assertTrue(any(x['state']=='RECOVERY' for x in r.states))
        self.assertFalse(any(r.actual.positions.values()))
        self.assertGreater(r.actual.fees,0)
        ledger=sum(((-1 if x['side']=='buy' else 1)*D(x['quantity_btc'])*D(x['price'])-D(x['fee_usdt']) for x in r.fills),D(0))
        self.assertEqual(ledger,r.actual.cash_pnl)

    def test_end_position_is_reported(self):
        c=self.config();c['end_ms']=4000
        r=Replay(c,'1').run(x for x in self.market() if x[0]<4000)
        self.assertEqual(r.summary()['status'],'INCOMPLETE')
        self.assertNotEqual(r.summary()['end_positions']['spot'],'0')

    def test_funding_not_used_as_predictor(self):
        a=Replay(self.config(),'1',[{'fundingTime':'5000','realizedRate':'.1'}]).run(self.market())
        b=Replay(self.config(),'1',[{'fundingTime':'5000','realizedRate':'-.5'}]).run(self.market())
        self.assertEqual(a.orders,b.orders)
        self.assertEqual(a.summary()['orders'],0)


if __name__=='__main__':unittest.main()
