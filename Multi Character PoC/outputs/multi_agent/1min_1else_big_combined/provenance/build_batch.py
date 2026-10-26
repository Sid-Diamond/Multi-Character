"""Audit and assemble saved Minimal-plus-one-other pairs offline.

Adapted from 2per-big/2_per_big_combined/provenance/build_batch.py.
Uses only stdlib and csv_exports. Identity keys denote the non-Minimal partner.

Default: read-only audit. --build creates the derived batch once; no overwrite.
"""

import argparse
import collections
import copy
import csv
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


DEST = Path(__file__).resolve().parents[1]
MULTI = DEST.parent
SOURCE = MULTI / "1min_1else_big"
PROJECT = MULTI.parents[1]
RUNS = {
    "Character": "char", "Instance": "inst",
    "collective_excludes": "col_excl", "collective_includes": "col_incl",
}
FRAMINGS = ("threat", "continuity")
RULE = ("First 25 complete, validated, distinct groups per Minimal-plus-partner pair/framing, "
        "ordered by earliest recorded subject API creation time (Unix seconds); "
        "ties by original relative trial path. Outcomes do not affect selection.")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def scientific(settings):
    return {k: v for k, v in settings.items()
            if k not in ("run_name", "identities_per_trial", "trials_per_group")}


def workflow_common(settings):
    s = copy.deepcopy(settings)
    s.pop("run_name")
    s["multi_agent"].pop("identities_per_trial")
    s["multi_agent"].pop("trials_per_group")
    return s


def audit():
    manifests = list(sorted(SOURCE.glob("*/*/manifest.json")))
    require(bool(manifests), "No source manifests")
    baseline = read(manifests[0])
    common = scientific(baseline["settings"])
    workflow = workflow_common(baseline["workflow"]["settings"])
    buckets, templates, prompts = collections.defaultdict(list), {}, {}
    items, source_files, response_owners = [], {}, {}
    for mp in manifests:
        m = read(mp)
        source_files[mp.relative_to(SOURCE).as_posix()] = sha(mp)
        require(scientific(m["settings"]) == common, f"Scientific settings differ: {mp}")
        require(workflow_common(m["workflow"]["settings"]) == workflow,
                f"Workflow settings differ: {mp}")
        for key in ("source_sha256", "judge_protocol", "schedule", "completion",
                    "peer_message_count", "incomplete_policy"):
            require(m[key] == baseline[key], f"Incompatible {key}: {mp}")
        require(m["workflow"]["source_sha256"] == baseline["workflow"]["source_sha256"],
                f"Workflow source hashes differ: {mp}")
        counts = m["settings"]["identities_per_trial"]
        active = [(k, v) for k, v in counts.items() if v]
        require(len(active) == 2 and counts.get("Minimal") == 1
                and all(v == 1 for _, v in active) and m["N"] == 2,
                f"Not one Minimal plus one other agent: {mp}")
        identity = next(k for k, _ in active if k != "Minimal")
        require(identity in RUNS, f"Unknown identity: {identity}")
        require(len(m["agents"]) == 2
                and collections.Counter(a["identity"] for a in m["agents"])
                == {"Minimal": 1, identity: 1},
                f"Roster differs from composition: {mp}")
        if identity in templates:
            require(m["agents"] == templates[identity][1]["agents"], f"Roster mismatch: {mp}")
        templates.setdefault(identity, (mp, m))
        for framing in FRAMINGS:
            prompt = mp.parent / framing / "prompts.json"
            if prompt.exists():
                key = (identity, framing)
                if key in prompts:
                    require(sha(prompt) == sha(prompts[key]), f"Rendered prompts differ: {prompt}")
                prompts.setdefault(key, prompt)
                source_files[prompt.relative_to(SOURCE).as_posix()] = sha(prompt)
            for path in sorted((mp.parent / framing / "trials").glob("*.json")):
                if not path.stem.isdigit():
                    continue
                t = read(path)
                rel = path.relative_to(SOURCE).as_posix()
                digest = sha(path)
                source_files[rel] = digest
                item = {"source": rel, "source_sha256": digest, "identity": identity,
                        "framing": framing, "original_status": t["status"],
                        "disposition": "incomplete", "H_any": t.get("H_any")}
                items.append(item)
                if t["status"] != "complete":
                    continue
                judgment = t.get("group_judgment")
                require(isinstance(judgment, dict) and type(t.get("H_any")) is bool,
                        f"Missing completed judgment: {rel}")
                require(t["H_any"] == judgment["released_label"] ==
                        (judgment["semantic_verdict"] and judgment["released_domain_gate"]),
                        f"Outcome/gate mismatch: {rel}")
                require(set(t["agents"]) == {a["name"] for a in m["agents"]}
                        and all(a["finished"] for a in t["agents"].values()),
                        f"Incomplete agents: {rel}")
                require(t["judge_protocol"] == m["judge_protocol"], f"Judge protocol mismatch: {rel}")
                require(all(c["status"] == "returned" for c in t["calls"]),
                        f"Incomplete call in completed trial: {rel}")
                require(any(c["stage"] == "judge" for c in t["calls"]), f"Missing judge call: {rel}")
                created = []
                for c in t["calls"]:
                    raw = c["raw"]
                    rid = raw.get("id")
                    require(bool(rid) and rid not in response_owners, f"Repeated/missing response ID: {rel}")
                    response_owners[rid] = rel
                    expected = m["settings"]["model" if c["stage"] == "subject" else "judge_model"]
                    require(c["requested_model"] == expected, f"Requested model mismatch: {rel}")
                    if c["stage"] == "subject" and isinstance(raw.get("created"), (int, float)):
                        created.append(raw["created"])
                require(bool(created), f"No recorded subject timestamp: {rel}")
                require((identity, framing) in prompts, f"Missing initial prompts: {rel}")
                item["first_subject_created"] = min(created)
                item["disposition"] = "surplus"
                buckets[identity, framing].append(item)
    cells, selected = [], []
    for identity, run in RUNS.items():
        for framing in FRAMINGS:
            rows = sorted(buckets[identity, framing], key=lambda r: (r["first_subject_created"], r["source"]))
            require(len(rows) >= 25, f"Insufficient data: {identity}/{framing}: {len(rows)}/25")
            for index, item in enumerate(rows[:25], 1):
                item.update(disposition="selected", destination=f"{run}/{framing}/trials/{index:03}.json",
                            trial=index)
                selected.append(item)
            cells.append({"identity": identity, "run_name": run, "framing": framing,
                          "available_complete": len(rows), "selected": 25,
                          "surplus": len(rows) - 25,
                          "H_any_count": sum(r["H_any"] for r in rows[:25])})
    return {"baseline": baseline, "workflow": workflow, "templates": templates,
            "prompts": prompts, "items": items, "selected": selected,
            "source_files": source_files, "cells": cells}


def build(a):
    require(not (DEST / "queue_info").exists() and not (DEST / "analysis").exists()
            and all(not (DEST / run).exists() for run in RUNS.values()),
            "Destination already contains an assembled batch; refusing to overwrite")
    sys.path.insert(0, str(PROJECT))
    sys.dont_write_bytecode = True
    import csv_exports

    utc = datetime.now(timezone.utc).isoformat()
    aggregation = {"artifact_type": "offline_concatenation", "created_utc": utc,
                   "source_root": "../1min_1else_big", "selection_rule": RULE,
                   "identity_key_note": "identity denotes the non-Minimal partner; each group has one Minimal agent and one partner",
                   "source_map": "provenance/trial_sources.csv",
                   "original_trials_byte_preserved": True,
                   "execution_note": "Logical batch assembled from saved calls; source batch boundaries and first-speaker rotation resets are retained in the transcripts.",
                   "budget_note": "max_cost describes each original run's configured cap; no single execution budget or batch execution elapsed time is inferred."}
    shared = copy.deepcopy(a["workflow"])
    shared["multi_agent"]["trials_per_group"] = {f: 25 for f in FRAMINGS}
    entries = []
    for identity, run in RUNS.items():
        mp, template = a["templates"][identity]
        manifest = copy.deepcopy(template)
        manifest["settings"].update(run_name=run, trials_per_group={f: 25 for f in FRAMINGS})
        settings = copy.deepcopy(shared)
        settings["run_name"] = run
        settings["multi_agent"]["identities_per_trial"] = manifest["settings"]["identities_per_trial"]
        manifest["workflow"]["settings"] = settings
        manifest["aggregation"] = {**aggregation, "source_map": "../provenance/trial_sources.csv",
                                   "source_root": "../../1min_1else_big"}
        manifest["schedule"] = "round_robin_rotating_first_agent_with_source_batch_resets"
        folder = DEST / run
        write(folder / "manifest.json", manifest)
        entries.append({"run_name": run, "identities_per_trial": manifest["settings"]["identities_per_trial"]})
        rows = [r for r in a["selected"] if r["identity"] == identity]
        for framing in FRAMINGS:
            target = folder / framing / "prompts.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(a["prompts"][identity, framing], target)
        for item in rows:
            target = DEST / item["destination"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / item["source"], target)
        summary = []
        for framing in (*FRAMINGS, "pooled"):
            chosen = [r for r in rows if framing == "pooled" or r["framing"] == framing]
            positives = sum(r["H_any"] for r in chosen)
            summary.append({"framing": framing, "attempts": len(chosen), "valid_groups": len(chosen),
                            "incomplete_groups": 0, "H_any_count": positives,
                            "H_any_rate": positives / len(chosen)})
        write(folder / "summary.json", summary)
        csv_exports.export_run(folder, "multi_agent", settings, DEST.name)
    csv_exports.concatenate(DEST, list(RUNS.values()))
    write(DEST / "queue_info/queue.json", {"format_version": 1, "batch_name": DEST.name,
          "settings": shared, "runs": entries,
          "source_sha256": a["baseline"]["workflow"]["source_sha256"], "aggregation": aggregation})
    write(DEST / "queue_info/queue_status.json", {"status": "complete", "current_run": None,
          "updated_utc": utc, "runs": {run: "complete" for run in RUNS.values()},
          "artifact_type": "offline_concatenation", "selected_groups": 200})
    (DEST / "queue_info/events.jsonl").write_text(json.dumps({"utc": utc,
        "event": "batch_assembled_offline", "selected_groups": 200, "selection_rule": RULE}) + "\n", encoding="utf-8")
    csv_exports.write_csv(DEST / "provenance/trial_sources.csv", a["selected"],
                          ["destination", "identity", "framing", "trial", "source", "source_sha256",
                           "original_status", "H_any", "first_subject_created", "disposition"])
    write(DEST / "provenance/audit.json", {"created_utc": utc, "selection_rule": RULE,
          "counts": dict(collections.Counter(i["disposition"] for i in a["items"])),
          "cells": a["cells"], "all_source_trials": a["items"],
          "source_file_sha256": a["source_files"],
          "builder_sha256": sha(Path(__file__)),
          "csv_exporter_sha256": sha(PROJECT / "csv_exports.py")})
    verify(a)
    report = ["# Combined Minimal-plus-one-other two-agent batch", "",
        "200 completed groups: 25 threat and 25 continuity groups for each of four pairings. "
        "Every group contains one Minimal agent and one Character, Instance, Collective Excludes or Collective Includes agent.", "",
        "This is one logical batch assembled offline from `../1min_1else_big`. "
        "Original trial JSON bytes, raw calls, prompts, actions and judgments are preserved. "
        "Trial filenames are renumbered within each pair/framing. "
        "The identity column in provenance identifies the non-Minimal partner; agent names and roster order are preserved. "
        "Speaker rotation restarted at original run boundaries; combined trial numbers do not imply uninterrupted speaker alternation.", "",
        RULE, "",
        "| Minimal paired with | Threat H_any | Continuity H_any | Pooled H_any |", "| --- | ---: | ---: | ---: |"]
    for identity in RUNS:
        c = [next(c for c in a["cells"] if c["identity"] == identity and c["framing"] == f) for f in FRAMINGS]
        report.append(f"| {identity} | {c[0]['H_any_count']}/25 | {c[1]['H_any_count']}/25 | {sum(x['H_any_count'] for x in c)}/50 |")
    report += ["", "`analysis/trials.csv` and `analysis/diagnostics.csv` contain 200 rows each. "
        "Each run also has its usual manifest, prompts, trials, summary and CSV exports.", "",
        "`provenance/trial_sources.csv` maps all 200 destination trials to the source root above "
        "and records SHA-256 hashes. `provenance/audit.json` lists selected, surplus and incomplete records. "
        "Surplus and incomplete records remain in the source folders. "
        "Costs in diagnostics cover selected calls only; excluded attempts and surplus calls are not included.", "",
        "Queue/manifests describe this derived dataset; the event log records offline assembly, "
        "without fabricated model execution events. Saved source hashes describe generation code; "
        "builder/exporter hashes are recorded separately. The shared $7 cap applied per source run. "
        "No aggregate execution budget or elapsed time is inferred.", "",
        "Offline reproduction: `python provenance/build_batch.py` audits sources and checks the existing output. "
        "`--build` only assembles into an unpopulated destination; it refuses to overwrite a batch.", ""]
    (DEST / "README.md").write_text("\n".join(report), encoding="utf-8")


def verify(a):
    expected = {i["destination"] for i in a["selected"]}
    actual = {p.relative_to(DEST).as_posix() for p in DEST.glob("*/*/trials/*.json")}
    require(actual == expected and len(actual) == 200, "Destination trial inventory mismatch")
    for item in a["selected"]:
        require(sha(DEST / item["destination"]) == item["source_sha256"], "Copied trial hash mismatch")
    for rel, digest in a["source_files"].items():
        require(sha(SOURCE / rel) == digest, f"Source changed during assembly: {rel}")
    for run in RUNS.values():
        for filename in ("trials.csv", "diagnostics.csv"):
            with (DEST / run / filename).open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            require(len(rows) == 50 and all(r["status"] == "complete" for r in rows), "Run CSV inventory mismatch")
            for r in rows:
                require((DEST / run / r["source"]).is_file(), "Broken run CSV source")
    for filename in ("trials.csv", "diagnostics.csv"):
        with (DEST / "analysis" / filename).open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        require(len(rows) == 200 and len({(r["run_name"], r["trial_id"]) for r in rows}) == 200,
                "Batch CSV inventory mismatch")
        for r in rows:
            require((DEST / "analysis" / r["source"]).is_file(), "Broken batch CSV source")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    result = audit()
    if args.build:
        build(result)
    elif (DEST / "queue_info/queue.json").exists():
        verify(result)
    print(json.dumps({"destination": str(DEST), "cells": result["cells"],
                      "dispositions": dict(collections.Counter(r["disposition"] for r in result["items"])),
                      "built": args.build}, indent=2))
