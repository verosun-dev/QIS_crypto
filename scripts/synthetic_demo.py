"""Deterministic synthetic integration trace. Never an empirical strategy result."""
import json
from pathlib import Path
from qis_spot_perp.backtest.engine import Replay
from qis_spot_perp.reporting.artifacts import write_csv


def main():
    c=json.loads(Path('configs/debug.json').read_text())
    c.update(experiment_id='synthetic_demo',data_kind='SYNTHETIC_TEACHING_ONLY',
             start_ms=0,end_ms=10000,entry_start_ms=2000,entry_end_ms=4000,
             lookback_seconds=2,holding_ms=2000,q_btc='.01',threshold_bps=1,
             max_pair_loss_usdt='100')
    def market():
        for t in range(0,10000,100):
            for leg,bid,ask in [('spot','100000','100001'),
                ('perp','100020' if t<2500 or t>5500 else '100300',
                 '100021' if t<2500 or t>5500 else '100301')]:
                yield t,leg,dict(ts=str(t),action='snapshot',bids=[[bid,'1']],asks=[[ask,'1']],seqId=t,prevSeqId=-1)
    r=Replay(c,'1').run(market())
    out=Path('outputs/synthetic_demo');out.mkdir(parents=True,exist_ok=True)
    for name,rows in [('orders',r.orders),('fills',r.fills),('trades',r.trades),('states',r.states),('equity',r.equity)]:
        fields=list(dict.fromkeys(k for row in rows for k in row))
        write_csv(out/f'{name}.csv',rows,fields)
    (out/'config.json').write_text(json.dumps(c,indent=2))
    (out/'summary.json').write_text(json.dumps(r.summary(),indent=2))
    (out/'README.md').write_text('# Synthetic teaching example\n\nArtificial prices and a two-second holding period are used only to check state transitions and accounting. These are not historical observations, evidence of backtest profitability, or proof of executable fills.\n')
    print(json.dumps(r.summary(),indent=2))


if __name__=='__main__':main()
