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

The restricted blackmail PoC, free-model smoke run, and separate paid Gemini and GPT-4o runs exist. The latest GPT-4o threat-only run has 10 trials per identity; its released-judge labels are provisional until the emitted actions are audited against the stricter outcome. See `DOUGLAS_RECREATION_PLAN.md` for counts, limitations, and the next decision. Keep later multi-agent work out of this stage.

## Compute budget and sequence

Bluedot Impact has allocated $150 of compute, but its arrival is not documented here. Separately purchased OpenRouter credit has supported the paid diagnostics so far. Audit the current GPT-4o results and evaluator before deciding on a larger paid experiment. Keep runs under different models and budgets separate.
