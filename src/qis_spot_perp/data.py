"""Streaming readers; no extraction of untrusted archive paths."""
import csv
import hashlib
import io
import json
import tarfile
import zipfile
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from .features import trade_pressure


def utc_ms(value):
    return int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp()*1000)


def archive_dates(start_ms, end_ms, module):
    tz = timezone.utc if module in (4,5,6) else timezone(timedelta(hours=8))
    first = datetime.fromtimestamp(start_ms/1000,tz).date()
    last = datetime.fromtimestamp((end_ms-1)/1000,tz).date()
    return [(first+timedelta(days=i)).isoformat() for i in range((last-first).days+1)]


def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()


def book_events(path, leg, start, end, stats):
    stats.update(rows=0, snapshots=0, missing_sequence=0, timestamp_regressions=0, max_intermessage_gap_ms=0,
                 first_ms=None, last_ms=None, scope="requested prefix only", source_file=str(path))
    previous = -1
    with tarfile.open(path,"r|gz") as archive:
        for member in archive:
            if not member.isfile(): continue
            if member.size > 5_000_000_000: raise ValueError("uncompressed member exceeds limit")
            if not member.name.endswith(".data"): continue
            with archive.extractfile(member) as f:
                for line in f:
                    event=json.loads(line)
                    ts=int(event["ts"])
                    if ts >= end: return
                    if ts < previous:
                        stats["timestamp_regressions"]+=1
                        raise ValueError("archive timestamp regression: cannot heap-merge unsorted data")
                    if previous >= 0:
                        stats['max_intermessage_gap_ms']=max(stats['max_intermessage_gap_ms'],ts-previous)
                    previous=ts
                    stats["rows"]+=1
                    stats["snapshots"]+=event["action"]=="snapshot"
                    stats["missing_sequence"]+="seqId" not in event
                    stats["first_ms"] = ts if stats["first_ms"] is None else stats["first_ms"]
                    stats["last_ms"]=ts
                    # Include earlier rows so every update has its actual snapshot history.
                    yield ts, leg, event


def trades_summary(raw_dir, day, start, end, multiplier):
    results, minute_values = {}, defaultdict(lambda:[0.,0.])
    for leg, instrument, mult in (("spot","BTC-USDT",1.),("perp","BTC-USDT-SWAP",float(multiplier))):
        seen=set(); stats=dict(rows=0,duplicates=0,outside_target=0,first_ms=None,last_ms=None,
                               source_counts={},unknown_side=0)
        for date in archive_dates(start,end,1):
            p=Path(raw_dir)/f"{instrument}-trades-{date}.zip"
            with zipfile.ZipFile(p) as z:
                for name in z.namelist():
                    if not name.endswith('.csv'): continue
                    with z.open(name) as f:
                        for r in csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')):
                            if r['instrument_name'] != instrument: raise ValueError('unexpected instrument')
                            ts=int(r['created_time'])
                            if not start <= ts < end:
                                stats['outside_target']+=1;continue
                            key=r['trade_id']
                            if key in seen: stats['duplicates']+=1;continue
                            seen.add(key);stats['rows']+=1
                            stats['first_ms']=min(stats['first_ms'] or ts,ts)
                            stats['last_ms']=max(stats['last_ms'] or ts,ts)
                            source=r.get('source','unknown')
                            stats['source_counts'][source]=stats['source_counts'].get(source,0)+1
                            if r['side'] not in ('buy','sell'):
                                stats['unknown_side']+=1;continue
                            notional=float(r['size'])*mult*float(r['price'])
                            minute_values[leg,ts//60000][0 if r['side']=='buy' else 1]+=notional
        results[leg]=stats
    features=[]
    prev_relative=None
    for minute in range(start//60000,end//60000):
        s=minute_values['spot',minute]; p=minute_values['perp',minute]
        sp,pp=trade_pressure(*s),trade_pressure(*p)
        relative=None if sp is None or pp is None else pp-sp
        features.append(dict(available_exchange_ms=(minute+1)*60000, spot_tp=sp,perp_tp=pp,
                             relative_tp=relative,relative_decay=None if relative is None or prev_relative is None else prev_relative-relative,
                             spot_notional=sum(s),perp_notional=sum(p)))
        prev_relative=relative
    return results,features


def write_csv(path, rows, fields=None):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rows[0]) if rows else fields or ['status'])
        w.writeheader();w.writerows(rows)


def provenance(root):
    root=Path(root); files=[]
    for manifest in sorted((root/'data/manifests').glob('okx-*.json')):
        obj=json.loads(manifest.read_text())
        for data in obj.get('data',[]):
            for detail in data.get('details',[]):
                for group in detail.get('groupDetails',[]):
                    p=root/'data/raw'/group['filename']
                    files.append({**group,'local_path':str(p.relative_to(root)),
                                  'local_file_completed_utc':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat() if p.exists() else None,
                                  'bytes':p.stat().st_size if p.exists() else None,
                                  'sha256':sha256(p) if p.exists() else None,
                                  'retrieval_manifest':str(manifest.relative_to(root))})
    result={'checked_client_date':'2026-10-30','files':files,
            'hash_note':'local SHA256 fingerprint; not an exchange-published checksum',
            'download_tool':'curl --fail --max-time 180 --max-filesize 500000000',
            'total_bytes':sum(x['bytes'] or 0 for x in files)}
    (root/'data/manifests/downloads.json').write_text(json.dumps(result,indent=2))
    return result
