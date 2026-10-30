"""Conservative funding admission and loss checks on reported inventory."""
from decimal import Decimal as D


def funding_in_interval(start, end, settlements):
    # Conservative ties: block boundaries too, because cross-feed ordering is unknown.
    return [x for x in settlements if start <= int(x["fundingTime"]) <= end]


def entry_crosses_funding(t, config, settlements):
    """Include holding, both order/report delays, and the recovery allowance."""
    end = (t + config['holding_ms'] + 2 * config['order_latency_ms']
           + 2 * config['report_latency_ms'] + config['recovery_timeout_ms'])
    return bool(funding_in_interval(t, end, settlements))


def loss_limit_hit(account, start_cash, spot_mid, perp_mid, max_loss):
    """Use known fills and observed mids; this is a trigger, not a guaranteed loss cap."""
    known_pnl = account.equity_pnl(spot_mid, perp_mid) - D(start_cash)
    return known_pnl <= -D(max_loss)
