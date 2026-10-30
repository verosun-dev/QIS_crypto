# QIS Spot–Perpetual Research Starter Version

## Research Question

When a perpetual futures contract trades at an unusually large positive premium relative to the same asset's spot price, can buying spot and shorting an equal notional amount of linear perpetual futures generate enough profit from subsequent spread convergence to cover all trading costs?

**At this stage, the project has no evidence of profitability.**

The first round of testing used a real, freely available OKX sample. Two hours of engineering debugging have been completed.

During 2026-10-23 00:00–02:00 UTC, the basis was negative at every second-level observation. Consequently, V0 did not open any positions under its specified trading direction.

Zero trades are neither evidence that the strategy is profitable nor evidence that it is unprofitable.

The figures and examples in the original Project Guide are synthetic educational materials. They must be kept separate from engineering reports based on real market data.

## Start Here

1. [Project Explained](docs/project_explained.md): Why can the strategy make money even when both prices rise? Why does a hypothetical gross profit of +0.20 USDT become -1.017 USDT after applying the illustrative transaction costs?

2. [19-Item Reading Guide](docs/reading_map.md): Key points, intended uses, and four recommended reading paths.

3. [Four Team Workstream Guides](docs/team_workstreams.md): Interfaces and workflows for data acquisition/downloads, L1/L2, modeling, backtesting, and transaction cost analysis.

4. [Results of the First Run](docs/first_run_results.md), [Actual Run Summary](outputs/okx_20261023_debug_v0/summary.json), [Basis Chart](outputs/okx_20261023_debug_v0/basis.png).

## Quick Start Commands

Run the following commands from the project root directory.

The core implementation uses only the Python standard library and requires no third-party packages.

The environment used for this round was Python 3.14.2. The project supports Python 3.10 and above, but other versions have not yet been individually tested.

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/synthetic_demo.py
PYTHONPATH=src python3 -m qis_spot_perp.cli run --config configs/debug.json
