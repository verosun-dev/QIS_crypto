# Source refactor validation

Local validation on 30 October 2026, using Python 3.14.2. The comparison baseline is commit `fd29da3384e4aec2fb4ce991e76cd584eb79cf29`, before the source reorganization. This record concerns software behavior; it adds no profitability or out-of-sample evidence.

## Automated suite

```bash
make test
```

**22 tests passed:** the 18 original checks, reorganized into unit/integration files, plus four checks for signal threshold/rejection boundaries, episode eligibility, and completed-minute pressure availability. Python compilation and the unchanged CLI help command also passed.

## Five synthetic behavior comparisons

Before editing, complete replay traces were saved for five scenarios. After refactoring, each trace was compared for equality across orders, fills, trades, features, equity, states, and summary.

| Scenario | Result |
|---|---|
| Normal paired entry and holding exit | All traces identical |
| Partial entry followed by recovery | All traces identical |
| Replay ending with outstanding exposure | All traces identical |
| Planned funding crossing blocked | All traces identical |
| Unexpected funding event during a position | All traces identical; unknown funding remains flagged |

The last scenario injects an unscheduled funding event to exercise the unknown-cash-flow path. It is a synthetic stress case, not evidence about historical funding settlement.

## Historical debug replay

The existing 23 October 2026, 00:00–02:00 UTC sample was replayed in a separate temporary workspace, using the original archives and unchanged `configs/debug.json`.

| Artifact | Comparison with the original debug |
|---|---|
| `features.csv`, `equity.csv`, `pressure.csv` | Byte-for-byte identical |
| `orders.csv`, `fills.csv`, `trades.csv`, `states.csv` | Byte-for-byte identical |
| `summary.json`, `config.json` | Byte-for-byte identical |
| `data_quality_report.json` | Identical after normalizing the temporary source directory |

The result remains **zero real-sample trades**, with 974,717 book messages replayed. The synthetic comparisons therefore provide the executed-order checks that this historical window cannot provide.

Experiment metadata is expected to differ: the source code changed, the temporary invocation has a different path, and new records use the documented `relative_path_and_content_v2` source fingerprint. Original output reports, configuration, raw data, manifests, and the historical experiment register were not overwritten.

## Local review artifacts

Temporary comparison traces, logs, and replay outputs are under ignored `tmp/structure_preview/` in the review workspace. They are not required to run the automated suite. Internal import paths have changed; repository scripts and tests use the new modules. External callers of the old flat imports should follow the [migration table](architecture.md#6-migration-from-the-flat-package).

This refactor does not implement multi-day replay, the proposed 24-hour reference, a complete funding/margin model, maker fills, or paper trading. Those gaps remain explicit in the [architecture roadmap](architecture.md#5-current-implementation-and-next-stage).
