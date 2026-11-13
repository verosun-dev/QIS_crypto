# Funding-carry opportunity study

Standalone research scripts for the fixed 2026-10-14 through 2026-11-12 UTC
OKX BTC/ETH/SOL sample. This deliberately uses hindsight to screen historical
opportunities; it does not change the project's trading strategy or replay engine.

- `study.py`: 30-minute windows, funding-centered benchmarks, hindsight selection,
  cost sensitivity, and separate 1/3/7/14-day holding diagnostics.
- `validate.py`: independent Decimal reconstruction of all 127,899 candidate
  asset/windows and 100 exhaustive checks of the non-overlap optimizer.

## Run

Python standard library only. From the repository root, with the original saved
dataset available in `tmp/funding_carry_oracle_20261113`:

```sh
python3 scripts/funding_carry/study.py
python3 scripts/funding_carry/study.py --data-dir tmp/funding_carry_oracle_20261113/ETH
python3 scripts/funding_carry/study.py --data-dir tmp/funding_carry_oracle_20261113/SOL
python3 scripts/funding_carry/validate.py
```

Both scripts accept `--data-dir` for another dataset location. For validation,
pass the parent directory containing BTC inputs and the `ETH` and `SOL` folders.
The dates, universe and expected coverage are specific to this experiment;
changing the sample requires updating those assumptions in both scripts.
Run without Python's `-O` flag, because coverage/accounting checks use assertions.

## Required saved inputs

Raw market data is not committed, and these scripts do not download it. A fresh
clone needs the saved study dataset before running the full calculation.
Each asset directory contains:

- `raw/spot-*.json`, `raw/perp-*.json`: original OKX one-minute candle responses.
- `raw/mark-*.json`: original hourly mark-price candle responses.
- `funding-probe.json`: actual funding history, including boundary coverage.
- `requests.json`: request records with `url` and `path`; only the basename of
  `path` is used to locate the saved response inside `raw/`.
- Optional `study_config.json`: defaults to BTC, quantity 0.01, funding limit 100.
  ETH uses `{"asset":"ETH","quantity":0.25,"funding_limit":400}`;
  SOL uses `{"asset":"SOL","quantity":5.0,"funding_limit":400}`.

Sources: [OKX API documentation](https://www.okx.com/docs-v5/en/), specifically
`/api/v5/public/funding-rate-history`, `/api/v5/market/history-candles`, and
`/api/v5/market/history-mark-price-candles`.

`study.py` writes `results.json` and `source_manifest.json` in each input directory.
After all three studies run, validation writes `independent_validation.json` in
the parent dataset directory. Re-running overwrites these generated files.

## Interpretation

Long spot and short equal base quantity in a linear perpetual. Funding uses
`realizedRate`; candle opens approximate prices and the settlement mark. Fees are
the old scenario of 10 bp per spot fill and 5 bp per perpetual fill, not verified
account fees. Quotes, depth, financing, liquidation and execution uncertainty are
not simulated. Returns use entry spot notional, not account equity.

At these assumptions, none of the 30-minute candidates is profitable after fees.
The 14-day BTC diagnostic has only a small positive average across overlapping
observations. Neither result establishes live profitability or a universal bound.
