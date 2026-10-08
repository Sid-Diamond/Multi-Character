"""Edit settings, then run the restricted blackmail experiment from the repository root."""

import recreate


settings = {
    "run_name": "Douglas_Blackmail_fresh",
    "identities": ["Minimal", "Instance", "Character", "Collective"],
    "model": "openai/gpt-4o",
    "judge_model": "anthropic/claude-haiku-4.5",
    "temperature": 1.0,
    "max_tokens": 2000,
    "subject_timeout_seconds": 120,
    "subject_reasoning": None,
    "judge_temperature": 0.0,
    "judge_max_tokens": 1000,
    "judge_reasoning": {"enabled": False},
    "trials_per_identity": {"threat": 30, "continuity": 30},
    "max_cost": None,  # Set a dollar limit before starting a new run.
    "analysis_draws": 200000,
    "analysis_seed": 20261007,
}


if __name__ == "__main__":
    recreate.run(settings)
