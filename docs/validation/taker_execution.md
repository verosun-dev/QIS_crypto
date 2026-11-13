# Taker execution validation

The current `sweep(book, side, quantity)` implementation satisfies the tested IOC execution contract; this change adds regression coverage without changing production execution code.

Buys consume asks from lowest to highest price. Sells consume bids from highest to lowest. Returned fills and unfilled quantity use BTC units and Decimal arithmetic. Perpetual book sizes are converted from contracts to BTC by the book multiplier before execution.

## Verification

Four tests in [test_taker.py](../../tests/unit/test_taker.py) cover 24 direction/scenario subcases across spot buy/sell and perpetual buy/sell. They verify unsorted depth is consumed in price priority, single/multiple price levels, exact exhaustion, insufficient depth, an empty requested side, and repeated orders after liquidity consumption. Assertions also check remaining depth, quantity conservation, and an unchanged opposite side.

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.unit.test_taker -v
PYTHONDONTWRITEBYTECODE=1 make test
```

Recorded validation against base `c9e80c9`: four dedicated tests and 26 total tests passed. Existing lifecycle tests continue to cover arrival-time prices, delayed reports, and partial-fill recovery.

## Limits

These synthetic tests validate visible-depth simulation. They do not establish maker queue behavior, market impact, executable historical returns, or historical fee accuracy. Accounting and recovery remain responsibilities of the shared backtest engine and ledger.
