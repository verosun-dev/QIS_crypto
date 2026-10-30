# Contributing

Use the [architecture](docs/architecture.md) to choose the module for a change. All four workstreams share instrument units, information timing, and fill accounting. Read the [implemented V0 rules](docs/baseline_spec.md) before changing strategy behavior.

## Development workflow

1. Start a focused branch for the task. For Codex-assisted changes, use `codex/<short-description>`.
2. Change the responsible module and its callers. Put reusable logic in `src/qis_spot_perp`; keep scripts as runnable tools.
3. Add a deterministic test when changing a trading rule, timestamp boundary, reconstruction rule, or accounting calculation. Keep raw historical data out of test fixtures.
4. Run `make test` from the repository root. Use a small synthetic scenario before any costly replay.
5. In the review description, state the changed behavior, validation command and result, and remaining limitations. Include the resolved configuration and manifest reference for research results.

## Module conventions

- Use English identifiers, comments, and documentation. Name quantities and timestamps with units where ambiguity is possible.
- Use Decimal for order sizes, fill prices, fees, and accounting. A contract count is not a BTC quantity.
- Calculate signals from information available at the decision time. Actual fills become known only after reports arrive.
- Keep execution costs in the shared ledger. Do not deduct a second spread/slippage charge from prices that already include it.
- Separate a new experiment from a behavior-preserving refactor. Record every attempted research configuration, including negative and no-trade outcomes.
- Add a package when there is a concrete responsibility and runnable code. Document proposed modules in the roadmap until implemented.

## Tests and artifacts

`tests/unit/` covers calculations and local rules. `tests/integration/` covers archive parsing and the full order lifecycle. `tests/fixtures/` holds small deterministic synthetic market helpers.

Raw downloads and large feature/equity tables are ignored. Small selected experiment reports are tracked, so `outputs/` is not entirely ignored. Before committing, inspect the diff for accidental dataset additions or changes to historical evidence.

Replays currently write under the configured `experiment_id` and append to the experiment register. Use a distinct ID for a new experiment, or a separate temporary workspace for a regression comparison. The existing debug runner does not enforce immutable output directories.

## Review by responsibility

Data changes should include timestamp/coverage evidence; signal changes should show causal inputs and a fixed comparison; execution changes should show partial-fill and timing behavior; accounting changes should reconcile gross P&L, fees, funding, and net cash flow. Coordinate cross-module decisions in the specification rather than allowing each group to adopt a different convention.
