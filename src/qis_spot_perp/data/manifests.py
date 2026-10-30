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
