# Contract and Source Verification

The check date is 2026-10-30. The raw public API responses are saved in data/manifests. They are the specifications as obtained at that time and do not automatically prove that the rules were the same on 2026-10-23.

| Item | Spot | Perpetual |
|---|---|---|
| Venue and symbol | OKX BTC-USDT | OKX BTC-USDT-SWAP |
| Underlying and settlement | BTC / USDT | linear, ctValCcy BTC, settleCcy USDT |
| Quantity unit | BTC | Contracts; 0.01 BTC per contract, ctMult=1 |
| Price tick | 0.1 USDT/BTC | 0.1 USDT/BTC |
| lotSz | 0.00000001 BTC | 0.01 contracts |
| minSz | 0.00001 BTC | 0.01 contracts |
| q this round | 0.01 BTC | 1 contract, i.e. 0.01 BTC |
| Fees | Scenario: 10 bps per trade | Scenario: 5 bps per trade |
| Fee currency | Assumed USDT in the model; real rules not verified | Assumed USDT in the model; account tier not verified |

The fee scenarios do not represent standard fee rates, VIP discounts, or available rebates. Minimum notional limits, historical validity periods, margin tiers, fee currency, and account eligibility have not been fully verified; placing real orders is out of scope.

The funding settlement times actually obtained for that day are 00:00, 08:00, and 16:00 UTC, with realizedRate of approximately 0.0000668879, 0.0000753334, and 0.0000685722 respectively. These are realized rates, not predicted values that were known beforehand. The interface does not include the settlement reference price needed here, so trades that cross a settlement point are not run for now; the rate must not be spread linearly over eight hours.

Actually downloaded this round: the 400-level order books of both legs for the 23rd; the trades of both legs for the 23rd and 24th, which are the adjacent UTC+8 files needed to cover the full UTC day. All compressed files total 606,258,642 bytes, about 606.3 decimal MB or 578.2 MiB. Only the first two hours of the order book were parsed event by event; the quality of the remaining content is not claimed to have passed.

Official documentation check: the historical-data endpoints (module 1/4), the day boundaries, and the publication delay are still consistent with the main description in the prompt; there is currently an additional module 11 for borrow rates. The checksum of the regular books channel is marked deprecated and fixed at 0, and sequence should be checked via seqId/prevSeqId. **This historical archive does not have these fields**, and the live-protocol documentation cannot be used to supply evidence for it. The three-column price levels also differ from the WebSocket format.

The current official REST documentation describes trade source=1 as RPI (formerly ELP). The trade archive for this run does contain source=1, which is kept and counted; pressure includes all sources, and the mapping of whether this field's liquidity is accessible in the archive has not yet been verified. Order book matching does not borrow liquidity from the trade records.

Verification entry points: [Historical data](https://www.okx.com/historical-data), [API docs](https://www.okx.com/docs-v5/en/), [Changelog](https://www.okx.com/docs-v5/log_en/). The archive listing and the contract responses are the actual access evidence, not merely the cited entry points. No API key was created, and no real order interface was purchased or used.

---
