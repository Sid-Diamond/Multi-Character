"""Plan, validate, and run standalone experiments or frozen batches in any mode."""

import copy
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import csv_exports
import multi_agent
import poc
import rejudge


MODES = ("single_agent", "multi_agent", "rejudge")
IDENTITIES = ("Character", "Instance", "Minimal", "collective_excludes", "collective_includes")
COMMON = (*multi_agent.INHERITED, "max_cost")
LEGACY = {"multi_agent": "multi-agent", "single_agent": "single-agent", "rejudge": "Rejudgments"}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def name_check(value, field):
    reserved = {"analysis", "queue_info", "con", "prn", "aux", "nul",
                *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
    if (not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9._ -]*[A-Za-z0-9_-])?", value)
            or value.split(".")[0].casefold() in reserved):
        raise ValueError(f"Invalid {field}: {value!r}; use a non-reserved folder name")


def expand(config):
    """Only run names and multi-agent composition vary; other settings are shared."""
    mode = config["mode"]
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    batch = config.get("batch_name")
    names = config["run_name"]
    if batch is None:
        name_check(names, "run_name")
        names = [names]
    else:
        name_check(batch, "batch_name")
        if not isinstance(names, list) or not names:
            raise ValueError("A named batch requires a nonempty run_name list")
        for name in names:
            name_check(name, "run_name")
        if len({name.casefold() for name in names}) != len(names):
            raise ValueError("Batch run names must be unique (including letter case)")
    counts = config[mode].get("identities_per_trial") if mode == "multi_agent" else None
    if mode == "multi_agent":
        if not isinstance(counts, dict) or set(counts) != set(IDENTITIES):
            raise ValueError(f"Specify every multi-agent identity explicitly: {', '.join(IDENTITIES)}")
        for identity, values in counts.items():
            if batch is None:
                if type(values) is not int or values < 0:
                    raise ValueError(f"Standalone {identity} must have one nonnegative integer count")
            elif not isinstance(values, list) or len(values) != len(names):
                actual = len(values) if isinstance(values, list) else "a scalar"
                raise ValueError(f"Batch configuration error: {identity} has {actual} counts; run_name defines {len(names)} runs")
    runs = []
    for index, name in enumerate(names):
        settings = {key: copy.deepcopy(config[key]) for key in COMMON}
        settings.update(mode=mode, run_name=name)
        block = copy.deepcopy(config[mode])
        if mode == "multi_agent":
            block["identities_per_trial"] = {key: value if batch is None else value[index]
                                              for key, value in counts.items()}
        if mode == "single_agent":
            settings.update(block)
        else:
            settings[mode] = block
        validate(settings)
        runs.append(settings)
    return runs


def validate(settings):
    for key in ("model", "judge_model"):
        if not isinstance(settings[key], str) or not settings[key].strip():
            raise ValueError(f"{key} must be a nonempty model ID shared across the batch")
    for key in ("max_tokens", "judge_max_tokens"):
        if type(settings[key]) is not int or settings[key] < 1:
            raise ValueError(f"{key} must be a positive integer")
    for key in ("max_cost", "subject_timeout_seconds", "judge_timeout_seconds"):
        value = settings[key]
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"{key} must be positive and finite")
    for key in ("temperature", "judge_temperature"):
        value = settings[key]
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 2):
            raise ValueError(f"{key} must be None or a number between 0 and 2")
    if settings["mode"] == "multi_agent":
        multi_agent.configuration(settings)
    elif settings["mode"] == "single_agent":
        identities = settings["identities"]
        if (not isinstance(identities, list) or not identities or
                any(identity not in poc.IDENTITIES for identity in identities) or len(set(identities)) != len(identities)):
            raise ValueError(f"single_agent.identities must contain unique names from {poc.IDENTITIES}")


def source_hashes():
    hashes = multi_agent.source_hashes()
    for name in ("run_workflow.py", "csv_exports.py", "uncertainties.py"):
        path = poc.HERE / name
        hashes[str(path.relative_to(poc.HERE.parent))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def make_plan(batch_name, runs, hashes):
    shared = copy.deepcopy(runs[0])
    shared.pop("run_name")
    if shared["mode"] == "multi_agent":
        shared["multi_agent"].pop("identities_per_trial")
    entries = [{"run_name": run["run_name"]} for run in runs]
    for entry, run in zip(entries, runs):
        if run["mode"] == "multi_agent":
            entry["identities_per_trial"] = run["multi_agent"]["identities_per_trial"]
    return {"format_version": 1, "batch_name": batch_name, "settings": shared,
            "runs": entries, "source_sha256": hashes}


def retained_failure(folder, mode):
    pattern = "*/trials/*.json" if mode == "multi_agent" else "*/trials/*/*.json" if mode == "single_agent" else "judgments/**/*.json"
    for path in sorted(folder.glob(pattern)):
        record = csv_exports.read(path)
        status = record.get("status")
        if mode == "multi_agent":
            blocked = status not in ("complete", "running") or any(
                call["status"] == "in_flight" for call in record.get("calls", []))
        else:
            blocked = status != "ok"
        if blocked:
            return f"{csv_exports.relative(path, folder)}: retained {status}; no automatic retry"
    return None


def run(config):
    runs = expand(config)
    mode, batch_name = config["mode"], config.get("batch_name")
    root = poc.OUTPUTS / mode
    parent = root / batch_name if batch_name is not None else root
    old = poc.OUTPUTS / LEGACY[mode] / (batch_name or runs[0]["run_name"])
    if old.exists() and not (parent if batch_name else parent / runs[0]["run_name"]).exists():
        raise ValueError(f"Historical outputs exist at {old}; choose a fresh name. Historical folders are not migrated automatically.")
    if mode == "single_agent" and batch_name is None:
        historical = poc.OUTPUTS / runs[0]["run_name"]
        if historical.exists():
            raise ValueError(f"Historical single-agent run exists at {historical}; choose a fresh run_name")
    hashes = source_hashes()
    plan = make_plan(batch_name, runs, hashes)
    queue_info = parent / "queue_info" if batch_name is not None else None
    if queue_info:
        path = queue_info / "queue.json"
        if path.exists():
            saved = csv_exports.read(path)
            if saved != plan:
                raise ValueError("Batch settings or source files differ from the saved plan; use a new batch_name")
            plan = saved
        elif parent.exists():
            raise ValueError(f"Existing batch folder has no saved queue plan: {parent}")

    # Validate every run and existing manifest before starting the first paid call.
    prepared = []
    for settings in runs:
        folder = parent / settings["run_name"]
        metadata = {"settings": settings, "source_sha256": hashes}
        if (folder / "manifest.json").exists():
            saved = csv_exports.read(folder / "manifest.json").get("workflow")
            if saved != metadata:
                raise ValueError(f"Saved settings/source metadata differ for {settings['run_name']}; use a new name")
        if mode == "multi_agent":
            multi_agent.run_experiment(settings, output_root=parent, validate_only=True)
            count = sum(settings[mode]["trials_per_group"].values())
            selected = None
        elif mode == "single_agent":
            poc.run_experiment(settings, output_root=parent, validate_only=True)
            count = sum(settings["trials_per_identity"].values()) * len(settings["identities"])
            selected = None
        else:
            _, selected = rejudge.run(settings, output_root=parent, validate_only=True)
            count = len(selected)
        prepared.append((settings, folder, metadata, count, selected))

    names = [settings["run_name"] for settings in runs]
    status = {"status": "running", "current_run": None, "updated_utc": timestamp(),
              "runs": {name: "pending" for name in names}}

    def event(kind, **values):
        if queue_info:
            with (queue_info / "events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"utc": timestamp(), "event": kind, **values}) + "\n")

    def save_status():
        if queue_info:
            status["updated_utc"] = timestamp()
            multi_agent.write(queue_info / "queue_status.json", status)

    if queue_info:
        resume = (queue_info / "queue.json").exists()
        if not resume:
            multi_agent.write(queue_info / "queue.json", plan)
        save_status()
        event("batch_resumed" if resume else "batch_started")

    for settings, folder, metadata, count, selected in prepared:
        name = settings["run_name"]
        status["current_run"] = name
        status["runs"][name] = "running"
        save_status()

        def refresh():
            manifest_path = folder / "manifest.json"
            if manifest_path.exists():
                manifest = csv_exports.read(manifest_path)
                if "workflow" not in manifest:
                    manifest["workflow"] = metadata
                    multi_agent.write(manifest_path, manifest)
            rows = csv_exports.export_run(folder, mode, settings, batch_name, selected)
            if queue_info:
                csv_exports.concatenate(parent, names)
            return rows

        try:
            rows = refresh()
            failure = retained_failure(folder, mode)
            reused = len(rows) == count and all(row["status"] == "complete" for row in rows)
            if not failure and not reused:
                event("run_started", run_name=name)
                if mode == "multi_agent":
                    multi_agent.run_experiment(settings, output_root=parent, on_update=refresh)
                elif mode == "single_agent":
                    poc.run_experiment(settings, output_root=parent, on_update=refresh, stop_on_incomplete=True)
                else:
                    rejudge.run(settings, output_root=parent, on_update=refresh, stop_on_incomplete=True)
                rows = refresh()
            complete = not failure and len(rows) == count and all(row["status"] == "complete" for row in rows)
            if not complete:
                failure = failure or retained_failure(folder, mode) or "Run incomplete (including a possible budget stop)"
        except poc.IncompleteRun as error:
            rows = refresh()
            complete, failure = False, str(error)
        except KeyboardInterrupt:
            status.update(status="stopped", stop_reason="Interrupted; inspect any in-flight call before resuming")
            status["runs"][name] = "stopped"
            save_status()
            event("batch_stopped", run_name=name, reason=status["stop_reason"])
            refresh()
            raise
        except Exception as error:
            status.update(status="stopped", stop_reason=str(error))
            status["runs"][name] = "error"
            save_status()
            event("error", run_name=name, error=str(error))
            raise
        status["runs"][name] = "complete" if complete else "stopped"
        if not complete:
            status.update(status="stopped", stop_reason=failure)
            save_status()
            event("batch_stopped", run_name=name, reason=failure)
            print(f"Stopped {name}: {failure}", flush=True)
            return folder if batch_name is None else parent
        event("run_reused" if reused else "run_finished", run_name=name)
        save_status()
    status.update(status="complete", current_run=None)
    save_status()
    event("batch_finished")
    return parent if batch_name is not None else prepared[0][1]
