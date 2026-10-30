"""Stable command-line entry point; experiment orchestration lives in backtest.runner."""
import argparse
import json
from pathlib import Path
from .backtest.runner import run
from .data.manifests import provenance


def main():
    p=argparse.ArgumentParser(description='QIS public-data research only')
    p.add_argument('command',choices=['manifest','run'])
    p.add_argument('--config',default='configs/debug.json')
    a=p.parse_args();root=Path.cwd()
    if a.command=='manifest': print(json.dumps(provenance(root),indent=2))
    else:run(root,a.config)


if __name__ == '__main__':
    main()
