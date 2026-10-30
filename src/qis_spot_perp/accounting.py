from dataclasses import dataclass, field
from decimal import Decimal as D


def paired_gross(q, spot_entry, perp_entry, spot_exit, perp_exit):
    return D(q) * (D(spot_exit)-D(spot_entry)+D(perp_entry)-D(perp_exit))


@dataclass
class Account:
    # Signed perpetual fill cash is a PnL accounting identity, NOT available margin.
    cash_pnl: D = D(0)
    fees: D = D(0)
    funding: D = D(0)
    positions: dict = field(default_factory=lambda: {"spot": D(0), "perp": D(0)})

    def fill(self, leg, side, quantity, price, fee_bps):
        qty, px = D(quantity), D(price)
        signed = qty if side == "buy" else -qty
        fee = qty * px * D(fee_bps) / 10000
        self.positions[leg] += signed
        self.cash_pnl -= signed * px + fee
        self.fees += fee
        return fee

    def settle_funding(self, rate, reference_price):
        amount = -self.positions["perp"] * D(reference_price) * D(rate)
        self.cash_pnl += amount
        self.funding += amount
        return amount

    def equity_pnl(self, spot_mark, perp_mark):
        return self.cash_pnl + self.positions["spot"]*D(spot_mark) + self.positions["perp"]*D(perp_mark)


def funding_in_interval(start, end, settlements):
    # Conservative ties: block boundaries too, because cross-feed ordering is unknown.
    return [x for x in settlements if start <= int(x["fundingTime"]) <= end]
