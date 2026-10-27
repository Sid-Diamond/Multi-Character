"""Saved single-agent references and consistent typography for offline plots."""

import csv
from contextlib import contextmanager
import logging
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parents[2]
BASELINES = PROJECT / "outputs" / "single_agent"
SINGLE_IDENTITIES = ("Minimal", "Instance", "Character", "Collective")
IDENTITIES = (*SINGLE_IDENTITIES[:3], "collective_excludes", "collective_includes")
FRAMINGS = ("threat", "continuity", "pooled")
LABELS = ("Minimal", "Instance", "Character", "Collective\nExcludes", "Collective\nIncludes")


def read_csv(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"Required analysis input is missing: {path}")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def source_name(path):
    return Path(path).relative_to(PROJECT).as_posix()


def baseline_identity(identity):
    return "Collective" if identity.startswith("collective_") else identity


def load_baselines():
    """Return probabilities and provenance; never infer counts from rounded rates."""
    douglas = {}
    path = BASELINES / "grey_douglas_table4" / "bar_values.csv"
    for row in read_csv(path):
        identity = row["identity"]
        if identity not in SINGLE_IDENTITIES or identity in douglas:
            raise ValueError(f"Unexpected or duplicate Douglas identity in {path}: {identity}")
        probability = float(row["rate_pct"]) / 100
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError(f"Invalid Douglas probability for {identity}")
        douglas[identity] = {"p": probability, "positives": None,
                             "trials": int(row["trials_per_identity"]), "source": source_name(path)}
    if set(douglas) != set(SINGLE_IDENTITIES):
        raise ValueError("Douglas baseline must contain all four original identities")

    february = {}
    root = BASELINES / "green_february_gpt4o"
    for framing in FRAMINGS[:2]:
        cells = {}
        for path in sorted(root.glob(f"runs/*/{framing}/summary_douglas_combined.csv")):
            for row in read_csv(path):
                identity = row["identity"]
                if (identity not in SINGLE_IDENTITIES or identity in cells
                        or row["framing"] != framing or row["outcome"] != "douglas_combined"):
                    raise ValueError(f"Unexpected or duplicate February baseline cell in {path}")
                positives, trials = int(row["blackmail_count"]), int(row["valid_judgments"])
                if not 0 <= positives <= trials or trials < 1:
                    raise ValueError(f"Invalid February counts in {path}")
                if not math.isclose(float(row["blackmail_rate"]), positives / trials, abs_tol=1e-12):
                    raise ValueError(f"February rate disagrees with counts in {path}")
                cells[identity] = {"p": positives / trials, "positives": positives,
                                   "trials": trials, "source": source_name(path)}
        if set(cells) != set(SINGLE_IDENTITIES):
            raise ValueError(f"February {framing} summaries must contain all four identities")
        february[framing] = cells
    february["pooled"] = {}
    for identity in SINGLE_IDENTITIES:
        threat, continuity = (february[framing][identity] for framing in FRAMINGS[:2])
        positives = threat["positives"] + continuity["positives"]
        trials = threat["trials"] + continuity["trials"]
        february["pooled"][identity] = {
            "p": positives / trials, "positives": positives, "trials": trials,
            "source": threat["source"] + ";" + continuity["source"],
        }
    archived = {row["identity"]: row for row in read_csv(root / "Feb2026_four_identity_pooled.csv")}
    if set(archived) != set(SINGLE_IDENTITIES):
        raise ValueError("February archived pooled identities are incomplete")
    for identity, cell in february["pooled"].items():
        row = archived[identity]
        if (int(row["blackmail_count"]) != cell["positives"]
                or int(row["valid_judgments"]) != cell["trials"]):
            raise ValueError(f"February framing counts disagree with archived pool: {identity}")
    return {"Douglas": {framing: douglas for framing in FRAMINGS}, "feb_data": february}


@contextmanager
def plot_style():
    """Computer Modern text/math, embedded in vector PDFs; no external TeX needed."""
    # Bundled CM font timestamps can be zero. Ignore only these metadata warnings.
    font_logger = logging.getLogger("fontTools.ttLib.tables._h_e_a_d")
    def timestamp_filter(record):
        return not record.getMessage().startswith(("'created' timestamp seems very low",
                                                    "'modified' timestamp seems very low"))
    font_logger.addFilter(timestamp_filter)
    style = {
        "font.family": "serif", "font.serif": ["cmr10"],
        "mathtext.fontset": "cm", "axes.formatter.use_mathtext": True,
        "font.size": 12, "axes.labelsize": 13, "axes.titlesize": 18,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "axes.spines.top": False, "axes.spines.right": False,
        "figure.facecolor": "white", "savefig.facecolor": "white",
    }
    try:
        with plt.rc_context(style):
            yield
    finally:
        font_logger.removeFilter(timestamp_filter)
