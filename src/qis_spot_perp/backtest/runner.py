"""Connect the configured OKX debug dataset, replay engine, and saved artifacts."""
import heapq
import json
from decimal import Decimal
from pathlib import Path
from ..core.instruments import matched_units
from ..data.archives import book_events
from ..data.trades import read_trade_notionals
from ..features.order_flow import pressure_rows
from ..reporting.artifacts import save_run
from .engine import Replay


def run(root,config_path):
    c=json.loads(Path(config_path).read_text())
    out=root/'outputs'/c['experiment_id'];out.mkdir(parents=True,exist_ok=True)
    spot=json.loads((root/'data/manifests/okx-spot-spec.json').read_text())['data'][0]
    perp=json.loads((root/'data/manifests/okx-swap-spec.json').read_text())['data'][0]
    matched_units(c['q_btc'],spot,perp)
    multiplier=str(Decimal(perp['ctVal'])*Decimal(perp.get('ctMult') or '1'))
    funding=json.loads((root/'data/manifests/okx-funding.json').read_text())
    if funding.get('code')!='0' or not funding.get('data'):
        raise ValueError('funding schedule unavailable; fail closed')
    quality={};streams=[]
    for leg,instrument in [('spot','BTC-USDT'),('perp','BTC-USDT-SWAP')]:
        quality[leg]={}
        path=root/'data/raw'/f"{instrument}-L2orderbook-400lv-{c['date']}.tar.gz"
        streams.append(book_events(path,leg,c['start_ms'],c['end_ms'],quality[leg]))
    print('Replaying original archive events; bounded to requested prefix.',flush=True)
    engine=Replay(c,multiplier,funding['data']).run(heapq.merge(*streams,key=lambda x:(x[0],x[1])))
    print('Replay complete; aggregating trade pressure.',flush=True)
    tq,notionals=read_trade_notionals(root/'data/raw',c['start_ms'],c['end_ms'],multiplier)
    pressure=pressure_rows(notionals,c['start_ms'],c['end_ms'])
    quality['trades']=tq
    quality['sequence_integrity']='UNVERIFIABLE: seqId/prevSeqId absent in source archive'
    quality['receiver_latency']='missing: scenarios only'
    from datetime import datetime,timezone
    quality['processed_window_utc']=[datetime.fromtimestamp(c[k]/1000,timezone.utc).isoformat() for k in ('start_ms','end_ms')]
    quality['unprocessed_remainder']='Raw full-day books downloaded; remainder not inspected in this experiment'
    quality['decision_rejections']=dict(engine.rejects)
    quality['book_update_status']=dict(engine.book_health)
    summary=save_run(root,out,config_path,c,engine,quality,pressure)
    print(json.dumps(summary,indent=2,ensure_ascii=False))
