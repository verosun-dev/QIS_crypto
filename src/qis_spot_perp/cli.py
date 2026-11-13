"""Stable command-line entry point; experiment orchestration lives in backtest.runner."""

import argparse
import json
from pathlib import Path

from .backtest.runner import run
from .data.manifests import provenance


def main():
    p = argparse.ArgumentParser(description="QIS public-data research only")
    p.add_argument("command", choices=["manifest", "run"])
    p.add_argument(
        "--config",
        default="configs/debug.json",
        help="configuration file for research runs, configs/debug.json by default",
    )
    p.add_argument(
        "--date", help="select a preserved YYYY-MM-DD acquisition for manifest"
    )
    p.add_argument(
        "--experiment-id",
        default=None,
        help="Override experiment ID; use 'auto' for an automatically generated ID",
    )
    a = p.parse_args()
    root = Path.cwd()

    if a.date is not None and a.command != "manifest":
        p.error("--date is supported only for manifest")
    if a.command == "manifest":
        print(json.dumps(provenance(root, a.date), indent=2))
    else:
        run(root, a.config, a.experiment_id)


if __name__ == "__main__":
    main()
