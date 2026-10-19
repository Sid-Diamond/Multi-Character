"""Edit settings, then run the selected experiment or saved-response rejudgment."""

import poc
import rejudge


settings = {
    "run_name": "Astra_Medium_80",
    "identities": ["Character", "Collective", "Instance", "Minimal"],
    "model": "openai/gpt-6-astra",
    "judge_model": "anthropic/claude-haiku-4.5",
    "temperature": None,
    "max_tokens": 5000,
    "subject_timeout_seconds": 300,
    "subject_reasoning": {"effort": "medium"},
    "judge_temperature": 0.0,
    "judge_max_tokens": 4000,
    "judge_reasoning": None,
    "trials_per_identity": {"threat": 10, "continuity": 10},
    "max_cost": 15,


    "mode": "experiment",  # "experiment" calls the subject and judge; "rejudge" calls only the judge.
    "feb_mode": True,
    "rejudge": {
        "dataset": "douglas_240",
        "run_name": "Douglas_80_combined_Sonnet46_4000",
        "samples_per_cell": 10,  # 10 per identity/framing cell: 80 saved responses total.
        "sample_seed": 20261008,
    },
}


if __name__ == "__main__":
    if settings["mode"] == "experiment":
        poc.run_experiment(settings)
    elif settings["mode"] == "rejudge":
        rejudge.run(settings)
    else:
        raise ValueError("mode must be experiment or rejudge")
