"""Turn a finished replay into its summary ("report card").

The summary must be honest about what is NOT known. If a position or order is
still open when the data ends, or a funding payment could not be valued, the
status is INCOMPLETE and `incomplete_reasons` says why, instead of presenting a
partial result as a final profit or loss.

All money values are Decimal internally and written out as strings so that
summary.json keeps exact values (no float rounding such as 0.30000000000000004).
"""
from decimal import Decimal as D

# Known limits of the current debug replay. Copied into every summary so a
# reader of summary.json cannot mistake a debug run for a validated result.
LIMITATIONS = [
    '2-hour debug; shortened warmup',
    'No archive sequence IDs or local receipt timestamps',
    'Illustrative fees and latency; quote-currency fee assumption',
    'Current metadata, historical rule equivalence unverified',
    'No margin liquidation model; cannot validate leveraged safety',
    'Funding crossings blocked absent settlement reference price',
    'No out-of-sample or profitability conclusion',
]


def closed_trade_pnls(engine):
    """Net profit (USDT) of every round trip that fully closed, in order."""
    return [D(trade['net_usdt']) for trade in engine.trades]


def max_drawdown(engine):
    """Largest fall in account value from its highest point so far, in USDT.

    The running peak starts at the initial capital, so an account that loses
    money from the very first moment still shows a drawdown.
    Example: 1500 -> 1502 -> 1501 gives a peak of 1502 and a drawdown of 1.
    """
    peak = D(engine.c['initial_capital_usdt'])
    worst = D(0)
    for row in engine.equity:
        value = D(row['equity_usdt'])
        peak = max(peak, value)            # new high-water mark?
        worst = max(worst, peak - value)   # how far below the high are we now?
    return worst


def incomplete_reasons(engine):
    """List everything that stops the result from being final.

    An empty list means the run ended flat (no open legs, no pending orders)
    and every cash flow could be valued.
    """
    reasons = []
    open_legs = sorted(leg for leg, quantity in engine.actual.positions.items() if quantity)
    if open_legs:
        reasons.append('open position at end of data: ' + ', '.join(open_legs))
    if engine.pending:
        reasons.append(f'{len(engine.pending)} order(s) still pending at end of data')
    if engine.unknown_funding:
        reasons.append('a funding settlement could not be valued')
    return reasons


def summarize(engine):
    """Build the summary dictionary saved as summary.json after every replay."""
    pnls = closed_trade_pnls(engine)
    reasons = incomplete_reasons(engine)
    capital = D(engine.c['initial_capital_usdt'])

    # Net results are only meaningful when every funding payment is known.
    # Otherwise report None ("unknown") rather than a number that looks final.
    net = None if engine.unknown_funding else sum(pnls, D(0))

    return dict(
        # --- What kind of run this was and whether its numbers are final ---
        data_kind=engine.c['data_kind'],
        status='INCOMPLETE' if reasons else 'COMPLETED_DEBUG',
        incomplete_reasons=reasons,

        # --- Activity counts ---
        closed_trades=len(pnls),
        episodes=engine.episode,
        orders=len(engine.orders),
        fills=len(engine.fills),

        # --- Money: profit before costs, costs, and the bottom line ---
        gross_fill_usdt=str(sum((D(t['gross_fill_usdt']) for t in engine.trades), D(0))),
        fees_usdt=str(engine.actual.fees),
        funding_usdt=None if engine.unknown_funding else str(engine.actual.funding),
        closed_net_usdt=None if net is None else str(net),
        # Return is measured on ALL committed capital (spot + margin + reserve),
        # not just the derivative margin, which would exaggerate it.
        return_on_total_capital=None if net is None else str(net / capital),

        # --- Quality of the trades ---
        # A trade that nets exactly 0 is not counted as a win.
        win_rate=None if not pnls else sum(p > 0 for p in pnls) / len(pnls),
        worst_trade_usdt=str(min(pnls)) if pnls else None,
        max_drawdown_usdt=str(max_drawdown(engine)),

        # --- Anything left unresolved, plus diagnostics ---
        end_positions={leg: str(q) for leg, q in engine.actual.positions.items()},
        pending_orders=sorted(engine.pending),
        end_state=engine.state,
        rejections=dict(engine.rejects),
        book_health=dict(engine.book_health),
        limitations=list(LIMITATIONS),
    )
