"""Streaming compression CRC checks, not proof of exchange sequence completeness."""
import gzip
import json
import zipfile
from pathlib import Path

results=[]
for p in sorted(Path('data/raw').iterdir()):
    if p.suffix=='.zip':
        with zipfile.ZipFile(p) as z:
            size=sum(i.file_size for i in z.infolist())
            if size>5_000_000_000:raise ValueError('decompression limit')
            bad=z.testzip()
            if bad:raise ValueError(f'ZIP CRC failed: {bad}')
        results.append({'file':p.name,'uncompressed_bytes':size,'compression_crc':'passed'})
    elif p.name.endswith('.tar.gz'):
        size=0
        with gzip.open(p,'rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):
                size+=len(chunk)
                if size>5_000_000_000:raise ValueError('decompression limit')
        results.append({'file':p.name,'uncompressed_tar_bytes':size,'compression_crc':'passed'})
Path('data/manifests/archive_integrity.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
