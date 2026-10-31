# Experiment configuration TEST PUSH

[`debug.json`](debug.json) is the complete, resolved configuration for the current two-hour debug. The runner copies it into each experiment output. It uses a 30-minute warm-up; it is not the proposed 24-hour-reference experiment.

| Concern | Fields |
|---|---|
| Identity and coverage | `experiment_id`, `data_kind`, `date`, `start_ms`, `end_ms` |
| Decisions and strategy | `entry_start_ms`, `entry_end_ms`, `decision_ms`, `lookback_seconds`, `threshold_bps`, `q_btc`, `holding_ms` |
| Execution scenarios | `spot_fee_bps`, `perp_fee_bps`, `feed_latency_ms`, `order_latency_ms`, `report_latency_ms` |
| Risk and data gates | `max_stale_ms`, `recovery_timeout_ms`, `max_pair_loss_usdt`, `allow_unsequenced_archive` |
| Capital and annotations | `initial_capital_usdt`, `fee_status`, `funding_policy`, `note` |

`fee_status`, `funding_policy`, and `note` describe assumptions; they are not selectors for alternative fee/funding engines. The current engine always blocks planned funding crossings without reference prices. Instrument units come from `data/manifests/okx-spot-spec.json` and `okx-swap-spec.json`; the funding schedule comes from `okx-funding.json`.

Keep one resolved file per experiment while the parameter set is small. When several runnable experiments need shared market, strategy, or execution settings, introduce composition with validation and save the resolved result. There are no YAML presets or configuration-override semantics in this version.
