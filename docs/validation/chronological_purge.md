# Chronological purge validation

`purged_split(events, boundary)` returns the pre-boundary subset of labeled observations. It retains a record only when both `decision_ms` and `label_end_ms` are strictly less than `boundary`. All timestamps use milliseconds. An outcome ending exactly at the boundary is excluded.

The existing filter is unchanged. Its docstring now states the boundary policy and that input order and original records are preserved.

## Verification

The six tests in [test_splits.py](../../tests/unit/test_splits.py) cover retained outcomes, touching/crossing labels, decisions at or after the boundary, empty input, generators, and preservation of order and records.

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.unit.test_splits -v
PYTHONDONTWRITEBYTECODE=1 make test
```

Recorded validation against base `c9e80c9`: six dedicated tests and 28 total tests passed.

## Limits

This helper does not construct development/validation/test partitions, add an embargo, or establish independence between repeated observations of one episode. It is not a completed out-of-sample evaluation pipeline.
