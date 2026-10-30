"""Trade-ID deduplication and raw minute-notional aggregation."""
import csv
import io
import zipfile
from collections import defaultdict
from pathlib import Path
from .archives import archive_dates


def read_trade_notionals(raw_dir, start, end, multiplier):
    """Return quality counters and (leg, minute) buy/sell quote-notional buckets."""
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
    return results, minute_values
