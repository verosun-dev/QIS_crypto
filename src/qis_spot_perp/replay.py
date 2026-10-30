"""Small two-leg IOC replay with separate exchange, observed and reported states.

Historical market replay cannot model participants reacting to our orders. Archive
sequence completeness and historical account margin rules are not established.
"""
import heapq
from collections import Counter
from decimal import Decimal as D
from .accounting import Account, funding_in_interval, paired_gross
from .book import Book
from .features import Features


class Replay:
    def __init__(self, config, multiplier="0.01", funding=()):
        self.c=config
        self.exchange={leg:Book(m,config['allow_unsequenced_archive']) for leg,m in [('spot','1'),('perp',multiplier)]}
        self.observed={leg:Book(m,config['allow_unsequenced_archive']) for leg,m in [('spot','1'),('perp',multiplier)]}
        self.actual, self.known=Account(),Account()
        self.feature_model=Features(config['lookback_seconds']*1000,config['decision_ms'])
        self.funding=list(funding)
        self.queue=[];self.counter=0;self.state='FLAT';self.pending=set()
        self.orders=[];self.fills=[];self.trades=[];self.features=[];self.equity=[];self.states=[]
        self.rejects=Counter();self.book_health=Counter();self.episode=0;self.armed=True
        self.current=None;self.halted=False;self.unknown_funding=False

    def schedule(self,t,priority,kind,payload=None):
        self.counter+=1
        heapq.heappush(self.queue,(t,priority,self.counter,kind,payload))

    def transition(self,t,state,reason):
        self.state=state
        self.states.append(dict(ts=t,state=state,reason=reason,
                               spot_known=str(self.known.positions['spot']),perp_known=str(self.known.positions['perp'])))

    def send(self,t,leg,side,q,reason):
        oid=len(self.orders)+1
        o=dict(order_id=oid,episode_id=self.episode,leg=leg,side=side,quantity_btc=str(q),
               send_ms=t,arrival_ms=t+self.c['order_latency_ms'],report_ms=None,reason=reason,status='PENDING')
        self.orders.append(o);self.pending.add(oid)
        self.schedule(o['arrival_ms'],2,'arrival',o)

    def close(self,t,reason):
        if self.pending:return
        self.transition(t,'EXITING' if reason=='holding' else 'RECOVERY',reason)
        if self.current is not None:
            self.current['exit_reason']=reason
            self.current.setdefault('recovery_start_ms',t)
            if all(b.healthy(t,self.c['max_stale_ms']) for b in self.observed.values()):
                self.current['exit_spot_mid']=str(self.observed['spot'].mid())
                self.current['exit_perp_mid']=str(self.observed['perp'].mid())
        for leg,q in self.known.positions.items():
            if q:self.send(t,leg,'sell' if q>0 else 'buy',abs(q),reason)

    def arrive(self,t,o):
        b=self.exchange[o['leg']]
        if b.healthy(t,self.c['max_stale_ms']):
            rows,remaining=b.sweep(o['side'],o['quantity_btc'])
        else:
            rows,remaining=[],D(o['quantity_btc'])
        fee_bps=self.c['spot_fee_bps' if o['leg']=='spot' else 'perp_fee_bps']
        report=[]
        for price,q in rows:
            fee=self.actual.fill(o['leg'],o['side'],q,price,fee_bps)
            row=dict(order_id=o['order_id'],episode_id=self.episode,leg=o['leg'],side=o['side'],
                     quantity_btc=str(q),price=str(price),fee_usdt=str(fee),fee_bps=str(fee_bps),
                     fill_ms=t,report_ms=t+self.c['report_latency_ms'])
            self.fills.append(row);report.append(row)
        o['status']='FILLED' if not remaining else ('PARTIAL_IOC' if rows else 'REJECTED')
        o['unfilled_btc']=str(remaining);o['report_ms']=t+self.c['report_latency_ms']
        self.schedule(o['report_ms'],3,'report',(o,report))

    def report(self,t,payload):
        o,rows=payload
        for r in rows:
            self.known.fill(r['leg'],r['side'],r['quantity_btc'],r['price'],r['fee_bps'])
        self.pending.remove(o['order_id'])
        if self.pending:return
        s,p=self.known.positions['spot'],self.known.positions['perp']
        if self.state=='ENTERING':
            if s==D(self.c['q_btc']) and p==-s:
                self.transition(t,'HEDGED','both_reports_received')
                # Holding clock starts at actual last entry fill; this is known only now.
                hedge=max(r['fill_ms'] for r in self.fills if r['episode_id']==self.episode)
                self.current['hedged_ms']=hedge
                self.schedule(max(t,hedge+self.c['holding_ms']),4,'exit_due')
            elif s or p:
                self.close(t,'entry_partial_unwind')
            else:
                self.finish(t,'both_entry_orders_rejected')
        elif self.state in ('EXITING','RECOVERY'):
            if not s and not p:self.finish(t,self.current['exit_reason'])
            elif t-self.current['recovery_start_ms']>=self.c['recovery_timeout_ms']:
                self.halted=True;self.transition(t,'RECOVERY','unresolved_exposure_timeout')
            else:
                self.transition(t,'RECOVERY','retry_remaining_inventory')
                self.schedule(t+1000,4,'retry')

    def finish(self,t,reason):
        r=self.current
        net=self.actual.cash_pnl-D(r['start_cash'])
        fees=self.actual.fees-D(r['start_fees'])
        funding=self.actual.funding-D(r['start_funding'])
        ideal=None
        if 'exit_spot_mid' in r:
            ideal=paired_gross(self.c['q_btc'],r['entry_spot_mid'],r['entry_perp_mid'],r['exit_spot_mid'],r['exit_perp_mid'])
        gross=net+fees-funding
        notional=D(self.c['q_btc'])*D(r['entry_spot_mid'])
        self.trades.append({**r,'exit_report_ms':t,'exit_reason':reason,'gross_fill_usdt':str(gross),
                            'gross_mid_benchmark_usdt':None if ideal is None else str(ideal),
                            'execution_loss_usdt':None if ideal is None else str(ideal-gross),
                            'fees_usdt':str(fees),'funding_usdt':str(funding),'net_usdt':str(net),
                            'net_bps_entry_spot':str(net/notional*10000),
                            'status':'CLOSED','benchmark_note':'decision mids; fixed q benchmark also on recovery, not pure slippage attribution'})
        self.current=None;self.transition(t,'FLAT','closed')

    def decision(self,t):
        valid=all(b.healthy(t,self.c['max_stale_ms']) for b in self.observed.values())
        if not valid:
            self.rejects['invalid_or_stale_decision']+=1
            if self.state=='HEDGED':self.close(t,'feed_unhealthy')
            return
        s,p=self.observed['spot'].mid(),self.observed['perp'].mid()
        f=self.feature_model.update(t,s,p)
        f['state']=self.state
        self.features.append(f)
        # Mark-to-market is diagnostic; this output is never an input to strategy.
        mark=self.actual.equity_pnl(s,p)
        self.equity.append(dict(ts=t,equity_usdt=str(D(self.c['initial_capital_usdt'])+mark),
                                pnl_usdt=str(mark),spot_btc=str(self.actual.positions['spot']),
                                perp_btc=str(self.actual.positions['perp']),
                                residual_btc=str(sum(self.actual.positions.values())),
                                state=self.state,valuation='observed_mid_not_liquidation_value'))
        x=f['excess_bps']
        if x is not None and x<=0:self.armed=True
        if self.state=='HEDGED':
            known_pnl=self.known.equity_pnl(s,p)-D(self.current['start_cash'])
            if known_pnl <= -D(self.c['max_pair_loss_usdt']):self.close(t,'observed_loss_limit')
        if self.halted or self.state!='FLAT' or self.pending:return
        if not self.c['entry_start_ms']<=t<self.c['entry_end_ms']:return
        if x is None:self.rejects['warmup_incomplete']+=1;return
        if f['basis_bps']<=0:self.rejects['nonpositive_basis']+=1;return
        if x<self.c['threshold_bps']:self.rejects['below_threshold']+=1;return
        if not self.armed:self.rejects['episode_not_reset']+=1;return
        end=t+self.c['holding_ms']+2*self.c['order_latency_ms']+2*self.c['report_latency_ms']+self.c['recovery_timeout_ms']
        if funding_in_interval(t,end,self.funding):self.rejects['funding_reference_unavailable']+=1;return
        self.episode+=1;self.armed=False
        self.current=dict(episode_id=self.episode,decision_ms=t,entry_spot_mid=str(s),entry_perp_mid=str(p),
                          basis_bps=f['basis_bps'],excess_bps=x,start_cash=str(self.actual.cash_pnl),
                          start_fees=str(self.actual.fees),start_funding=str(self.actual.funding))
        self.transition(t,'ENTERING','v0')
        self.send(t,'spot','buy',D(self.c['q_btc']),'entry')
        self.send(t,'perp','sell',D(self.c['q_btc']),'entry')

    def handle(self,t,kind,payload):
        if kind=='observed':
            leg,event=payload;self.observed[leg].apply(event)
        elif kind=='arrival':self.arrive(t,payload)
        elif kind=='report':self.report(t,payload)
        elif kind=='decision':
            self.decision(t)
            if t+self.c['decision_ms']<self.c['end_ms']:
                self.schedule(t+self.c['decision_ms'],5,'decision')
        elif kind=='exit_due' and self.state=='HEDGED':self.close(t,'holding')
        elif kind=='retry' and self.state=='RECOVERY' and not self.halted:self.close(t,'recovery_retry')
        elif kind=='funding' and self.actual.positions['perp']:
            # Missing reference prices are NOT silently assumed to imply zero cashflow.
            self.unknown_funding=True;self.halted=True
            self.transition(t,'RECOVERY','unknown_funding_cashflow')
            if not self.pending:self.close(t,'unknown_funding_cashflow')

    def run(self,events):
        self.schedule(self.c['start_ms'],5,'decision')
        for f in self.funding:
            if self.c['start_ms']<=int(f['fundingTime'])<self.c['end_ms']:
                self.schedule(int(f['fundingTime']),1,'funding',f)
        # Equal timestamps: all exchange updates precede arrivals. Ties are a model assumption.
        for ts,leg,event in events:
            while self.queue and self.queue[0][0]<ts:
                t,_,_,kind,payload=heapq.heappop(self.queue)
                if t>=self.c['end_ms']:break
                self.handle(t,kind,payload)
            self.book_health[self.exchange[leg].apply(event)]+=1
            self.schedule(ts+self.c['feed_latency_ms'],1,'observed',(leg,event))
        while self.queue and self.queue[0][0]<self.c['end_ms']:
            t,_,_,kind,payload=heapq.heappop(self.queue);self.handle(t,kind,payload)
        return self

    def summary(self):
        pnl=[D(r['net_usdt']) for r in self.trades]
        eq=[D(x['equity_usdt']) for x in self.equity]
        peak=D(self.c['initial_capital_usdt']);drawdown=D(0)
        for value in eq:peak=max(peak,value);drawdown=max(drawdown,peak-value)
        unresolved=bool(self.pending or any(self.actual.positions.values()))
        return dict(data_kind=self.c['data_kind'],status='INCOMPLETE' if unresolved or self.unknown_funding else 'COMPLETED_DEBUG',
                    closed_trades=len(pnl),episodes=self.episode,orders=len(self.orders),fills=len(self.fills),
                    gross_fill_usdt=str(sum((D(r['gross_fill_usdt']) for r in self.trades),D(0))),
                    fees_usdt=str(self.actual.fees),funding_usdt=None if self.unknown_funding else str(self.actual.funding),
                    closed_net_usdt=None if self.unknown_funding else str(sum(pnl,D(0))),
                    return_on_total_capital=None if self.unknown_funding else str(sum(pnl,D(0))/D(self.c['initial_capital_usdt'])),
                    win_rate=None if not pnl else sum(x>0 for x in pnl)/len(pnl),
                    worst_trade_usdt=str(min(pnl)) if pnl else None,max_drawdown_usdt=str(drawdown),
                    end_positions={k:str(v) for k,v in self.actual.positions.items()},pending_orders=sorted(self.pending),
                    end_state=self.state,rejections=dict(self.rejects),book_health=dict(self.book_health),
                    limitations=['2-hour debug; shortened warmup','No archive sequence IDs or local receipt timestamps',
                                 'Illustrative fees and latency; quote-currency fee assumption',
                                 'Current metadata, historical rule equivalence unverified',
                                 'No margin liquidation model; cannot validate leveraged safety',
                                 'Funding crossings blocked absent settlement reference price',
                                 'No out-of-sample or profitability conclusion'])
