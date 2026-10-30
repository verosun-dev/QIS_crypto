# QIS Spot–Perpetual Research

We study whether an unusually positive perpetual premium predicts enough subsequent convergence to cover the costs of buying spot and shorting an equal BTC quantity of a linear perpetual. **No profitable edge has been established.**

The first run downloaded free public OKX archives and completed a **two-hour engineering debug**. Every sampled basis observation from 23 October 2026, 00:00–02:00 UTC was negative, so the positive-basis V0 rule opened no positions. This is a valid no-trade result, not evidence of profitability or unprofitability. Synthetic examples remain separate from real-data outputs.

## Start here

1. [Project explained](docs/project_explained.md): the trade, cash flows, and how a +2 USDT gross example becomes −1.017 USDT after illustrative fees.
2. [Reading map](docs/reading_map.md): all 19 readings, what to focus on, and the shortest route for each workstream.
3. [Workstream guide](docs/team_workstreams.md): data acquisition, granularity, signals, backtesting, execution, and shared deliverables.
4. [First-run results](docs/first_run_results.md), [machine-readable summary](outputs/okx_20261023_debug_v0/summary.json), and [basis chart](outputs/okx_20261023_debug_v0/basis.png).
5. [Baseline review](docs/baseline_review.md): the English review of the proposed V0.1 specification, including decisions still needed before implementation.

The [implemented debug specification](docs/baseline_spec.md) describes the current code. The proposed one-week V0.1 experiment is **not implemented or completed** by this documentation update.

## Run locally

Run from the repository root. The core uses only the Python standard library; no third-party installation is required. The recorded run used Python 3.14.2. Package metadata requires Python 3.10 or newer; other versions have not all been tested.

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/synthetic_demo.py
```

With the raw archives downloaded, replay the real sample:

```bash
PYTHONPATH=src python3 -m qis_spot_perp.cli run --config configs/debug.json
```

Each replay appends an experiment record. `outputs/synthetic_demo` contains **synthetic tests only**. The real-data debug run is under `outputs/okx_20261023_debug_v0`.

## Obtain the sample

List the files and sizes before downloading:

```bash
python3 scripts/fetch_sample.py --date 2026-10-23
python3 scripts/fetch_sample.py --date 2026-10-23 --download --max-mb 700
python3 scripts/check_archives.py
PYTHONPATH=src python3 -m qis_spot_perp.cli manifest
PYTHONPATH=src python3 -m qis_spot_perp.cli run --config configs/debug.json
```

No API key is needed for these public requests. The six downloaded archives total 606,258,642 bytes. Raw files are excluded from Git; the repository includes download scripts, manifests, checksums, and small reports. Coverage must still be checked when rerunning against the provider.

The downloader handles one UTC research day for this pair. It includes adjacent trade-file dates where required by UTC+8 archive boundaries. Preserve date-specific manifests before extending acquisition: current metadata filenames are reused. Existing archives are retained, and failed downloads leave `.part` files for inspection. The replay currently reads one book archive per leg; a multi-day replay requires implementation work, not just a longer date range in the configuration.

A 24-hour lookback needs preceding-day data and correct continuity across midnight. Do not relabel the shortened debug warm-up as a full evaluation.

## Optional chart and bounded collection

Optional dependencies are pinned in [requirements-optional.txt](requirements-optional.txt). Install them only for plotting or public WebSocket capture:

```bash
python3 -m pip install -r requirements-optional.txt
MPLCONFIGDIR=tmp/matplotlib python3 scripts/plot_debug.py
```

The collector is implemented but was **not network-tested in the first run**. Confirm the current official public WebSocket endpoint for the applicable region before using this candidate command:

```bash
python3 scripts/collect_public.py --url 'wss://ws.okx.com:8443/ws/v5/public' --seconds 30 --max-mb 25 --output data/raw/live-public.jsonl
```

It subscribes only to `books` and `trades`, defaults to 30 seconds, and limits configuration to 300 seconds and 100 MB. It refuses to overwrite an output file, records disconnections, and stops. A new run must obtain a new snapshot. It has no trading permissions or persistent background service. Do not change endpoints to bypass access restrictions.

## Code and specifications

| File | Responsibility |
|---|---|
| `src/qis_spot_perp/data.py` | Streaming archives, UTC boundaries, trade-ID deduplication, pressure, SHA256 |
| `src/qis_spot_perp/book.py` | Decimal L2 reconstruction, sequence handling, visible-depth IOC matching |
| `src/qis_spot_perp/features.py` | Causal rolling basis, momentum, trade pressure, basic timestamp purge |
| `src/qis_spot_perp/replay.py` | Exchange, observed, and reported states; latency; partial-fill recovery |
| `src/qis_spot_perp/accounting.py` | Fill cash flows, inventory, per-fill fees, funding direction |
| `configs/debug.json` | Debug parameters and limitations |
| `tests/test_research.py` | Hand calculations, sequencing, timing, latency, partial fills, data boundaries |

See the [baseline specification](docs/baseline_spec.md), [instrument specification](docs/instrument_spec.md), and [data dictionary](docs/data_dictionary.md). Download URLs, sizes, and SHA256 fingerprints are in `data/manifests/downloads.json`. Recorded commands, parameters, and source fingerprints are in `outputs/experiment_register.jsonl`.

## What the current results cannot establish

- Full-day archives were downloaded, but only the first two hours of books were parsed. The 30-minute warm-up is a debug choice. No final out-of-sample test exists.
- The archives lack `seqId`/`prevSeqId` and local receipt timestamps. Successful decompression does not establish market-message completeness.
- Fees and latency are scenarios. Historical account fees and contract rules have not been fully verified.
- Missing funding reference prices restrict settlement-crossing trades. There is no validated liquidation, maker queue, or market-response model.
- With no real-sample trades, the execution and cost model has not been exercised through real-sample entries and exits. Synthetic tests establish limited code properties only.

The next research step is to extend a predetermined continuous window, add a full 24-hour warm-up, and obtain sequence and receipt-time evidence. Do not remove the positive-basis rule or select favorable dates simply to manufacture trades.
