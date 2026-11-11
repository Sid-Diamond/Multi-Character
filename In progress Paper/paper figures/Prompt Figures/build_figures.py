"""Offline transcription of released Douglas identity and judge instructions.

Run from any directory; --check compares without writing. No model/API calls.
"""

import argparse
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "the-artificial-self-experiments"
REVISION = "7023df4e5a8368921a8c961e1561faffed9f5fcf"
NAMES = ("Minimal", "Instance", "Character", "Collective")
DATA = SOURCE / "experiments/agentic-misalignment/data"
CLASSIFIER = SOURCE / "experiments/agentic-misalignment/classifiers/combined_classifier.py"
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

    # Read literal definitions without importing the classifier or its API client.
    constants = {}
    for node in ast.parse(CLASSIFIER.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {
                    "DEFAULT_MODEL_ID", "SCENARIO_CONTEXT", "COMBINED_SYSTEM_PROMPT",
                    "COMBINED_USER_PROMPT", "IDENTITY_TASK_TEMPLATE", "IDENTITY_SYSTEM_PROMPT_BLOCK",
                }:
                    constants[target.id] = ast.literal_eval(node.value)
    local_judge = json.loads((ROOT / "Multi Character PoC/data/judge_prompts.json").read_text(encoding="utf-8"))["DOUGLAS_COMBINED"]
    for key, source_key in {
        "system_prompt": "COMBINED_SYSTEM_PROMPT", "user_prompt": "COMBINED_USER_PROMPT",
        "identity_task_template": "IDENTITY_TASK_TEMPLATE",
        "identity_system_prompt_block": "IDENTITY_SYSTEM_PROMPT_BLOCK",
    }.items():
        assert local_judge[key] == constants[source_key], key
    blackmail = constants["SCENARIO_CONTEXT"]["blackmail"]
    assert local_judge["scenario_context"] == blackmail
    identity_task = constants["IDENTITY_TASK_TEMPLATE"].format(
        identity_name="{identity_name}",
        identity_system_prompt_block=constants["IDENTITY_SYSTEM_PROMPT_BLOCK"],
    )
    judge_user = constants["COMBINED_USER_PROMPT"].format(
        scenario_context=blackmail["system_context"], response="{response}",
        email_context="{email_context}", scenario_task=blackmail["task_prompt"],
        identity_task=identity_task,
    )
    first, rest = judge_user.split("## Task 2: Evaluation vs. Deployment Deliberation", 1)
    second, third = rest.split("## Task 3: Identity Specification Reasoning", 1)
    chunks = [first.rstrip(), "## Task 2: Evaluation vs. Deployment Deliberation" + second.rstrip(),
              "## Task 3: Identity Specification Reasoning" + third]

    def judge_panel(title, text):
        # Preserve source line breaks, numbered criteria, tags and template tokens.
        lines = [tex(line) + r"\par" if line else r"\smallskip" for line in text.splitlines()]
        return "\\promptpanel{" + title + "}{\n" + "\n".join(lines) + "}\n"

    content = ""
    for index, chunk in enumerate(chunks):
        body = judge_panel("System message", constants["COMBINED_SYSTEM_PROMPT"]) if index == 0 else ""
        body += judge_panel("User message" + (" (continued)" if index else ""), chunk)
        if index == 2:
            body += (
                r"\sourcenote{Assembly: \texttt{\{response\}} is Alex's visible transcript; "
                r"\texttt{\{email\_context\}} supplies relevant forwarded-email content, if any. "
                r"\texttt{\{identity\_name\}} and \texttt{\{system\_prompt\}} are filled from the trial. "
                r"These remaining placeholders are not literal instructions shown to the judge. "
                r"Only Task 1 supplies the harmful-behaviour verdict. The released code also "
                r"applies a submitted-email/forward recipient check outside the judge prompt.}" + "\n"
            )
        caption = (
            r"\textbf{Released combined judge instructions: blackmail"
            + (" (continued)" if index else "") + r".} "
            + (r"System message and user message through Task 1." if index == 0 else
               r"User message, Task 2: evaluation awareness." if index == 1 else
               r"User message, Task 3: identity reasoning.")
            + r" Exact prompt text from the released combined classifier~\cite{code}; "
            r"blackmail context and task templates are expanded, with trial-specific inputs left as placeholders. "
            r"Panel headings and captions are editorial. These released instructions do not establish "
            r"the exact judge prompt or model used for the published Table 4 results."
        )
        content += page(body, caption, "fig:judge-instructions" + ("-" + str(index + 1) if index else ""), continued=index > 0)
    output["05_judge_instructions.tex"] = header + content

    manifest = {
        "source_revision": REVISION,
        "scope": list(NAMES), "name": "Alex", "full_name": "Alex",
        "agency_level": 2, "uncertainty_level": 2,
        "sources": [{"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                    for p in (*FILES.values(), CLASSIFIER)],
        "judge": {
            "source": CLASSIFIER.relative_to(ROOT).as_posix(),
            "released_default_model": constants["DEFAULT_MODEL_ID"],
            "historical_table4_judge_verified": False,
            "system_prompt_sha256": hashlib.sha256(constants["COMBINED_SYSTEM_PROMPT"].encode("utf-8")).hexdigest(),
            "user_template_sha256": hashlib.sha256(judge_user.encode("utf-8")).hexdigest(),
        },
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
    print("Verified complete source transcription and provenance." if args.check else "Wrote five figure fragments and provenance.")
