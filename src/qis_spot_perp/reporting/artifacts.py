"""Persist replay tables, quality reports, and source/configuration provenance."""
import csv
import hashlib
import json
import sys
from pathlib import Path


def write_csv(path, rows, fields=None):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rows[0]) if rows else fields or ['status'])
        w.writeheader();w.writerows(rows)


def save_run(root, out, config_path, c, engine, quality, pressure):
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
    for p in sorted((root/'src').rglob('*.py')):
        code_hash.update(p.relative_to(root/'src').as_posix().encode()+p.read_bytes())
    record={'experiment_id':c['experiment_id'],'hypothesis':'Abnormally positive basis converges within 30 minutes',
            'phase':'development_debug','command':f'PYTHONPATH=src python3 -m qis_spot_perp.cli run --config {config_path}',
            'python':sys.version,'source_sha256':code_hash.hexdigest(),'source_hash_scheme':'relative_path_and_content_v2','config':c,'summary':summary,
            'data_manifest':'data/manifests/downloads.json'}
    (out/'experiment.json').write_text(json.dumps(record,indent=2,ensure_ascii=False))
    with (root/'outputs/experiment_register.jsonl').open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    return summary
