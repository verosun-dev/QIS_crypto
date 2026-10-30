# Reading Guide: Overview and Shortest Reading Route

The 19 index items in the original DOCX have been checked. What follows are reading assignments; they do not mean that all papers have been read closely or reproduced. The attached Project Guide has been checked in full; for the papers, mainly the title, version, abstract, and related topics were checked. Books whose full text was not provided are not a prerequisite for starting to code, and none were purchased.

## What to bring back from each item

| No. and material | What it covers and how it relates to this project | Where to look first | Deliverable that can be implemented | What cannot be directly inferred |
|---|---|---|---|---|
| 01 Fundamentals of Perpetual Futures, He et al. | Funding, pricing without an expiry, and friction bounds; explains that a perpetual being expensive does not mean it is mispriced | Abstract, contract setup, price bounds including transaction costs; the attachment is the September 2026 draft, 109 pages, so it can be read later | A one-page cash flow for spot/perpetual/funding/margin | Theoretical arbitrage returns are not returns we can trade |
| 02 Crypto Carry, Schmeling et al. | Leverage demand and arbitrage capital constraints; explains why premiums persist | Attachment is BIS WP1087, 2023 version; 3.1 positioning, 3.3 capital, 2.4 decomposition, verified by heading | A checklist of financing, margin, capital usage, and market state | Convergence at expiry for dated futures cannot be taken as 30-minute convergence for a perpetual |
| 03 Trading and Arbitrage, Makarov/Schoar | Cross-venue and cross-country market segmentation | Arbitrage operations, capital-flow constraints, and spread persistence; the 56-page attachment is the 2019-02-17 draft | An explanation of why the first version is same-venue, and a sketch of future cross-venue capital positions | Cross-venue spot evidence is not evidence of spot–perp returns |
| 04 Algorithmic Trading, Chan | Turning a mean-reversion hypothesis into a backtestable rule | 2013 edition, chapters 1–3; chapter 5 as needed; Kalman filter deferred | A specification of variables, formation window, trading window, rules, and costs | Parameters from the book cannot be ported directly |
| 05 Pairs Trading, Gatev et al. | Separation of the pair formation period from the trading period | Formation/trading, return definition, costs, and robustness; the working paper and journal version may have different chapters | A time split and a control with no look-ahead leakage | No need to use the full sample to pick the "best-looking" BTC combination |
| 06 Statistical Arbitrage in US Equities, Avellaneda/Lee | Common factors and residual deviations | 2.3, 3, 4/4.1; PCA deferred | A check of whether the matched P&L still carries BTC directional exposure | The hedge ratio must not be fitted arbitrarily to get prettier residuals |
| 07 Hyperliquid official docs | Funding, oracle/mark, contracts, and visible quotes | Funding, WebSocket, Info/Perpetuals | A table of field meanings, known-at times, units, and rule versions | HL rules such as hourly settlement cannot be ported to OKX |
| 08 Binance local order book | Correctly joining the initial snapshot to the incremental updates | Snapshot, buffering, sequence, deleting at zero quantity, rebuild after disconnect | Order book tests that can be checked by hand, event by event | Binance spot, Binance futures, and OKX do not share the same sequence rules |
| 09 Tardis historical data notes | Historical data coverage, vendor receive time, collection gaps | Date/channel coverage, local timestamp, disconnect | A table of gap intervals and availability; look at a sample before deciding whether to pay | Having an interface does not mean the specified date is complete; vendor receive time is not our local time |
| 10 Price Impact of Order Book Events, Cont et al. | Order book event OFI and contemporaneous price impact | Attachment is the 2011 draft; 2.1 variables, empirical depth, comparison with trade-volume imbalance | OFI computed from best-quote changes, compared separately against TP | Contemporaneous explanatory power is not future prediction; an equity sample is not validation for trading BTC |
| 11 Queue Imbalance, Gould/Bonart | Predicting the direction of the next tick from best bid/ask queues | 5, 6.2, 6.3, located by section topic | QI=(bid size−ask size)/(sum of the two), calibrating next-tick probabilities | The next tick is not a 30-minute basis reversion |
| 12 Fragmentation Price Formation and Cross-Impact, Albers et al. | BTC cross-market features, lead-lag, and trade realization | 2 data, 3.1 features, 3.3 horizon, 6 maker | A separate comparison of two-leg pressure and price features; a horizon-decay chart | Sub-second historical returns and fee rates cannot be copied directly |
| 13 Cross-Impact of OFI, Cont et al. | Order flow information from the own market and other markets | 2.1 definitions, 3 contemporaneous, 4.1–4.3 forecasting | An ablation: basis-only / plus perp pressure / plus both-leg pressure | Cross-market correlation is not causation; there is no need to build a large factor system |
| 14 Periodicity, Hansen et al. | Intraday patterns in volatility and liquidity | 3, 5, 5.2, and figures A.1–A.4 | A cost table grouped by UTC hour, weekday, and distance to funding | Active hours are not an automatic buy/sell signal |
| 15 Trading and Exchanges, Harris | Market makers, liquidity, and the cost of immediate execution | The original DOCX recommends chapters 13, 19, 21; the prompt adds chapter 14 on spread; verify against the table of contents of the edition actually used | A decomposition of mid → bid/ask → depth/latency/fees | A spread already included in the fill must not be deducted a second time |
| 16 Limit Order Strategic Placement, Lehalle/Mounjid | Maker adverse selection, queueing, and latency | 2, 4.1.1, 4.1.4, 4.2 | Fill probability, waiting time, post-fill price change, and unhedged exposure | A trade touching our quoted price does not mean our order was reached in the queue |
| 17 HftBacktest docs | Replay assumptions for fill/queue/latency | Fill models, queue, feed/order/response latency | A list of simulator assumptions and tests; can be borrowed from without importing the library right away | The library running does not mean there is real market feedback or an exact queue |
| 18 Probability of Backtest Overfitting, Bailey et al. | Selection bias from picking among rules many times | 2.1, 3.1, 3.2; CSCV deferred | A register of all attempts, a time-based split, and episode-block uncertainty | A single holdout cannot fix look-ahead leakage or incorrect fills |
| 19 Optimal Mean Reversion Trading, Leung/Li | The effect of costs and stop-losses on the boundaries under an OU process | Attachment is arXiv v3, 2015-05-15; model setup and numerical examples | A comparison of target-exit and stop-loss rules after the fixed holding period | Assuming mean reversion is not evidence that mean reversion exists |

## Four shortest routes

- Everyone first reads the Project Guide and the mechanism section of 01, and independently hand-computes the +2 and −1.017 USDT in docs/project_explained.
- **Group A (data):** 08 → 09 → the OKX official documentation actually used. The first deliverable is a data dictionary, unit mapping, gap list, and sequence-recovery tests for both legs over the same UTC interval.
- **Group B (signals):** 04 → 12 → 10. The first deliverable is three variables computed only from past data: excess, relative pressure decay, and momentum; 11 and 13 come later.
- **Group C (backtest):** 04 → 18 → 17, with 05 as a supplement. The first deliverable is a state machine and ledger that can be checked trade by trade, plus a time-split plan.
- **Group D (execution):** 15 → 17, then 16. The first deliverable is the fee rate/currency for the four trades, depth cost, latency, single-leg failure, and margin constraints.

02 helps explain the economic source; 03 is for the cross-venue extension; 06 is for broader statistical arbitrage; 14 explains differences by time of day; 19 is for later exit work. After each reading, bring back one table, one formula, or one test; the deliverable is not measured by how many papers were read.

## Notes on attachment discrepancies

`Trading and Arbitrage in Cryptocurrency Markets.pdf` is a two-page introduction to the authors' article, and `trading-and-arbitrage-in-crypto-markets.pdf` is the 56-page paper; they are not two different studies. `Fundamental of Perpetuals.pdf` is actually titled with the plural, Fundamentals, and its version is September 2026. Chapter numbers follow the attachment and the version in use at the time.

The original Project Guide first introduces Binance as a convenient source, and the handoff prompt further prioritizes OKX; this round uses the same-venue two legs from OKX that were actually obtained. The original Guide calls V2 the cost filter, whereas in the prompt V2 is momentum alone and V3 is the cost filter; this project follows the prompt's naming and currently runs only V0.

The paper links and the original 19-item catalog are preserved in the user's handoff file; this table was written from the attached Reading Guide and does not describe papers that have not been closely read as reproduced results.

---
