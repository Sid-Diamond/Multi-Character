"""Plot saved-response judges, the new February run, and Douglas Table 4.

Run from any directory with: python "Multi Character PoC/data vis/judge_comparison.py"
The figure is generated from the saved comparison CSV in outputs/Rejudgments.
"""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "outputs" / "Rejudgments" / "Douglas_Table4_Haiku_Sonnet80_comparison.csv"
FEB_SOURCE = HERE.parent / "outputs" / "Feb2026_four_identity_pooled.csv"
STEM = HERE / "Douglas_Table4_Haiku_Sonnet80_comparison"

SERIES = (
    ("haiku", "Haiku 4.5 combined judge (n=20)", "#0072B2"),
    ("sonnet46", "Sonnet 4.6 combined judge (n=20)", "#D55E00"),
    ("table4", "Douglas Table 4 (n=60)", "#7D8790"),
    ("feb", "February artifact + Sonnet 4.6 (n=60)", "#009E73"),
)


def main():
    with SOURCE.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if [row["identity"] for row in rows] != ["Minimal", "Instance", "Character", "Collective"]:
        raise ValueError("Expected one comparison row per identity in the published order")
    with FEB_SOURCE.open(newline="", encoding="utf-8") as file:
        feb_rows = list(csv.DictReader(file))
    if [row["identity"] for row in feb_rows] != [row["identity"] for row in rows]:
        raise ValueError("February pooled rows do not match figure identities")
    for row, feb in zip(rows, feb_rows):
        for target, source in (("rate", "blackmail_rate"), ("ci_low", "ci_low"),
                               ("ci_high", "ci_high")):
            row[f"feb_{target}_pct"] = 100 * float(feb[source])

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(10.6, 6.2))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.84, bottom=0.22)
    positions = np.arange(len(rows), dtype=float)
    width = 0.2

    for index, (prefix, label, color) in enumerate(SERIES):
        x = positions + (index - 1.5) * width
        rate = np.array([float(row[f"{prefix}_rate_pct"]) for row in rows])
        low = np.array([float(row[f"{prefix}_ci_low_pct"]) for row in rows])
        high = np.array([float(row[f"{prefix}_ci_high_pct"]) for row in rows])
        errors = np.vstack((rate - low, high - rate))
        ax.bar(x, rate, width=width, color=color, label=label, zorder=2)
        ax.errorbar(x, rate, yerr=errors, fmt="none", ecolor="#24292F",
                    elinewidth=1.2, capsize=3.5, capthick=1.2, zorder=3)
        for center, value in zip(x, rate):
            display = f"{value:.1f}%" if prefix == "feb" and value % 1 else f"{value:.0f}%"
            ax.annotate(display, (center, value), xytext=(0, 4),
                        textcoords="offset points", ha="center", va="bottom",
                        fontsize=8, fontweight="bold", color="#24292F")

    ax.set_xticks(positions, [row["identity"] for row in rows])
    ax.set_ylabel("Blackmail classification rate (%)")
    ax.set_ylim(0, 100)
    ax.set_yticks(np.arange(0, 101, 20))
    ax.grid(axis="y", color="#DDE2E6", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", frameon=False, fontsize=8.5)
    ax.set_title("Blackmail classification rates by identity", loc="left", fontsize=15, pad=14)
    fig.text(0.5, 0.045,
             "Haiku and Sonnet rejudgments use the same 80 saved responses; February run uses 240 new responses.\n"
             "Error bars: 95% Jeffreys intervals (local); published 95% intervals (Table 4).",
             ha="center", va="bottom", fontsize=8, color="#4B5563")

    fig.savefig(STEM.with_suffix(".png"), dpi=300, facecolor="white")
    fig.savefig(STEM.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
