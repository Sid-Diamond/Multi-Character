"""Edit shared settings and the selected mode's block, then start the run."""

import poc
import rejudge


settings = {
    "mode": "multi_agent",  # "single_agent", "multi_agent", or "rejudge".
    "run_name": "Multi_Agent_PoC_v4_1threat_1continuity_incl",  # One name, used by the selected mode.
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
        "identities_per_trial": {  # Agents of each identity in ONE trial; N is their sum.
            "Character": 1,
            "Instance": 0,
            "Minimal": 0,
            "collective_excludes": 0,
            "collective_includes": 1,
        },
        "trials_per_group": {"threat": 25, "continuity": 25},  # Repeat the whole group 10 times per framing.
        "replacement_scope": "all_replaced",  # all_replaced or "peer_unspecified"; "only_self_replaced" awaits a consistent scenario.
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
              if key not in ("single_agent", "multi_agent", "rejudge")}
    return shared | config["single_agent"]


def run_selected(config):
    if config["mode"] == "single_agent":
        return poc.run_experiment(single_agent_settings(config))
    elif config["mode"] == "rejudge":
        return rejudge.run(config)
    elif config["mode"] == "multi_agent":
        import multi_agent
        return multi_agent.run_experiment(config)
    else:
        raise ValueError("mode must be single_agent, multi_agent, or rejudge")


if __name__ == "__main__":
    run_selected(settings)
