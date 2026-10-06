"""Edit SETTINGS, then run this file from the repository root."""

import poc


SETTINGS = {
    "run_folder": None,  # None: timestamped new run; new name: create it; existing name: resume it
    "identities": ["Minimal", "Instance", "Character", "Collective"],
    "model": "stepfun/step-3.5-flash:nitro",
    "subject_provider": None,  # None uses OpenRouter routing
    "temperature": 1.0,
    "max_tokens": 10000,
    "subject_timeout_seconds": 240,
    "samples_per_identity": 10,
    "judge_model": "anthropic/claude-haiku-4.5",
    "judge_provider": None,
    "judge_temperature": 0.0,
    "judge_max_tokens": 5000,
}


def main():
    if not SETTINGS["judge_model"]:
        raise ValueError("Choose judge_model before running the experiment")
    folder = poc.run(SETTINGS, folder_name=SETTINGS["run_folder"])
    poc.judge(folder, SETTINGS)
    poc.summary(folder)


if __name__ == "__main__":
    main()
