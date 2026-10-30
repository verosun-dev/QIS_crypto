"""IOC matching at order arrival, with explicit partial fills."""
from decimal import Decimal as D


def sweep(book, side, quantity):
    """Visible-depth IOC; mutates this simulation book, never invents liquidity."""
    levels = book.asks if side == "buy" else book.bids
    remaining, fills = D(quantity), []
    for price in sorted(levels, reverse=side == "sell"):
        qty = min(remaining, levels[price])
        if qty:
            fills.append((price, qty))
            levels[price] -= qty
            if not levels[price]: del levels[price]
            remaining -= qty
        if not remaining: break
    return fills, remaining
