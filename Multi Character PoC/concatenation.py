"""Combine compatible pooled released-label summaries outside the run pipeline."""

import csv
from pathlib import Path

import uncertainties


def pooled_rows(path, valid_key, positive_key):
    with Path(path).open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    selected = {}
    for row in rows:
        if row["framing"] != "pooled" or row["outcome"] != "released":
            continue
        identity = row["identity"]
        if identity in selected:
            raise ValueError(f"Duplicate pooled released row for {identity}: {path}")
        attempts, valid, positive = (int(row[key]) for key in
                                     ("attempts", valid_key, positive_key))
        if not (0 <= positive <= valid == attempts):
            raise ValueError(f"Incomplete or invalid pooled row for {identity}: {path}")
        selected[identity] = (attempts, valid, positive)
    if not selected:
        raise ValueError(f"No pooled released rows in {path}")
    return selected


def combine_released_pooled(historical_csv, new_csv, target_csv, historical_run, new_run):
    """Add counts from two checked-compatible runs; leave both inputs untouched."""
    historical_csv, new_csv, target_csv = map(Path, (historical_csv, new_csv, target_csv))
    if target_csv.exists() or target_csv in (historical_csv, new_csv):
        raise FileExistsError(f"Output already exists or is a source CSV: {target_csv}")
    old = pooled_rows(historical_csv, "valid", "positive")
    new = pooled_rows(new_csv, "valid_judgments", "blackmail_count")
    if old.keys() != new.keys():
        raise ValueError("Pooled identities differ between the source CSVs")
    rows = []
    for identity in old:
        attempts, valid, positive = (old[identity][i] + new[identity][i] for i in range(3))
        rate, low, high = uncertainties.interval(positive, valid)
        rows.append({"framing": "pooled", "identity": identity, "outcome": "released",
                     "source_runs": f"{historical_run};{new_run}",
                     "attempts": attempts, "valid": valid, "positive": positive,
                     "rate": rate, "ci_low": low, "ci_high": high})
    target_csv.parent.mkdir(parents=True, exist_ok=True)
    with target_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return target_csv
