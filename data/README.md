# Research data

| Location | Contents | Git policy |
|---|---|---|
| `manifests/` | Download responses, instrument/funding responses, local checksums, integrity report, input-document index | Track small provenance files |
| `raw/` | Original compressed L2/trade archives and bounded public captures | Ignored |
| `processed/` | Reserved location for generated datasets; not required by the current streaming runner | Ignored |

From the repository root, inspect the required downloads before fetching:

```bash
python3 scripts/fetch_sample.py --date 2026-10-23
python3 scripts/fetch_sample.py --date 2026-10-23 --download --max-mb 700
python3 scripts/check_archives.py
PYTHONPATH=src python3 -m qis_spot_perp.cli manifest
```

The recorded six-file sample totals 606,258,642 bytes. Book files use UTC days; trade files use UTC+8 days. The current run processes only 00:00–02:00 UTC, although full-day book archives were downloaded. Compression integrity and local SHA256 fingerprints do not establish message completeness. The historical sample lacks sequence IDs and local receipt timestamps.

Do not overwrite date-specific provenance when extending acquisition: current scripts reuse manifest filenames. A continuous multi-day dataset needs explicit coverage, reconstruction across midnight, warm-up, and exit-tail checks. See the [data dictionary](../docs/data_dictionary.md) and [first-run report](../docs/first_run_results.md).
