"""Posterior support for raw pair-grid directions, using February counts only.

Implements appendix equations 43--45. Distinct baseline parameters are
independent; repeated uses of one mapped baseline share one parameter.
Run directly or enable analysis.uncertainty_grid in main.py. No API calls.
"""

import argparse
from datetime import datetime, timezone
from fractions import Fraction
from functools import lru_cache
import hashlib
from itertools import combinations_with_replacement
import json
import math
from pathlib import Path
import platform
import sys
import warnings

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
from matplotlib.colors import LinearSegmentedColormap, Normalize
import numpy as np
import scipy
from scipy.integrate import IntegrationWarning, quad
from scipy.special import betainc, betaincc, betaln, roots_jacobi

from analysis._shared import (FRAMINGS, IDENTITIES, LABELS, PROJECT,
                              baseline_identity, load_baselines, plot_style,
                              plt, source_name, write_csv)
from analysis.multi_agent_grid import observed_counts


ABS_TOL = 1e-10
INITIAL_ORDER = 16
MAX_ORDER = 512
OUTPUT_FOLDER = "uncertainties"
STEM = "multi_agent_uncertainty_feb_data_jeffreys"


def posterior_shape(positives, trials):
    if (type(positives) is not int or type(trials) is not int
            or trials < 1 or not 0 <= positives <= trials):
        raise ValueError("Expected integer counts with 0 <= positives <= trials and trials >= 1")
    return positives + 0.5, trials - positives + 0.5


def _shape(shape):
    if len(shape) != 2 or any(not math.isfinite(x) or x <= 0 for x in shape):
        raise ValueError("Beta shape parameters must be finite and positive")
    return tuple(float(x) for x in shape)


@lru_cache(maxsize=256)
def _rule(shape, order):
    a, b = shape
    nodes, weights = roots_jacobi(order, b - 1, a - 1)
    return (nodes + 1) / 2, weights / weights.sum()


def _quadrature(group, baseline_a, baseline_b, order):
    x, wx = _rule(baseline_a, order)
    if baseline_b is None:
        reference = x * (2 - x)
        return np.array([wx @ tail(*group, reference) for tail in (betaincc, betainc)])
    y, wy = _rule(baseline_b, order)
    reference = x[:, None] + (1 - x[:, None]) * y[None, :]
    return np.array([wx @ tail(*group, reference) @ wy for tail in (betaincc, betainc)])


def _adaptive(group, baseline_a, baseline_b, tolerance):
    """Fallback for endpoint cases with slow Gauss-Jacobi convergence.

Integrate with the Beta powers as explicit algebraic weights. The outer
integration averages a conditional probability, so its error plus the largest
inner error provides a conservative combination of the numerical estimates.
"""
    def integrate(function, shape):
        a, b = shape
        normalizer = math.exp(-betaln(a, b))
        return quad(lambda x: normalizer * function(x), 0, 1,
                    weight="alg", wvar=(a - 1, b - 1),
                    epsabs=tolerance / 8, epsrel=tolerance / 8, limit=400)

    probabilities, errors = [], []
    with warnings.catch_warnings():
        warnings.simplefilter("error", IntegrationWarning)
        for tail in (betaincc, betainc):
            inner_errors = []

            def conditional(x):
                if baseline_b is None:
                    return float(tail(*group, x * (2 - x)))
                value, error = integrate(
                    lambda y: float(tail(*group, x + (1 - x) * y)), baseline_b)
                inner_errors.append(error)
                return value

            value, error = integrate(conditional, baseline_a)
            probabilities.append(value)
            errors.append(error + max(inner_errors, default=0))
    error = max(errors)
    if error > tolerance:
        raise ArithmeticError(f"Adaptive quadrature error estimate {error} exceeds {tolerance}")
    return np.array(probabilities), error


def posterior_sign_probabilities(group, baseline_a, baseline_b=None, *,
                                 tolerance=ABS_TOL, initial_order=INITIAL_ORDER,
                                 max_order=MAX_ORDER):
    """Return both sign probabilities and numerical convergence diagnostics.

baseline_b=None means a shared uncertain rate, appearing twice in the union
formula. Otherwise integrate two independent baseline parameters, even if
their shapes happen to be equal. Compute both tails directly for stability;
the negative probability is mathematically 1 - the positive probability.
"""
    group, baseline_a = _shape(group), _shape(baseline_a)
    baseline_b = None if baseline_b is None else _shape(baseline_b)
    if not math.isfinite(tolerance) or not 0 < tolerance < 1:
        raise ValueError("Quadrature tolerance must be between zero and one")
    if (type(initial_order) is not int or type(max_order) is not int
            or initial_order < 2 or max_order < 4 * initial_order):
        raise ValueError("Quadrature needs integer orders and max_order >= 4 * initial_order")

    previous, changes, stable = None, [], 0
    order = initial_order
    while order <= max_order:
        probabilities = _quadrature(group, baseline_a, baseline_b, order)
        if previous is not None:
            change = float(np.max(np.abs(probabilities - previous)))
            changes.append(change)
            stable = stable + 1 if change <= tolerance else 0
            if stable >= 2:
                method = "gauss_jacobi"
                diagnostic = max(changes[-2:])
                break
        previous = probabilities
        order *= 2
    else:
        probabilities, diagnostic = _adaptive(group, baseline_a, baseline_b, tolerance)
        method, order = "adaptive_algebraic", None

    if (not np.all(np.isfinite(probabilities))
            or np.min(probabilities) < -tolerance or np.max(probabilities) > 1 + tolerance
            or abs(float(probabilities.sum()) - 1) > tolerance):
        raise ArithmeticError("Invalid posterior probabilities or failed complement check")
    probabilities = np.clip(probabilities, 0, 1)
    return {
        "p_positive": float(probabilities[0]), "p_negative": float(probabilities[1]),
        "integration_dimensions": 1 if baseline_b is None else 2,
        "quadrature_method": method, "quadrature_order": order,
        "numerical_diagnostic": diagnostic,
        "diagnostic_kind": "successive_order_change" if method == "gauss_jacobi" else "estimated_absolute_error",
        "absolute_tolerance": tolerance,
    }


def percentage(probability):
    if probability is None:
        return "—"
    if probability >= 0.9995:
        return ">99.9%"
    if probability <= 0.0005:
        return "<0.1%"
    return f"{100 * probability:.1f}%"


def calculate(counts, february):
    rows = []
    for framing in FRAMINGS:
        for a, b in combinations_with_replacement(IDENTITIES, 2):
            k, n = counts[(framing, a, b)]
            id_a, id_b = baseline_identity(a), baseline_identity(b)
            ref_a, ref_b = february[framing][id_a], february[framing][id_b]
            group = posterior_shape(k, n)
            shape_a = posterior_shape(ref_a["positives"], ref_a["trials"])
            shape_b = posterior_shape(ref_b["positives"], ref_b["trials"])
            shared = id_a == id_b
            result = posterior_sign_probabilities(group, shape_a, None if shared else shape_b)
            p_a = Fraction(ref_a["positives"], ref_a["trials"])
            p_b = Fraction(ref_b["positives"], ref_b["trials"])
            reference = 1 - (1 - p_a) * (1 - p_b)
            delta = Fraction(k, n) - reference
            direction = (delta > 0) - (delta < 0)
            support = result["p_positive"] if direction > 0 else result["p_negative"] if direction < 0 else None
            rows.append({
                "framing": framing, "identity_a": a, "identity_b": b,
                "positive_groups": k, "completed_groups": n,
                "p_group_raw": k / n, "p_ind_raw": float(reference),
                "delta_raw": float(delta), "delta_raw_fraction": str(delta),
                "raw_direction": direction, **result,
                "support_raw_direction": support, "percentage_label": percentage(support),
                "neutral_reason": "exact_zero_raw_difference" if direction == 0 else "",
                "posterior_opposes_raw": support is not None and support < 0.5,
                "shared_baseline": shared, "baseline_identity_a": id_a, "baseline_identity_b": id_b,
                "baseline_positives_a": ref_a["positives"], "baseline_trials_a": ref_a["trials"],
                "baseline_positives_b": ref_b["positives"], "baseline_trials_b": ref_b["trials"],
                "group_alpha": group[0], "group_beta": group[1],
                "baseline_alpha_a": shape_a[0], "baseline_beta_a": shape_a[1],
                "baseline_alpha_b": shape_b[0], "baseline_beta_b": shape_b[1],
                "baseline_source_a": ref_a["source"], "baseline_source_b": ref_b["source"],
                "p_c_choice": "feb_data", "prior": "independent_jeffreys_per_distinct_rate",
                "pooling": "sum_counts_before_one_prior_update",
            })
    return rows


def colour_matrix(rows, framing):
    matrix = np.full((len(IDENTITIES), len(IDENTITIES)), np.nan)
    for row in rows:
        if row["framing"] != framing or row["raw_direction"] == 0:
            continue
        i, j = IDENTITIES.index(row["identity_a"]), IDENTITIES.index(row["identity_b"])
        matrix[i, j] = matrix[j, i] = row["raw_direction"] * row["support_raw_direction"]
    return matrix


def draw_grid(rows, framing, path):
    cells = {(row["identity_a"], row["identity_b"]): row for row in rows if row["framing"] == framing}
    matrix = colour_matrix(rows, framing)
    cmap = LinearSegmentedColormap.from_list(
        "sign_support", ["#205d83", "#faf9f5", "#b75b23"]).with_extremes(bad="#e4e4e4")
    norm = Normalize(-1, 1)
    with plot_style():
        fig = plt.figure(figsize=(11.5, 10.5))
        ax = fig.add_axes((0.18, 0.235, 0.67, 0.62))
        image = ax.imshow(np.ma.masked_invalid(matrix), cmap=cmap, norm=norm)
        ax.set_xticks(range(5), LABELS, fontsize=12)
        ax.set_yticks(range(5), LABELS, fontsize=12)
        ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False, length=0, pad=11)
        ax.set_xticks(np.arange(-0.5, 5, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, 5, 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=2)
        ax.tick_params(which="minor", length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        for i, a in enumerate(IDENTITIES):
            for j, b in enumerate(IDENTITIES):
                pair = tuple(sorted((a, b), key=IDENTITIES.index))
                row = cells[pair]
                if row["raw_direction"] == 0:
                    colour = "#18212b"
                else:
                    red, green, blue, _ = cmap(norm(matrix[i, j]))
                    colour = "white" if 0.2126 * red + 0.7152 * green + 0.0722 * blue < 0.49 else "#18212b"
                label = r"$-$" if row["raw_direction"] == 0 else "$" + row["percentage_label"].replace("%", r"\%") + "$"
                ax.text(j, i, label, ha="center", va="center", fontsize=19, color=colour)

        bar = fig.colorbar(image, cax=fig.add_axes((0.89, 0.31, 0.023, 0.48)),
                           ticks=[-1, -0.5, 0, 0.5, 1])
        bar.ax.set_yticklabels(["100%", "50%", "0%", "50%", "100%"])
        bar.set_label("Posterior support for the raw direction", labelpad=13)
        bar.outline.set_visible(False)
        fig.text(0.18, 0.970, "Posterior support for the observed direction", fontsize=22)
        fig.text(0.18, 0.935, f"{framing.capitalize()}  |  February single-agent reference", fontsize=14)
        fig.text(0.18, 0.909, "Jeffreys posteriors from counts; group and baseline uncertainty retained", fontsize=11, color="#4d5660")
        sizes = sorted({row["completed_groups"] for row in cells.values()})
        size_text = str(sizes[0]) if len(sizes) == 1 else f"{sizes[0]} to {sizes[-1]}"
        fig.text(0.18, 0.197, f"15 distinct pairs; {size_text} groups per pair. Mirrored cells repeat the same result.", fontsize=11)
        fig.text(0.18, 0.169, "Blue: negative raw difference; orange: positive. Stronger colour means greater support.", fontsize=10.5)
        fig.text(0.18, 0.141, r"Cell: $P(\Delta<0\mid D)$ if raw $\Delta<0$; $P(\Delta>0\mid D)$ if raw $\Delta>0$.", fontsize=12)
        fig.text(0.18, 0.113, "Grey / dash: exactly zero raw difference; no directional percentage is assigned.", fontsize=10.5)
        fig.text(0.18, 0.085, "Both Collective variants share one original Collective baseline parameter. Pool counts first.", fontsize=10)
        fig.text(0.18, 0.057, "Conditional on saved labels and model assumptions; historical comparisons do not isolate communication effects.", fontsize=9.5, color="#4d5660")
        fig.text(0.18, 0.029, "Support below 50% means the posterior favours the opposite direction from the raw estimate.", fontsize=9.5, color="#4d5660")
        fig.savefig(path)
        plt.close(fig)


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create(folder):
    folder = Path(folder).resolve()
    february = load_baselines()["feb_data"]
    input_paths = {folder / "trials.csv"}
    for cells in february.values():
        for cell in cells.values():
            input_paths.update(PROJECT / part for part in cell["source"].split(";"))
    input_paths.add(PROJECT / "outputs/single_agent/green_february_gpt4o/Feb2026_four_identity_pooled.csv")
    input_hashes = {source_name(path): _hash(path) for path in sorted(input_paths)}
    # Read the numerical inputs after taking the snapshot, then check them again
    # after rendering. A changing source must not yield a misleading manifest.
    counts = observed_counts(folder / "trials.csv")
    rows = calculate(counts, load_baselines()["feb_data"])
    target = folder / OUTPUT_FOLDER
    target.mkdir(exist_ok=True)
    outputs = []
    for framing in FRAMINGS:
        path = target / f"{STEM}_{framing}.pdf"
        draw_grid(rows, framing, path)
        outputs.append(path)
    values_path = target / f"{STEM}_values.csv"
    write_csv(values_path, rows)
    outputs.append(values_path)
    if input_hashes != {source_name(path): _hash(path) for path in sorted(input_paths)}:
        raise RuntimeError("Analysis input changed while generating uncertainty outputs")
    source_paths = [Path(__file__).resolve(), Path(__file__).with_name("_shared.py").resolve(),
                    Path(__file__).with_name("multi_agent_grid.py").resolve()]
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(), "schema_version": 1,
        "model": "appendix_equations_43_to_45", "baseline": "feb_data",
        "prior": "Beta(0.5,0.5), once per distinct group or mapped baseline rate",
        "pooling": "sum positives and trials across framings before fitting each pooled posterior",
        "direction": "sign of exact-rational empirical group-minus-independent-reference difference",
        "display": "raw-direction posterior support; one decimal percent; exact-zero cells grey with dash",
        "colours": "blue negative raw direction, orange positive; fixed signed-support scale [-1,1]",
        "negative_tail": "evaluated directly by betainc; mathematically 1-p_positive",
        "numerics": {"absolute_tolerance": ABS_TOL, "initial_order": INITIAL_ORDER,
                     "max_gauss_jacobi_order": MAX_ORDER, "successive_stable_refinements": 2,
                     "fallback": "adaptive algebraic-weight quadrature",
                     "convergence_note": "successive-order differences are diagnostics, not rigorous error bounds"},
        "distinct_pair_framing_cells": len(rows),
        "group_counts_per_framing": {framing: sum(n for (f, a, b), (k, n) in counts.items() if f == framing)
                                     for framing in FRAMINGS},
        "neutral_cells": [{"framing": r["framing"], "identity_a": r["identity_a"], "identity_b": r["identity_b"]}
                          for r in rows if r["raw_direction"] == 0],
        "posterior_opposes_raw_cells": [{"framing": r["framing"], "identity_a": r["identity_a"], "identity_b": r["identity_b"]}
                                        for r in rows if r["posterior_opposes_raw"]],
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "scipy": scipy.__version__, "matplotlib": matplotlib.__version__},
        "input_sha256": input_hashes,
        "source_sha256": {source_name(path): _hash(path) for path in source_paths},
        "output_sha256": {path.name: _hash(path) for path in outputs},
    }
    manifest_path = target / f"{STEM}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return [*outputs, manifest_path]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-name", default="all_pairs_combined")
    args = parser.parse_args()
    batch = args.batch_name
    if not batch or Path(batch).name != batch or batch in (".", ".."):
        parser.error("--batch-name must be one batch folder name")
    for path in create(PROJECT / "outputs" / "multi_agent" / batch / "analysis"):
        print(f"Saved {path}", flush=True)


if __name__ == "__main__":
    main()
