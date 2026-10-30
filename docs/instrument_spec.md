# Instruments and source verification

Checked on 30 October 2026. Public API responses are saved in `data/manifests`. They describe specifications at retrieval time and do not automatically establish that the rules were identical on 23 October 2026.

| Item | Spot | Perpetual |
|---|---|---|
| Venue and instrument | OKX BTC-USDT | OKX BTC-USDT-SWAP |
| Underlying and settlement | BTC / USDT | Linear; `ctValCcy=BTC`, `settleCcy=USDT` |
| Size unit | BTC | Contracts; 0.01 BTC per contract, `ctMult=1` |
| Price tick | 0.1 USDT/BTC | 0.1 USDT/BTC |
| `lotSz` | 0.00000001 BTC | 0.01 contracts |
| `minSz` | 0.00001 BTC | 0.01 contracts |
| Debug quantity | 0.01 BTC | 1 contract, equivalent to 0.01 BTC |
| Fee scenario | 10 bps per fill | 5 bps per fill |
| Fee currency | USDT assumed; actual rule unverified | USDT assumed; account tier unverified |

The fee scenario does not represent a verified standard tier, VIP discount, or rebate. Minimum-notional constraints, historical effective dates, margin tiers, fee currencies, and account eligibility have not been fully verified. Live orders are outside the project scope.

The retrieved funding settlements for the research day are at 00:00, 08:00, and 16:00 UTC. Their realized rates are approximately 0.0000668879, 0.0000753334, and 0.0000685722, respectively. These are realized outcomes, not estimates known before settlement. The response lacks the reference prices needed here; settlement-crossing trades are restricted. Do not prorate funding uniformly over eight hours.

Downloaded files comprise both legs' 400-level books for 23 October and both legs' trade archives for 23/24 October, covering the adjacent UTC+8 trade-file dates required for a UTC research day. The compressed total is 606,258,642 bytes, approximately 606.3 decimal MB or 578.2 MiB. Only the first two hours of books were parsed; quality claims do not extend to the unprocessed remainder.

## Documentation checks and actual file differences

At the recorded check, historical API modules 1 and 4, day boundaries, and publication delays broadly matched the handoff. The documentation also included module 11 for borrowing rates. Ordinary `books` checksums were marked deprecated and fixed to zero; sequence continuity should use `seqId`/`prevSeqId`. **The downloaded historical files have neither sequence field.** A live-channel protocol description cannot establish completeness of an archive missing those fields. The archive's three-column price levels also differ from WebSocket formats.

Current REST trade documentation described `source=1` as RPI, formerly ELP. The archives contain such records, which are retained and counted. Pressure currently includes all sources; the archive-specific mapping and liquidity eligibility remain to be fully verified. Trade prints are not used to invent additional executable book liquidity.

Verification entry points: [historical data](https://www.okx.com/historical-data), [API documentation](https://www.okx.com/docs-v5/en/), and [change log](https://www.okx.com/docs-v5/log_en/). Saved archive lists and instrument responses document actual requests. No API key, purchase, or real-order endpoint was used.
