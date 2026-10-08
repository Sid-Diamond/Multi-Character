"""Append Jeffreys uncertainty intervals to binary-count result rows."""

from scipy.stats import beta


def interval(positive, valid):
    if not valid:
        return ("", "", "")
    low, high = beta.ppf([0.025, 0.975], positive + 0.5, valid - positive + 0.5)
    return (positive / valid, float(low), float(high))


def append_intervals(rows, positive_key, valid_key):
    """Add interval columns to binary-count rows, including future audit rows."""
    result = []
    for row in rows:
        _, low, high = interval(row[positive_key], row[valid_key])
        result.append({**row, "ci_low": low, "ci_high": high})
    return result

