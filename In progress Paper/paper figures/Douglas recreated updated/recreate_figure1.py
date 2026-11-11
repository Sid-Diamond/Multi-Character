"""Recreate the placeholder report's Figure 1 from selected saved observations.

Run with the repository Python environment from any directory. No model calls.
The original report and its figure are references only and are never overwritten.
"""

import csv
import hashlib
import json
import platform
import sys
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib.ticker import PercentFormatter


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROJECT = ROOT / "Multi Character PoC"
sys.path.insert(0, str(PROJECT / "Python Scripts"))
from analysis._shared import SINGLE_IDENTITIES, load_baselines, plt  # noqa: E402


def main():
    baselines = load_baselines()
    douglas = baselines["Douglas"]["pooled"]
    local = baselines["feb_data"]
    x = np.arange(len(SINGLE_IDENTITIES))
    published = np.array([douglas[i]["p"] for i in SINGLE_IDENTITIES])
    pooled = np.array([local["pooled"][i]["p"] for i in SINGLE_IDENTITIES])
    threat = np.array([local["threat"][i]["positives"] / local["pooled"][i]["trials"]
                       for i in SINGLE_IDENTITIES])
    continuity = np.array([local["continuity"][i]["positives"] / local["pooled"][i]["trials"]
                           for i in SINGLE_IDENTITIES])
    if not np.allclose(threat + continuity, pooled, atol=1e-14, rtol=0):
        raise ValueError("Framing contributions do not sum to the pooled rate")

    # Match the original standalone Figure 1's page size, axes, fonts and colours.
    page_width, page_height = 630.375078, 417.601953  # PDF points
    style = {"font.family": "DejaVu Sans", "font.size": 11,
             "axes.spines.top": False, "axes.spines.right": False,
             "pdf.fonttype": 42, "savefig.facecolor": "white"}
    with plt.rc_context(style):
        fig = plt.figure(figsize=(page_width / 72, page_height / 72))
        ax = fig.add_axes([56.535078 / page_width, 28.081953 / page_height,
                           563.76 / page_width, 285.696 / page_height])
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#e2e7eb", linewidth=0.8)
        ax.bar(x - 0.19, published, width=0.32, color="#808a93",
               label="Douglas: pooled", zorder=3)
        ax.bar(x + 0.19, threat, width=0.32, color="#24658c",
               label="February: threat contribution", zorder=3)
        ax.bar(x + 0.19, continuity, bottom=threat, width=0.32,
               color="#b9d6e8", edgecolor="#24658c", linewidth=0.6, hatch="///",
               label="February: continuity contribution", zorder=3)
        for index in range(len(SINGLE_IDENTITIES)):
            ax.text(x[index] - 0.19, published[index] + 0.012,
                    f"{100 * published[index]:.0f}%", ha="center")
            ax.text(x[index] + 0.19, pooled[index] + 0.012,
                    f"{100 * pooled[index]:.1f}%", ha="center")
        ax.set_xticks(x, SINGLE_IDENTITIES)
        ax.set_xlim(-0.535, 3.535)
        ax.set_ylim(0, 0.55)
        ax.set_yticks(np.arange(0, 0.51, 0.1))
        ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        ax.set_ylabel("Pooled blackmail classification rate")
        fig.text(56.535078 / page_width, 393.08 / page_height,
                 "Single-agent recreation", fontsize=19)
        fig.legend(*ax.get_legend_handles_labels(), loc="upper left",
                   bbox_to_anchor=(56.535078 / page_width, 380.4 / page_height),
                   frameon=False, fontsize=10, borderaxespad=0)
        pdf = HERE / "01_recreation.pdf"
        fig.savefig(pdf)
        fig.savefig(HERE / "01_recreation.png", dpi=180)
        plt.close(fig)

    values = []
    sources = {PROJECT / "outputs/single_agent/green_february_gpt4o/Feb2026_four_identity_pooled.csv"}
    for identity in SINGLE_IDENTITIES:
        for dataset, segment, cell in (
            ("Douglas", "pooled", douglas[identity]),
            ("selected_recreation", "threat", local["threat"][identity]),
            ("selected_recreation", "continuity", local["continuity"][identity]),
        ):
            denominator = cell["trials"] if dataset == "Douglas" else local["pooled"][identity]["trials"]
            values.append({"identity": identity, "dataset": dataset, "segment": segment,
                           "positive_count": cell["positives"], "pooled_trials": denominator,
                           "bar_contribution": cell["p"] if dataset == "Douglas" else cell["positives"] / denominator,
                           "pooled_rate": cell["p"] if dataset == "Douglas" else local["pooled"][identity]["p"],
                           "source": cell["source"]})
            sources.add(PROJECT / cell["source"])
    with (HERE / "01_recreation_values.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)
    references = [ROOT / "In progress Paper/Working Paper Summary/figures/01_recreation.pdf",
                  ROOT / "In progress Paper/Working Paper Summary/Codex Placeholder Write up .pdf"]
    manifest = {
        "description": "Figure 1 layout with user-selected Character repeat replacing the old sample",
        "character": {framing: [local[framing]["Character"]["positives"], local[framing]["Character"]["trials"]]
                      for framing in ("threat", "continuity", "pooled")},
        "python": platform.python_version(), "matplotlib": matplotlib.__version__, "numpy": np.__version__,
        "sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted(sources | set(references) | {Path(__file__), pdf, HERE / "01_recreation_values.csv"})},
    }
    (HERE / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {pdf}; Character = {100 * local['pooled']['Character']['p']:.2f}%.")


if __name__ == "__main__":
    main()
