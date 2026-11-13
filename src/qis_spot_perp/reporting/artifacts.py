"""Save a replay's tables, summary, and provenance so the result can be reproduced.

Every run is saved under outputs/<experiment_id>/ and appended to
outputs/experiment_register.jsonl. An experiment ID can be used only once:
saving a second run under an existing ID raises ExperimentExistsError instead
of silently overwriting the earlier evidence. To rerun, give the config a new
experiment_id (or use a separate temporary workspace for regression checks).
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

REGISTER = Path('outputs') / 'experiment_register.jsonl'

# Column headers used when a table has no rows, so an empty CSV still shows
# which columns would have existed (e.g. a run that made zero trades).
EMPTY_TABLE_FIELDS = {
    'orders': ['order_id', 'episode_id', 'leg', 'side', 'quantity_btc', 'send_ms', 'arrival_ms', 'status'],
    'fills': ['order_id', 'leg', 'side', 'quantity_btc', 'price', 'fee_usdt', 'fill_ms', 'report_ms'],
    'trades': ['episode_id', 'decision_ms', 'exit_report_ms', 'gross_fill_usdt', 'fees_usdt',
               'funding_usdt', 'net_usdt', 'status'],
    'states': ['ts', 'state', 'reason'],
}


class ExperimentExistsError(FileExistsError):
    """Raised when saving would overwrite or duplicate an earlier experiment."""


def write_csv(path, rows, fields=None):
    """Write a list of dictionaries as a CSV file, creating folders as needed.

    Columns come from `fields`; if none are given, from the first row's keys;
    if there are no rows either, a single 'status' column.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not fields:
        fields = list(rows[0]) if rows else ['status']
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def ensure_new_experiment(root, out, experiment_id):
    """Refuse to continue if this experiment ID has already been used.

    Two checks, because either kind of evidence means the ID is taken:
    1. The output folder already contains files (hidden files such as macOS
       .DS_Store are ignored; an empty folder made by the runner is fine).
    2. The experiment register already has a record with this ID, even if
       someone deleted the folder afterwards.
    """
    out = Path(out)
    if out.exists() and any(not p.name.startswith('.') for p in out.iterdir()):
        raise ExperimentExistsError(
            f"{out} already contains results for '{experiment_id}'. "
            'Use a new experiment_id in the config instead of overwriting.')

    register = Path(root) / REGISTER
    if register.exists():
        for line in register.read_text().splitlines():
            if line.strip() and json.loads(line).get('experiment_id') == experiment_id:
                raise ExperimentExistsError(
                    f"experiment_id '{experiment_id}' is already in {register}. "
                    'Use a new experiment_id in the config.')


def source_fingerprint(root):
    """SHA-256 of every Python file under src/ (path + contents).

    If any line of code changes, the fingerprint changes, so a saved result can
    always be matched to the exact code that produced it.
    """
    src = Path(root) / 'src'
    digest = hashlib.sha256()
    for p in sorted(src.rglob('*.py')):
        digest.update(p.relative_to(src).as_posix().encode() + p.read_bytes())
    return digest.hexdigest()


def save_run(root, out, config_path, c, engine, quality, pressure):
    """Save every table and record of one replay, then return its summary.

    Steps: (1) make sure the experiment ID is new, (2) write the raw tables as
    CSV, (3) write the summary, data-quality report, and config as JSON,
    (4) write experiment.json describing how to reproduce the run, and
    (5) append the same record to the shared experiment register.
    """
    root, out = Path(root), Path(out)

    # (1) Stop before writing anything if this would overwrite earlier evidence.
    ensure_new_experiment(root, out, c['experiment_id'])

    # (2) One CSV per table. Columns are the union of keys across all rows.
    tables = [('features', engine.features), ('orders', engine.orders), ('fills', engine.fills),
              ('trades', engine.trades), ('equity', engine.equity), ('states', engine.states),
              ('pressure', pressure)]
    for name, rows in tables:
        fields = list(dict.fromkeys(key for row in rows for key in row))
        write_csv(out / f'{name}.csv', rows, fields or EMPTY_TABLE_FIELDS.get(name, ['status']))

    # (3) The report card plus the inputs needed to interpret it.
    summary = engine.summary()
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    (out / 'data_quality_report.json').write_text(json.dumps(quality, indent=2, ensure_ascii=False))
    (out / 'config.json').write_text(json.dumps(c, indent=2))

    # (4) Everything needed to reproduce this result: command, Python version,
    # code fingerprint, exact config, and which data manifest was used.
    record = {
        'experiment_id': c['experiment_id'],
        'hypothesis': 'Abnormally positive basis converges within 30 minutes',
        'phase': 'development_debug',
        'command': f'PYTHONPATH=src python3 -m qis_spot_perp.cli run --config {config_path}',
        'python': sys.version,
        'source_sha256': source_fingerprint(root),
        'source_hash_scheme': 'relative_path_and_content_v2',
        'config': c,
        'summary': summary,
        'data_manifest': 'data/manifests/downloads.json',
    }
    (out / 'experiment.json').write_text(json.dumps(record, indent=2, ensure_ascii=False))

    # (5) Append-only log of every experiment ever run in this workspace.
    with (root / REGISTER).open('a') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    return summary
