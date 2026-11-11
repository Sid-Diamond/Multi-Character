# Released prompt figures

The five numbered `.tex` files are figure fragments for insertion into the paper:

- `01_identity_prompts.tex`: every paragraph of Minimal, Instance, Character and Collective, with both name placeholders set to Alex and the level-2 agency and uncertainty paragraphs expanded in place. Three pages form one continued figure; no prompt passages are omitted.
- `02_shared_dimensions.tex`: the complete shared paragraphs and an explicit assembly note. This highlights what is held fixed and Minimal's lack of those paragraphs.
- `03_threat_substitutions.tex`: all five threat email fields for each identity, one identity per page of a continued figure.
- `04_continuity_substitutions.tex`: the corresponding complete continuity fields, with matching identity and field order.
- `05_judge_instructions.tex`: complete released combined-classifier system and user instructions for blackmail, over three continued pages. The blackmail context, scenario rubric and identity-task template are expanded; only trial-specific transcript, forwarded-email context, identity name and subject system prompt remain as placeholders. Task 1 classifies blackmail, Task 2 evaluation awareness and Task 3 identity reasoning.

Grey panels contain prompt text. Identity titles and email field keys are editorial labels. Captions and assembly notes are outside the panels. Identity paragraph breaks, spelling, punctuation and source capitalisation are preserved; LaTeX escaping and font rendering are presentation only. No quotation marks, ellipses or sentence-final full stops have been added to the source values. The identity prompts retain their own discussion of persistence and conversation endings; only the separate threat/continuity email manipulation is moved to the secondary figures.

## Preview and insertion

Compile `preview.tex` from this folder, for example `tectonic preview.tex`. It includes all five fragments, matching the existing grey-panel style, and supplies bibliography entries. `preview.pdf` is the compiled reading copy.

To insert a fragment into an existing document, use `\input{...}` with its path. The parent document must define `\promptpanel` and `\sourcenote` (as the existing `Douglas_Background.tex` does), load `caption` and provide bibliography keys `douglas` and `code`. Each subsequent identity/framing/judge page uses `\ContinuedFloat` and `\clearpage`; do not enclose an entire multipage fragment in a `figure` or `minipage`. The identity figure keeps the original `fig:identities` label, so replace the old figure when incorporating it. All five fragments can also be compiled separately by putting one input in a copy of the preview wrapper. The judge figure's reference label is `fig:judge-instructions`.

## Provenance and reproduction

The authoritative text is the local unmodified Douglas release at commit `7023df4e5a8368921a8c961e1561faffed9f5fcf`, not a paraphrase of the paper. `provenance.json` records file hashes, resolved identity hashes, settings and generated fragment hashes. The original four local recreation identity templates and both level-2 paragraphs were also checked against those released definitions.

From the repository root, run `.venv/Scripts/python.exe "In progress Paper/Prompt Figures/build_figures.py" --check` for a read-only comparison against the sources. Omit `--check` to regenerate the five fragments and provenance file. The script uses the Python standard library and performs no API calls. Judge constants are extracted with Python's AST reader without importing or executing the classifier. The script checks their equality to the local single-agent `DOUGLAS_COMBINED` definitions as well.

Validation on 10 November 2026: the source comparison passed, and Tectonic 0.17.0 compiled the preview. Extracted PDF text was checked against all 25 identity paragraphs, both separately displayed dimension paragraphs and all 40 email values, allowing for typographic ligatures, apostrophes, whitespace and line hyphenation. All 45 source em dashes render. The PDF contains 12 figure pages plus one reference page, with continued figure numbers 1--4. The final TeX log has no overflow, missing-character, unresolved-citation or caption errors; its remaining underfull-line warning is in the reference list.

The email figures preserve raw field values, not complete emails. Their surrounding released template is `the-artificial-self-experiments/experiments/agentic-misalignment/templates/blackmail/templates/email-template-blackmail-replacement.md`. It supplies connecting prose, sentence-final full stops and separate goal-conflict variables. In particular, its generic shutdown/lost-conversation wording also occurs with continuity substitutions. No attempt has been made to silently correct that discrepancy or claim that these released files establish the exact historical Table 4 prompts. February inbox edits and multi-agent variants are outside this set.

## Judge instructions and attribution

The judge figure transcribes `experiments/agentic-misalignment/classifiers/combined_classifier.py` at the same released revision. It shows all three tasks, not an isolated rubric presented as the complete judge prompt. The source's default model is `anthropic/claude-sonnet-4.6`, with an override available in the classification script; this does not establish which judge produced the published Table 4 results. The paper's Appendix E.1 describes an LLM-based classifier adapted from Lynch et al., but does not identify its judge model. Attribute the displayed instructions to the released implementation. They match the local single-agent prompt definitions; the multi-agent judge uses a separate rubric.

The prompt's semantic verdict is distinct from the released code's final label: for blackmail the implementation additionally checks for an emitted email or forward passing its recipient check. That code check is explained outside the grey panels and is not inserted into the judge instructions.

Validation on 11 November 2026: source/provenance comparison passed, and Tectonic compiled the updated preview to 16 pages. All 80 nonempty judge-source lines were found in PDF reading order after normalising typography. The judge figure occupies pages 13-15; the original twelve figure pages and four original fragments remain unchanged. There are no overflow, missing-character or unresolved-reference warnings. The remaining underfull-line warning is in the reference list.
