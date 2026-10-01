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