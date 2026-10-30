# First-Round Results, October 30, 2026

The real-data download, the two-hour order book replay, the zero-trade V0 report, the synthetic fill ledger, and 18 tests are complete. **The strategy has not been shown to be profitable, and no full-day, one-week, or out-of-sample study has been done.**

## Inputs and Downloads

The handoff prompt, the 14-page Project Guide, and all 19 index entries of the Reading Guide were fully checked. I also checked the titles, versions, abstracts, and relevant topics of the six paper/introduction attachments, and identified the two arbitrage materials as a two-page introduction and a 56-page paper. I do not claim to have reproduced all the papers in full.

The workspace originally contained only a Git directory, so no existing research code was overwritten. All implementation from this round is in the current workspace, and the original attachments were not modified.

From OKX's official public endpoints I obtained the following for BTC-USDT and BTC-USDT-SWAP: the 400-level order books of both legs for 2026-10-23, both legs' trades for the 23rd and 24th (UTC+8 day boundaries), the current contract specifications, and the funding history for the study day. The six compressed files total 606,258,642 bytes, about 606.3 MB. All ZIP/GZIP CRC checks passed, and SHA256 values were saved. This proves the downloaded files can be fully decompressed; it does not prove that the exchange's messages are free of omissions.

Download manifest: `data/manifests/downloads.json`. Integrity: `archive_integrity.json`. Attachment fingerprints: `input_documents.json`. Everything was obtained free of charge from public sources, with no API keys or purchases.

## Actual Processing Scope and Quality

The raw full-day files have been downloaded, but the event-by-event order book reconstruction covers only **2026-10-23 00:00-02:00 UTC**. A 30-minute warm-up is used, explicitly labeled as a debugging warm-up; the originally planned 24 hours requires adding samples from the previous day. This debug window is not treated as the final test set.

| Metric | Spot | Perpetual |
|---|---:|---:|
| Order book messages processed | 355,299 | 619,418 |
| Snapshots | 8 | 8 |
| Messages missing sequence fields | 355,299 | 619,418 |
| Time reversals | 0 | 0 |
| Trade records in target two hours | 35,678 | 227,138 |
| Duplicate trade IDs | 0 | 0 |
| source=1 trades | 251 | 635 |

The archive contains only the action and a millisecond ts. It has no seqId/prevSeqId and no local receive time. A restricted exchange-time study is therefore allowed, but **sequence continuity is unverified**. There were 7,199 valid per-second decision observations; the first decision at the start was rejected because no quotes had arrived yet. There was no interpolation and no future nearest-match. Future completeness assessment still requires live sequence or vendor evidence.

## Why V0 Did Not Open Any Positions

Across the valid per-second observations, basis had a minimum of −5.7822 bps, a median of −4.1477 bps, and a maximum of −2.4632 bps. The perpetual was consistently cheaper than spot throughout this window. V0 allows only the positive-premium direction, so all 2,999 decisions during the entry-allowed period were rejected by the positive-basis condition.

![Mid prices of both legs and basis, from real data](../outputs/okx_20261023_debug_v0/basis.png)

Result: orders=0, fills=0, closed trades=0, ending inventory=0. An empty trade table with a field header row was generated instead of fabricating a trade. Gross PnL, fees, funding, and net cash flow are all 0; this is the account identity result of **not trading**. Win rate and worst trade are blank, and this should not be read as zero risk or as costs having been validated.

Fees use the illustrative scenario of 10 bps per trade for spot and 5 bps per trade for the perpetual; feed/order/report latencies are assumed to be 100/150/100 ms. Because there were no real sample orders, the economic impact of these cannot be estimated from this round. Actual account fee rates, historical rules, and margin/liquidation have not been verified. The funding reference price is missing, so planned trades that cross a settlement point are blocked; the missing cash flow must not be treated as 0.

## Verified Program Behavior

The 18 tests cover: a teaching example with gross profit +2; equal dollar gains offsetting each other; absolute-quantity overwrite and deletion at quantity 0; rejection when sequence is missing; heartbeat/duplicate/reset; the VWAP of 100006; partial fill when depth is insufficient; spread crossing and fee loss in a static market; positive and negative funding and actual quantities; UTC/UTC+8 boundaries; the same timestamp with different trade_ids; future data not altering past features; warm-up gaps; time-based purge; contract multiplier; quotes at order arrival; report latency; unwind after a partial fill; and an open position at the end of data.

`outputs/synthetic_demo` also contains a complete simulated order/fill/trade table: with artificial prices and a two-second holding period, one trade was produced, with gross −0.02 USDT, fees 3.003015 USDT, and net −3.023015 USDT. This only checks the ledger and the state machine. It is not a historical backtest and must not be merged with the real zero-trade result.

Both the first and the final replay are recorded in `outputs/experiment_register.jsonl`, and the two results are identical. The later version added quality metrics and Decimal unit conversion. Each record keeps the run command, parameters, Python version, and source fingerprint; all attempts are retained.

## Reproducible Commands

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/synthetic_demo.py
PYTHONPATH=src python3 -m qis_spot_perp.cli run --config configs/debug.json
```

The core has no third-party dependencies; this round used Python 3.14.2. See the README for the download, manifest, archive-integrity, and plotting commands. A live collection script is ready, with duration and byte limits, but it was not run online this round; the endpoint implementation is not to be described as validated real collection.

## Most Valuable Next Experiment

Fix a continuous date range in advance, add a 24-hour warm-up, and then count whether there are enough positive-premium episodes. If an entire week lacks events suited to this direction, report that this direction lacks opportunities in that period, rather than removing the positive-basis condition or picking only the profitable days.

Once there are real trades, first verify each fill, the historical fees and their currency, the funding reference price, and the margin path, then compare the incremental contributions of pressure and momentum separately. No Sharpe ratio or confidence interval is given for the two-hour sample, and synthetic correctness is not to be taken as evidence of executable returns.

---
