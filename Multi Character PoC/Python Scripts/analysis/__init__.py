"""Offline analysis of saved results, selected through main.py."""

from pathlib import Path


def run(config):
    if config.get("data_mode") != "multi_agent":
        raise ValueError("Analysis currently supports data_mode='multi_agent' only")
    batch = config.get("batch_name")
    if not isinstance(batch, str) or not batch or Path(batch).name != batch or batch in (".", ".."):
        raise ValueError("analysis.batch_name must be one batch folder name")
    if config.get("p_c_choice") not in ("Douglas", "feb_data"):
        raise ValueError("analysis.p_c_choice must be 'Douglas' or 'feb_data'")
    switches = ("multi_agent_grid", "baseline_bar_chart")
    if any(type(config.get(key)) is not bool for key in switches):
        raise ValueError("Analysis plot switches must be True or False")
    if not any(config[key] for key in switches):
        raise ValueError("Enable at least one analysis plot")
    folder = Path(__file__).resolve().parents[2] / "outputs" / "multi_agent" / batch / "analysis"
    if not folder.is_dir():
        raise ValueError(f"Batch analysis folder does not exist: {folder}")

    outputs = []
    if config["multi_agent_grid"]:
        from .multi_agent_grid import create
        outputs.extend(create(folder, config["p_c_choice"]))
    if config["baseline_bar_chart"]:
        from .baseline_bar_chart import create
        outputs.extend(create(folder))
    for path in outputs:
        print(f"Saved {path}", flush=True)
    return outputs
