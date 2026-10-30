# Source guide

The source follows the research pipeline: **read market data → compute signals → simulate execution → account for positions → evaluate results**.

Start with [the annotated tree](../../docs/repository_structure.txt) and [architecture and interfaces](../../docs/architecture.md). To trace an actual run, read [`backtest/runner.py`](backtest/runner.py), then [`backtest/engine.py`](backtest/engine.py).

| Directory | Responsibility | Entry point |
|---|---|---|
| [`core/`](core/) | Match instrument units and valid quantities | `instruments.matched_units` |
| [`data/`](data/) | Read original archives, rebuild books, retain provenance | `archives.book_events`, `orderbook.Book` |
| [`features/`](features/) | Compute trailing basis and completed-minute pressure | `basis.Features`, `order_flow.pressure_rows` |
| [`strategies/`](strategies/) | Decide whether a V0 signal is eligible | `basis_threshold.entry_rejection` |
| [`execution/`](execution/) | Fill IOC orders against arrival-time depth | `taker.sweep` |
| [`risk/`](risk/) | Check funding crossings and known-account loss | `controls.entry_crosses_funding`, `controls.loss_limit_hit` |
| [`backtest/`](backtest/) | Coordinate events, order reports, recovery, and accounting | `runner.run`, `engine.Replay`, `accounting.Account` |
| [`evaluation/`](evaluation/) | Summarize debug results and purge crossing labels | `metrics.summarize`, `splits.purged_split` |
| [`reporting/`](reporting/) | Write tables and experiment records | `artifacts.save_run` |

Three distinct states matter: **exchange books** determine fills, **observed books** determine signals after feed delay, and **known accounts** reflect fills only after report delay. The engine keeps them separate.

The implemented strategy is the [two-hour V0 debug](../../docs/baseline_spec.md). Trade pressure is diagnostic. Multi-day V0.1, OFI, maker execution, and paper trading are future work described in the architecture; they are not hidden behind placeholder files.

From the repository root:

```bash
make test
make replay
```

`make replay` requires the downloaded archives. See the [root README](../../README.md) for acquisition and reproduction commands.
