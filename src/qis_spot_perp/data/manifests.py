"""Local fingerprints and provenance for downloaded public archives."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()


def provenance(root, date=None):
    """Inspect legacy inputs, or finalize/verify an immutable dated acquisition."""
    root=Path(root); directory=root/'data/manifests'; files=[]
    if date is not None:
        if datetime.strptime(date,'%Y-%m-%d').date().isoformat()!=date:
            raise ValueError('date must use YYYY-MM-DD')
        directory=directory/date
        names=[f'okx-{leg}-{kind}.json' for leg in ('spot','swap') for kind in ('spec','trades','books')]
        manifests=sorted(directory/name for name in names+['okx-funding.json'])
    else:
        manifests=sorted(directory.glob('okx-*.json'))
    for manifest in manifests:
        obj=json.loads(manifest.read_text())
        if date is not None and obj.get('code')!='0':
            raise ValueError(f'unsuccessful source response: {manifest}')
        for data in obj.get('data',[]):
            for detail in data.get('details',[]):
                for group in detail.get('groupDetails',[]):
                    if Path(group['filename']).name!=group['filename']:
                        raise ValueError('unsafe archive filename')
                    p=root/'data/raw'/group['filename']
                    files.append({**group,'local_path':str(p.relative_to(root)),
                                  'local_file_completed_utc':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat() if p.exists() else None,
                                  'bytes':p.stat().st_size if p.exists() else None,
                                  'sha256':sha256(p) if p.exists() else None,
                                  'retrieval_manifest':str(manifest.relative_to(root))})
    now=datetime.now(timezone.utc)
    result={'checked_client_date':now.date().isoformat(),'files':files,
            'hash_note':'local SHA256 fingerprint; not an exchange-published checksum',
            'download_tool':'curl --fail --max-time 180 --max-filesize 500000000',
            'total_bytes':sum(x['bytes'] or 0 for x in files)}
    if date is None:return result
    if len(files)!=6 or len({f['local_path'] for f in files})!=6:
        raise ValueError('expected six distinct archives in dated acquisition')
    missing=[f['local_path'] for f in files if f['sha256'] is None]
    if missing:raise ValueError('missing raw archives: '+', '.join(missing))
    sources=manifests+[directory/'retrieval_requests.json']
    result.update(research_date=date,checked_at_utc=now.isoformat(),
                  source_manifests=[{'path':str(p.relative_to(root)),'sha256':sha256(p)} for p in sources])
    output=directory/'downloads.json'
    if output.exists():
        saved=json.loads(output.read_text())
        def content(record):
            stable={k:v for k,v in record.items() if k not in ('checked_client_date','checked_at_utc')}
            stable['files']=[{k:v for k,v in row.items() if k!='local_file_completed_utc'} for row in record.get('files',[])]
            return stable
        if content(saved)!=content(result):
            raise ValueError('dated provenance inputs changed; existing downloads.json preserved')
        return saved
    with output.open('x') as f:f.write(json.dumps(result,indent=2))
    return result
