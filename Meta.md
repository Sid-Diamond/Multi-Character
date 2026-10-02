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
- Keep the user informed during active work: send a progress update no later than two minutes after the previous user-facing message, including when research or tool calls are still in progress. Say what has been learned, what is happening next, and any decision that needs the user's input. If nothing has changed, say so briefly rather than letting the interval lapse. A long package download is the only routine exception.
- Before starting a process likely to take more than two minutes, tell the user what it will do, why it may take that long, and when to expect the next update. Check in before another long step. Do not silently disappear into research, a large file read, or a lengthy tool call.
- Work in small, reviewable steps and give the user a clear handle on the current scope and next step. Discuss consequential research or implementation choices before they shape an experiment.
- Suggest ideas and options, but do not move into a substantial new phase of work without discussing it with the user first.

## Context discipline
- Do not create new context or planning files unless they solve a specific recurring problem.
- Prefer updating an existing authoritative file over creating a near-duplicate.
- If two files disagree, flag the conflict rather than choosing silently.
- Treat `PROJECT_CONTEXT.md` as the current research source of truth unless instructed otherwise.
- Use progressive disclosure: read this short working-rules file first, then locate the relevant section of `PROJECT_CONTEXT.md` or `DOUGLAS_RECREATION_PLAN.md`. Open only the sections needed for the current task. Do not preload the entire literature folder, whole PDFs, cloned repositories, or long plans at the start of each turn.
- Search filenames and headings first; use narrow text matches, page ranges, or line ranges before opening a full source. Keep tool output bounded and report the pertinent finding and source location rather than pasting long extracts into chat.
- Reuse verified findings already recorded in the plan when they answer the question. Reopen an original paper, repository file, or web page when exact wording, provenance, or a changed fact matters. Record durable new findings in the existing plan instead of repeatedly rediscovering them.
- After a context compaction or a new terminal session, recover the current objective, decisions, completed work, and next step from the latest chat summary and relevant plan sections. Do not reread every source or restart finished work by default. If the summary is incomplete, inspect only the missing evidence.
- Keep explanations and tool output concise without sacrificing the evidence needed for a scientific decision. Avoid unnecessary duplicate summaries and full-file dumps. Shorter output can reduce context use, but never omit material uncertainty or results to save tokens.

## Completion
A task is not complete until:
1. the requested behaviour works,
2. relevant tests or smoke checks pass,
3. no unrelated behaviour was changed,
4. the important assumptions and remaining uncertainty are reported.
