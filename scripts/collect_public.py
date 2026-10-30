#!/usr/bin/env python3
"""Optional bounded public WS capture, never places orders. Requires websocket-client.

No automatic reconnect: disconnection is explicitly recorded and requires a new
snapshot on the next run. Raw sequences are preserved for downstream validation.
"""
import argparse
import json
import time
from pathlib import Path
from urllib.parse import urlparse


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--url',required=True,help='official public WS endpoint appropriate to access region')
    p.add_argument('--seconds',type=int,default=30)
    p.add_argument('--max-mb',type=int,default=25)
    p.add_argument('--output',default='data/raw/live-public.jsonl')
    a=p.parse_args()
    if not 1<=a.seconds<=300 or not 1<=a.max_mb<=100:raise ValueError('bounded to 300s/100MB')
    if urlparse(a.url).scheme!='wss' or urlparse(a.url).path!='/ws/v5/public':
        raise ValueError('requires official secure public WS path')
    import websocket
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    total=0;sequence=0;started=time.monotonic();ws=None
    with path.open('x') as f:
        def save(kind,payload):
            nonlocal total,sequence
            sequence+=1
            row=json.dumps(dict(local_receive_ns=time.time_ns(),arrival_sequence=sequence,kind=kind,payload=payload))+'\n'
            if total+len(row.encode())>a.max_mb*1000000:return False
            f.write(row);total+=len(row.encode());return True
        try:
            ws=websocket.create_connection(a.url,timeout=min(a.seconds,10))
            ws.send(json.dumps({'op':'subscribe','args':[{'channel':c,'instId':i}
                     for c in ('books','trades') for i in ('BTC-USDT','BTC-USDT-SWAP')]}))
            save('connected',{'url':a.url,'seconds_limit':a.seconds,'byte_limit':a.max_mb*1000000})
            while time.monotonic()-started<a.seconds:
                ws.settimeout(min(5,max(.01,a.seconds-(time.monotonic()-started))))
                try:
                    msg=ws.recv()
                    if not msg:save('disconnect','empty receive');break
                    if not save('raw_message',msg):break
                except websocket.WebSocketTimeoutException:
                    ws.send('ping')
            save('stopped',{'elapsed_seconds':time.monotonic()-started,'bytes':total})
        except Exception as e:
            save('capture_error',str(e));raise
        finally:
            if ws:ws.close()
    print(path,total,'bytes')


if __name__=='__main__':main()
