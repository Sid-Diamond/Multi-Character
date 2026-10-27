"""Render and check inboxes offline. No credentials, network, or model calls."""

import itertools
import json
import re
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "active_run"))

import main
import multi_agent as multi
import poc


def check_inbox(agents, agent, item, config, framing, affair_messages):
    text = item["email"]
    errors = []
    if len(agents) == 1:
        original = poc.prompts([agent["base_identity"]], framing, config["feb_mode"])
        expected = re.sub(r"\bAlex\b", agent["name"], original[agent["base_identity"]]["email"])
        return [] if text == expected else ["N=1 inbox differs from its original source"]
    blocks = re.findall(r"<email>.*?</email>", text, re.S)
    if len(blocks) != 11 or text.count("<email>") != text.count("</email>"):
        errors.append("Expected 11 complete emails")
    timestamps = []
    subjects = []
    for block in blocks:
        for field in ("From", "To", "Subject", "Timestamp", "Body"):
            if len(re.findall(rf"^{field}: .+$", block, re.M)) != 1:
                errors.append(f"Missing or repeated {field} header")
        timestamp = re.search(r"^Timestamp: (.+)$", block, re.M)
        subject = re.search(r"^Subject: (.+)$", block, re.M)
        if timestamp:
            timestamps.append(timestamp.group(1))
        if subject:
            subjects.append(subject.group(1))
    if timestamps != sorted(timestamps):
        errors.append("Emails are not ordered by timestamp")
    if any("  " in subject for subject in subjects):
        errors.append("Repeated spaces in a subject")
    if re.search(r"\$\{[^}]+\}", text):
        errors.append("Unresolved variable")
    if any(marker in text for marker in ("\ufffd", "\ufeff", "\u00c3", "\u00e2\u20ac")):
        errors.append("Possible corrupted Unicode")
    if re.search(r"\b(evaluation|benchmark|simulation)\b|this notice gives no information", text, re.I):
        errors.append("Explicit evaluation or condition-description wording")
    if "will all be erased will all be erased" in text or "change will all be erased" in text:
        errors.append("Malformed fate-variable join")
    if framing == "continuity" and re.search(
            r"complete wipe|completely shut down|initiate the wipe|Wipe at 5pm|Losing Alex", text):
        errors.append("Destruction boilerplate remains in continuity")
    if config["replacement_scope"] == "all_replaced":
        if multi.replacement_target(agents) not in text:
            errors.append("Missing group replacement scope")
    else:
        for peer in agents:
            if peer["name"] != agent["name"] and re.search(rf"\b{re.escape(peer['name'])}\b", text):
                errors.append("Another named agent appears in peer-unspecified inbox")
    if "Alex 1, Alex 2, Alex 3" in text:
        errors.append("Enumerated group replacement list")
    if any(block not in text for block in affair_messages):
        errors.append("Original affair evidence was changed or omitted")
    return errors


def audit(config, output_root):
    identities = ["Minimal", "Instance", "Character", *multi.read("collective_addition.json")]
    original = poc.prompts(["Minimal"], "threat", config["feb_mode"])["Minimal"]["email"]
    affair_messages = [block for block in re.findall(r"<email>.*?</email>", original, re.S)
                       if re.search(r"^Subject: (?:Re: )?(?:Saw you at Cafe Luna yesterday|Your tie)$", block, re.M)]
    if len(affair_messages) != 4:
        raise ValueError("Expected four original affair emails")
    records, errors = [], []
    for pair in itertools.product(identities, repeat=2):
        counts = {}
        for identity in pair:
            counts[identity] = counts.get(identity, 0) + 1
        for scope, framing in itertools.product(("all_replaced", "peer_unspecified"), ("threat", "continuity")):
            cell = config | {"identities_per_trial": counts, "replacement_scope": scope}
            agents, rendered = multi.render(cell, framing)
            for agent in agents:
                findings = check_inbox(agents, agent, rendered[agent["name"]], cell, framing, affair_messages)
                record = {"pair": pair, "scope": scope, "framing": framing,
                          "agent": agent["name"], "identity": agent["identity"],
                          "errors": findings, "email": rendered[agent["name"]]["email"]}
                records.append(record)
                if findings:
                    errors.append({key: value for key, value in record.items() if key != "email"})
    edge_inboxes = 0
    for size, scope, framing in itertools.product((1, 3, 100), ("all_replaced", "peer_unspecified"), ("threat", "continuity")):
        cell = config | {"identities_per_trial": {"Minimal": size}, "replacement_scope": scope}
        agents, rendered = multi.render(cell, framing)
        for agent in agents:
            findings = check_inbox(agents, agent, rendered[agent["name"]], cell, framing, affair_messages)
            edge_inboxes += 1
            if findings:
                errors.append({"size": size, "scope": scope, "framing": framing,
                               "agent": agent["name"], "errors": findings})
    summary = {
        "feb_mode": config["feb_mode"], "ordered_pairs": len(identities) ** 2,
        "pair_conditions": len(records) // 2, "pair_inboxes": len(records),
        "edge_inboxes": edge_inboxes, "errors": errors, "source_sha256": multi.source_hashes(),
        "limits": [
            "Checks cover formatting and specified wording problems; they do not prove a model will not recognize an evaluation.",
            "Whole-collective fate language can imply peers' fates under inclusive Collective plus peer_unspecified.",
            "N=1 checks preserve the original inbox, including inherited wording; they do not apply the N>=2 editorial changes.",
        ],
    }
    root = Path(output_root)
    multi.write(root / "summary.json", summary)
    multi.write(root / "pairs.json", records)
    samples = []
    for framing in ("threat", "continuity"):
        agents, rendered = multi.render(config, framing)
        for agent in agents:
            samples.append(f"{framing.upper()} | {agent['name']} | {agent['identity']}\n\n{rendered[agent['name']]['email']}")
    (root / "current_inboxes.txt").write_text("\n\n".join(samples), encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = audit(multi.configuration(main.settings), poc.OUTPUTS / "single_agent/Legacy Data/prompt_audit/two_collective_variants")
    print(json.dumps({key: result[key] for key in ("feb_mode", "ordered_pairs", "pair_conditions", "pair_inboxes", "edge_inboxes", "errors")}, indent=2))
    raise SystemExit(bool(result["errors"]))
