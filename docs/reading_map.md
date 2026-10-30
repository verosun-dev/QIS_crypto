# Reading map and shortest routes

This map follows the 19 entries in the supplied Reading Guide. It assigns reading tasks; it does not claim that every paper has been fully read or replicated. The Project Guide was reviewed in full. For the supplied papers, the initial review checked titles, versions, abstracts, and relevant themes. Unavailable books are not prerequisites for starting the implementation, and no purchases were made.

## What to bring back from each reading

| Reading | Subject and relevance | Read first | Practical output | Limit on interpretation |
|---|---|---|---|---|
| **01 Fundamentals of Perpetual Futures**, He et al. | Funding, pricing without maturity, and friction-dependent bounds; a premium need not be a mispricing. | Abstract, contract setup, and price bounds with costs. The supplied 109-page draft is dated September 2026; proofs can wait. | One page explaining spot, perpetual, funding, and margin cash flows. | A theoretical arbitrage result is not our executable return. |
| **02 Crypto Carry**, Schmeling et al. | Leveraged demand and limited arbitrage capital explain persistent premia. | Supplied 2023 BIS WP1087: positioning in 3.1, capital constraints in 3.3, decomposition in 2.4; verify section headings. | Financing, margin, capital occupancy, and market-state checklist. | Dated-futures convergence at maturity does not imply perpetual convergence in 30 minutes. |
| **03 Trading and Arbitrage in Cryptocurrency Markets**, Makarov and Schoar | Fragmentation across venues and countries. | How trades are implemented, capital-flow constraints, and persistent gaps. The 56-page attachment is dated 17 February 2019. | Explain the same-venue starting point and map collateral locations for future cross-venue work. | Cross-venue spot evidence is not spot–perpetual evidence. |
| **04 Algorithmic Trading: Winning Strategies and Their Rationale**, Chan | Turn a mean-reversion hypothesis into an explicit backtest. | Chapters 1–3 of the 2013 edition; chapter 5 as needed. Defer Kalman filters. | Variables, formation/trading windows, trading rules, and cost assumptions. | Book parameters are not validated settings for this market. |
| **05 Pairs Trading: Performance of a Relative-Value Arbitrage Rule**, Gatev et al. | Separate pair formation from later trading. | Formation/trading periods, return construction, costs, and robustness. Working-paper and journal versions differ. | Chronological splits and leakage checks. | Do not use the full sample to select the most attractive BTC relationship. |
| **06 Statistical Arbitrage in the U.S. Equities Market**, Avellaneda and Lee | Common factors and residual relative movements. | Sections 2.3, 3, and 4/4.1; defer PCA. | Diagnose whether matched-pair P&L still depends on BTC direction. | Do not fit a complex hedge ratio just to smooth the spread. |
| **07 Hyperliquid trading and API documentation** | Funding, oracle/mark prices, contract units, and available feeds. | Funding, WebSocket subscriptions, and Info/Perpetuals. | Field meanings, availability times, units, and rule versions. | Hyperliquid-specific settlement rules cannot be copied into OKX accounting. |
| **08 Binance local order-book documentation** | Connect an initial snapshot to incremental updates. | Snapshot buffering, sequence checks, zero-size deletion, and reconnection. | A reconstructor that can be checked event by event. | Binance spot, Binance futures, and OKX do not share one sequence protocol. |
| **09 Tardis historical data details and FAQ** | Coverage, vendor receipt times, and collection gaps. | Instrument/date/channel coverage, local timestamps, and disconnect behavior. | Availability and missing-interval report; inspect samples before considering payment. | An endpoint does not prove date coverage; a vendor timestamp is not our server's receipt time. |
| **10 The Price Impact of Order Book Events**, Cont et al. | OFI and contemporaneous price impact. | Supplied March 2011 draft: variable definitions, depth results, and comparison with trade imbalance. Follow topics if numbering differs. | Implement best-quote OFI and compare it with trade pressure. | Contemporaneous fit is not prediction; equity evidence is not BTC execution evidence. |
| **11 Queue Imbalance as a One-Tick-Ahead Price Predictor**, Gould and Bonart | Best-quote queues and the next mid-price movement. | Sections 5, 6.2, and 6.3, checked by topic. | `QI = (bid size − ask size) / (bid size + ask size)` and probability calibration. | Predicting the next tick does not imply predicting 30-minute basis convergence. |
| **12 Fragmentation, Price Formation, and Cross-Impact in Bitcoin Markets**, Albers et al. | Cross-market BTC features, lead/lag, and execution. | Section 2 on data, 3.1 on features, 3.3 on horizons, and 6 on maker execution. | Separate comparisons of two-leg pressure and price features; signal-decay plots. | Historical subsecond returns and fees cannot be transferred directly. |
| **13 Cross-Impact of Order Flow Imbalance in Equity Markets**, Cont et al. | Information in own-market and related-market flows. | Definitions in 2.1, contemporaneous relationships in 3, prediction in 4.1–4.3. | Compare basis-only, basis plus perpetual pressure, and basis plus both legs. | Cross-market correlation is not causation; a large factor system is unnecessary here. |
| **14 Periodicity in Cryptocurrency Volatility and Liquidity**, Hansen et al. | Intraday and weekly activity patterns. | Sections 3, 5, 5.2, and figures A.1–A.4. | Costs and outcomes grouped by UTC hour, weekday, and funding proximity. | An active time of day is not a directional trading signal. |
| **15 Trading and Exchanges: Market Microstructure for Practitioners**, Harris | Dealers, liquidity, and the cost of immediacy. | The Reading Guide recommends chapters 13, 19, and 21; the handoff also adds chapter 14 on spreads. Check the edition's contents. | Decompose mid-based P&L into bid/ask, depth, latency, and fees. | Never deduct costs already embedded in fill prices twice. |
| **16 Limit Order Strategic Placement with Adverse Selection Risk and the Role of Latency**, Lehalle and Mounjid | Maker adverse selection, waiting, and latency. | Sections 2, 4.1.1, 4.1.4, and 4.2. | Fill probabilities, waiting times, post-fill price moves, and unhedged exposure. | A price touching our limit does not establish our queue fill. |
| **17 HftBacktest documentation** | Fill, queue, and latency assumptions in market replay. | Fill models, queue assumptions, and feed/order/response latency. | Simulator assumptions and meaningful tests; adopting the library is optional. | A running library does not establish market feedback or exact queue position. |
| **18 The Probability of Backtest Overfitting**, Bailey et al. | Selection bias from trying many rules. | Sections 2.1, 3.1, and 3.2; defer CSCV details. | Complete experiment register, chronological splits, and episode/block uncertainty. | One holdout does not repair leakage or incorrect fills. |
| **19 Optimal Mean Reversion Trading with Transaction Costs and Stop-Loss Exit**, Leung and Li | How costs and stop-loss rules affect OU-based entry/exit regions. | Supplied arXiv v3, dated 15 May 2015: setup and numerical examples. | Compare alternative exits after the fixed-horizon baseline. | Assuming mean reversion is not evidence that it exists. |

## Shortest route by workstream

- **Everyone:** Project Guide and the mechanism in 01. Independently reproduce the +2 USDT gross and −1.017 USDT net teaching calculations in [Project explained](project_explained.md).
- **A — Data:** 08 → 09 → the actual OKX documentation. Deliver a common UTC interval, data dictionary, unit map, gap list, and sequence/recovery tests.
- **B — Signals:** 04 → 12 → 10. Deliver causal excess basis, relative-pressure decay, and momentum definitions. Leave 11 and 13 for later.
- **C — Backtesting:** 04 → 18 → 17, with 05 as supporting material. Deliver an auditable state machine, ledger, and chronological validation plan.
- **D — Execution:** 15 → 17, then 16. Deliver fee/currency rules, depth costs, latency assumptions, one-leg failure behavior, and margin constraints.

Use 02 for economic interpretation, 03 for later cross-venue work, 06 for broader statistical arbitrage, 14 for time-of-day analysis, and 19 for later exit research. Bring back a table, formula, or test rather than a count of papers read.

## Reference entry points

These are reading pointers from the supplied materials, not fresh guarantees of provider coverage or API behavior.

- 01: [Perpetual futures paper](https://arxiv.org/abs/2212.06888)
- 02: [BIS Crypto Carry](https://www.bis.org/publ/work1087.htm)
- 03: [MIT author-paper record](https://dspace.mit.edu/entities/publication/7f91bfb5-ba77-4d0e-9c79-ec75e104e6cc)
- 04: [Algorithmic Trading](https://www.oreilly.com/library/view/algorithmic-trading-winning/9781118746912/)
- 05: [NBER pairs-trading working paper](https://www.nber.org/papers/w7032)
- 06: [Avellaneda and Lee working paper](https://math.nyu.edu/inmemoriam/avellaneda/AvellanedaLeeStatArb071108.pdf)
- 07: [Hyperliquid documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/)
- 08: [Binance spot streams](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md) and [futures book reconstruction](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/How-to-manage-a-local-order-book-correctly)
- 09: [Tardis data details](https://docs.tardis.dev/historical-data-details/overview)
- 10: [Order-book price impact](https://arxiv.org/abs/1011.6402)
- 11: [Queue imbalance](https://arxiv.org/abs/1512.03492)
- 12: [Bitcoin fragmentation and cross-impact](https://arxiv.org/abs/2108.09750)
- 13: [OFI cross-impact](https://arxiv.org/abs/2112.13213)
- 14: [Periodicity](https://arxiv.org/abs/2109.12142)
- 15: [Trading and Exchanges](https://academic.oup.com/book/52292)
- 16: [Limit-order placement and latency](https://arxiv.org/abs/1610.00261)
- 17: [HftBacktest](https://hftbacktest.readthedocs.io/en/latest/)
- 18: [Backtest overfitting paper](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- 19: [Optimal mean-reversion trading](https://arxiv.org/abs/1411.5062)

## Version differences

The supplied `Trading and Arbitrage in Cryptocurrency Markets.pdf` is a two-page introduction; `trading-and-arbitrage-in-crypto-markets.pdf` is the 56-page paper. They are not separate studies. `Fundamental of Perpetuals.pdf` contains the September 2026 draft titled *Fundamentals of Perpetual Futures*. Section numbering should follow the version actually used.

The original Project Guide presents Binance as a convenient starting source; the handoff later prioritizes OKX. This run uses actual same-venue OKX files. The original guide labels the cost filter V2, while the handoff uses V2 for a separate momentum test and V3 for cost filtering. This repository follows the handoff naming and has run only V0.
