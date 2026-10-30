import argparse
import hashlib
import heapq
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from .book import matched_units
from .data import book_events, provenance, trades_summary, write_csv
from .replay import Replay


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
    tq,pressure=trades_summary(root/'data/raw',c['date'],c['start_ms'],c['end_ms'],multiplier)
    quality['trades']=tq
    quality['sequence_integrity']='UNVERIFIABLE: seqId/prevSeqId absent in source archive'
    quality['receiver_latency']='missing: scenarios only'
    from datetime import datetime,timezone
    quality['processed_window_utc']=[datetime.fromtimestamp(c[k]/1000,timezone.utc).isoformat() for k in ('start_ms','end_ms')]
    quality['unprocessed_remainder']='Raw full-day books downloaded; remainder not inspected in this experiment'
    quality['decision_rejections']=dict(engine.rejects)
    quality['book_update_status']=dict(engine.book_health)
    for name,rows in [('features',engine.features),('orders',engine.orders),('fills',engine.fills),
                      ('trades',engine.trades),('equity',engine.equity),('states',engine.states),('pressure',pressure)]:
        fields=list(dict.fromkeys(k for r in rows for k in r))
        if not fields:
            fields={'orders':['order_id','episode_id','leg','side','quantity_btc','send_ms','arrival_ms','status'],
                    'fills':['order_id','leg','side','quantity_btc','price','fee_usdt','fill_ms','report_ms'],
                    'trades':['episode_id','decision_ms','exit_report_ms','gross_fill_usdt','fees_usdt','funding_usdt','net_usdt','status'],
                    'states':['ts','state','reason']}.get(name,['status'])
        write_csv(out/f'{name}.csv',rows,fields)
    summary=engine.summary()
    (out/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
    (out/'data_quality_report.json').write_text(json.dumps(quality,indent=2,ensure_ascii=False))
    (out/'config.json').write_text(json.dumps(c,indent=2))
    code_hash=hashlib.sha256()
    for p in sorted((root/'src').rglob('*.py')):code_hash.update(p.name.encode()+p.read_bytes())
    record={'experiment_id':c['experiment_id'],'hypothesis':'Abnormally positive basis converges within 30 minutes',
            'phase':'development_debug','command':f'PYTHONPATH=src python3 -m qis_spot_perp.cli run --config {config_path}',
            'python':sys.version,'source_sha256':code_hash.hexdigest(),'config':c,'summary':summary,
            'data_manifest':'data/manifests/downloads.json'}
    (out/'experiment.json').write_text(json.dumps(record,indent=2,ensure_ascii=False))
    with (root/'outputs/experiment_register.jsonl').open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    print(json.dumps(summary,indent=2,ensure_ascii=False))


def main():
    p=argparse.ArgumentParser(description='QIS public-data research only')
    p.add_argument('command',choices=['manifest','run'])
    p.add_argument('--config',default='configs/debug.json')
    a=p.parse_args();root=Path.cwd()
    if a.command=='manifest': print(json.dumps(provenance(root),indent=2))
    else:run(root,a.config)


if __name__=='__main__':main()
