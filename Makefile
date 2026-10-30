PYTHON ?= python3
CONFIG ?= configs/debug.json

.PHONY: help test demo replay manifest

help:
	@echo "make test      Run deterministic unit and integration tests"
	@echo "make demo      Generate the labeled synthetic example"
	@echo "make replay    Replay downloaded archives (CONFIG=configs/debug.json)"
	@echo "make manifest  Recompute local download fingerprints"

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

demo:
	PYTHONPATH=src $(PYTHON) scripts/synthetic_demo.py

replay:
	PYTHONPATH=src $(PYTHON) -m qis_spot_perp.cli run --config "$(CONFIG)"

manifest:
	PYTHONPATH=src $(PYTHON) -m qis_spot_perp.cli manifest
