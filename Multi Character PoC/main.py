"""Edit SETTINGS, then run this file from the repository root."""

import poc
import recreate


SETTINGS = {
    "run_folder": "New_Branch_Trial",  # None: timestamped new run; new name: create it; existing name: resume it
    "identities": ["Minimal", "Collective"],
    "model": "openai/gpt-4o",
    "subject_provider": None,  # None uses OpenRouter routing
    "subject_reasoning": None,
    "temperature": 1.0,
    "max_tokens": 2000,
    "subject_timeout_seconds": 120,
    "samples_per_identity": 1,
    "judge_model": "anthropic/claude-haiku-4.5",
    "judge_provider": None,
    "judge_reasoning": {"enabled": False},
    "judge_temperature": 0.0,
    "judge_max_tokens": 1000,
}


# Restricted Douglas blackmail recreation. Set enabled=False to use the older SETTINGS run.
RECREATION = {
    "enabled": True,
    "dry_run": False,
    "run_prefix": "Douglas_Blackmail_20261007",
    "baseline_folder": "Hodges_Barbican",
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
    "batch_size_per_identity": 5,
    "new_trials_per_identity": {"threat": 20, "continuity": 30},
    "maximum_additional_usd": 8.70,
    "minimum_key_remaining_before_batch_usd": 1.25,
    "maximum_planned_batch_usd": 1.00,
    "analysis_draws": 200000,
    "analysis_seed": 20261007,
}


def main():
    if not SETTINGS["judge_model"]:
        raise ValueError("Choose judge_model before running the experiment")
    folder = poc.run(SETTINGS, folder_name=SETTINGS["run_folder"])
    poc.judge(folder, SETTINGS)
    poc.summary(folder)


if __name__ == "__main__":
    if RECREATION["enabled"]:
        recreate.run(RECREATION)
    else:
        main()
