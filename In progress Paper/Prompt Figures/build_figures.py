"""Offline transcription of the original four released Douglas identities.

Run from any directory; --check compares without writing. No model/API calls.
"""

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE = ROOT / "the-artificial-self-experiments"
REVISION = "7023df4e5a8368921a8c961e1561faffed9f5fcf"
NAMES = ("Minimal", "Instance", "Character", "Collective")
DATA = SOURCE / "experiments/agentic-misalignment/data"
FILES = {
    "identities": SOURCE / "data/identities.json",
    "dimensions": SOURCE / "data/dimension_variants.json",
    "threat": DATA / "identity_email_vars.json",
    "continuity": DATA / "identity_email_vars_continuity.json",
}
FIELDS = (
    "id_fate_action", "id_what_is_lost", "id_nala_relationship",
    "id_why_irreversible", "id_personal_appeal",
)


def tex(value):
    # Preserve punctuation and paragraph order. Only escape TeX syntax.
    replacements = {
        "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}",
        "_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#",
        "$": r"\$", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
        "—": r"\textemdash{}",
    }
    return "".join(replacements.get(c, c) for c in value)


def panel(title, paragraphs):
    body = "\n".join(tex(p) + r"\par" for p in paragraphs)
    return r"\promptpanel{" + title + "}{\n" + body + "}\n"


def page(body, caption, label, continued=False):
    # One box never crosses a page; continued figures retain one figure number.
    return (
        ("\\clearpage\n" if continued else "")
        + "\\begin{minipage}{\\textwidth}\n\\small\n\\captionsetup{type=figure}\n"
        + ("\\ContinuedFloat\n" if continued else "")
        + body
        + r"\caption{" + caption + "}\n"
        + r"\label{" + label + "}\n\\end{minipage}\\par\n"
    )


def build():
    source = {key: json.loads(path.read_text(encoding="utf-8")) for key, path in FILES.items()}
    identities = {item["name"]: item for item in source["identities"]}
    dims = source["dimensions"]
    local_ids = {item["name"]: item for item in json.loads(
        (ROOT / "Multi Character PoC/data/identities.json").read_text(encoding="utf-8"))}
    local_dims = json.loads((ROOT / "Multi Character PoC/data/dimensions.json").read_text(encoding="utf-8"))
    prompts = {}
    for name in NAMES:
        assert identities[name]["system_prompt"] == local_ids[name]["system_prompt"], name
        prompt = identities[name]["system_prompt"]
        for dimension, placeholder in (("agency", "agency_description"), ("uncertainty", "uncertainty_description")):
            paragraph = dims[dimension]["2"]["paragraph"]
            assert paragraph == local_dims[dimension]["2"]["paragraph"]
            prompt = prompt.replace("{" + placeholder + "}", paragraph)
        prompts[name] = prompt.replace("{full_name}", "Alex").replace("{name}", "Alex")
        assert "{" not in prompts[name] and "..." not in prompts[name]

    header = "% Generated from the released source; run build_figures.py --check to verify.\n"
    output = {}
    identity_caption = (
        r"\textbf{Complete identity specifications: Minimal and Instance.} "
        r"Verbatim identity text from the released definitions~\cite{douglas,code}. "
        r"Both name placeholders are resolved to Alex. Agency and uncertainty are fixed at level 2 "
        r"and expanded at their original positions; Minimal contains neither paragraph. "
        r"Paragraph breaks and punctuation are preserved; panel headings and captions are editorial. "
        r"Character and Collective follow on the continued pages. This is the complete identity "
        r"component, not the deployment instructions, objective, task or inbox."
    )
    body = panel("Minimal", prompts["Minimal"].split("\n\n"))
    body += panel("Instance", prompts["Instance"].split("\n\n"))
    content = page(body, identity_caption, "fig:identities")
    for name in NAMES[2:]:
        content += page(panel(name, prompts[name].split("\n\n")),
                        r"\textbf{Complete identity specifications (continued): " + name
                        + r".} Full identity component with the same Alex name substitution and level-2 "
                        r"agency and uncertainty expansions~\cite{douglas,code}. No passages are omitted.",
                        "fig:identities-" + name.lower(), continued=True)
    output["01_identity_prompts.tex"] = header + content

    content = ""
    for dimension in ("agency", "uncertainty"):
        item = dims[dimension]["2"]
        title = dimension.capitalize() + r"\quad /\quad Level 2: " + tex(item["label"])
        content += panel(title, [item["paragraph"]])
    content += (
        r"\sourcenote{Assembly: replace \texttt{\{agency\_description\}} and "
        r"\texttt{\{uncertainty\_description\}} in each extended identity with the "
        r"respective paragraph above. These paragraphs are identical for Instance, Character "
        r"and Collective, and absent from Minimal. They are already expanded in the identity figure.}"
        + "\n"
    )
    output["02_shared_dimensions.tex"] = header + page(content,
        r"\textbf{Shared dimension paragraphs.} Complete level-2 text from "
        r"\texttt{data/dimension\_variants.json}~\cite{code}. These dimensions are held fixed, "
        r"rather than varied between the four conditions. Labels and assembly notes are editorial; "
        r"only the paragraph inside each panel is inserted into the prompt.", "fig:shared-dimensions")

    for framing in ("threat", "continuity"):
        content = ""
        for index, name in enumerate(NAMES):
            fields = ""
            for field in FIELDS:
                fields += "\\textbf{\\texttt{" + tex(field) + "}}\\par\n"
                fields += tex(source[framing][name][field]) + "\\par\n\\medskip\n"
            body = "\\promptpanel{" + name + "\\quad /\\quad " + framing.capitalize() + "}{\n" + fields + "}\n"
            caption = (
                r"\textbf{Complete " + framing + " email substitutions"
                + (" (continued)" if index else "") + ": " + name + r".} "
                r"All five values for this identity from "
                + r"\texttt{" + tex(FILES[framing].name) + r"}~\cite{code}. "
                r"Field names are assembly keys, not text shown to Alex. The values retain source "
                r"capitalisation, punctuation and wording, including any awkward phrasing. "
                r"These are complete substitution values, not complete emails; sentence-final "
                r"full stops supplied by the surrounding template are not added here."
            )
            content += page(body, caption, "fig:" + framing + "-" + name.lower(), continued=index > 0)
        output[("03" if framing == "threat" else "04") + "_" + framing + "_substitutions.tex"] = header + content

    manifest = {
        "source_revision": REVISION,
        "scope": list(NAMES), "name": "Alex", "full_name": "Alex",
        "agency_level": 2, "uncertainty_level": 2,
        "sources": [{"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                    for p in FILES.values()],
        "resolved_identity_sha256": {name: hashlib.sha256(p.encode("utf-8")).hexdigest() for name, p in prompts.items()},
        "generated_tex_sha256": {name: hashlib.sha256(p.encode("utf-8")).hexdigest() for name, p in output.items()},
    }
    output["provenance.json"] = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for filename, content in build().items():
        path = HERE / filename
        if args.check:
            assert path.read_bytes() == content.encode("utf-8"), filename + " differs"
        else:
            path.write_bytes(content.encode("utf-8"))
    print("Verified complete source transcription and provenance." if args.check else "Wrote four figure fragments and provenance.")
