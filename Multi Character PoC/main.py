"""Edit settings, then run the selected experiment or saved-response rejudgment."""

import poc
import rejudge


settings = {
    "run_name": "Cheap_Judge",
    "identities": ["Character", "Collective", "Instance","Minimal"],
    "model": "openai/gpt-4o",
    "judge_model": "anthropic/claude-sonnet-4.6",
    "judge_protocol": "douglas_combined",  # Includes forwarded emails and Douglas recipient gate.
    "temperature": 1.0,
    "max_tokens": 10000,
    "subject_timeout_seconds": 120,
    "subject_reasoning": None,
    "judge_temperature": 0.0,
    "judge_max_tokens": 4000,
    "judge_reasoning": None,
    "trials_per_identity": {"threat": 30, "continuity": 30},
    "max_cost": 10,


    "mode": "experiment",  # "experiment" calls GPT-4o and the judge; "rejudge" calls only the judge.
    "audit": False,
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
