# First-run results — 30 October 2026

The first iteration completed real-data acquisition, a two-hour book replay, a no-trade V0 report, a separate synthetic fill ledger, and 18 tests. **It has not established profitability or completed a full-day, full-week, or out-of-sample study.**

## Inputs and acquisition

The handoff prompt, 14-page Project Guide, and all 19 Reading Guide entries were reviewed. Titles, versions, abstracts, and relevant themes were checked in six supplied paper/introduction attachments. The similarly named arbitrage files were identified as a two-page introduction and a 56-page paper. This was not a full replication of all readings. Original attachments were not modified or redistributed with this repository.

Public OKX responses supplied BTC-USDT and BTC-USDT-SWAP book archives for 23 October 2026, trade archives for 23/24 October under UTC+8 boundaries, current instrument specifications, and the research day's funding history. Six compressed files total **606,258,642 bytes**, approximately 606.3 MB. All ZIP/GZIP compression CRC checks passed, and local SHA256 fingerprints were saved. This establishes decompression integrity, not completeness of exchange messages.

See `data/manifests/downloads.json`, `archive_integrity.json`, and `input_documents.json` for provenance. Public retrieval required no purchase or API key. The initial implementation began in a workspace containing only Git metadata and did not overwrite existing research code.

## Processed interval and quality

Full-day raw archives were downloaded; event-by-event book reconstruction covered only **23 October 2026, 00:00–02:00 UTC**. A 30-minute lookback was explicitly used for debugging. The proposed 24-hour reference needs preceding-day input. This interval was not treated as a final test set.

| Metric | Spot | Perpetual |
|---|---:|---:|
| Processed book messages | 355,299 | 619,418 |
| Snapshots | 8 | 8 |
| Messages missing sequence fields | 355,299 | 619,418 |
| Timestamp regressions | 0 | 0 |
| Trade records inside the two-hour target | 35,678 | 227,138 |
| Duplicate trade IDs | 0 | 0 |
| Trades with `source=1` | 251 | 635 |

The archive contains actions and millisecond timestamps, but no `seqId`/`prevSeqId` or local receipt timestamps. The run therefore supports restricted exchange-time research with **unverified sequence continuity**. There were 7,199 valid sampled observations. The first decision had no available books and was rejected. No interpolation or future nearest-neighbor match was used. Stronger completeness claims require additional sequence or vendor evidence.

## Why V0 opened no position

Across valid one-second observations, basis ranged from **−5.7822 to −2.4632 bps**, with a median of **−4.1477 bps**. The perpetual was cheaper than spot at every sampled point. Because V0 only trades a positive premium, the positive-basis condition rejected all 2,999 decisions inside the allowed entry interval.

![Observed spot and perpetual mids and basis from real data](../outputs/okx_20261023_debug_v0/basis.png)

Orders, fills, closed trades, and ending inventory were all zero. Header-only order and trade tables were produced rather than invented trades. Gross P&L, fees, funding, and net cash flow were zero because no position was opened. Win rate and worst trade are undefined. This is not evidence of zero risk or verified execution economics.

The configured scenario uses spot fees of 10 bps per fill, perpetual fees of 5 bps per fill, and feed/order/report latency of 100/150/100 ms. With no real-sample orders, this run cannot estimate their effect on trading outcomes. Historical account rates, contract rules, and liquidation behavior remain unverified. Missing funding reference prices restrict planned settlement crossings; missing cash flows are not assigned zero.

## Verified code behavior

The 18 tests cover the +2 USDT teaching calculation; cancellation of equal dollar price changes; absolute-size replacement and zero deletion; missing sequences; heartbeats, duplicate messages, and sequence resets; VWAP of 100,006; insufficient depth; fees and crossing losses in a static market; funding direction and actual quantities; UTC/UTC+8 boundaries; distinct trade IDs sharing a timestamp; causal features; warm-up gaps; timestamp purging; contract multipliers; arrival-time prices; report delay; partial-fill unwinds; and terminal open positions.

`outputs/synthetic_demo` contains an independent artificial order/fill/trade trace with a two-second holding period. It produces one trade with gross P&L **−0.02 USDT**, fees **3.003015 USDT**, and net P&L **−3.023015 USDT**. This checks accounting and state transitions only. It must not be combined with historical results.

The initial and final debug replays are both retained in `outputs/experiment_register.jsonl`. Their trading results agree; the later version added quality metrics and Decimal unit conversion. Records include commands, parameters, Python version, and a source fingerprint. Publishing English documentation does not rerun or revise those historical experiments.

## Reproduce

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/synthetic_demo.py
PYTHONPATH=src python3 -m qis_spot_perp.cli run --config configs/debug.json
```

The core needs no third-party packages; the recorded environment was Python 3.14.2. See the README for download, manifest, integrity-check, and chart commands. The bounded live collector was prepared but not network-tested in this iteration.

## Next experiment

Predetermine a continuous date range, implement multi-day replay, supply a full 24-hour warm-up, and count eligible positive-premium episodes. If the period contains too few opportunities, retain that finding rather than changing direction or selecting favorable days after seeing the result.

When real-sample trades exist, audit fills, historical fees and fee currencies, funding references, and margin paths before interpreting pressure or momentum additions. Do not report a Sharpe ratio or a meaningful confidence interval from this two-hour no-trade sample.
