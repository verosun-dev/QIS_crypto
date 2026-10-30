# Spot–Perpetual Project Interpretation

What we are testing: when the perpetual is unusually expensive relative to spot, buy spot and sell an equal quantity of the perpetual. Does the profit from the spread narrowing later cover four fills and the other cash flows? **No positive net profit has been shown so far.**

## What exactly does one trade earn?

The numbers below are teaching numbers, not real market data. Buy 0.01 BTC spot at 100,000 USDT, and short 0.01 BTC of the linear perpetual at 100,300. Later, sell the spot at 101,000 and buy back the perpetual at 101,100.

| Leg | Calculation | Gross profit (USDT) |
|---|---|---:|
| Spot | 0.01 × (101000 − 100000) | 10 |
| Perpetual | 0.01 × (100300 − 101100) | −8 |
| Pair | 0.01 × (300 − 100) | 2 |

The trade makes money even if both prices rise, because what we trade is the narrowing of the spread in dollar terms. If both legs rise by the same dollar amount, the profits offset; a rise by the same percentage does not offset completely.

The quantity must be the same 0.01 BTC of exposure on both sides. Buying and selling 1000 USDT on each side is not strictly hedged, because the prices differ. The OKX perpetual specification obtained here is 0.01 BTC per contract, so this example corresponds to 1 contract. Decimal is used to preserve quantity and price precision, and lot/min size is checked.

Now add **illustrative fee rates**: 10 bps per trade for spot and 5 bps per trade for the perpetual. The two spot fees are 1 + 1.01 = 2.01; the two perpetual fees are 0.5015 + 0.5055 = 1.007. Total fees are 3.017. If no funding settlement falls within this holding period, net profit is **−1.017 USDT**. If the position actually crosses a settlement, funding must be computed separately and must not be spread linearly by minutes held.

If the prices above are already actual fill prices obtained from the real trade direction and depth, the bid-ask spread is not deducted a second time. If the capital allocation in the teaching example is 1000 for spot, 200 for margin and 300 for reserve, the denominator for the portfolio return is 1500, not just 200.

## Why the spread may narrow, and why it may not

Buying spot requires capital, whereas a perpetual long can obtain leveraged exposure. Urgent buying in the perpetual may push it higher. Arbitrageurs buying spot and selling the perpetual would relieve this pressure, but fees, margin, available capital, liquidity, and platform risk limit how quickly they can react.

Positive funding usually means longs pay shorts, but the perpetual has no fixed expiry that forces the two prices to be equal on some day. A high premium may reflect persistent financing demand or a change of regime rather than a temporary mispricing. A short perpetual position may also be liquidated for insufficient margin before the spread converges; paper profit on the spot leg does not mean the perpetual account has received additional margin.

Distinguish the following: a trade price is a transaction that has occurred; bid/ask are visible, executable quotes; mark is a risk valuation price; index/oracle is a reference price. The latter two cannot be used directly as fill prices.

## From an observed spread to a checkable rule

1. Same venue, BTC-USDT and BTC-USDT-SWAP, with USDT and BTC quantities unified.
2. The mid price of each leg is `(bid+ask)/2`; `basis = 10000×(perp_mid/spot_mid−1)`, in bps.
3. Estimate the normal basis using the median of a window before the current time; `excess = current basis − historical median`. This round has only a two-hour debug window, so it explicitly uses the past 30 minutes instead; the formal candidate's 24 hours requires extra data from the previous day.
4. A two-leg IOC taker simulated order may be issued only if basis > 0, excess ≥ 2 bps, the data is fresh, and warm-up is complete. The 2 bps is an engineering default and has been neither optimized nor validated.
5. After the legs are truly balanced, hold for 30 minutes; exit under explicit rules when data is abnormal, the known loss reaches the limit, or one leg fails. At most one pair of positions.
6. Fills level by level and fees per fill go into the public ledger. At the end, look separately at gross profit, execution loss, fees, funding, and net profit.

For example, a basis of 30 bps with a historical median of 28 bps means the anomaly is only 2 bps. This does not imply a 30 bps profit margin, let alone that the roughly 30 bps of illustrative round-trip fees can be afforded.

## What each of the three later signals asks

`TP=(aggressive buy value − aggressive sell value)/(sum of the two)`, computed first from the most recent completed one-minute window, normalized separately for each market. With buys of 80 and sells of 20, TP=0.6. If there is no trading, it returns missing, which must not be treated as zero. `r=TP_perp−TP_spot`; `d=r_previous window − r_current window`, and d>0 is only a candidate condition indicating that the perpetual's relative buying advantage is weakening.

`momentum=basis_t−basis_(t−60 seconds)`; a negative value means the basis has already started to narrow recently. It may reduce the risk of shorting into an expanding spread, but it may also miss the best price. The program currently computes it, but V0 does not use it to filter.

TP does not include cancellations and replenishments. Order book snapshot quantity imbalance (QI) and order book change (OFI) are also different concepts. Test the incremental effect of each one at a time; the contemporaneous explanatory power reported in papers must not be taken as future predictive returns.

In the original Project Guide, pages 1-4 establish the cash flows, pages 5-9 present the mechanism and signals, pages 10-12 call for data and execution, and pages 13-14 are for team organization and sources. Its charts are all teaching synthetic examples; the real outputs of this project are stored separately in outputs.

Sources: the user-provided `Spot_Perpetual_Project_Guide.pdf` (14 pages) and the execution prompt; for the raw response of the current contract specification, see `data/manifests/okx-swap-spec.json`. The funding and strategy interpretation is for the research specification and is not live trading advice or a conclusion about profitability.

---
