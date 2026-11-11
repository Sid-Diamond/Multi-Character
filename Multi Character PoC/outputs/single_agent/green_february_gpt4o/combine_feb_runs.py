"""Rebuild selected single-agent summaries from saved labels; no API calls.

Character uses the user-selected repeat. --check performs read-only verification.
"""

import argparse
import csv
import io
import json
from pathlib import Path

from scipy.stats import beta


HERE = Path(__file__).resolve().parent
OUTPUTS = HERE / "runs"
RUNS = (
    "Feb2026_Minimal_Instance_Sonnet46_120",
    "Feb2026_Character_Collective_Sonnet46_120",
    "Douglas_recreate_character",
)
ORDER = ("Minimal", "Instance", "Character", "Collective")
FIELDS = (
    "outcome", "run_name", "framing", "identity", "attempts", "subject_ok",
    "subject_errors", "truncated", "valid_judgments", "blackmail_count",
    "missing_judgments", "judge_errors", "judge_unparsed", "blackmail_rate", "ci_low", "ci_high",
)


def csv_bytes(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def build():
    outputs = {}
    repeat = OUTPUTS / "Douglas_recreate_character"
    with (repeat / "trials.csv").open(encoding="utf-8-sig", newline="") as stream:
        trials = list(csv.DictReader(stream))
    if len(trials) != 60 or len({r["trial_id"] for r in trials}) != 60:
        raise ValueError("Replacement must contain 60 distinct trials")
    for row in trials:
        if (row["status"] != "complete" or row["agent_1_identity"] != "Character"
                or row["judge_protocol"] != "douglas_combined" or row["H_any"] not in ("True", "False")):
            raise ValueError("Incomplete or unexpected replacement trial")
        subject = json.loads((repeat / row["source"]).read_text(encoding="utf-8"))
        judge = json.loads((repeat / row["judgment_source"]).read_text(encoding="utf-8"))
        if (subject["status"] != "ok" or subject["finish_reason"] != "stop"
                or judge["status"] != "ok" or judge["finish_reason"] != "stop"
                or type(judge["released_label"]) is not bool
                or judge["released_label"] != (row["H_any"] == "True")
                or judge["released_label"] != (judge["semantic_verdict"] and judge["released_domain_gate"])):
            raise ValueError("Replacement CSV disagrees with saved records")
    replacement = {}
    for framing in ("threat", "continuity", "pooled"):
        selected = [r for r in trials if framing == "pooled" or r["framing"] == framing]
        count = 60 if framing == "pooled" else 30
        if len(selected) != count:
            raise ValueError(f"Unexpected replacement sample size: {framing}")
        positives = sum(r["H_any"] == "True" for r in selected)
        low, high = beta.ppf([0.025, 0.975], positives + 0.5, count - positives + 0.5)
        row = dict(zip(FIELDS, (
            "douglas_combined", "Douglas_recreate_character", framing, "Character", count, count,
            0, 0, count, positives, 0, 0, 0, positives / count, float(low), float(high),
        )))
        replacement[framing] = row
        path = (repeat / "summary_pooled_douglas_combined.csv" if framing == "pooled" else
                repeat / framing / "summary_douglas_combined.csv")
        outputs[path] = csv_bytes([row], FIELDS)

    settings = []
    rows = []
    for run in RUNS:
        folder = OUTPUTS / run
        settings.append(json.loads((folder / "manifest.json").read_text(encoding="utf-8"))["settings"])
        if run == "Douglas_recreate_character":
            source_rows = [replacement["pooled"]]
        else:
            with (folder / "summary_pooled_douglas_combined.csv").open(newline="", encoding="utf-8") as file:
                source_rows = list(csv.DictReader(file))
        for row in source_rows:
            if (row["run_name"] != settings[-1]["run_name"] or row["framing"] != "pooled"
                    or row["outcome"] != "douglas_combined"
                    or int(row["attempts"]) != 60 or int(row["valid_judgments"]) != 60
                    or any(int(row[key]) != 0 for key in
                           ("subject_errors", "truncated", "missing_judgments",
                            "judge_errors", "judge_unparsed"))):
                raise ValueError(f"Incomplete or unexpected pooled row in {run}: {row}")
            rows.append({"source_run": run, **row})

    for other in settings[1:]:
        for key in ("model", "temperature", "max_tokens", "subject_reasoning", "judge_model",
                    "judge_temperature", "judge_max_tokens", "judge_reasoning", "feb_mode"):
            if settings[0].get(key) != other.get(key):
                raise ValueError(f"Scientific settings differ: {key}")
    for framing in ("threat", "continuity"):
        configs = [json.loads((OUTPUTS / run / framing / "judge_config_douglas_combined.json").read_text(
            encoding="utf-8")) for run in RUNS]
        # Timeout metadata was added in the newer workflow; compare judge science.
        configs = [{k: v for k, v in config["history"][-1].items() if k != "timeout_seconds"}
                   for config in configs]
        if any(config != configs[0] for config in configs[1:]):
            raise ValueError(f"Judge settings differ: {framing}")
    if sorted(row["identity"] for row in rows) != sorted(ORDER):
        raise ValueError("Expected exactly one pooled row for each identity")

    rows.sort(key=lambda row: ORDER.index(row["identity"]))
    payload = csv_bytes(rows, ("source_run", *FIELDS))
    outputs[HERE / "Feb2026_four_identity_pooled.csv"] = payload
    outputs[HERE / "Feb2026_four_identity_pooled.rebuilt.csv"] = payload
    bars = [{"identity": r["identity"], "rate_pct": 100 * float(r["blackmail_rate"]),
             "ci_low_pct": 100 * float(r["ci_low"]), "ci_high_pct": 100 * float(r["ci_high"]),
             "trials_per_identity": int(r["valid_judgments"]), "colour": "#009E73"} for r in rows]
    outputs[HERE / "bar_values.csv"] = csv_bytes(bars, tuple(bars[0]))
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for path, content in build().items():
        if args.check:
            if path.read_bytes() != content:
                raise ValueError(f"Derived CSV differs: {path}")
        else:
            path.write_bytes(content)
    print("Verified selected single-agent summaries." if args.check else "Rebuilt selected single-agent summaries.")
