"""Absolute-size L2 reconstruction. Decimal prices/sizes retain source precision."""
from decimal import Decimal as D


class Book:
    def __init__(self, multiplier="1", allow_unsequenced=False):
        self.multiplier = D(multiplier)
        self.allow_unsequenced = allow_unsequenced
        self.bids, self.asks = {}, {}
        self.seq = None
        self.valid = False
        self.ts = -1
        self.sequence_verified = False
        self.reason = "no_snapshot"
        self.last_message = None

    def apply(self, event):
        ts = int(event["ts"])
        seq, prev = event.get("seqId"), event.get("prevSeqId")
        if self.last_message == event:
            return "duplicate"
        if ts < self.ts:
            self.valid = False
            self.reason = "out_of_order"
            return self.reason
        if event["action"] == "snapshot":
            self.bids.clear(); self.asks.clear()
            self.valid = True
            self.sequence_verified = seq is not None
        else:
            if not self.valid:
                return "awaiting_snapshot"
            if seq is not None and prev != self.seq:
                self.valid = False
                self.reason = "sequence_gap"
                return self.reason
            # A reset seq < prev is legal when prev matches; empty same-seq is heartbeat.
            if seq == self.seq and seq is not None and (event["bids"] or event["asks"]):
                self.valid = False
                self.reason = "nonempty_same_sequence"
                return self.reason
        if seq is None:
            self.sequence_verified = False
            if not self.allow_unsequenced:
                self.valid = False
                self.reason = "missing_sequence"
                return self.reason
        for side, levels in ((self.bids, event["bids"]), (self.asks, event["asks"])):
            for level in levels:
                price, size = D(level[0]), D(level[1]) * self.multiplier
                if price <= 0 or size < 0:
                    self.valid = False
                    self.reason = "invalid_price_size"
                    return self.reason
                if size == 0:
                    side.pop(price, None)
                else:
                    side[price] = size
        self.ts, self.seq, self.last_message = ts, seq, event
        self.reason = "ok" if self.sequence_verified else "unverified_sequence"
        return self.reason

    def healthy(self, now, max_age):
        return (self.valid and 0 <= now - self.ts <= max_age and self.bids and self.asks
                and max(self.bids) < min(self.asks))

    def mid(self):
        return (max(self.bids) + min(self.asks)) / 2

    def sweep(self, side, quantity):
        """Visible-depth IOC; mutates this simulation book, never invents liquidity."""
        levels = self.asks if side == "buy" else self.bids
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


def matched_units(q, spot_spec, perp_spec):
    q = D(q)
    if perp_spec["ctType"] != "linear" or perp_spec["ctValCcy"] != spot_spec["baseCcy"]:
        raise ValueError("unsupported exposure mapping")
    if spot_spec["quoteCcy"] != perp_spec["settleCcy"]:
        raise ValueError("quote/settlement mismatch")
    contracts = q / (D(perp_spec["ctVal"]) * D(perp_spec.get("ctMult") or "1"))
    for value, spec in ((q, spot_spec), (contracts, perp_spec)):
        if value < D(spec["minSz"]) or value % D(spec["lotSz"]):
            raise ValueError("quantity violates lot/minimum size")
    return q, contracts
