# How the Four Workstreams Start

All groups share configs, the raw manifest, and a single fill/account ledger. If the two-leg matching, the time definitions, or the fee currency changes, first update the common specification, then generate a new experiment ID.

## A. Data and Order Book

**Where does the trade data come from, and does it need to be purchased?** This round already downloaded real archives from OKX's public historical-data interface; no purchase or API key is needed. Run `python3 scripts/fetch_sample.py --date 2026-10-23` first to view the files and their sizes; add `--download --max-mb 700` to actually download, with a single-file request limit of 180 seconds. In this example the actual size is about 606.3 MB (the official sizeMB is closer to MiB and must not be taken directly as decimal MB), and the raw uncompressed size exceeds 3 GB; the code reads in a streaming fashion rather than decompressing everything. For longer periods, list the manifest in segments first; downloads must not be left unlimited.

Entry points: [OKX historical download](https://www.okx.com/historical-data), [official API](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-historical-market-data). Module 1 is trades and module 4 is the 400-level order book; the API returns the download links first. Order books are by UTC day and trades by UTC+8 day; one full UTC day requires two adjacent trade archives. This round downloaded both legs' trades for the 23rd and 24th and both legs' order books for the 23rd. A record at 01:00 must be assigned by the UTC time inside the row, not by the file name.

A "one file per day" archive can hold millions of records, which is completely different from daily candlesticks. Daily/minute bars can sketch an overview but cannot prove sub-second execution returns. Tick is event-time granularity; L1 is the best quote and its size; L2 is quantity aggregated per price level; L3 is order by order. The current L2 archive often has updates at roughly 10 ms intervals, which does not match the 100 ms description of the ordinary live books channel and is not every event of the matching engine.

Screening first looks at the same underlying, the same quote/settlement currency, concurrent coverage of both legs, time quality, depth, fees, and rules. Prioritizing BTC is an engineering default. ETH can be added, but the coin must not be chosen by the highest return in hindsight. Binance's official archive can serve as an alternative for mechanism screening; when switching, both legs switch together and the run is registered anew, and one leg must not come from OKX with the other from Binance. Commercial historical L2 is to be discussed only when a specific gap cannot be solved for free.

Program entry points: data.py does streaming decompression, UTC filtering, and deduplication by trade_id; book.py overwrites by absolute quantity, deletes at 0, and keeps deep levels. The historical archive has no sequence fields, so this round cannot produce a complete proof of no missed packets; live collection should save the raw message, the exchange ts, the local receive UTC, and the arrival order. A quote that stays unchanged for a long time must be judged together with the heartbeat and must not be treated directly as a disconnect.

Week-one deliverables: a manifest for a continuous week, a field table, gap intervals, the time difference/receive latency between the two legs, the proportion of special source=1 trades, and sequence verification. Do not hand the signal group a fabricated "complete, no gaps" label.

## B. Spread and Signals

features.py currently implements basis, the past-window median excess, and the 60-second momentum; pressure.csv stores the two legs' aggressor-trade-value pressure and its decay by completed minute, and V0 does not use pressure yet.

Suggested order: first fix q and the holding period on the development set; run an event-path study over a few preset horizons: 1 second, 10 seconds, 1 minute, 5 minutes, and 30 minutes; compare, within the same starting excess range, the convergence and the maximum adverse widening when pressure strengthens versus decays. Do not select only the events that ended up converging. The available_exchange_ms of the minute TP also needs the feed latency added before it becomes locally available time.

The precise label is `10000×[(P_t−S_t)−(P_(t+H)−S_(t+H))]/S_t`. When all prices are mids, this is the ideal gross convergence; `basis_t−basis_(t+H)` must not be treated as exactly equal PnL. When appropriate, run `Y=α+β1×excess+β2×pressure_decay+β3×momentum+ε`; do single-variable ablations first, and do not rush to regress on all factors.

V1 adds only the weakening of pressure; V2 adds only momentum; V3 estimates, on a model with supporting evidence, the future costs knowable at the time, and sets a buffer. Every version counts costs; the absence of a cost filter does not mean free fills. An OU model is to be considered only after stable mean reversion has been evidenced; the first version needs no GPU.

## C. Backtest and Statistics

replay.py handles exchange updates, observed quotes, order arrival, and fill reports; accounting.py maintains quantity, fees, and the cash identity based on actual fills. First run `PYTHONPATH=src python3 -m unittest discover -s tests -v`, then review the orders/fills/trades of the synthetic example, and finally check the real sample.

New signals only produce order intents and do not change the ledger formulas. Each trade keeps its decision/send/arrival/fill/report times; partial fills and failed trades must not be deleted. Positions still open at the end of the data are reported explicitly. The denominator for net return uses, respectively, the opening spot notional and the total configured capital.

Later, split by date into development → validation → final, with parameters frozen before final. Remove events whose labels span a boundary; an episode that crosses a boundary also must not be split into two independent samples. A basic timestamp purge helper has been implemented, but the full multi-day split, episode-block bootstrap, robustness checks, and out-of-sample report have not yet been implemented. A two-hour sample with zero trades cannot support a confidence interval or an annualized Sharpe.

Week-two deliverables: for each version, the number of trades, the number of independent episodes, the fee/gross/net decomposition, the worst trade, the drawdown, the maximum adverse widening, the breakdown by time of day and capital usage, and the picture with the largest winner removed. All attempts are appended to experiment_register.

## D. Execution, Costs, and Risk

From day one, verify the contract multiplier, lot, tick, minimum size, fee currency, and historical account tier. The current specification response is a snapshot at the time of retrieval, and it cannot be claimed that the rules were never changed during the historical period. The current fees are scenarios; the applicable account fee rates have not been obtained.

Start with four taker trades: buy spot at the ask and sell the perpetual at the bid; sell spot at the bid and buy the perpetual at the ask. If depth is insufficient, the fill is partial, and a single-leg failure is unwound by the predetermined rule. Latency is split into feed/order/report; 100/500/1000/2000 ms and the like are preset stress scenarios and must not be treated as measurements. Different sizes must satisfy the contract unit, and the depth at that time must be checked.

Items that need to be added separately: the funding reference price, settlement eligibility, margin equity and maintenance requirements, inability to transfer in time, residual fees in coin-margined terms, and financing and stablecoin risk. The current program cannot verify liquidation safety. Maker orders require a separate queue/cancellation/adverse-selection model and must not simply be swapped in with a lower fee rate.

This round involved no purchases, real orders, live deployment, or resident background tasks. The most valuable next work is to expand the continuous sample and record sequence and receive times, giving the signal group a genuinely applicable research interval.

---
