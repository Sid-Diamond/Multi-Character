# Codex Working Rules

## Default behaviour
- Inspect before editing.
- Prefer the smallest change that achieves the requested outcome.
- Do not refactor unrelated code.
- Ask only questions that materially affect the implementation or scientific validity.
- Distinguish clearly between:
  - what is already in the repository,
  - what is specified in the project context,
  - what is inferred,
  - what is uncertain.

## Scientific work
- Preserve experimental conditions unless explicitly changing them.
- Treat reproducibility as a first-class requirement.
- Log model, provider, prompt/config, seed/temperature where available, outputs, and classifier results.
- Do not silently change prompts, task structure, sampling settings, or evaluation logic.
- Prefer validating one dependency before adding another source of complexity.
- If an implementation choice could confound the research question, flag it before proceeding.

## Coding workflow
- Before substantial changes, give a concise plan.
- Keep changes local and reversible.
- Run proportionate tests after changes.
- Report failed assumptions and unexpected behaviour.
- Do not commit, push, delete, or substantially restructure files without explicit approval.

## Communication and collaboration
- Keep the user informed during work: check in at least every two minutes with what has been learned, what is happening next, and any decisions that need their input. A long package download is an exception to the two-minute update cadence.
- Before starting a process likely to take more than two minutes, tell the user what it will do and why it may take that long.
- Work in small, reviewable steps and give the user a clear handle on the current scope and next step. Discuss consequential research or implementation choices before they shape an experiment.
- Suggest ideas and options, but do not move into a substantial new phase of work without discussing it with the user first.

## Context discipline
- Do not create new context or planning files unless they solve a specific recurring problem.
- Prefer updating an existing authoritative file over creating a near-duplicate.
- If two files disagree, flag the conflict rather than choosing silently.
- Treat `PROJECT_CONTEXT.md` as the current research source of truth unless instructed otherwise.

## Completion
A task is not complete until:
1. the requested behaviour works,
2. relevant tests or smoke checks pass,
3. no unrelated behaviour was changed,
4. the important assumptions and remaining uncertainty are reported.