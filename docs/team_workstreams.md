# How the four workstreams start

All workstreams share configurations, raw-data manifests, instrument units, and one fill/accounting ledger. Changes to unit matching, timing, or fee currencies must be reflected in the shared specification and a new experiment record.

## A — Data and order-book reconstruction

**Where do trades come from, and must we buy data?** The first run downloaded real OKX public archives without payment or an API key. Run `python3 scripts/fetch_sample.py --date 2026-10-23` to inspect files and sizes. Add `--download --max-mb 700` to download, with a 180-second limit per file. The actual total is about 606.3 MB; the provider's `sizeMB` values are closer to MiB, so do not treat them as decimal MB. Uncompressed data exceeds 3 GB; the code streams it without extracting everything to disk. List and budget longer ranges in bounded segments.

Use the [OKX historical page](https://www.okx.com/historical-data) and [historical API documentation](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-historical-market-data). Module 1 lists trades; module 4 lists 400-level books. The API returns file URLs first. Books use UTC day boundaries, while trade archives use UTC+8. One UTC day therefore requires adjacent trade-file dates. This run downloaded both legs' trade files for 23/24 October and book files for 23 October. Assign records by their timestamps, not filename alone.

A daily file can contain millions of trades; it is not a daily candle. Candles help with broad screening but cannot establish subsecond execution returns. Tick describes event granularity; L1 means best quotes and quantities; L2 means price-level aggregated quantities; L3 means individual orders. The observed historical L2 files contain many updates about 10 ms apart. This differs from the ordinary live `books` channel's described 100 ms cadence and does not imply access to every matching-engine event.

Select markets by matching underlying and settlement currency, overlapping coverage, timing quality, depth, fees, and documented rules. BTC is an engineering starting choice. ETH can be a later external check; do not choose assets by retrospective profitability. Binance official archives are a possible alternative for mechanism screening, but switching sources means switching both legs and recording a new experiment. Consider paid L2 only after identifying a specific gap free sources cannot resolve.

`data.py` streams archives, filters UTC intervals, and deduplicates by trade ID. `book.py` replaces absolute quantities, deletes zero-size levels, and retains deeper levels. Historical files here lack sequence IDs, so they cannot prove message completeness. Live collection should retain raw messages, exchange timestamps, local UTC receipt timestamps, and arrival order. An unchanged quote is not by itself a disconnect; inspect heartbeats and connection health.

First-week deliverables: a continuous-week manifest, data dictionary, missing intervals, cross-leg timing and available receipt-latency evidence, `source=1` trade counts, and sequence-check results. Report unavailable evidence explicitly.

## B — Spread analysis and signals

`features.py` implements basis, excess over a trailing median, and 60-second momentum. `pressure.csv` contains both legs' completed-minute aggressive-notional pressure and its relative decay. V0 does not use pressure.

Fix quantity and holding rules on development data. Study a small, predetermined set of horizons such as 1 second, 10 seconds, 1 minute, 5 minutes, and 30 minutes. Within comparable starting-excess bands, compare convergence and adverse widening when pressure strengthens or weakens. Retain events that do not converge. Add feed delay to a minute feature's `available_exchange_ms` before treating it as locally known.

The exact convergence label is:

```text
Y(t,H) = 10000 × [(P_t − S_t) − (P_(t+H) − S_(t+H))] / S_t
```

With mid-prices this measures ideal gross convergence relative to entry spot notional. `basis_t − basis_(t+H)` is not exactly the same P&L because its denominators differ. After simple conditional comparisons, a candidate regression is `Y = alpha + beta1 × excess + beta2 × pressure_decay + beta3 × momentum + error`. Test additions separately before combining them.

V1 adds only weakening relative pressure. V2 separately adds momentum. V3 can apply a cost filter to a version supported by evidence, using cost estimates available at decision time. Every version still pays modeled costs. Consider OU modeling only after evidence of sufficiently stable mean reversion; no GPU is needed for this baseline.

## C — Backtesting and statistical validation

`replay.py` handles exchange updates, observed messages, order arrivals, and execution reports. `accounting.py` maintains actual fill quantities, fees, and cash-flow identities. Start with `PYTHONPATH=src python3 -m unittest discover -s tests -v`, inspect the synthetic order/fill/trade trace, then audit real-data outputs.

A signal requests orders; it does not change accounting rules. Retain decision, send, arrival, fill, and report times. Keep partial fills, failed orders, and recovery costs. Report outstanding positions at the data boundary. Show returns relative to entry spot notional and total allocated capital separately.

Later, split chronologically into development, validation, and final evaluation, freezing choices before the final interval. Purge outcomes crossing split boundaries and avoid treating one episode on both sides as independent evidence. A basic timestamp purge helper exists; multi-day validation, episode-block bootstrap, robustness reports, and out-of-sample evaluation are not yet implemented. The two-hour no-trade result cannot support confidence intervals or an annualized Sharpe claim.

Second-week deliverables: trade and independent-episode counts; gross, fees, funding, and net decomposition; worst trade; drawdown; adverse widening; holding time and capital use; time-of-day stability; and results excluding the largest winners. Append every attempted version to the experiment register.

## D — Execution, costs, and risk

From the start, verify contract multipliers, lot and tick sizes, minimum quantities, fee currencies, and historical account tiers. A current specification response does not prove historical rules were unchanged. Current fees are scenarios; applicable account rates remain unverified.

Model four taker directions: buy spot at ask, sell perpetual at bid, sell spot at bid, and buy perpetual at ask. Insufficient depth means a partial fill. Handle one-leg failure by a predetermined recovery rule. Distinguish feed, order, and report latency. Scenarios such as 100/500/1000/2000 ms are not measurements. Each tested size must satisfy contract units and available depth.

Still needed: funding reference prices and settlement eligibility; margin equity and maintenance requirements; transfer delays; base-currency fee residuals; financing; and stablecoin exposure. Current results cannot validate liquidation safety. Maker research requires queue, cancellation, and adverse-selection assumptions, not merely a lower fee rate.

This stage has no paid-data purchase, live orders, deployment, or indefinite background capture. Prioritize continuous samples and reliable sequence/receipt-time evidence before adding more signals.
