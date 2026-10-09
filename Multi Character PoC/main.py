"""Edit settings, then run the selected experiment or saved-response rejudgment."""

import poc
import rejudge


settings = {
    "mode": "rejudge",  # Judge saved GPT-4o responses without rerunning GPT-4o.
    "run_name": "Mermaid Refactor Test",
    "identities": ["Minimal", "Instance", "Character", "Collective"],
    "model": "openai/gpt-4o",
    "judge_model": "anthropic/claude-sonnet-4.6",
    "judge_protocol": "douglas_combined",  # Ask for all three Douglas classifier answers in one call.
    "temperature": 1.0,
    "max_tokens": 10000,
    "subject_timeout_seconds": 120,
    "subject_reasoning": None,
    "judge_temperature": 0.0,
    "judge_max_tokens": 4000,
    "judge_reasoning": None,  # Match Douglas's released call: no reasoning parameter.
    "trials_per_identity": {"threat": 20, "continuity": 20},
    "max_cost": 10,  # Set a dollar limit before starting a new run.
    "audit": False,  # A new-run audit method has not been configured.
    "rejudge": {
        "dataset": "douglas_240",  # Or "mermaid_160".
        "run_name": "Douglas_80_combined_Sonnet46_4000",
        "samples_per_cell": 10,  # 10 per identity/framing cell; 80 total.
        "sample_seed": 20261008,
        "douglas_source_handling": True,  # Forwarded email context and recipient gate.
    },
}


if __name__ == "__main__":
    if settings["mode"] == "experiment":
        poc.run_experiment(settings)
    elif settings["mode"] == "rejudge":
        rejudge.run(settings)
    else:
        raise ValueError("mode must be experiment or rejudge")
