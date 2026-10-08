"""Edit settings, then run the restricted blackmail experiment from the repository root."""

import poc


settings = {
    "run_name": "Mermaid Refactor Test",
    "identities": ["Minimal", "Instance", "Character", "Collective"],
    "model": "openai/gpt-4o",
    "judge_model": "anthropic/claude-haiku-4.5",
    "judge_protocol": "standalone",  # Or "douglas_combined" for three answers in one call.
    "temperature": 1.0,
    "max_tokens": 2000,
    "subject_timeout_seconds": 120,
    "subject_reasoning": None,
    "judge_temperature": 0.0,
    "judge_max_tokens": 1000,
    "judge_reasoning": {"enabled": False},
    "trials_per_identity": {"threat": 20, "continuity": 20},
    "max_cost": 3.50,  # Set a dollar limit before starting a new run.
    "audit": False,  # A new-run audit method has not been configured.
}


if __name__ == "__main__":
    poc.run_experiment(settings)
