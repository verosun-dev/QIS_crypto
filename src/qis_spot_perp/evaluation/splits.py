"""Basic label-boundary purge; a full validation pipeline is not implemented."""


def purged_split(events, boundary):
    """Return records whose decision and label end are strictly before boundary.

    Records require decision_ms and label_end_ms timestamps in milliseconds;
    boundary uses the same units. Labels ending exactly at boundary are excluded.
    Input order is preserved and records are not modified. This selects only the
    pre-boundary subset, not other partitions or independent episodes.
    """
    return [e for e in events if e["decision_ms"] < boundary and e["label_end_ms"] < boundary]
