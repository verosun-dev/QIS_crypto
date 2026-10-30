# Implemented V0 debug specification

The parameter source is `configs/debug.json`. This document describes the implemented two-hour debug, not the proposed one-week V0.1 experiment. The run covers 23 October 2026, 00:00–02:00 UTC. Warm-up starts at 00:00; entry decisions are allowed from 00:30:01 up to, but not including, 01:20. The remaining data supplies holding and exit buffers. The current warm-up requires a complete preceding one-second grid; even one missing observation prevents readiness. No final test set has been established.

## Information and event timing

Signals are calculated every second using only books that have reached `observed_state`. Original archive events are replayed individually; the feature grid is not treated as the execution feed. Exchange state independently determines IOC fills.

Assumed feed, order, and report latency is 100, 150, and 100 ms, respectively. These are scenarios, not measurements. All exchange updates sharing a timestamp precede order arrivals at that timestamp. The actual order of simultaneous cross-channel events is unknown.

## Entry, exit, and recovery

Entry requires a positive basis and excess of at least 2 bps above the median of the preceding 1,800 seconds, excluding the current point. Buy 0.01 BTC spot and short 0.01 BTC-equivalent perpetual exposure. Allow one paired position, with no pyramiding. A new episode can be armed after excess returns to zero or below. Order state remains `ENTERING` until both execution reports arrive.

The main states are `FLAT`, `ENTERING`, `HEDGED`, `EXITING`, and `RECOVERY`. If either leg does not reach its target quantity, unwind executed exposure. Unfilled IOC quantities are canceled immediately; there is no maker queue model. The 30-minute holding clock starts at the last actual entry fill completing the hedge, which the strategy learns about only when reports arrive.

Recovery retries are scheduled one second after an unresolved recovery report, with another configured order delay before arrival. If exposure remains unresolved at the timeout check after 10 seconds, stop new entries and retain the open exposure in the report. The 10 USDT known pair-loss threshold is a debug risk setting. The code evaluates known fill cash flows and inventory at observed mids, including known fees; it then submits exit orders. The trigger is not a guaranteed maximum realized loss.

Invalid or stale data prevents new positions. An existing hedged position receiving an unhealthy observed feed generates an exit request. If exchange-side quotes are unavailable, orders are rejected rather than given invented fills. At the data boundary, report residual inventory and pending orders instead of closing for free at the final price.

## Book quality and execution

The archive lacks sequence IDs. `allow_unsequenced_archive=true` explicitly permits restricted research while keeping sequence verification unknown. Setting it to false rejects unsequenced input. Price validity and sequence completeness are separate checks.

Scan visible depth at order arrival. Insufficient depth produces partial fills. A simulated order consumes liquidity in the simulated book; later historical absolute-size updates can replenish it. Other participants do not react to our simulated orders. This model is intended for small-size diagnostics and does not validate market impact, maker execution, historical fee currencies, or liquidation.

## Accounting and capital

Each fill incurs quantity × price × fee rate. The scenario uses 10 bps for spot and 5 bps for the perpetual, both booked in USDT. These are not verified account rates or verified base-currency fee rules. Net P&L comes from signed fill cash flows, inventory, fees, and funding, including recovery trades.

The default total capital is 2,000 USDT. The equity series marks the research account at observed mids. Signed perpetual fill cash is an accounting identity, not available margin. Liquidation, maintenance requirements, transfer delays, financing, and venue risk are not modeled; the curve cannot establish leverage safety.

The gross benchmark uses mids at entry and exit decisions. Actual fill-based gross P&L already includes bid/ask, depth, and order-delay effects. `execution_loss = gross_mid_benchmark − gross_fill` may be negative. For recovery trades, the fixed-quantity benchmark also captures quantity differences and is not pure slippage attribution.

## Funding limitation

Retrieved funding data contains settlement times and realized rates, but not the required settlement reference prices. Planned trades crossing a known settlement are blocked. If failed recovery causes an unexpected crossing, flag funding cash flow as unknown, stop new entries, and do not present complete net returns. Per-trade values in such an incomplete report must not be interpreted as complete net outcomes.

This is a debug admission rule, not a restriction selected after observing losses. Normal holdings in the 00:00–02:00 window do not cross the 08:00 settlement.

## Next implementation work

Add continuous multi-day replay, a genuine 24-hour warm-up, historical rule verification, and sequence/receipt-time evidence before interpreting signal ablations. Record all attempts in the experiment register. The separate [V0.1 review](baseline_review.md) identifies proposed decisions; it does not silently change this implemented configuration.
