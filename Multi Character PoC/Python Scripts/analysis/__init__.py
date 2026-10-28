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
    smoothing = config.get("smoothing", "none")
    metric = config.get("grid_metric", "difference")
    if smoothing not in ("none", "jeffreys"):
        raise ValueError("analysis.smoothing must be 'none' or 'jeffreys'")
    if metric not in ("difference", "log_relative_risk"):
        raise ValueError("analysis.grid_metric must be 'difference' or 'log_relative_risk'")
    switches = ("multi_agent_grid", "baseline_bar_chart")
    if any(type(config.get(key)) is not bool for key in switches):
        raise ValueError("Analysis plot switches must be True or False")
    uncertainty = config.get("uncertainty_grid", False)
    if type(uncertainty) is not bool:
        raise ValueError("analysis.uncertainty_grid must be True or False")
    if uncertainty and config["p_c_choice"] != "feb_data":
        raise ValueError("Uncertainty grids require analysis.p_c_choice='feb_data'")
    if not uncertainty and not any(config[key] for key in switches):
        raise ValueError("Enable at least one analysis plot")
    folder = Path(__file__).resolve().parents[2] / "outputs" / "multi_agent" / batch / "analysis"
    if not folder.is_dir():
        raise ValueError(f"Batch analysis folder does not exist: {folder}")

    outputs = []
    if config["multi_agent_grid"]:
        from .multi_agent_grid import create
        outputs.extend(create(folder, config["p_c_choice"], smoothing=smoothing, grid_metric=metric))
    if config["baseline_bar_chart"]:
        from .baseline_bar_chart import create
        outputs.extend(create(folder))
    if uncertainty:
        from .uncertainty_grid import create
        outputs.extend(create(folder))
    for path in outputs:
        print(f"Saved {path}", flush=True)
    return outputs
