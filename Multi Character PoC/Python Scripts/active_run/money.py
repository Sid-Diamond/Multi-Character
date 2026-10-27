"""Shared cost report and automatic budget check for both subject modes."""

import json
import math
from pathlib import Path


PROBE_PAIRS = 5


def paired_costs(experiment: Path) -> list[float]:
    costs = []
    for subject_path in sorted(experiment.glob("*/trials/*/[0-9][0-9][0-9].json")):
        judge_path = subject_path.with_name(f"{subject_path.stem}_judge_douglas_combined.json")
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


def review_costs(folder: Path, costs, planned_trials: int, max_cost: float, *,
                 unit="trials", minimum_samples=None) -> bool:
    """Save/print the estimate and continue automatically within the budget.

    A trial costs one subject+judge pair in single-agent mode, or all subject
    turns and the group judge in multi-agent mode. No API calls are made here.
    """
    if (type(planned_trials) is not int or planned_trials < 1 or
            type(max_cost) not in (int, float) or not math.isfinite(max_cost) or max_cost <= 0):
        raise ValueError("The trial target and max_cost must be positive")
    required_samples = min(PROBE_PAIRS, planned_trials) if minimum_samples is None else minimum_samples
    if (type(required_samples) is not int or required_samples < 1 or required_samples > planned_trials):
        raise ValueError("The cost probe sample target must be positive and no larger than the planned total")
    if len(costs) < required_samples:
        raise RuntimeError("The cost probe has incomplete trials")
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in costs):
        raise ValueError("Missing or invalid API cost in the cost probe")
    spent = sum(costs)
    estimate = spent / len(costs) * planned_trials
    report = {"completed_trials": len(costs), "unit": unit, "spent": spent,
              "estimated_total": estimate, "max_cost": max_cost}
    path = Path(folder) / "cost_estimate.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    print(f"Cost after {len(costs)} {unit}: ${spent:.4f}; "
          f"estimated total for {planned_trials} {unit}: ${estimate:.4f}; "
          f"max_cost: ${max_cost:.4f}", flush=True)
    if estimate > max_cost:
        print("Estimated cost exceeds max_cost; stopping before remaining calls.", flush=True)
        return False
    return True


def within_estimate(experiment: Path, planned_pairs: int, max_cost: float, *, minimum_samples=None) -> bool:
    return review_costs(experiment, paired_costs(experiment), planned_pairs, max_cost,
                        unit="single-agent trials", minimum_samples=minimum_samples)
