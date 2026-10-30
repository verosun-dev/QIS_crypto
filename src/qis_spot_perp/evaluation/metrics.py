"""Debug-run metrics from recorded fills, trades, and marked inventory."""
from decimal import Decimal as D


def summarize(engine):
    """Report closed cash flows and expose unresolved inventory or unknown funding."""
    pnl=[D(r['net_usdt']) for r in engine.trades]
    eq=[D(x['equity_usdt']) for x in engine.equity]
    peak=D(engine.c['initial_capital_usdt']);drawdown=D(0)
    for value in eq:peak=max(peak,value);drawdown=max(drawdown,peak-value)
    unresolved=bool(engine.pending or any(engine.actual.positions.values()))
    return dict(data_kind=engine.c['data_kind'],status='INCOMPLETE' if unresolved or engine.unknown_funding else 'COMPLETED_DEBUG',
                closed_trades=len(pnl),episodes=engine.episode,orders=len(engine.orders),fills=len(engine.fills),
                gross_fill_usdt=str(sum((D(r['gross_fill_usdt']) for r in engine.trades),D(0))),
                fees_usdt=str(engine.actual.fees),funding_usdt=None if engine.unknown_funding else str(engine.actual.funding),
                closed_net_usdt=None if engine.unknown_funding else str(sum(pnl,D(0))),
                return_on_total_capital=None if engine.unknown_funding else str(sum(pnl,D(0))/D(engine.c['initial_capital_usdt'])),
                win_rate=None if not pnl else sum(x>0 for x in pnl)/len(pnl),
                worst_trade_usdt=str(min(pnl)) if pnl else None,max_drawdown_usdt=str(drawdown),
                end_positions={k:str(v) for k,v in engine.actual.positions.items()},pending_orders=sorted(engine.pending),
                end_state=engine.state,rejections=dict(engine.rejects),book_health=dict(engine.book_health),
                limitations=['2-hour debug; shortened warmup','No archive sequence IDs or local receipt timestamps',
                             'Illustrative fees and latency; quote-currency fee assumption',
                             'Current metadata, historical rule equivalence unverified',
                             'No margin liquidation model; cannot validate leveraged safety',
                             'Funding crossings blocked absent settlement reference price',
                             'No out-of-sample or profitability conclusion'])
