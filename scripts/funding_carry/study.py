"""Historical opportunity screen, NOT a causal strategy or executable backtest.

Run with Python's standard library. Reads saved, unmodified OKX responses from --data-dir. Deliberately permits hindsight; never treats candles as bid/ask quotes.
"""
import argparse
import bisect
import hashlib
import json
import math
import statistics as st
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parents[2]/'tmp/funding_carry_oracle_20261113')
ROOT = parser.parse_args().data_dir.resolve()
CONFIG = json.loads((ROOT/'study_config.json').read_text()) if (ROOT/'study_config.json').exists() else {}
ASSET = CONFIG.get('asset', 'BTC')
MINUTE = 60_000
HOLD = 30 * MINUTE
Q = CONFIG.get('quantity', 0.01)
START = int(datetime(2026, 10, 14, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2026, 11, 13, tzinfo=timezone.utc).timestamp() * 1000)


def iso(t):
    return datetime.fromtimestamp(t / 1000, timezone.utc).isoformat()


def stats(values):
    x = sorted(values)
    if not x:
        return {"n": 0, "mean": None}
    return dict(n=len(x), mean=st.mean(x), median=st.median(x), min=x[0],
                p05=x[int((len(x)-1)*.05)], p95=x[int((len(x)-1)*.95)],
                max=x[-1], sum=sum(x), positive=sum(v > 0 for v in x))


def load_candles(name, step):
    rows = {}
    for path in sorted((ROOT/'raw').glob(name+'-*.json')):
        response = json.loads(path.read_text())
        assert response['code'] == '0' and response['data'], path
        for row in response['data']:
            t = int(row[0])
            if not START <= t <= END:
                continue
            assert row[-1] == '1', (path, row)
            assert t % step == 0
            o, h, low, c = map(float, row[1:5])
            assert all(math.isfinite(p) and p > 0 for p in (o,h,low,c))
            assert low <= min(o,c) <= max(o,c) <= h
            if t in rows:
                assert rows[t] == row, (name, 'conflicting duplicate', t)
            rows[t] = row
    expected = set(range(START, END+1, step))
    assert set(rows) == expected, (name, 'missing bars', len(expected-set(rows)))
    return rows


def summary(rows):
    return {field: stats([r[field] for r in rows]) for field in
            ('basis_usdt','funding_usdt','gross_usdt','fees_usdt','net_usdt',
             'basis_bps','funding_bps','gross_bps','fees_bps','net_bps')}


def optimal_schedule(rows, score):
    """Weighted interval scheduling; one pair at a time, optional no-trade.

    A one-minute flat gap after each 30-minute round trip prevents impossible
    instant reuse of capital/quotes. This remains an intentionally optimistic
    candle-price calculation with no margin or execution simulation.
    """
    rows = sorted(rows, key=lambda r:r['exit_ms'])
    ends = [r['exit_ms'] for r in rows]
    best = [0.0]*(len(rows)+1)
    take = [False]*len(rows)
    predecessors = []
    for i, r in enumerate(rows):
        p = bisect.bisect_right(ends, r['entry_ms']-MINUTE, hi=i)
        predecessors.append(p)
        value = best[p]+score(r)
        if value > best[i]+1e-12:
            best[i+1] = value
            take[i] = True
        else:
            best[i+1] = best[i]
    selected=[]
    i=len(rows)
    while i:
        if take[i-1]:
            selected.append(rows[i-1]); i=predecessors[i-1]
        else:
            i-=1
    selected.reverse()
    assert all(a['exit_ms']+MINUTE<=b['entry_ms'] for a,b in zip(selected,selected[1:]))
    assert math.isclose(sum(score(r) for r in selected), best[-1], abs_tol=1e-9)
    return dict(total_usdt=best[-1], trades=len(selected),
                mean_usdt=st.mean(score(r) for r in selected) if selected else None,
                selected=[{'entry_utc':r['entry_utc'], 'exit_utc':r['exit_utc'],
                           'score_usdt':score(r)} for r in selected])


def main():
    spot=load_candles('spot',MINUTE)
    perp=load_candles('perp',MINUTE)
    mark=load_candles('mark',60*MINUTE)
    response=json.loads((ROOT/'funding-probe.json').read_text())
    assert response['code']=='0'
    funding=sorted(response['data'],key=lambda r:int(r['fundingTime']))
    assert len({r['fundingTime'] for r in funding})==len(funding)
    times=[int(r['fundingTime']) for r in funding]
    assert times[0]<START and times[-1]>END
    # Verify this sample's actual cadence; do not assume this for other contracts.
    assert all(b-a==8*60*MINUTE for a,b in zip(times,times[1:]))
    inside=[r for r in funding if START<=int(r['fundingTime'])<END]
    assert len(inside)==90
    by_time={int(r['fundingTime']):r for r in funding}
    relevant=[t for t in times if START<=t<=END]
    rates=[float(r['realizedRate'])*10000 for r in inside]
    # Trades cannot open/close within two minutes of a nominal funding timestamp.
    # OKX warns actual assessment may take up to one minute.
    blocked={f+d*MINUTE for f in relevant for d in (-1,0,1)}

    def trade(t, price_column=1):
        end=t+HOLD
        s0,s1=float(spot[t][price_column]),float(spot[end][price_column])
        p0,p1=float(perp[t][price_column]),float(perp[end][price_column])
        crossings=[f for f in relevant if t<f<end]
        assert len(crossings)<=1
        amount=sum(Q*float(mark[f][1])*float(by_time[f]['realizedRate']) for f in crossings)
        basis=Q*((s1-s0)+(p0-p1))
        fees=Q*((s0+s1)*.001+(p0+p1)*.0005)
        notional=Q*s0
        r=dict(entry_ms=t,exit_ms=end,entry_utc=iso(t),exit_utc=iso(end),
               spot_entry=s0,spot_exit=s1,perp_entry=p0,perp_exit=p1,
               notional_usdt=notional,funding_times=[iso(f) for f in crossings],
               basis_usdt=basis,funding_usdt=amount,gross_usdt=basis+amount,
               fees_usdt=fees,net_usdt=basis+amount-fees)
        for k in ('basis','funding','gross','fees','net'):
            r[k+'_bps']=r[k+'_usdt']/notional*10000
        # Independent two-leg identity.
        assert math.isclose(basis,Q*((p0-s0)-(p1-s1)),abs_tol=1e-9)
        return r

    candidates=[trade(t) for t in range(START,END-HOLD+1,MINUTE)
                if t not in blocked and t+HOLD not in blocked]
    settlement_rows=[r for r in candidates if r['funding_times']]
    centered=[trade(f-15*MINUTE) for f in relevant if START+15*MINUTE<=f<=END-15*MINUTE]
    per_settlement=[]
    per_settlement_bps=[]
    for f in relevant:
        rows=[r for r in settlement_rows if r['funding_times']==[iso(f)]]
        if rows:
            assert len(rows)==27
            winner=max(rows,key=lambda r:r['net_usdt'])
            per_settlement.append(dict(settlement_utc=iso(f),candidates=len(rows),best_trade=winner))
            per_settlement_bps.append(dict(settlement_utc=iso(f),candidates=len(rows),
                                           best_trade=max(rows,key=lambda r:r['net_bps'])))
    best_each=[x['best_trade'] for x in per_settlement]
    assert len(centered)==len(best_each)==89
    costs=[]
    for cost_bps in (0,1,2,5,10,20,30):
        score=lambda r:r['gross_usdt']-r['notional_usdt']*cost_bps/10000
        schedule=optimal_schedule(candidates,score)
        costs.append(dict(flat_round_trip_cost_bps=cost_bps,
                          positive_candidates=sum(score(r)>0 for r in candidates),
                          best_single_usdt=max(score(r) for r in candidates),
                          oracle_total_usdt=schedule['total_usdt'],
                          oracle_trades=schedule['trades']))
    # Alternative candle close proxy is a sensitivity, NOT exact synchronization.
    close_rows=[trade(r['entry_ms'],4) for r in candidates]
    # Longer holdings are a separate no-prediction diagnostic, fixed every day at
    # 00:15 UTC; no additional tuning and no overlap-based cumulative portfolio P&L.
    horizons=[]
    for days in (1,3,7,14):
        h=days*24*60*MINUTE
        rows=[]
        for t in range(START+15*MINUTE,END-h+1,24*60*MINUTE):
            end=t+h;s0=float(spot[t][1]);s1=float(spot[end][1]);p0=float(perp[t][1]);p1=float(perp[end][1])
            received=sum(Q*float(mark[f][1])*float(by_time[f]['realizedRate']) for f in relevant if t<f<end)
            basis=Q*(s1-s0+p0-p1);fees=Q*((s0+s1)*.001+(p0+p1)*.0005)
            row=dict(entry_utc=iso(t),exit_utc=iso(end),basis_usdt=basis,funding_usdt=received,
                     gross_usdt=basis+received,fees_usdt=fees,net_usdt=basis+received-fees)
            for k in ('basis','funding','gross','fees','net'):row[k+'_bps']=row[k+'_usdt']/(Q*s0)*10000
            rows.append(row)
        horizons.append(dict(holding_days=days,stats=summary(rows),trades=rows))
    # Small accounting and oracle checks independent of the observations.
    assert math.isclose(.01*80000*.0001,.08)
    assert math.isclose(2*(1000*.001+1000*.0005),3)
    assert math.isclose(.01*((101000-100000)+(100300-101100)),2)
    assert all(costs[i]['oracle_total_usdt']>=costs[i+1]['oracle_total_usdt']-1e-9 for i in range(len(costs)-1))
    result=dict(
        study=f'OKX {ASSET} 30-minute funding-carry hindsight opportunity screen',
        start_utc=iso(START),end_exclusive_funding_utc=iso(END),base_asset=ASSET,quantity_base=Q,
        scope=f'Long {ASSET}-USDT spot, short equal {ASSET} quantity {ASSET}-USDT-SWAP; no reverse trade, no forecasting.',
        price_assumption='1m candle OPEN as a trade-price proxy; not mid, not bid/ask, not guaranteed simultaneous or executable.',
        funding_assumption='Actual realizedRate; settlement-hour mark candle OPEN approximates settlement mark. Rate is not prorated by 30m/8h.',
        fee_assumption='Old project scenario: spot 10 bps and perp 5 bps per fill, four prices, USDT equivalent. Not verified account fees.',
        omitted=['bid/ask and depth','order/feed latency','legging and partial fills','margin/liquidation','financing','fee currency/rounding'],
        coverage=dict(spot_1m=len(spot),perp_1m=len(perp),mark_1h=len(mark),missing_bars=0,
                      settlement_cadence_hours=8,settlements_for_rate_stats=len(inside),
                      settlement_windows_with_full_context=len(centered),
                      excluded_entry_exit_boundary_windows=(END-HOLD-START)//MINUTE+1-len(candidates)),
        funding_rate_bps=stats(rates),positive_funding_rate_bps=stats([r for r in rates if r>0]),
        funding_rate_records=inside,
        all_30m_candidates=summary(candidates),settlement_crossing_candidates=summary(settlement_rows),
        fixed_15m_before_15m_after=summary(centered),fixed_event_trades=centered,
        best_30m_per_settlement_forced=summary(best_each),per_settlement_oracle=per_settlement,
        best_30m_per_settlement_forced_by_bps=summary([x['best_trade'] for x in per_settlement_bps]),
        per_settlement_oracle_by_bps=per_settlement_bps,
        best_single_trade=max(candidates,key=lambda r:r['net_usdt']),
        best_settlement_trade=max(settlement_rows,key=lambda r:r['net_usdt']),
        best_single_trade_by_bps=max(candidates,key=lambda r:r['net_bps']),
        best_settlement_trade_by_bps=max(settlement_rows,key=lambda r:r['net_bps']),
        top20_trades=sorted(candidates,key=lambda r:r['net_usdt'],reverse=True)[:20],
        oracle_with_no_trade=optimal_schedule(candidates,lambda r:r['net_usdt']),
        flat_cost_sensitivity=costs,
        close_proxy_sensitivity=dict(stats=summary(close_rows),best_single=max(close_rows,key=lambda r:r['net_usdt'])),
        longer_hold_diagnostic=horizons,
        interpretation='Oracle is restricted to the stated minute grid, quantity, direction and price model. Overlapping candidate trades are not independent or summable. No annualized performance claim.')
    (ROOT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    requests=json.loads((ROOT/'requests.json').read_text())
    manifest=[]
    for r in requests:
        p=ROOT/'raw'/Path(r['path']).name
        manifest.append(dict(url=r['url'],path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,
                             sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    p=ROOT/'funding-probe.json'
    manifest.append(dict(url=f'https://www.okx.com/api/v5/public/funding-rate-history?instId={ASSET}-USDT-SWAP&limit={CONFIG.get("funding_limit",100)}',
                         path=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    (ROOT/'source_manifest.json').write_text(json.dumps(dict(retrieval_client_date='2026-11-13',files=manifest),indent=2))
    compact=dict(asset=ASSET, coverage=result['coverage'], funding_rate_bps=result['funding_rate_bps'],
                 fixed_event_mean_bps={k:v['mean'] for k,v in result['fixed_15m_before_15m_after'].items() if k.endswith('_bps')},
                 best_per_event_mean_net_bps=result['best_30m_per_settlement_forced']['net_bps']['mean'],
                 best_single_net_bps=result['all_30m_candidates']['net_bps']['max'],
                 profitable_candidates=result['all_30m_candidates']['net_bps']['positive'],
                 oracle_total_usdt=result['oracle_with_no_trade']['total_usdt'],
                 flat_cost_sensitivity=costs)
    compact['longer_hold_diagnostic']=[dict(days=r['holding_days'],n=r['stats']['net_bps']['n'],
                                          mean_net_bps=r['stats']['net_bps']['mean']) for r in horizons]
    print(json.dumps(compact,indent=2))


if __name__=='__main__':
    main()
