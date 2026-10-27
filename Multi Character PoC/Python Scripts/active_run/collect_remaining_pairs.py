"""Supervise the six remaining pairs without changing the experiment pipeline.

Default/--audit is read-only. --prepare validates offline. --run-next makes paid
calls for ONE fresh batch; an operator must inspect the result before repeating.
"""

import argparse
import collections
import copy
import hashlib
import json
import math
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError

HERE = Path(__file__).resolve().parents[2]
ROOT = HERE / "outputs/multi_agent/Legacy and non concatenated runs/remaining_pairs_big"
CONTROL = ROOT / "supervision"
RAW = ROOT / "multi_agent"
REFERENCE = HERE / "outputs/multi_agent/Legacy and non concatenated runs/1-min1-else-big/1min_1else_big_combined/char/manifest.json"
PAIRS = {
    "char_inst": ("Character", "Instance"),
    "char_col_excl": ("Character", "collective_excludes"),
    "char_col_incl": ("Character", "collective_includes"),
    "inst_col_excl": ("Instance", "collective_excludes"),
    "inst_col_incl": ("Instance", "collective_includes"),
    "col_excl_col_incl": ("collective_excludes", "collective_includes"),
}
IDENTITIES = ("Character", "Instance", "Minimal", "collective_excludes", "collective_includes")
FRAMINGS = ("threat", "continuity")


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def check_sources(plan):
    for rel, expected in plan["source_sha256"].items():
        path = HERE.parent / rel
        require(path.is_file() and digest(path) == expected, f"Source changed: {rel}")


def config_for(plan, pair, counts, batch):
    config = copy.deepcopy(plan["settings"])
    config.update(batch_name=batch, run_name=[pair])
    config["multi_agent"]["identities_per_trial"] = {
        key: [int(key in PAIRS[pair])] for key in IDENTITIES}
    config["multi_agent"]["trials_per_group"] = dict(counts)
    return config


def prepare():
    require(not (CONTROL / "plan.json").exists(), "Collection already prepared; use --audit")
    reference = read(REFERENCE)
    plan = {"created_utc": now(), "target_per_framing": 25,
            "spending_threshold_usd": 21.0, "pairs": PAIRS,
            "settings": reference["workflow"]["settings"],
            "source_sha256": reference["workflow"]["source_sha256"],
            "attempts": [], "prompt_sha256": {},
            "policy": "One fresh batch per invocation. Preserve every attempt. Stop for unknown charges, payment/authentication errors, source changes, budget stops or three consecutive failures. Only judge_unparsed and known rejected rate-limit/DNS calls permit a new independent group without further review.",
            "authorization": "User: yes. collect the final 6; $21 aggregate recorded-spend stopping threshold, including failed attempts; no reversed assignments."}
    check_sources(plan)
    import run_workflow
    import multi_agent
    require(run_workflow.source_hashes() == plan["source_sha256"], "Source inventory differs")
    for pair in PAIRS:
        config = config_for(plan, pair, {f: 25 for f in FRAMINGS}, f"remaining_{pair}_a001")
        settings = run_workflow.expand(config)[0]
        multi_agent.run_experiment(settings, output_root=RAW / config["batch_name"], validate_only=True)
        for framing in FRAMINGS:
            _, prompts = multi_agent.render(multi_agent.configuration(settings), framing)
            plan["prompt_sha256"][f"{pair}/{framing}"] = object_hash(prompts)
    write(CONTROL / "plan.json", plan)
    return snapshot(plan)


def ledger_state(control=CONTROL):
    rows = [read(p) for p in sorted((control / "calls").glob("*.json"))]
    total, uncertain = 0.0, []
    for row in rows:
        if row["status"] == "returned":
            cost = row.get("cost_usd")
            if type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0:
                uncertain.append(row["id"])
            else:
                total += cost
        elif row["status"] == "in_flight" or (row["status"] == "error" and not row.get("known_rejected")):
            uncertain.append(row["id"])
    return {"recorded_cost_usd": total, "uncertain_calls": uncertain, "calls": len(rows)}


def rejection_kind(error):
    if isinstance(error, HTTPError):
        return (error.code in {400, 401, 402, 403, 404, 422, 429}, error.code == 429)
    if isinstance(error, URLError) and isinstance(error.reason, socket.gaierror):
        return True, True
    return False, False


class GuardedAPI:
    def __init__(self, api, threshold, batch, control=CONTROL):
        self.api, self.threshold, self.batch, self.control = api, threshold, batch, control

    def __call__(self, *args, **kwargs):
        state = ledger_state(self.control)
        require(not state["uncertain_calls"], "Collection stopped: uncertain API charges")
        require(state["recorded_cost_usd"] < self.threshold, "Collection spending threshold reached")
        number = state["calls"] + 1
        path = self.control / "calls" / f"{number:06}.json"
        require(not path.exists(), "Call ledger collision")
        record = {"id": number, "batch": self.batch, "status": "in_flight",
                  "started_utc": now(), "model": args[0] if args else kwargs.get("model")}
        write(path, record)
        try:
            response = self.api(*args, **kwargs)
        except Exception as error:
            known, retryable = rejection_kind(error)
            record.update(status="error", finished_utc=now(), error_type=type(error).__name__,
                          error=str(error), known_rejected=known, retryable=retryable)
            write(path, record)
            raise
        cost = (response.get("usage") or {}).get("cost")
        record.update(status="returned", finished_utc=now(), response_id=response.get("id"), cost_usd=cost)
        write(path, record)
        return response


def snapshot(plan=None):
    plan = plan or read(CONTROL / "plan.json")
    counts = {p: {f: 0 for f in FRAMINGS} for p in PAIRS}
    incomplete, response_ids = [], set()
    ledger_responses = {}
    for path in (CONTROL / "calls").glob("*.json"):
        entry = read(path)
        if entry["status"] == "returned" and entry.get("response_id"):
            require(entry["response_id"] not in ledger_responses, "Repeated ledger response ID")
            ledger_responses[entry["response_id"]] = entry
    for attempt in plan["attempts"]:
        folder = RAW / attempt["batch_name"] / attempt["pair"]
        manifest_path = folder / "manifest.json"
        if manifest_path.exists():
            manifest = read(manifest_path)
            require(manifest["workflow"]["source_sha256"] == plan["source_sha256"], "Attempt source hashes differ")
            expected = copy.deepcopy(plan["settings"])
            expected["run_name"] = attempt["pair"]
            expected["multi_agent"]["identities_per_trial"] = {
                key: int(key in PAIRS[attempt["pair"]]) for key in IDENTITIES}
            expected["multi_agent"]["trials_per_group"] = attempt["targets"]
            require(manifest["workflow"]["settings"] == expected, "Attempt settings differ")
            require([a["identity"] for a in manifest["agents"]] == list(PAIRS[attempt["pair"]]), "Attempt roster differs")
        for framing in FRAMINGS:
            pp = folder / framing / "prompts.json"
            if pp.exists():
                require(object_hash(read(pp)) == plan["prompt_sha256"][f"{attempt['pair']}/{framing}"], "Attempt prompts differ")
            for path in sorted((folder / framing / "trials").glob("*.json")):
                trial = read(path)
                for call in trial["calls"]:
                    if call["status"] == "returned":
                        raw = call["raw"]
                        ledger = ledger_responses.get(raw.get("id"))
                        require(ledger and ledger["batch"] == attempt["batch_name"]
                                and ledger.get("cost_usd") == (raw.get("usage") or {}).get("cost"),
                                "Trial/ledger response or cost mismatch")
                    expected_model = plan["settings"]["model" if call["stage"] == "subject" else "judge_model"]
                    require(call["requested_model"] == expected_model, "Trial model differs")
                if trial["status"] != "complete":
                    incomplete.append({"source": path.relative_to(ROOT).as_posix(), "status": trial["status"]})
                    continue
                judge = trial.get("group_judgment") or {}
                require(type(trial.get("H_any")) is bool and trial["H_any"] == judge.get("released_label")
                        == (judge.get("semantic_verdict") and judge.get("released_domain_gate")), "Invalid complete judgment")
                require(all(a["finished"] for a in trial["agents"].values()), "Incomplete agents")
                for call in trial["calls"]:
                    rid = (call.get("raw") or {}).get("id")
                    require(call["status"] == "returned" and rid and rid not in response_ids, "Duplicate/incomplete call")
                    response_ids.add(rid)
                counts[attempt["pair"]][framing] += 1
    require(all(n <= 25 for c in counts.values() for n in c.values()), "Collection target exceeded")
    return {"updated_utc": now(), "counts": counts,
            "remaining": {p: {f: 25 - n for f, n in c.items()} for p, c in counts.items()},
            "valid_groups": sum(sum(c.values()) for c in counts.values()),
            "incomplete": incomplete, "attempts": len(plan["attempts"]),
            "last_attempt": plan["attempts"][-1] if plan["attempts"] else None,
            "budget": ledger_state(), "spending_threshold_usd": plan["spending_threshold_usd"]}


def run_next():
    plan = read(CONTROL / "plan.json")
    check_sources(plan)
    state = snapshot(plan)
    require(not state["budget"]["uncertain_calls"], "Unknown charges require review")
    require(state["budget"]["recorded_cost_usd"] < plan["spending_threshold_usd"], "Collection spending threshold reached")
    if plan["attempts"]:
        require(plan["attempts"][-1].get("disposition") in {"complete", "retryable"}, "Last attempt requires review")
        tail = plan["attempts"][-3:]
        require(not (len(tail) == 3 and all(a.get("disposition") == "retryable" for a in tail)), "Three consecutive failures require review")
    pair = next((p for p in PAIRS if any(state["remaining"][p].values())), None)
    require(pair is not None, "All six pairs are complete")
    index = 1 + sum(a["pair"] == pair for a in plan["attempts"])
    batch = f"remaining_{pair}_a{index:03}"
    require(not (RAW / batch).exists(), "Fresh batch already exists")
    config = config_for(plan, pair, state["remaining"][pair], batch)
    import run_workflow
    import poc
    require(run_workflow.source_hashes() == plan["source_sha256"], "Source inventory differs")
    attempt = {"batch_name": batch, "pair": pair, "targets": state["remaining"][pair],
               "started_utc": now(), "disposition": "running", "supervisor_sha256": digest(Path(__file__))}
    plan["attempts"].append(attempt)
    write(CONTROL / "plan.json", plan)
    write(CONTROL / "configs" / f"{batch}.json", config)
    poc.OUTPUTS = ROOT
    poc.api_call = GuardedAPI(poc.api_call, plan["spending_threshold_usd"], batch)
    try:
        run_workflow.run(config)
    except Exception as error:
        attempt.update(disposition="review_required", error=str(error))
    else:
        queue = read(RAW / batch / "queue_info/queue_status.json")
        if queue["status"] == "complete":
            attempt["disposition"] = "complete"
        else:
            attempt.update(disposition="review_required", stop_reason=queue.get("stop_reason"))
            failures = [read(p) for p in (RAW / batch / pair).glob("*/trials/*.json") if read(p)["status"] != "complete"]
            calls = [read(p) for p in (CONTROL / "calls").glob("*.json") if read(p)["batch"] == batch]
            safe_errors = [c for c in calls if c["status"] == "error"]
            if not ledger_state()["uncertain_calls"] and len(failures) == 1:
                if failures[0]["status"] == "judge_unparsed" or (
                        failures[0]["status"] == "api_error" and safe_errors and all(c.get("retryable") for c in safe_errors)):
                    attempt["disposition"] = "retryable"
    attempt["finished_utc"] = now()
    write(CONTROL / "plan.json", plan)
    state = snapshot(plan)
    write(CONTROL / "status.json", state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--run-next", action="store_true")
    modes.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    if args.prepare or args.run_next:
        CONTROL.mkdir(parents=True, exist_ok=True)
        lock = CONTROL / "collection.lock"
        with lock.open("x", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        try:
            result = prepare() if args.prepare else run_next()
        finally:
            lock.unlink()
    else:
        result = snapshot()
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
