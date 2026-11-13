# Basis feature validation

Basis is `10000 * (perp_mid / spot_mid - 1)`, in basis points. Excess basis subtracts the median of the strictly preceding reference window; the current point does not enter its own reference. Warm-up still requires the complete preceding decision grid.

## Momentum corrections

Momentum is the current basis minus basis exactly 60 seconds earlier. Previously, a missing exact lag could silently select an older observation, measuring a longer interval. It now returns `None` when the exact lag is missing.

Previously, a median lookback shorter than 60 seconds discarded the observation needed by momentum. A separate deque now retains the preceding 60 seconds independently of the median window. Older momentum observations expire as time advances.

Both regressions were reproduced as failing tests before the source fix. Constructor arguments, output fields, median behavior, and V0 entry rules remain unchanged. Momentum remains a diagnostic rather than a V0 entry filter.

## Verification

The ten tests in [test_basis.py](../../tests/unit/test_basis.py) cover signs and units, odd/even preceding medians, exclusion of an extreme current point, first warm-up and rolling-expiration boundaries, missing observations, exact positive/negative momentum, both regressions, causal outputs, and the exact first-ready boundary for a 24-hour window.

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.unit.test_basis -v
PYTHONDONTWRITEBYTECODE=1 make test
```

Recorded validation against base `c9e80c9`: ten dedicated tests and 32 total tests passed.

## Limits

The 24-hour test uses synthetic observations; it does not complete the proposed historical experiment or multi-day replay. Calls follow the engine's increasing decision grid; duplicate/off-grid direct calls are outside this validation scope.
