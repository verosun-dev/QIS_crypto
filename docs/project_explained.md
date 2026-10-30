# The spot–perpetual project explained

We want to test whether buying spot and shorting the same underlying quantity of an unusually expensive perpetual can earn enough subsequent spread convergence to pay for four executions and other cash flows. Positive net returns have not been established.

## What one trade earns

The following numbers are synthetic teaching examples. Buy 0.01 BTC spot at 100,000 USDT and short a linear perpetual representing 0.01 BTC at 100,300. Later, sell spot at 101,000 and buy back the perpetual at 101,100.

| Leg | Calculation | Gross P&L, USDT |
|---|---|---:|
| Spot | 0.01 × (101000 − 100000) | 10 |
| Perpetual | 0.01 × (100300 − 101100) | −8 |
| Pair | 0.01 × (300 − 100) | 2 |

Both prices rise, yet the pair earns money because their dollar gap narrows. Equal dollar increases in both legs cancel for matched quantities. Equal percentage increases do not cancel exactly.

Both legs must represent 0.01 BTC. Buying and selling 1,000 USDT of each does not exactly match BTC exposure when prices differ. The retrieved OKX specification assigns 0.01 BTC to one perpetual contract, so this example uses one contract. Decimal arithmetic preserves price and size precision; lot and minimum-size checks remain necessary.

Now apply **illustrative fees**, not verified account rates: 10 bps per spot fill and 5 bps per perpetual fill. Spot fees are 1 + 1.01 = 2.01 USDT; perpetual fees are 0.5015 + 0.5055 = 1.007 USDT. Total fees are 3.017 USDT. With no funding settlement during the holding interval, net P&L is **−1.017 USDT**. If a settlement is crossed, calculate its cash flow separately under the applicable rule; do not prorate funding by minutes held.

If these are already executable fill prices, do not subtract the bid–ask spread again. If committed capital is 1,000 for spot, 200 for derivative margin, and 300 in reserves, the portfolio-return denominator is 1,500, not just the 200 of margin.

## Why the spread may narrow or persist

Spot purchases require capital; perpetual longs obtain leveraged exposure. Aggressive demand for perpetuals can push their price above spot. Arbitrageurs buying spot and selling perpetuals can reduce the gap, but fees, margin, available capital, liquidity, and venue risk constrain that response.

Positive funding commonly transfers cash from longs to shorts. A perpetual has no fixed maturity forcing the two prices to meet. A premium may reflect persistent financing demand or a changed market state. The short can face liquidation before convergence, and a spot profit does not automatically replenish the derivative account's margin.

Keep four prices distinct: an executed trade price; visible bid and ask quotes; the mark used for risk valuation; and an index or oracle reference. Mark and index prices are not automatically executable prices.

## From an observed gap to a testable rule

1. Use same-venue BTC-USDT spot and BTC-USDT-SWAP, with matched BTC exposure and USDT denomination.
2. Define each mid as `(bid + ask) / 2`, and `basis = 10000 × (perp_mid / spot_mid − 1)`, in bps.
3. Estimate normal basis using the median of a strictly preceding window. `excess = current basis − trailing median`. The two-hour debug explicitly uses 30 minutes; the proposed 24-hour reference requires earlier data.
4. Submit simulated IOC taker orders only when basis is positive, excess is at least 2 bps, the books are fresh, and warm-up is complete. The threshold is an engineering default, not an optimized parameter.
5. Hold for 30 minutes after actual hedge completion, subject to specified data, loss-limit, and execution-failure exits. Allow only one paired position.
6. Record depth-dependent fills and per-fill fees in one ledger. Separate ideal gross convergence, fill-based gross P&L, execution loss, fees, funding, and net P&L.

A 30 bps basis with a 28 bps trailing median has only 2 bps of excess. This does not imply 30 bps of available profit or enough convergence to cover the illustrative round-trip fees.

## What the candidate signals ask

For each leg, compute `TP = (aggressive buy notional − aggressive sell notional) / total aggressive notional` over a completed minute. Normalize the two markets separately. Buy notional of 80 and sell notional of 20 gives TP = 0.6. With no activity, return missing rather than zero.

Define `r = TP_perp − TP_spot`, and `d = previous r − current r`. Positive d indicates that the perpetual's relative buying advantage has weakened. Whether this predicts tradable convergence is a hypothesis.

Define `momentum = basis_t − basis_(t−60 seconds)`. Negative momentum means the gap has recently narrowed. Waiting for confirmation may reduce the risk of fading continued expansion, but may also sacrifice a favorable entry. The code calculates momentum; V0 does not use it as a filter.

Trade pressure excludes cancellations and replenishment. Snapshot queue imbalance, QI, and order-book flow imbalance, OFI, are different measures. Test incremental information one feature at a time; contemporaneous explanatory power in a paper is not a demonstrated trading forecast.

## Source context

The supplied 14-page Project Guide introduces cash flows on pages 1–4, mechanisms and signals on pages 5–9, data and execution on pages 10–12, and organization and references on pages 13–14. Its charts are synthetic teaching illustrations. Real-data outputs are stored separately in this repository.

This explanation draws on that guide and the project handoff prompt. The retrieved contract response is in `data/manifests/okx-swap-spec.json`. The explanation specifies a research exercise; it does not establish an executable edge.
