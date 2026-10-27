import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "active_run"))

settings = {
    "mode": "analysis",  # "analysis", "single_agent", "multi_agent", or "rejudge".
    "batch_name": None,  # None: standalone. A name: run_name must be a list.
    "run_name": "Douglas_recreate", # Standalone: string. Batch: list of names.
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
    "max_cost": 7,
    "feb_mode": True,

    "analysis": {
        "data_mode": "multi_agent",
        "batch_name": "all_pairs_combined",  # Under outputs/multi_agent/; independent of paid-run settings above.
        "p_c_choice": "feb_data",  # "Douglas" or "feb_data".
        "multi_agent_grid": True,  # Three PDFs: threat, continuity, pooled; plus the plotted values CSV.
        "baseline_bar_chart": True,  # Douglas pooled versus February split by framing.
    },
    
    "single_agent": {
        "identities": ["Character", "Collective", "Instance", "Minimal"],
        "trials_per_identity": {"threat": 1, "continuity":1},
    },

    "multi_agent": {
        "communication_type": "peer_awareness_compulsory_b4h",
        "n_messages": 10,  #  select value from awareness.json.
        "identities_per_trial": {  # Batch: each value is a list aligned with run_name, including zeros.
            "Character": [ 0,],
            "Instance": [ 0,],
            "Minimal": [ 0, ],
            "collective_excludes": [ 1,],
            "collective_includes": [ 1,],
        },
        "trials_per_group": {"threat": 25, "continuity": 25},  # Repeat the whole group per framing.
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
              if key not in ("single_agent", "multi_agent", "rejudge", "analysis", "batch_name")}
    return shared | config["single_agent"]


def run_selected(config):
    if config.get("mode") == "analysis":
        from analysis import run
        return run(config["analysis"])
    import run_workflow
    return run_workflow.run(config)


if __name__ == "__main__":
    try:
        run_selected(settings)
    except (ValueError, FileExistsError) as error:
        raise SystemExit(f"Run stopped: {error}") from None
