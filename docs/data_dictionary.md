# Data Dictionary and Time Semantics

| Source or output | Field | Unit and purpose |
|---|---|---|
| raw trade CSV | instrument_name, trade_id | Instrument and unique trade ID; deduplication is not done by timestamp |
| raw trade CSV | side, price, size | Aggressor buy/sell; USDT / BTC; spot size is in BTC, swap size is in contracts |
| raw trade CSV | created_time | Unix milliseconds, exchange time; no local receive time |
| raw trade CSV | source | Counted as-is as 0/1; the current official REST docs say 1 means RPI (formerly ELP), and the corresponding semantics in the archive remain to be confirmed |
| raw book JSON | instId, action, ts | Instrument, snapshot/update, Unix milliseconds |
| raw book JSON | bids/asks [price,size,count] | Price, absolute quantity, number of orders; this archive has three columns and must not be treated as the four-column WebSocket format |
| raw book JSON | seqId/prevSeqId/checksum | All missing in this run and not fabricated; completeness is unknown |
| metadata | ctVal, ctMult, ctValCcy | Contracts × face value × multiplier → BTC; currently 0.01 × 1 BTC/contract |
| metadata | lotSz, minSz, tickSz | Order lot size, minimum size, tick size; mapped as Decimal |
| features.csv | ts | Local simulated decision time in ms; reads only quotes already received |
| features.csv | spot_mid, perp_mid | Mid prices observed at that time, not trade prices |
| features.csv | basis_bps, excess_bps, momentum_60s_bps | Basis points; excess references a strictly past window |
| pressure.csv | available_exchange_ms | End time of that minute; using it as a signal additionally requires a receive latency |
| pressure.csv | spot_tp, perp_tp, relative_tp, relative_decay | Aggressor trade value normalized per market; missing if there is no volume; currently includes all sources; not OFI |
| orders.csv | send_ms, arrival_ms, report_ms | Time sent, time arrived at the exchange, time the fill report was received |
| fills.csv | quantity_btc, price, fee_usdt | Base-currency quantity filled at each level, USDT/BTC, fee in USDT |
| trades.csv | gross_fill_usdt, fees_usdt, funding_usdt, net_usdt | Cash flows from the same public ledger; an empty CSV means there were no trades |
| equity.csv | equity_usdt, residual_btc, state | Total configured capital + PnL marked at mid, residual BTC (spot + perp), current known state |
| funding.json | fundingTime, realizedRate | Actual settlement time and final rate; cannot be used as past entry information |

In this run, a book's `valid` flag only means that a reconstructable snapshot and updates exist and that no format or ordering errors were detected; `sequence_verified` remains false. Each second, the strategy checks that both legs are non-empty, that bid < ask, and that the data is not stale (≤ 2 seconds). The quality report does not rewrite "no anomalies found" as "the raw data has no gaps."

The local SHA256 of each compressed file is recorded in `downloads.json`; it proves which file this run of the code used, and is not a checksum issued by the exchange. Raw data is not committed to Git, while processed files and reports can be regenerated. The full UTC day of raw data has been downloaded, but only the first two hours of the order book were checked, and trade statistics likewise describe only the target two hours.

Whether source=1 liquidity can be obtained by an ordinary API taker is a separate question. Pressure, as observed market information, currently includes these trades, so no equivalent liquidity should be added to our orders on that basis. V0 does not use pressure and is therefore unaffected by this candidate definition.

