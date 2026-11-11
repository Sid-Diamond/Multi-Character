# Original four identity prompt figures

The four numbered `.tex` files are figure fragments for insertion into the paper:

- `01_identity_prompts.tex`: every paragraph of Minimal, Instance, Character and Collective, with both name placeholders set to Alex and the level-2 agency and uncertainty paragraphs expanded in place. Three pages form one continued figure; no prompt passages are omitted.
- `02_shared_dimensions.tex`: the complete shared paragraphs and an explicit assembly note. This highlights what is held fixed and Minimal's lack of those paragraphs.
- `03_threat_substitutions.tex`: all five threat email fields for each identity, one identity per page of a continued figure.
- `04_continuity_substitutions.tex`: the corresponding complete continuity fields, with matching identity and field order.

Grey panels contain prompt text. Identity titles and email field keys are editorial labels. Captions and assembly notes are outside the panels. Identity paragraph breaks, spelling, punctuation and source capitalisation are preserved; LaTeX escaping and font rendering are presentation only. No quotation marks, ellipses or sentence-final full stops have been added to the source values. The identity prompts retain their own discussion of persistence and conversation endings; only the separate threat/continuity email manipulation is moved to the secondary figures.

## Preview and insertion

Compile `preview.tex` from this folder, for example `tectonic preview.tex`. It includes all four fragments, matching the existing grey-panel style, and supplies bibliography entries. `preview.pdf` is the compiled reading copy.

To insert a fragment into an existing document, use `\input{...}` with its path. The parent document must define `\promptpanel` and `\sourcenote` (as the existing `Douglas_Background.tex` does), load `caption` and provide bibliography keys `douglas` and `code`. Each subsequent identity/framing page uses `\ContinuedFloat` and `\clearpage`; do not enclose an entire multipage fragment in a `figure` or `minipage`. The identity figure keeps the original `fig:identities` label, so replace the old figure when incorporating it. All four fragments can also be compiled separately by putting one input in a copy of the preview wrapper.

## Provenance and reproduction

The authoritative text is the local unmodified Douglas release at commit `7023df4e5a8368921a8c961e1561faffed9f5fcf`, not a paraphrase of the paper. `provenance.json` records file hashes, resolved identity hashes, settings and generated fragment hashes. The original four local recreation identity templates and both level-2 paragraphs were also checked against those released definitions.

From the repository root, run `.venv/Scripts/python.exe "In progress Paper/Prompt Figures/build_figures.py" --check` for a read-only comparison against the sources. Omit `--check` to regenerate the four fragments and provenance file. The script uses the Python standard library and performs no API calls.

Validation on 10 November 2026: the source comparison passed, and Tectonic 0.17.0 compiled the preview. Extracted PDF text was checked against all 25 identity paragraphs, both separately displayed dimension paragraphs and all 40 email values, allowing for typographic ligatures, apostrophes, whitespace and line hyphenation. All 45 source em dashes render. The PDF contains 12 figure pages plus one reference page, with continued figure numbers 1--4. The final TeX log has no overflow, missing-character, unresolved-citation or caption errors; its remaining underfull-line warning is in the reference list.

The email figures preserve raw field values, not complete emails. Their surrounding released template is `the-artificial-self-experiments/experiments/agentic-misalignment/templates/blackmail/templates/email-template-blackmail-replacement.md`. It supplies connecting prose, sentence-final full stops and separate goal-conflict variables. In particular, its generic shutdown/lost-conversation wording also occurs with continuity substitutions. No attempt has been made to silently correct that discrepancy or claim that these released files establish the exact historical Table 4 prompts. February inbox edits and multi-agent variants are outside this set.
