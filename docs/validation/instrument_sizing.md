# Instrument sizing validation

`matched_units(q, spot_spec, perp_spec)` validates matched BTC exposure and returns Decimal BTC quantity and perpetual contract count. Contract count is BTC quantity divided by `ctVal * ctMult`; an absent or empty multiplier defaults to one. Each leg must satisfy its own minimum quantity and lot increment in that leg's native units.

The saved retrieval-time specifications map 0.01 BTC to one perpetual contract and 0.0001 BTC to 0.01 contracts. Production sizing code and its API are unchanged.

## Verification

The ten tests in [test_instruments.py](../../tests/unit/test_instruments.py) cover saved specifications, exact fractional conversion, nonunit/default multipliers, independent spot/perpetual minimum and lot-step failures, valid boundary quantities, zero/negative quantities, and incompatible contract type, underlying denomination, or settlement currency. Invalid quantities are rejected rather than rounded to fit.

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.unit.test_instruments -v
PYTHONDONTWRITEBYTECODE=1 make test
```

Recorded validation against base `c9e80c9`: ten dedicated tests and 32 total tests passed.

## Evidence boundary

The saved responses establish arithmetic against retrieval-time metadata. They do not prove that the same rules applied on the historical research date. Minimum-notional constraints, tick enforcement, margin tiers, liquidation, account eligibility, and fee conventions are not established by these tests. See the existing [instrument specification](../instrument_spec.md).
