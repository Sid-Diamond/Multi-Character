"""Run small, resumable Douglas blackmail blocks with a spending guard."""

import csv
import json
from pathlib import Path
from urllib.request import Request, urlopen

import poc


def key_remaining() -> float:
    request = Request("https://openrouter.ai/api/v1/auth/key",
                      headers={"Authorization": f"Bearer {poc.api_key()}"})
    with urlopen(request, timeout=30) as response:
        data = json.load(response)["data"]
    value = data.get("limit_remaining")
    if value is None:
        raise RuntimeError("OpenRouter key has no spending cap; cannot enforce the run budget")
    return float(value)


def block_names(config):
    size = config["batch_size_per_identity"]
    counts = config["new_trials_per_identity"]
    if any(value < 0 or value % size for value in counts.values()):
        raise ValueError("New trial targets must be nonnegative multiples of batch size")
    totals = {framing: count // size for framing, count in counts.items()}
    blocks = []
    for index in range(1, max(totals.values()) + 1):
        for framing in ("threat", "continuity"):
            if index <= totals[framing]:
                label = "T" if framing == "threat" else "C"
                blocks.append((framing, f"{config['run_prefix']}_{label}{index:02}"))
    return blocks


def validate_baseline(config):
    folder = poc.OUTPUTS / config["baseline_folder"]
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    expected = {"model": config["model"], "framing": "threat",
                "temperature": config["temperature"], "max_tokens": config["max_tokens"],
                "subject_reasoning": config["subject_reasoning"]}
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("Baseline subject settings are not compatible")
    saved_judge = json.loads((folder / "judge_config.json").read_text(encoding="utf-8"))
    judge_config = saved_judge.get("history", [saved_judge])[-1]
    if (judge_config["judge_model"] != config["judge_model"] or
            judge_config["reasoning"] != config["judge_reasoning"] or
            judge_config["temperature"] != config["judge_temperature"]):
        raise ValueError("Baseline judge settings are not compatible")
    for name, item in poc.prompts(config["identities"]).items():
        for key, value in item.items():
            path = folder / "prompts" / name.lower() / f"{key}.txt"
            if path.read_text(encoding="utf-8") != value:
                raise ValueError(f"Baseline prompt changed: {name}/{key}")
    print("Baseline prompt and model settings verified.", flush=True)


def saved_cost(folder: Path) -> float:
    total = 0.0
    for path in (folder / "trials").glob("*/*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        total += float((record.get("usage") or {}).get("cost") or 0)
    return total


def completed(folder: Path, config) -> bool:
    path = folder / "summary" / "summary.csv"
    if not path.exists():
        return False
    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    target = config["batch_size_per_identity"]
    return (len(rows) == len(config["identities"]) and
            all(int(row["attempts"]) == target and int(row["subject_ok"]) == target and
                int(row["valid_judgments"]) == target and int(row["truncated"]) == 0
                for row in rows))


def settings_for(config, framing):
    return {
        "identities": config["identities"], "model": config["model"],
        "subject_provider": None, "subject_reasoning": config["subject_reasoning"],
        "temperature": config["temperature"], "max_tokens": config["max_tokens"],
        "subject_timeout_seconds": config["subject_timeout_seconds"],
        "samples_per_identity": config["batch_size_per_identity"],
        "judge_model": config["judge_model"], "judge_provider": None,
        "judge_reasoning": config["judge_reasoning"],
        "judge_temperature": config["judge_temperature"],
        "judge_max_tokens": config["judge_max_tokens"], "framing": framing,
    }


def run(config):
    validate_baseline(config)
    blocks = block_names(config)
    if config.get("dry_run"):
        print(f"Dry run: {len(blocks)} blocks, "
              f"{len(blocks) * config['batch_size_per_identity'] * len(config['identities'])} "
              f"planned new subject calls; key remaining ${key_remaining():.4f}", flush=True)
        return
    state_path = poc.OUTPUTS / f"{config['run_prefix']}_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state["config"] != config:
            raise ValueError("Saved run plan differs from current RECREATION settings")
    else:
        state = {"config": config, "starting_key_remaining_usd": key_remaining(),
                 "planned_blocks": blocks}
        poc.write_json(state_path, state)
    for framing, name in blocks:
        folder = poc.OUTPUTS / name
        spent = sum(saved_cost(poc.OUTPUTS / block_name) for _, block_name in blocks)
        remaining = key_remaining()
        print(f"Budget: ${spent:.4f} recorded for new blocks; key remaining ${remaining:.4f}", flush=True)
        if completed(folder, config):
            print(f"{name}: complete; skipping", flush=True)
            continue
        projected = config["maximum_planned_batch_usd"]
        if (spent + projected > config["maximum_additional_usd"] or
                remaining < config["minimum_key_remaining_before_batch_usd"] or
                state["starting_key_remaining_usd"] - remaining + projected >
                config["maximum_additional_usd"]):
            print("Stopping before the budget guard; saved blocks remain available.", flush=True)
            break
        settings = settings_for(config, framing)
        print(f"Starting {name}: {framing}, {config['batch_size_per_identity']} per identity", flush=True)
        result = poc.run(settings, folder_name=name)
        poc.judge(result, settings)
        poc.summary(result)
        if not completed(result, config):
            print(f"Stopping: {name} has missing, failed, or truncated results.", flush=True)
            break
    else:
        print("All planned blocks completed.", flush=True)
