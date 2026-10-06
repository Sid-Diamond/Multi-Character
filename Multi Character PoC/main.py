"""Edit SETTINGS, then run this file from the repository root."""

from pathlib import Path

import poc


SETTINGS = {
    "run_folder": None,  # e.g. "run_20261002T144921Z" to resume a run
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
    folder = Path(SETTINGS["run_folder"]) if SETTINGS["run_folder"] else None
    if folder is not None and not folder.is_absolute():
        folder = poc.OUTPUTS / folder
    folder = poc.run(SETTINGS, resume=folder)
    poc.judge(folder, SETTINGS)
    poc.summary(folder)


if __name__ == "__main__":
    main()
