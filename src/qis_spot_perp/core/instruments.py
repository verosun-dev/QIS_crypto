"""Validate matched BTC exposure against spot lots and linear contract units."""
from decimal import Decimal as D


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
