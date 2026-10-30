"""UTC/archive calendars and streaming L2 reads; never extract archive paths."""
import json
import tarfile
from datetime import datetime, timezone, timedelta


def utc_ms(value):
    return int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp()*1000)


def archive_dates(start_ms, end_ms, module):
    tz = timezone.utc if module in (4,5,6) else timezone(timedelta(hours=8))
    first = datetime.fromtimestamp(start_ms/1000,tz).date()
    last = datetime.fromtimestamp((end_ms-1)/1000,tz).date()
    return [(first+timedelta(days=i)).isoformat() for i in range((last-first).days+1)]


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
