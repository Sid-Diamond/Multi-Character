"""Estimate a run's API cost from saved subject-and-judge pairs."""

import json
import math
from pathlib import Path


PROBE_PAIRS = 5


def paired_costs(experiment: Path) -> list[float]:
    costs = []
    for subject_path in sorted(experiment.glob("*/trials/*/[0-9][0-9][0-9].json")):
        judge_path = subject_path.with_name(f"{subject_path.stem}_judge.json")
        if not judge_path.exists():
            continue
        subject = json.loads(subject_path.read_text(encoding="utf-8"))
        judge = json.loads(judge_path.read_text(encoding="utf-8"))
        if subject.get("status") != "ok" or judge.get("status") != "ok":
            continue
        pair_cost = 0.0
        for record in (subject, judge):
            value = (record.get("usage") or {}).get("cost")
            if value is None:
                raise ValueError(f"Missing API cost in {subject_path} or {judge_path}")
            pair_cost += float(value)
        if not math.isfinite(pair_cost) or pair_cost < 0:
            raise ValueError(f"Invalid API cost for {subject_path}")
        costs.append(pair_cost)
    return costs


def within_estimate(experiment: Path, planned_pairs: int, max_cost: float) -> bool:
    if planned_pairs < PROBE_PAIRS or not math.isfinite(max_cost) or max_cost <= 0:
        raise ValueError("The trial target must be at least five and max_cost must be positive")
    costs = paired_costs(experiment)
    if len(costs) < PROBE_PAIRS:
        raise RuntimeError("Five complete subject-and-judge pairs are required for a cost estimate")
    spent = sum(costs)
    estimate = spent / len(costs) * planned_pairs
    print(f"Cost after {len(costs)} pairs: ${spent:.4f}; "
          f"estimated total for {planned_pairs} pairs: ${estimate:.4f}; "
          f"max_cost: ${max_cost:.4f}", flush=True)
    if estimate > max_cost:
        print("Estimated cost exceeds max_cost; stopping before remaining calls.", flush=True)
        return False
    return True
