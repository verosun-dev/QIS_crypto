#!/usr/bin/env python3
"""Bounded public archive fetch. No keys, no accounts, no private endpoints."""
import argparse
import hashlib
import json
import subprocess
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse


def curl(url,path,limit=5_000_000,seconds=30):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    partial=path.with_name(path.name+'.part')
    subprocess.run(['curl','--fail','--location','--silent','--show-error','--max-time',str(seconds),
                    '--max-filesize',str(limit),url,'-o',str(partial)],check=True)
    if partial.stat().st_size>limit:raise ValueError('download byte budget exceeded')
    partial.replace(path)


def acquisition_files(manifest,requests):
    """Read the complete saved acquisition without replacing source responses."""
    retrieval=json.loads((manifest/'retrieval_requests.json').read_text())
    if [(Path(r['file']).name,r['url']) for r in retrieval]!=requests:
        raise ValueError('saved acquisition requests do not match the research date')
    files=[]
    for name,_ in requests:
        obj=json.loads((manifest/name).read_text())
        if obj.get('code')!='0':raise ValueError(obj)
        for d in obj['data']:
            for group in d.get('details',[]):files.extend(group.get('groupDetails',[]))
    if len(files)!=6 or len({f['filename'] for f in files})!=6:
        raise ValueError('expected two books plus four distinct trade files; inspect missing coverage')
    output=manifest/'downloads.json'
    if output.exists():
        saved=json.loads(output.read_text())
        sources=[manifest/name for name,_ in sorted(requests)]+[manifest/'retrieval_requests.json']
        fingerprints=[{'path':str(Path('data/manifests')/manifest.name/p.name),
                       'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources]
        if saved.get('source_manifests')!=fingerprints:
            raise ValueError('saved acquisition source bytes changed; existing provenance preserved')
    return files


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--date',default='2026-10-23');p.add_argument('--max-mb',type=float,default=700)
    p.add_argument('--download',action='store_true',help='default only lists sizes')
    a=p.parse_args()
    day=datetime.strptime(a.date,'%Y-%m-%d').replace(tzinfo=timezone.utc)
    if day.date().isoformat()!=a.date:raise ValueError('date must use YYYY-MM-DD')
    if day.date()>datetime.now(timezone.utc).date()-timedelta(days=4):
        raise ValueError('choose a day at least 4 UTC dates earlier; verify actual publication')
    start=int(day.timestamp()*1000);end=start+86400000
    base='https://www.okx.com/api/v5/';manifest=Path('data/manifests')/a.date
    requests=[]
    for leg,kind,inst in [('spot','SPOT','BTC-USDT'),('swap','SWAP','BTC-USDT-SWAP')]:
        requests.append((f'okx-{leg}-spec.json','public/instruments',{'instType':kind,'instId':inst}))
        for module,name in [(1,'trades'),(4,'books')]:
            params={'module':module,'instType':kind,'instIdList' if kind=='SPOT' else 'instFamilyList':'BTC-USDT',
                    'dateAggrType':'daily','begin':start,'end':end if module==1 else start}
            requests.append((f'okx-{leg}-{name}.json','public/market-data-history',params))
    requests.append(('okx-funding.json','public/funding-rate-history',
                     {'instId':'BTC-USDT-SWAP','before':start-1,'after':end,'limit':100}))
    requests=[(name,base+endpoint+'?'+urlencode(params)) for name,endpoint,params in requests]
    if manifest.exists():
        files=acquisition_files(manifest,requests)
    else:
        manifest.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f'.{a.date}-',dir=manifest.parent) as directory:
            staged=Path(directory);retrieval=[]
            for name,url in requests:
                curl(url,staged/name)
                obj=json.loads((staged/name).read_text())
                if obj.get('code')!='0':raise ValueError(obj)
                retrieval.append({'url':url,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'file':str(manifest/name)})
                time.sleep(.45)
            (staged/'retrieval_requests.json').write_text(json.dumps(retrieval,indent=2))
            files=acquisition_files(staged,requests)
            staged.rename(manifest)
    total=sum(float(x['sizeMB']) for x in files)
    print(json.dumps({'listed_mb':total,'files':files},indent=2))
    if not a.download:return
    if total*1.05>a.max_mb:raise ValueError('listed files plus safety margin exceed budget')
    remaining=int(a.max_mb*1_000_000)
    for f in files:
        u=urlparse(f['url'])
        if u.scheme!='https' or u.hostname!='static.okx.com':raise ValueError('unexpected archive host')
        name=Path(f['filename']).name
        if name!=f['filename']:raise ValueError('unsafe filename')
        target=Path('data/raw')/name
        if target.exists():
            remaining-=target.stat().st_size
            print('Existing file retained; verify with manifest/hash:',target)
            continue
        if remaining<=0:raise ValueError('resource budget exhausted')
        curl(f['url'],target,min(500_000_000,remaining),180)
        remaining-=target.stat().st_size


if __name__=='__main__':main()
