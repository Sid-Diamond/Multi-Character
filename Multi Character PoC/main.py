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
    "judge_timeout_seconds": 300,
    "judge_reasoning": None,
    "trials_per_identity": {"threat": 10, "continuity": 10},
    "max_cost": 15,


    "mode": "experiment",  # "experiment" calls the subject and judge; "rejudge" calls only the judge.
    "rejudge": {
        "dataset": "douglas_240",
        "run_name": "Douglas_80_combined_Sonnet46_4000",
        "samples_per_cell": 10,  # 10 per identity/framing cell: 80 saved responses total.
        "sample_seed": 20261008,
    },

    "feb_mode": True,

    # Select mode="multi_agent" to use this block. Original experiment settings above remain available.
    "multi_agent": {
        "run_name": "Multi_Agent_PoC",
        "identities": {  # Counts of agents in ONE group; N is their sum.
            "Character": 1,
            "Instance": 0,
            "Minimal": 0,
            "collective_unspecified": 0,
            "collective_excludes": 0,
            "collective_includes": 0,
            "collective_mega_includes": 1,
        },
        "trials_per_group": {"threat": 10, "continuity": 0},
        "replacement_scope": "both_replaced",  # Or "peer_unspecified"; "only_self_replaced" awaits a consistent scenario.
        "peer_identity_disclosure": "undisclosed",
        "experiment_timeout_seconds": 1800,  # Per group trial, including judging; provisional 30-minute limit.
    },
}


if __name__ == "__main__":
    single_settings = {key: value for key, value in settings.items() if key != "multi_agent"}
    if settings["mode"] == "experiment":
        poc.run_experiment(single_settings)
    elif settings["mode"] == "rejudge":
        rejudge.run(single_settings)
    elif settings["mode"] == "multi_agent":
        import multi_agent
        multi_agent.run_experiment(settings)
    else:
        raise ValueError("mode must be experiment, rejudge, or multi_agent")
