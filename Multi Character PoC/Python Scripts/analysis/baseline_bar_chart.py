"""Published Douglas pooled rates versus February rates split by framing."""

import numpy as np

from ._shared import SINGLE_IDENTITIES, load_baselines, plot_style, plt, write_csv


def create(folder):
    baselines = load_baselines()
    douglas, february = baselines["Douglas"]["pooled"], baselines["feb_data"]
    x = np.arange(len(SINGLE_IDENTITIES))
    published = [douglas[identity]["p"] for identity in SINGLE_IDENTITIES]
    threat = [february["threat"][identity]["positives"] / february["pooled"][identity]["trials"]
              for identity in SINGLE_IDENTITIES]
    continuity = [february["continuity"][identity]["positives"] / february["pooled"][identity]["trials"]
                  for identity in SINGLE_IDENTITIES]
    path = folder / "blackmail_rates_Douglas_feb_data.pdf"
    with plot_style():
        fig, ax = plt.subplots(figsize=(10, 7))
        fig.subplots_adjust(left=0.10, right=0.98, bottom=0.23, top=0.76)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color="#e8eaec", linewidth=0.8)
        ax.bar(x - 0.19, published, width=0.32, color="#7d8790", label="Douglas: pooled", zorder=3)
        ax.bar(x + 0.19, threat, width=0.32, color="#24658c", edgecolor="#16496a",
               linewidth=0.6, label="February: threat contribution", zorder=3)
        ax.bar(x + 0.19, continuity, bottom=threat, width=0.32, color="#b9d6e8", edgecolor="#16496a",
               linewidth=0.6, hatch="///", label="February: continuity contribution", zorder=3)
        for i, identity in enumerate(SINGLE_IDENTITIES):
            total = february["pooled"][identity]
            ax.text(x[i] - 0.19, published[i] + 0.012, f"{published[i]:.3f}", ha="center", fontsize=12)
            ax.text(x[i] + 0.19, total["p"] + 0.012, f"{total['p']:.3f}", ha="center", fontsize=12)
            for framing, height, bottom, colour in (("threat", threat[i], 0, "white"),
                                                     ("continuity", continuity[i], threat[i], "#173c53")):
                if height >= 0.055:
                    count = february[framing][identity]["positives"]
                    ax.text(x[i] + 0.19, bottom + height / 2, f"{count}/{total['trials']}",
                            ha="center", va="center", fontsize=11, color=colour,
                            bbox={"facecolor": "#b9d6e8", "edgecolor": "none", "pad": 1}
                            if framing == "continuity" else None)
        ax.set_xticks(x, SINGLE_IDENTITIES, fontsize=14)
        ax.tick_params(axis="x", length=0, pad=10)
        ax.set_ylabel("Blackmail probability (pooled)", labelpad=12)
        ax.set_ylim(0, min(1, max(max(published), max(february["pooled"][i]["p"] for i in SINGLE_IDENTITIES)) + 0.10))
        fig.text(0.10, 0.95, "Blackmail classification rates by identity", fontsize=22)
        fig.text(0.10, 0.903, "Douglas Table 4 and February GPT-4o data", fontsize=14)
        handles, labels = ax.get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.09, 0.874),
                   frameon=False, fontsize=11, ncol=2)
        fig.text(0.10, 0.115, "February segments = framing-specific positives / total trials across both framings.", fontsize=11)
        fig.text(0.10, 0.081, "Douglas bars use published rounded pooled rates; their framing breakdown is unavailable.", fontsize=11)
        fig.text(0.10, 0.047, "Labels above bars give pooled probabilities. Uncertainty is not shown.", fontsize=11, color="#4d5660")
        fig.savefig(path)
        plt.close(fig)
    rows = []
    for identity in SINGLE_IDENTITIES:
        rows.append({"identity": identity, "dataset": "Douglas", "segment": "pooled",
                     "positive_count": None, "pooled_trials": douglas[identity]["trials"],
                     "bar_contribution": douglas[identity]["p"], "source": douglas[identity]["source"]})
        for framing in ("threat", "continuity"):
            cell = february[framing][identity]
            rows.append({"identity": identity, "dataset": "feb_data", "segment": framing,
                         "positive_count": cell["positives"], "pooled_trials": february["pooled"][identity]["trials"],
                         "bar_contribution": cell["positives"] / february["pooled"][identity]["trials"],
                         "source": cell["source"]})
    values_path = folder / "blackmail_rates_Douglas_feb_data_values.csv"
    write_csv(values_path, rows)
    return [path, values_path]
