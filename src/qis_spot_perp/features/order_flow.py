"""Aggressive trade-notional pressure; this is not order-book OFI."""


def trade_pressure(buy_notional, sell_notional, minimum=0):
    total = buy_notional+sell_notional
    return None if total <= minimum else (buy_notional-sell_notional)/total


def pressure_rows(minute_values, start, end):
    """Label completed-minute diagnostics by earliest exchange availability.

    A strategy consumer must also add feed latency. V0 does not consume these rows.
    """
    features=[]
    prev_relative=None
    for minute in range(start//60000,end//60000):
        s=minute_values['spot',minute]; p=minute_values['perp',minute]
        sp,pp=trade_pressure(*s),trade_pressure(*p)
        relative=None if sp is None or pp is None else pp-sp
        features.append(dict(available_exchange_ms=(minute+1)*60000, spot_tp=sp,perp_tp=pp,
                             relative_tp=relative,relative_decay=None if relative is None or prev_relative is None else prev_relative-relative,
                             spot_notional=sum(s),perp_notional=sum(p)))
        prev_relative=relative
    return features
