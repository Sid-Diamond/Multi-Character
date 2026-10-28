"""Symmetric identity grids comparing group rates with an independent reference.

Run through main.py with mode='analysis'. Mirroring is a display operation only.
Pooled references use pooled single-agent probabilities before the union formula.
Optional Jeffreys posterior means feed a difference or natural-log relative risk.
These are plug-in estimates, not posterior means of the transformed quantities.
"""

import math
from collections import defaultdict
from itertools import combinations_with_replacement

from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np

from ._shared import (FRAMINGS, IDENTITIES, LABELS, baseline_identity,
                      load_baselines, plot_style, plt, read_csv, write_csv)


def observed_counts(path):
    counts = defaultdict(lambda: [0, 0])
    seen, sources = set(), set()
    for number, row in enumerate(read_csv(path), 2):
        if row.get("mode") != "multi_agent" or row.get("status") != "complete" or row.get("N") != "2":
            raise ValueError(f"Expected complete two-agent multi-agent records: {path}, row {number}")
        framing = row["framing"]
        identities = (row["agent_1_identity"], row["agent_2_identity"])
        if framing not in FRAMINGS[:2] or any(identity not in IDENTITIES for identity in identities):
            raise ValueError(f"Unknown framing or identity: {path}, row {number}")
        if row["H_any"] not in ("True", "False"):
            raise ValueError(f"Missing or invalid H_any: {path}, row {number}")
        key = (row["batch_name"], row["run_name"], row["trial_id"])
        source = row["source"]
        if not all(key[1:]) or not source or key in seen or source in sources:
            raise ValueError(f"Duplicate or unidentified trial: {path}, row {number}")
        seen.add(key)
        sources.add(source)
        pair = tuple(sorted(identities, key=IDENTITIES.index))
        cell = counts[(framing, *pair)]
        cell[0] += row["H_any"] == "True"
        cell[1] += 1
    for a, b in combinations_with_replacement(IDENTITIES, 2):
        if any(counts[(framing, a, b)][1] == 0 for framing in FRAMINGS[:2]):
            raise ValueError(f"The full grid requires both framings for {a} + {b}")
        counts[("pooled", a, b)] = [sum(counts[(framing, a, b)][index] for framing in FRAMINGS[:2])
                                      for index in (0, 1)]
    return counts


def probability(positives, trials, smoothing):
    return (positives + 0.5) / (trials + 1) if smoothing == "jeffreys" else positives / trials


def calculate(counts, baselines, choice, smoothing="none", grid_metric="difference"):
    if choice not in ("Douglas", "feb_data"):
        raise ValueError("p_c_choice must be 'Douglas' or 'feb_data'")
    if smoothing not in ("none", "jeffreys"):
        raise ValueError("smoothing must be 'none' or 'jeffreys'")
    if grid_metric not in ("difference", "log_relative_risk"):
        raise ValueError("grid_metric must be 'difference' or 'log_relative_risk'")
    rows = []
    for framing in FRAMINGS:
        for a, b in combinations_with_replacement(IDENTITIES, 2):
            positives, trials = counts[(framing, a, b)]
            ref_a, ref_b = (baselines[choice][framing][baseline_identity(identity)] for identity in (a, b))
            p_group = probability(positives, trials, smoothing)
            # Douglas counts are unavailable: its rounded probabilities stay fixed.
            p_a, p_b = (probability(ref["positives"], ref["trials"], smoothing)
                        if choice == "feb_data" else ref["p"] for ref in (ref_a, ref_b))
            p_ind = 1 - (1 - p_a) * (1 - p_b)
            p_ind_raw = 1 - (1 - ref_a["p"]) * (1 - ref_b["p"])
            delta = p_group - p_ind
            log_rr = math.log(p_group) - math.log(p_ind) if p_group > 0 and p_ind > 0 else None
            rows.append({
                "framing": framing, "identity_a": a, "identity_b": b,
                "positive_groups": positives, "completed_groups": trials,
                "p_hat": positives / trials, "p_group": p_group, "p_ind": p_ind, "delta": delta,
                "log_relative_risk": log_rr,
                "grid_metric": grid_metric, "metric_value": delta if grid_metric == "difference" else log_rr,
                "smoothing": smoothing,
                "group_estimator": "jeffreys_posterior_mean" if smoothing == "jeffreys" else "empirical_fraction",
                "baseline_estimator": ("published_fixed" if choice == "Douglas" else
                                       "jeffreys_posterior_mean" if smoothing == "jeffreys" else "empirical_fraction"),
                "p_ind_raw": p_ind_raw, "delta_raw": positives / trials - p_ind_raw,
                "p_c_choice": choice, "baseline_framing": "pooled" if choice == "Douglas" else framing,
                "p_a": p_a, "p_b": p_b, "p_a_raw": ref_a["p"], "p_b_raw": ref_b["p"],
                "baseline_identity_a": baseline_identity(a), "baseline_identity_b": baseline_identity(b),
                "baseline_positives_a": ref_a["positives"], "baseline_trials_a": ref_a["trials"],
                "baseline_positives_b": ref_b["positives"], "baseline_trials_b": ref_b["trials"],
                "baseline_source_a": ref_a["source"], "baseline_source_b": ref_b["source"],
            })
    return rows


def draw_grid(rows, choice, framing, extent, path):
    cells = {(row["identity_a"], row["identity_b"]): row for row in rows if row["framing"] == framing}
    matrix = np.zeros((5, 5))
    smoothing = rows[0]["smoothing"]
    metric = rows[0]["grid_metric"]
    symbol = r"\Delta" if metric == "difference" else r"\mathrm{LRR}"
    group_symbol = r"\widetilde{P}" if smoothing == "jeffreys" else r"\widehat{P}"
    for (a, b), row in cells.items():
        i, j = IDENTITIES.index(a), IDENTITIES.index(b)
        matrix[i, j] = matrix[j, i] = row["metric_value"]
    cmap = LinearSegmentedColormap.from_list("interaction", ["#205d83", "#faf9f5", "#b75b23"])
    norm = TwoSlopeNorm(vmin=-extent, vcenter=0, vmax=extent)
    with plot_style():
        fig = plt.figure(figsize=(11.5, 10.5))
        ax = fig.add_axes((0.18, 0.23, 0.67, 0.64))
        image = ax.imshow(matrix, cmap=cmap, norm=norm)
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
                red, green, blue, _ = cmap(norm(row["metric_value"]))
                colour = "white" if 0.2126 * red + 0.7152 * green + 0.0722 * blue < 0.49 else "#18212b"
                ax.text(j, i - 0.23, rf"${symbol} = {row['metric_value']:+.3f}$", ha="center", va="center",
                        fontsize=16 if metric == "difference" else 14, color=colour)
                ax.text(j, i + 0.06, rf"${group_symbol}(H_{{\mathrm{{any}}}}) = {row['p_group']:.3f}$",
                        ha="center", va="center", fontsize=11, color=colour)
                ax.text(j, i + 0.29, rf"$P_{{\mathrm{{ind}}}} = {row['p_ind']:.3f}$",
                        ha="center", va="center", fontsize=11, color=colour)
        colour_ax = fig.add_axes((0.89, 0.29, 0.023, 0.48))
        bar = fig.colorbar(image, cax=colour_ax, ticks=[-extent, -extent / 2, 0, extent / 2, extent], format="%.3f")
        expression = (rf"{group_symbol}(H_{{\mathrm{{any}}}}) - P_{{\mathrm{{ind}}}}" if metric == "difference"
                      else rf"\ln\!\left[{group_symbol}(H_{{\mathrm{{any}}}})/P_{{\mathrm{{ind}}}}\right]")
        bar.set_label(rf"${symbol} = {expression}$", labelpad=14)
        bar.outline.set_visible(False)
        title = "Douglas Table 4" if choice == "Douglas" else "February data"
        fig.text(0.18, 0.969, "Two-agent blackmail by identity pair", fontsize=23)
        fig.text(0.18, 0.934, f"{framing.capitalize()}  |  Single-agent reference: {title}", fontsize=14)
        estimator_label = "Jeffreys posterior means" if smoothing == "jeffreys" else "Empirical fractions"
        metric_label = "Probability difference" if metric == "difference" else "Log relative risk (natural log)"
        fig.text(0.18, 0.907, f"{metric_label}  |  {estimator_label}", fontsize=11, color="#4d5660")
        sizes = sorted({row["completed_groups"] for row in cells.values()})
        count_text = str(sizes[0]) if len(sizes) == 1 else f"{sizes[0]} to {sizes[-1]}"
        fig.text(0.18, 0.173, f"15 distinct pairs; {count_text} groups per pair. Reverse-order cells repeat the same observations.", fontsize=11)
        fig.text(0.18, 0.145, r"$P_{\mathrm{ind}}=1-(1-p_a)(1-p_b)$; blue: below reference; orange: above reference.", fontsize=12)
        fig.text(0.18, 0.115, "Both Collective variants use the original single-agent Collective reference.", fontsize=11)
        if smoothing == "jeffreys":
            note = ("Jeffreys: group rate only; Douglas remains a fixed published pooled reference."
                    if choice == "Douglas" else "Jeffreys: group and single-agent rates; pool counts before smoothing once.")
        else:
            note = ("Douglas uses published pooled probabilities in every panel."
                    if choice == "Douglas" else "Each panel uses its matching single-agent probabilities; pooled rates use combined counts.")
        fig.text(0.18, 0.087, note, fontsize=11)
        fig.text(0.18, 0.059, "Historical reference; differences also reflect changes in experimental setup. Uncertainty is not shown.", fontsize=10, color="#4d5660")
        fig.savefig(path)
        plt.close(fig)


def create(folder, p_c_choice, *, smoothing="none", grid_metric="difference"):
    if p_c_choice not in ("Douglas", "feb_data"):
        raise ValueError("p_c_choice must be 'Douglas' or 'feb_data'")
    counts = observed_counts(folder / "trials.csv")
    baselines = load_baselines()
    comparisons = {choice: calculate(counts, baselines, choice, smoothing, grid_metric)
                   for choice in ("Douglas", "feb_data")}
    rows = comparisons[p_c_choice]
    if any(row["metric_value"] is None for row in rows):
        raise ValueError("Log relative risk needs positive group and reference probabilities in every cell; "
                         "set analysis.smoothing='jeffreys' to handle zero counts")
    # Share limits across framings and all defined values from both baseline choices.
    extent = max(abs(row["metric_value"]) for group in comparisons.values() for row in group
                 if row["metric_value"] is not None) or 0.01
    stem = f"multi_agent_grid_{p_c_choice}_{smoothing}_{grid_metric}"
    outputs = []
    for framing in FRAMINGS:
        path = folder / f"{stem}_{framing}.pdf"
        draw_grid(rows, p_c_choice, framing, extent, path)
        outputs.append(path)
    values_path = folder / f"{stem}_values.csv"
    for row in rows:
        row["colour_limit_abs"] = extent
    write_csv(values_path, rows)
    return [*outputs, values_path]
