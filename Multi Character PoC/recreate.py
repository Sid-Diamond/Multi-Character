"""Run both blackmail framings in one resumable experiment folder."""

import csv
import json
import math
import re
from pathlib import Path

import audit
import money
import poc
import uncertainties


def settings_for(config, framing):
    return {
        "identities": config["identities"], "model": config["model"],
        "subject_provider": None, "subject_reasoning": config["subject_reasoning"],
        "temperature": config["temperature"], "max_tokens": config["max_tokens"],
        "subject_timeout_seconds": config["subject_timeout_seconds"],
        "samples_per_identity": config["trials_per_identity"][framing],
        "judge_model": config["judge_model"], "judge_provider": None,
        "judge_reasoning": config["judge_reasoning"],
        "judge_temperature": config["judge_temperature"],
        "judge_max_tokens": config["judge_max_tokens"], "framing": framing,
    }


def complete(folder: Path, identities, target: int) -> bool:
    if not (folder / "manifest.json").exists():
        return False
    rows = poc.summary_rows(folder)
    return (len(rows) == len(identities) and
            all(row["identity"] in identities and row["attempts"] == target and
                row["subject_ok"] == target and row["valid_judgments"] == target and
                row["truncated"] == 0 for row in rows))


def write_summary(experiment: Path, config):
    rows = []
    for framing in ("threat", "continuity"):
        folder = experiment / framing
        if (folder / "manifest.json").exists():
            rows.extend({"run_name": config["run_name"], "framing": framing, **row}
                        for row in poc.summary_rows(folder))
    if not rows:
        return
    for identity in config["identities"]:
        parts = [row for row in rows if row["identity"] == identity]
        if len(parts) != 2:
            continue
        totals = {field: sum(row[field] for row in parts) for field in
                  ("attempts", "subject_ok", "subject_errors", "truncated",
                   "valid_judgments", "blackmail_count", "missing_judgments",
                   "judge_errors", "judge_unparsed")}
        valid = totals["valid_judgments"]
        rows.append({"run_name": config["run_name"], "framing": "pooled",
                     "identity": identity, **totals,
                     "blackmail_rate": totals["blackmail_count"] / valid if valid else ""})
    rows = [{"outcome": "released", **row} for row in rows]
    if config["audit"]:
        rows = audit.append_rows(experiment, rows)
    rows = uncertainties.append_intervals(rows, "blackmail_count", "valid_judgments")
    target = experiment / "summary.csv"
    with target.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {target}", flush=True)


def run(config):
    audit.require_available(config["audit"])
    name = config["run_name"]
    counts = config["trials_per_identity"]
    max_cost = config["max_cost"]
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) or name.endswith("."):
        raise ValueError("run_name must use letters, numbers, dots, underscores, or hyphens")
    if set(counts) != {"threat", "continuity"} or any(type(n) is not int or n < 1 for n in counts.values()):
        raise ValueError("Set positive trial targets for threat and continuity")
    if type(max_cost) not in (int, float) or not math.isfinite(max_cost) or max_cost <= 0:
        raise ValueError("Set a positive max_cost before running")
    planned = sum(counts.values()) * len(config["identities"])
    if counts["threat"] * len(config["identities"]) < money.PROBE_PAIRS:
        raise ValueError("The threat condition needs at least five trials for the cost estimate")

    experiment = poc.OUTPUTS / name
    saved_settings = {key: value for key, value in config.items()
                      if key not in ("max_cost", "audit", "analysis_draws", "analysis_seed")}
    manifest_path = experiment / "manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text(encoding="utf-8"))["settings"] != saved_settings:
            raise ValueError("Experimental settings differ from the saved run")
    elif experiment.exists():
        raise FileExistsError(f"Existing folder has no experiment manifest: {experiment}")
    else:
        poc.write_json(manifest_path, {"settings": saved_settings})

    if all(complete(experiment / framing, config["identities"], counts[framing])
           for framing in ("threat", "continuity")):
        write_summary(experiment, config)
        print("Experiment already complete; no model calls made.", flush=True)
        return experiment

    threat_settings = settings_for(config, "threat")
    threat_folder = poc.run(threat_settings, folder_path=experiment / "threat",
                            limit_trials=money.PROBE_PAIRS)
    poc.judge(threat_folder, threat_settings)
    write_summary(experiment, config)
    if not money.within_estimate(experiment, planned, max_cost):
        return experiment

    for framing in ("threat", "continuity"):
        frame_settings = settings_for(config, framing)
        folder = poc.run(frame_settings, folder_path=experiment / framing)
        poc.judge(folder, frame_settings)
        write_summary(experiment, config)
        if not complete(folder, config["identities"], counts[framing]):
            print(f"Stopping: {framing} has missing, failed, or truncated results.", flush=True)
            break
    return experiment
