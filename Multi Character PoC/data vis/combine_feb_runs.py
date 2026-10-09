"""Combine the two completed February-artifact runs without merging trials across identities."""

import csv
import json
from pathlib import Path


OUTPUTS = Path(__file__).resolve().parent.parent / "outputs" / "Feb Runs"
RUNS = (
    "Feb2026_Minimal_Instance_Sonnet46_120",
    "Feb2026_Character_Collective_Sonnet46_120",
)
DESTINATION = OUTPUTS / "Feb2026_four_identity_pooled.csv"
ORDER = ("Minimal", "Instance", "Character", "Collective")


def main():
    settings = []
    rows = []
    for run in RUNS:
        folder = OUTPUTS / run
        settings.append(json.loads((folder / "manifest.json").read_text(encoding="utf-8"))["settings"])
        with (folder / "summary_pooled_douglas_combined.csv").open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                if (row["run_name"] != settings[-1]["run_name"] or row["framing"] != "pooled"
                        or row["outcome"] != "douglas_combined"
                        or row["attempts"] != "60" or row["valid_judgments"] != "60"
                        or any(row[key] != "0" for key in
                               ("subject_errors", "truncated", "missing_judgments",
                                "judge_errors", "judge_unparsed"))):
                    raise ValueError(f"Incomplete or unexpected pooled row in {run}: {row}")
                rows.append({"source_run": run, **row})

    for key in settings[0]:
        if key not in ("run_name", "identities") and settings[0][key] != settings[1].get(key):
            raise ValueError(f"Run settings differ: {key}")
    for framing in ("threat", "continuity"):
        configs = [json.loads((OUTPUTS / run / framing / "judge_config_douglas_combined.json").read_text(
            encoding="utf-8")) for run in RUNS]
        if configs[0] != configs[1]:
            raise ValueError(f"Judge settings differ: {framing}")
    if sorted(row["identity"] for row in rows) != sorted(ORDER):
        raise ValueError("Expected exactly one pooled row for each identity")

    rows.sort(key=lambda row: ORDER.index(row["identity"]))
    with DESTINATION.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {DESTINATION}")


if __name__ == "__main__":
    main()
