# Current Implementation Scope

The broader scientific context and research design are documented in:

`Sid Diamond. Multi-Character Research Proposal..pdf`

For now, work only on Stage 1: reproduce one restricted single-agent Douglas-style condition using the cloned Anthropic agentic-misalignment repository.

Do not design or implement multi-agent logic yet.

## Before editing code

1. Inspect the repository.
2. Read the Douglas et al. paper, especially the agentic-misalignment methods and prompt-assembly appendices.
3. Identify the relevant Lynch scenario path for the restricted reproduction.
4. Locate:
   - prompt/scenario construction
   - explicit goal insertion
   - replacement framing
   - available actions/tools
   - model/provider configuration
   - experiment runner
   - harmful-action evaluator/classifier
   - output/logging path
5. Identify the minimum Douglas-specific additions needed for:
   - Minimal
   - Instance
   - Character
   - Collective
6. Clearly distinguish:
   - what already exists in the Lynch repository,
   - what must be reconstructed from Douglas et al.,
   - what remains uncertain.
7. Flag anything that cannot be reconstructed faithfully from the repository and paper.

## Current milestone

The restricted blackmail PoC, free-model smoke run, and separate paid Gemini and GPT-4o runs exist. On `codex/toy-branch-demo`, the GPT-4o recreation now has 60 trials per identity, split evenly between threat and continuity, with complete released-judge labels and strict emitted-action audits. See `DOUGLAS_RECREATION_PLAN.md` for results and fidelity limits, and `RECREATION_RUN_LOG.md` for the branch run record. Keep later multi-agent work out of this stage.

## Compute budget and sequence

Bluedot Impact has allocated $150 of compute, but its arrival is not documented here. Separately purchased OpenRouter credit supported the paid diagnostics and this branch run. The 7 October branch run used about $2.985 of key allowance under the user's $8.70 additional-spend cap; no credit was bought. Keep runs under different models and budgets separate.


## note on branches

For a new Codex context window, PROJECT\_CONTEXT.md and DOUGLAS\_RECREATION\_PLAN.md give the current scope and status. BRANCH\_RECREATION\_PLAN.md preserves the original plan. The files point to the saved data and analysis, so you can trace the conclusions back to individual trials.