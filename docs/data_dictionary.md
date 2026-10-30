# Data dictionary and timing conventions

| Source or output | Fields | Units and interpretation |
|---|---|---|
| Raw trade CSV | `instrument_name`, `trade_id` | Instrument and trade ID; deduplicate by ID, not timestamp. |
| Raw trade CSV | `side`, `price`, `size` | Aggressor buy/sell; price in USDT/BTC; spot size in BTC, swap size in contracts. |
| Raw trade CSV | `created_time` | Unix milliseconds, exchange time. No local receipt timestamp. |
| Raw trade CSV | `source` | Preserve and count 0/1. REST documentation describes 1 as RPI, formerly ELP; archive-specific semantics need further verification. |
| Raw book JSON | `instId`, `action`, `ts` | Instrument, snapshot/update, and Unix milliseconds. |
| Raw book JSON | `bids/asks [price,size,count]` | Price, absolute size, order count. Three archive columns must not be mistaken for a four-column WebSocket format. |
| Raw book JSON | `seqId`, `prevSeqId`, `checksum` | Absent in these files; no values were fabricated. Sequence completeness is unknown. |
| Instrument metadata | `ctVal`, `ctMult`, `ctValCcy` | Contracts × face value × multiplier → BTC; retrieved mapping is 0.01 × 1 BTC per contract. |
| Instrument metadata | `lotSz`, `minSz`, `tickSz` | Size increment, minimum size, and price increment; Decimal conversion. |
| `features.csv` | `ts` | Simulated local decision time in milliseconds; only arrived observations are used. |
| `features.csv` | `spot_mid`, `perp_mid` | Observed mid-prices, not fill prices. |
| `features.csv` | `basis_bps`, `excess_bps`, `momentum_60s_bps` | Basis points; excess uses a strictly preceding reference window. |
| `pressure.csv` | `available_exchange_ms` | Completed-minute boundary. Add receipt delay before using it as locally available information. |
| `pressure.csv` | `spot_tp`, `perp_tp`, `relative_tp`, `relative_decay` | Aggressive-notional pressure normalized per market; missing for zero activity; includes all sources. This is not OFI. |
| `orders.csv` | `send_ms`, `arrival_ms`, `report_ms` | Order transmission, exchange arrival, and local execution-report receipt. |
| `fills.csv` | `quantity_btc`, `price`, `fee_usdt` | Fill quantity in BTC, price in USDT/BTC, and fee in USDT. |
| `trades.csv` | `gross_fill_usdt`, `fees_usdt`, `funding_usdt`, `net_usdt` | Cash flows from the shared ledger. A header-only table means no trades. |
| `equity.csv` | `equity_usdt`, `residual_btc`, `state` | Allocated capital plus mid-marked P&L; spot plus signed perpetual BTC; known order/position state. |
| Funding response | `fundingTime`, `realizedRate` | Actual settlement time and final rate; not permissible earlier entry information. |

In this restricted run, `Book.valid` means a snapshot/update state exists and no handled format or ordering error has invalidated it. `sequence_verified` remains false. Each decision checks that both books have two sides, bid < ask, and age no greater than two seconds. No detected anomaly is not proof that the raw feed has no gaps.

Local archive SHA256 values in `downloads.json` identify the exact files used. They are not exchange-issued checksums. Raw files are excluded from Git, and derived files can be regenerated. Full UTC-day archives were downloaded, but parsed book quality and reported trade counts cover only the target two hours.

Whether ordinary API takers can access `source=1` liquidity is a separate question. Pressure currently treats those prints as observed market information, but the matching model does not add their size to the book. V0 does not use pressure, so this candidate feature definition did not affect its decisions.
