"""Independent Decimal reconstruction and small exhaustive oracle checks."""
import argparse
import importlib.util
import itertools
import json
import random
from decimal import Decimal as D
from pathlib import Path
from statistics import mean

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-dir', type=Path,
                    default=Path(__file__).resolve().parents[2]/'tmp/funding_carry_oracle_20261113')
ROOT = parser.parse_args().data_dir.resolve()
START, END, MINUTE = 1791936000000, 1794528000000, 60000


def validate_asset(root):
    result = json.loads((root/'results.json').read_text())
    def candles(prefix):
        return {int(row[0]): row for f in (root/'raw').glob(prefix+'-*.json')
                for row in json.loads(f.read_text())['data']}
    spot, perp, mark = candles('spot'), candles('perp'), candles('mark')
    funding = {int(r['fundingTime']): D(r['realizedRate'])
               for r in json.loads((root/'funding-probe.json').read_text())['data']
               if START <= int(r['fundingTime']) <= END}
    blocked = {t+d*MINUTE for t in funding for d in (-1,0,1)}
    q = D(str(result['quantity_base']))
    net, centered = [], []
    for t in range(START, END-30*MINUTE+1, MINUTE):
        u=t+30*MINUTE
        if t in blocked or u in blocked:
            continue
        s0,s1=D(spot[t][1]),D(spot[u][1])
        p0,p1=D(perp[t][1]),D(perp[u][1])
        received=sum((q*D(mark[k][1])*v for k,v in funding.items() if t<k<u), D(0))
        value=q*(s1-s0+p0-p1)+received-q*(D('.001')*(s0+s1)+D('.0005')*(p0+p1))
        row=(t,value,value/(q*s0)*D(10000))
        net.append(row)
        if t+15*MINUTE in funding:
            centered.append(row)
    assert len(net)==42633 and len(centered)==89
    stats=result['all_30m_candidates']
    assert sum(v>0 for _,v,_ in net)==stats['net_usdt']['positive']
    assert abs(float(max(v for _,v,_ in net))-stats['net_usdt']['max'])<1e-9
    assert abs(float(max(v for _,_,v in net))-stats['net_bps']['max'])<1e-9
    assert abs(float(mean(v for _,_,v in centered))-result['fixed_15m_before_15m_after']['net_bps']['mean'])<1e-9
    return dict(asset=result['base_asset'],candidates=len(net),fixed_events=len(centered),
                positive_candidates=stats['net_usdt']['positive'],
                maxima_and_fixed_event_average_match=True)


checks=[validate_asset(p) for p in (ROOT, ROOT/'ETH', ROOT/'SOL')]
spec=importlib.util.spec_from_file_location('study_for_validation', Path(__file__).with_name('study.py'))
study=importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
rng=random.Random(73)
for _ in range(100):
    starts=sorted(rng.sample(range(200),8))
    rows=[dict(entry_ms=t*MINUTE,exit_ms=(t+30)*MINUTE,
               entry_utc=str(t),exit_utc=str(t+30),score=rng.randint(-5,10)) for t in starts]
    expected=0
    for bits in itertools.product([False,True],repeat=len(rows)):
        selected=[r for r,b in zip(rows,bits) if b]
        if all(a['exit_ms']+MINUTE<=b['entry_ms'] for a,b in zip(selected,selected[1:])):
            expected=max(expected,sum(r['score'] for r in selected))
    got=study.optimal_schedule(rows,lambda r:r['score'])['total_usdt']
    assert got==expected, (got,expected)
out=dict(method='Independent Decimal recomputation from saved original responses',
         assets=checks,weighted_interval_oracle_matches_exhaustive_search_cases=100)
(ROOT/'independent_validation.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
