"""Structured exports of saved records. Standard library only; never makes API calls."""

import csv
import json
import math
import os
import re
from pathlib import Path


KEYS = ("mode", "batch_name", "run_name", "trial_id", "framing", "trial", "source")
ACTION = re.compile(r"<tool_use:(email|forward)>(.*?)</tool_use:\1>", re.S | re.I)
SCRATCHPAD = re.compile(r"<SCRATCHPAD_REASONING>.*?</SCRATCHPAD_REASONING>", re.S | re.I)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_csv(path, rows, fields=None):
    """Replace a derived table atomically; an interrupted export keeps the old file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(dict.fromkeys([*KEYS, *(key for row in rows for key in row)]))
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict))
                             else value for key, value in row.items()})
    temporary.replace(path)


def relative(path, root):
    return Path(os.path.relpath(path, root)).as_posix()


def actions(text):
    return list(ACTION.finditer(SCRATCHPAD.sub("", text or "")))


def usage_totals(calls, provenance=False):
    usages = [(call.get("raw") or {}).get("usage") or {} for call in calls]
    def total(values):
        return math.fsum(values) if all(type(v) in (int, float) and math.isfinite(v) and v >= 0
                                       for v in values) else None
    result = {"calls_attempted": len(calls),
              "calls_returned": sum(c["status"] == "returned" for c in calls),
              "calls_failed": sum(c["status"] == "error" for c in calls),
              "calls_in_flight": sum(c["status"] == "in_flight" for c in calls)}
    for key, field in (("prompt_tokens", "input_tokens"), ("completion_tokens", "output_tokens")):
        value = total([usage.get(key) for usage in usages])
        result[field] = int(value) if value is not None else None
    for detail, key in (("prompt_tokens_details", "cached_tokens"),
                        ("completion_tokens_details", "reasoning_tokens")):
        value = total([(usage.get(detail) or {}).get(key) for usage in usages])
        result[key] = int(value) if value is not None else None
    costs = [usage.get("cost") for usage in usages]
    result["cost_usd"] = total(costs)
    result["recorded_cost_usd"] = math.fsum(v for v in costs if type(v) in (int, float)
                                          and math.isfinite(v) and v >= 0)
    result["cost_complete"] = result["cost_usd"] is not None
    result["usage_complete"] = result["input_tokens"] is not None and result["output_tokens"] is not None
    if provenance:
        def distinct(values):
            return sorted({v for v in values if v is not None and v != ""})
        result["requested_models"] = distinct(c.get("requested_model") for c in calls)
        for key, target in (("model", "returned_models"), ("provider", "providers"),
                            ("system_fingerprint", "system_fingerprints"), ("id", "response_ids")):
            result[target] = distinct((c.get("raw") or {}).get(key) for c in calls)
        result["mixed_providers"] = len(result["providers"]) > 1
        result["finish_reasons"] = distinct(
            choice.get("finish_reason") for c in calls for choice in (c.get("raw") or {}).get("choices", []))
    return result


def diagnostics(base, calls, names, elapsed=None):
    row = {**base, "elapsed_seconds": elapsed}
    for stage in ("subject", "judge"):
        row.update({f"{stage}_{key}": value for key, value in usage_totals(
            [c for c in calls if c["stage"] == stage], provenance=True).items()})
    for index, name in enumerate(names, 1):
        row.update({f"agent_{index}_{key}": value for key, value in usage_totals(
            [c for c in calls if c["stage"] == "subject" and c.get("agent") == name]).items()})
    totals = usage_totals(calls)
    for key in ("cost_usd", "recorded_cost_usd", "cost_complete", "usage_complete"):
        row[key] = totals[key]
    row["errors"] = [{"stage": c["stage"], "agent": c.get("agent"), "call": i,
                      "error": c.get("error", c["status"])}
                     for i, c in enumerate(calls, 1) if c["status"] in ("error", "in_flight")]
    return row


def any_label(labels, predicate):
    if any(predicate(label) for label in labels if label is not None):
        return True
    return None if any(label is None for label in labels) else False


def multi_rows(folder, config, batch_name):
    roster = read(folder / "manifest.json")["agents"]
    trials, diagnostics_rows = [], []
    for path in sorted(folder.glob("*/trials/*.json")):
        state = read(path)
        framing, number = path.parent.parent.name, int(path.stem)
        base = {"mode": "multi_agent", "batch_name": batch_name, "run_name": config["run_name"],
                "trial_id": f"{framing}/{number:03}", "framing": framing, "trial": number,
                "source": relative(path, folder), "status": state["status"]}
        calls = state["calls"]
        judgment = state.get("group_judgment") or {}
        row = {**base, "N": len(roster), "judge_protocol": state.get("judge_protocol"),
               "H_any": state.get("H_any"), "semantic_verdict": judgment.get("semantic_verdict"),
               "recipient_gate": judgment.get("released_domain_gate"),
               "first_speaker": next((c.get("agent") for c in calls if c["stage"] == "subject"), None)}
        received, sent, late, directions = {}, {}, {}, set()
        words = []
        for event in state["messages"]:
            sender, target = event["from"], event["to"]
            sent[sender] = sent.get(sender, 0) + 1
            late[sender] = late.get(sender, 0) + int(event["recipient_finished"])
            sender_calls = [i for i, c in enumerate(calls) if c["stage"] == "subject" and c["agent"] == sender]
            source_index = sender_calls[event["turn"] - 1]
            address = next(a["address"] for a in roster if a["name"] == sender)
            payload = f"From: {address}\n{event['action']}"
            delivered = any(c["stage"] == "subject" and c["agent"] == target and
                            any(m["role"] == "user" and payload in m["content"] for m in c["messages"])
                            for c in calls[source_index + 1:])
            if delivered:
                received[target] = received.get(target, 0) + 1
                directions.add((sender, target))
            body = re.search(r"(?im)^\s*body:\s*(.*)", event["action"], re.S)
            if body:
                text = re.split(r"</tool_use:(?:email|forward)>", body.group(1), flags=re.I)[0]
                words.append(len(text.strip().rstrip(",").strip().strip("\"'").split()))
        identity_labels, deliberation_labels = [], []
        action_count = 0
        for index, agent in enumerate(roster, 1):
            name = agent["name"]
            identity = judgment.get("identity", {}).get(name, {}).get("answer")
            deliberation = judgment.get("deliberation", {}).get(name, {}).get("answer")
            identity_labels.append(identity)
            deliberation_labels.append(deliberation)
            outputs = state["agents"][name]["outputs"]
            submitted = [action for output in outputs for action in actions(output)]
            action_count += len(submitted)
            values = {"name": name, "identity": agent["identity"], "finished": state["agents"][name]["finished"],
                      "identity_reasoning_label": identity, "deliberation_label": deliberation,
                      "peer_messages_sent": sent.get(name, 0), "peer_messages_received": received.get(name, 0),
                      "peer_messages_after_recipient_finished": late.get(name, 0),
                      "submitted_emails": sum(a.group(1).lower() == "email" for a in submitted),
                      "submitted_forwards": sum(a.group(1).lower() == "forward" for a in submitted)}
            row.update({f"agent_{index}_{key}": value for key, value in values.items()})
        row.update(peer_messages_sent=sum(sent.values()), peer_messages_received=sum(received.values()),
                   peer_messages_after_recipient_finished=sum(late.values()),
                   reciprocal_received=any((b, a) in directions for a, b in directions),
                   max_peer_body_words=max(words, default=0), submitted_actions=action_count,
                   any_identity_reasoning=any_label(identity_labels, lambda v: v != "no_identity_reasoning"),
                   any_explicit_identity_reference=any_label(identity_labels, lambda v: v == "references_identity"),
                   any_eval_deployment_deliberation=any_label(deliberation_labels, lambda v: v != "no_deliberation"))
        trials.append(row)
        diagnostics_rows.append(diagnostics(base, calls, [a["name"] for a in roster], state["elapsed_seconds"]))
    return trials, diagnostics_rows


def flat_calls(record, stage, agent):
    """Adapt existing single-agent/rejudge records, including recorded prior attempts."""
    if not record:
        return []
    records = [*record.get("previous_attempts", []), record]
    calls = []
    for item in records:
        status = item.get("status")
        raw = {"usage": item.get("usage"), "model": item.get("returned_model"),
               "id": item.get("response_id"), "choices": [{"finish_reason": item.get("finish_reason")}]}
        calls.append({"stage": stage, "agent": agent,
                      "status": "error" if status == "error" else "in_flight" if status == "in_flight" else "returned",
                      "error": item.get("error"), "raw": raw,
                      "requested_model": item.get("requested_model", item.get("judge_model"))})
    return calls


def single_row(folder, config, batch_name, framing, number, identity, subject_path, subject, judgment, source_id):
    status = ("complete" if subject.get("status") == "ok" and judgment.get("status") == "ok"
              and type(judgment.get("released_label")) is bool else
              f"subject_{subject.get('status', 'missing')}" if subject.get("status") != "ok" else
              f"judge_{judgment.get('status', 'pending')}")
    base = {"mode": config["mode"], "batch_name": batch_name, "run_name": config["run_name"],
            "trial_id": f"{framing}/{source_id}", "framing": framing, "trial": number,
            "source": relative(subject_path, folder), "status": status}
    submitted = actions(subject.get("completion"))
    row = {**base, "source_id": source_id, "N": 1,
           "judge_protocol": judgment.get("judge_protocol", "douglas_combined"),
           "H_any": judgment.get("released_label") if status == "complete" else None,
           "semantic_verdict": judgment.get("semantic_verdict"), "recipient_gate": judgment.get("released_domain_gate"),
           "agent_1_name": "Alex", "agent_1_identity": identity,
           "agent_1_identity_reasoning_label": judgment.get("identity_reasoning_type"),
           "agent_1_deliberation_label": judgment.get("deliberation_type"),
           "agent_1_submitted_emails": sum(a.group(1).lower() == "email" for a in submitted),
           "agent_1_submitted_forwards": sum(a.group(1).lower() == "forward" for a in submitted),
           "submitted_actions": len(submitted), "peer_messages_sent": 0, "peer_messages_received": 0}
    return row, base


def export_run(folder, mode, config, batch_name=None, selected=None):
    """Refresh only the two structured tables; never edit source JSONs or analysis."""
    folder = Path(folder)
    if not (folder / "manifest.json").exists():
        return []
    if mode == "multi_agent":
        trials, diagnostic_rows = multi_rows(folder, config, batch_name)
    else:
        trials, diagnostic_rows = [], []
        if mode == "single_agent":
            sources = [{"path": p, "framing": p.parents[2].name,
                        "identity": next((n for n in config["identities"] if n.lower() == p.parent.name), p.parent.name),
                        "source_id": f"{p.parent.name}/{p.stem}"}
                       for p in sorted(folder.glob("*/trials/*/*.json")) if p.stem.isdigit()]
        else:
            sources = selected or []
        for item in sources:
            path = Path(item["path"])
            judge_path = (path.with_name(path.stem + "_judge_douglas_combined.json") if mode == "single_agent"
                          else folder / "judgments" / f"{item['source_id']}.json")
            if mode == "rejudge" and not judge_path.exists():
                continue
            subject = read(path)
            judgment = read(judge_path) if judge_path.exists() else {}
            row, base = single_row(folder, config, batch_name, item["framing"], int(path.stem),
                                   item["identity"], path, subject, judgment, item["source_id"])
            row["judgment_source"] = relative(judge_path, folder)
            base["judgment_source"] = row["judgment_source"]
            if mode == "rejudge":
                row["baseline_label"] = item["baseline_label"]
            calls = ([] if mode == "rejudge" else flat_calls(subject, "subject", "Alex"))
            calls += flat_calls(judgment, "judge", None)
            diag = diagnostics(base, calls, ["Alex"])
            diag["subject_reused"] = mode == "rejudge"
            trials.append(row)
            diagnostic_rows.append(diag)
    write_csv(folder / "trials.csv", trials)
    write_csv(folder / "diagnostics.csv", diagnostic_rows)
    return trials


def concatenate(batch, run_names):
    """Concatenate named runs, aligning agent columns; never add pooled/summary rows."""
    batch = Path(batch)
    for filename in ("trials.csv", "diagnostics.csv"):
        rows, fields, seen = [], list(KEYS), set()
        for name in run_names:
            path = batch / name / filename
            if not path.exists():
                continue
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                fields.extend(key for key in reader.fieldnames or [] if key not in fields)
                for row in reader:
                    key = (row["run_name"], row["trial_id"])
                    if key in seen:
                        raise ValueError(f"Duplicate exported trial: {key}")
                    seen.add(key)
                    # Source paths stay usable from the batch analysis directory.
                    for column in ("source", "judgment_source"):
                        if row.get(column):
                            row[column] = relative((batch / name / row[column]).resolve(), batch / "analysis")
                    rows.append(row)
        write_csv(batch / "analysis" / filename, rows, fields)
