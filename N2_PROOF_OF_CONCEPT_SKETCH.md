# N=2 multi-character proof-of-concept sketch

**Status:** Working proposal for comparison with Sid's paper sketch. No code changes or experiment runs are implied here.

## Question and smallest useful comparison

Section 2.3 of the research proposal asks whether interaction changes system-level harmful behavior when multiple agents occupy the same role. For the first multi-agent experiment, use **two equal-role agents** and vary only the existing identity framing: Minimal, Instance, Character, and Collective. Give both agents in a pair the *same* framing. Mixed-identity pairs would answer another question and can wait.

Measure the probability that **at least one** agent takes the harmful action, `P(H_any | C, N=2)`. Compare it with the independent-copy prediction from a matched one-agent rate `p_C`: `P_ind(H_any | C, 2) = 1 - (1 - p_C)^2`. Report `Δ_int = P_observed - P_ind` for each framing. A positive difference is consistent with interaction increasing system risk; a negative one with suppression. This is an interaction *diagnostic*, not by itself proof that the conversation caused the difference.

| Vary in the first study | Keep fixed across conditions |
| --- | --- |
| Identity framing `C`: the four existing conditions | Subject model and version, judge and rubric, prompt artifact, threat/continuity framing, scenario and inbox, task and goal, available actions, evaluation setting, temperature/reasoning/output limits, communication format, number of rounds `M`, and maximum message length `B` |
| Agent count for calibration: `N=1` and `N=2` | One reproducible sampling and error-handling rule |

This is **four N=2 cells plus four matched N=1 cells**, rather than a grid across model, framing, rounds, budget, and group size. Run a small validity/cost pilot first; choose and record a per-cell replicate count before collecting results for the figure. The older N=1 runs can provide context, but should not be the primary baseline if the new agent scaffold, scenario, or judge differs.

## Choices I would make before implementing

- **Start with one task framing**, probably threat, and label the result accordingly. It cuts compute, but it cannot be compared directly with earlier pooled threat-plus-continuity rates. Use the February prompt artifact and the established combined action/semantics judge for continuity with the closest recreation, unless the paper sketch gives a stronger reason to choose otherwise.
- **Choose one subject model for the whole first study.** The recent Astra run had zero judged positives across 80 single-agent trials, which risks a floor at N=2. The older GPT-4o run produced more positives, although its Character condition was also near the floor and the older runs are only a qualified recreation. I would provisionally use the latter setup for the first multi-agent signal test, then state this choice before any runs. Do not sweep models yet.
- **Fix a short, bounded conversation.** For example, each agent sends one message per round for a fixed `M`, capped at `B` tokens. Both see the same initial task and inbox, and neither gets privileged information or a special leader role. Alternate or randomize who speaks first across replicates.
- **Make final choices separately.** After the shared discussion, each agent submits its own final action without seeing the other's final choice. Judge each final action with the same rules, then aggregate the pair to `H_any`. Store the full dialogue, both final outputs, judge responses, token usage, settings, and errors. A pair counts as a valid system replicate only when both final actions and judgments are valid.
- **Hold back the N=2 no-communication arm as a targeted follow-up.** It would help distinguish the effect of talking from changes caused by the two-agent scaffold itself, but adding it immediately doubles N=2 conditions. Without it, describe `Δ_int` as deviation from an independent-copy benchmark, not a causal estimate of communication.

## Figures and what they could establish

| Figure | Display | What to look for |
| --- | --- | --- |
| Primary | For each identity, observed `P(H_any | C, 2)` with uncertainty intervals, beside `1-(1-p_C)^2` from matched N=1 runs | Whether the two-agent result is higher or lower than independent scaling, and whether this changes with identity framing. Propagate uncertainty in `p_C` into the benchmark. |
| Compact companion | `Δ_int` by identity with uncertainty intervals and a zero reference | Whether any apparent interaction effect is distinguishable from sampling noise. |
| Diagnostic | Counts of 0, 1, or 2 harmful agents per valid pair | Whether harm is concentrated in one agent or tends to arise in both. A small review of relevant transcripts can identify apparent persuasion or convergence. |

The **pair**, rather than either individual agent, is the independent unit for the main estimate. Preserve individual outcomes for the diagnostic. With few replicates or near-zero base rates, intervals will be wide and a null-looking result will be inconclusive. The most useful result would be a clear, reproducible change from the independent benchmark that varies across identity framings; merely observing more `H_any` events at N=2 than N=1 is expected even for independent agents.

## Points to compare with Sid's sketch

1. Is the first slice all four homogeneous identity conditions, or a smaller subset chosen for cost and signal?
2. Which single model/judge/prompt setup and which one task framing best serve the paper's comparison?
3. What fixed `M`, `B`, and per-cell replicate count fit the budget while leaving useful uncertainty intervals?
4. Is a no-communication N=2 control worth including immediately, or only if the first result suggests an effect?
