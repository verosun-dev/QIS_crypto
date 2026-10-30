"""Small deterministic market messages shared by unit and integration tests."""
import json
from pathlib import Path


def event(ts,bid='100',ask='101',size='1',action='snapshot',seq=1,prev=-1):
    return dict(ts=str(ts),bids=[[bid,size]],asks=[[ask,size]],action=action,seqId=seq,prevSeqId=prev)


def config():
    c=json.loads((Path(__file__).resolve().parents[2] / 'configs/debug.json').read_text())
    c.update(start_ms=0,end_ms=10000,entry_start_ms=2000,entry_end_ms=4000,
             lookback_seconds=2,holding_ms=2000,q_btc='.01',threshold_bps=1,
             max_stale_ms=2000,max_pair_loss_usdt='100',feed_latency_ms=100,
             order_latency_ms=150,report_latency_ms=300,data_kind='SYNTHETIC_TEST_ONLY')
    return c


def market(partial=False):
    for t in range(0,10000,100):
        yield t,'spot',event(t,'100','100.1',size='.006' if partial and t==3200 else '1')
        yield t,'perp',event(t,'100.1' if t<2500 or t>5500 else '101','101.1' if 2500<=t<=5500 else '100.2')
