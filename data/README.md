# Research data

| Location | Contents | Git policy |
|---|---|---|
| `manifests/` | Download responses, instrument/funding responses, local checksums, integrity report, input-document index | Track small provenance files |
| `manifests/YYYY-MM-DD/` | Preserved source responses, retrieval log, and immutable archive/source fingerprints for one research date | Track small provenance files |
| `raw/` | Original compressed L2/trade archives and bounded public captures | Ignored |
| `processed/` | Reserved location for generated datasets; not required by the current streaming runner | Ignored |

From the repository root, inspect the required downloads before fetching:

```bash
python3 scripts/fetch_sample.py --date 2026-10-23
python3 scripts/fetch_sample.py --date 2026-10-23 --download --max-mb 700
PYTHONPATH=src python3 -m qis_spot_perp.cli manifest --date 2026-10-23
```

The recorded six-file sample totals 606,258,642 bytes. Book files use UTC days; trade files use UTC+8 days. The current run processes only 00:00–02:00 UTC, although full-day book archives were downloaded. Compression integrity and local SHA256 fingerprints do not establish message completeness. The historical sample lacks sequence IDs and local receipt timestamps.

New acquisition metadata is staged and published only after all seven public responses and the six-file listing are valid. Existing dated metadata is reused without requests or rewrites, so listing and downloading can be separate commands. Failed metadata retrieval can be retried; a malformed saved acquisition must be inspected rather than replaced automatically. Existing raw files are retained, and failed raw downloads leave `.part` files.

`manifest --date` requires all six raw files before creating the dated `downloads.json`. It records UTC check time, local archive sizes/hashes, and hashes of all source responses and the retrieval log. The record is immutable: repeating the command verifies the same content and preserves the original record. Changed archive/source bytes are rejected; modification-time changes alone are accepted. Hashes identify local bytes, not exchange-certified completeness.

The historical root metadata remains untouched. `manifest` without a date only prints a current legacy inspection. The existing debug replay and experiment records still use the root instrument, funding, and download manifests; dated acquisitions are not yet selected by replay. The legacy `scripts/check_archives.py` scans all raw files and rewrites the root integrity report, so it is not part of the dated-preservation workflow.

A continuous multi-day dataset still needs explicit coverage, reconstruction across midnight, warm-up, and exit-tail checks. See the [data dictionary](../docs/data_dictionary.md) and [first-run report](../docs/first_run_results.md).
