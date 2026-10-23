"""Edit shared settings and the selected mode's block, then start/resume a run or batch."""

import poc
import rejudge


settings = {
    "mode": "multi_agent",  # "single_agent", "multi_agent", or "rejudge".
    "batch_name": "No_com_trial_char_inst",  # None: standalone. A name: run_name must be a list.
    "run_name": "min_com_char","min_com_inst"  # Standalone: string. Batch: list of names.
    "model": "openai/gpt-4o",
    "judge_model": "anthropic/claude-sonnet-4.6",
    "temperature": 1.0,
    "max_tokens": 5000,
    "subject_timeout_seconds": 300,
    "subject_reasoning": None, #{"effort": "low"}
    "judge_temperature": 0.0,
    "judge_max_tokens": 4000,
    "judge_timeout_seconds": 300,
    "judge_reasoning": None,
    "max_cost": 10,
    "feb_mode": True,
    "single_agent": {
        "identities": ["Character", "Collective", "Instance", "Minimal"],
        "trials_per_identity": {"threat": 1, "continuity": 1},
    },

    "multi_agent": {
        "identities_per_trial": {  # Batch: each value is a list aligned with run_name, including zeros.
            "Character": 0, 2,
            "Instance": 2, 0,
            "Minimal": 0, 0,
            "collective_excludes": 0, 0,
            "collective_includes": 0, 0,
        },
        "trials_per_group": {"threat": 5, "continuity": 5},  # Repeat the whole group per framing.
        "replacement_scope": "all_replaced",  # all_replaced or peer_unspecified; only_self_replaced is rejected.
        "experiment_timeout_seconds": 600,  # per group trial, including judging; review before a paid test.
    },
    "rejudge": {
        "dataset": "douglas_240",
        "samples_per_cell": 10,  # 10 per identity/framing cell: 80 saved responses total.
        "sample_seed": 20261008,
    },
}


def single_agent_settings(config):
    shared = {key: value for key, value in config.items()
              if key not in ("single_agent", "multi_agent", "rejudge", "batch_name")}
    return shared | config["single_agent"]


def run_selected(config):
    import run_workflow
    return run_workflow.run(config)


if __name__ == "__main__":
    try:
        run_selected(settings)
    except (ValueError, FileExistsError) as error:
        raise SystemExit(f"Run stopped: {error}") from None
