"""Basic label-boundary purge; a full validation pipeline is not implemented."""


def purged_split(events, boundary):
    """Timestamp-based exclusion of labels crossing a chronological boundary."""
    return [e for e in events if e["decision_ms"] < boundary and e["label_end_ms"] < boundary]
