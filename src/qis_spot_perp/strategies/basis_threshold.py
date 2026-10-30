"""V0 entry eligibility: positive basis and excess above a trailing median.

The engine owns the entry window, episode reset, orders, and lifecycle. This
function only returns the first signal rejection reason, or None for eligibility.
"""


def entry_rejection(feature, threshold_bps, armed):
    if feature['excess_bps'] is None:
        return 'warmup_incomplete'
    if feature['basis_bps'] <= 0:
        return 'nonpositive_basis'
    if feature['excess_bps'] < threshold_bps:
        return 'below_threshold'
    if not armed:
        return 'episode_not_reset'
    return None
