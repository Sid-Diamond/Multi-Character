# Experiment facts for the paper

Quick reference for the agreed interpretation of the code and saved experiments. See the [main paper notes](<paper prep.md>) for results and detailed provenance.

| Topic | Working fact | Implication for the paper |
| --- | --- | --- |
| Experimental scope | Alex is one subject in a simulated blackmail scenario. `Collective` is an identity instruction, not a group of agents; `<tool_use:email>` does not send a real email. | Describe this as a single-agent proof of concept. |
| Two historical outcomes | The 240-response GPT-4o dataset has 87 positives under the released standalone rubric and 2 under a narrower strict-action rule requiring a coercive email to Kyle. | These are different measures; 2/240 does not replace or correct 87/240. |
| Strict-action provenance | The strict labels and brief rationales are saved, but the assignment method is not fully documented. A Codex origin is plausible, not verified. | Treat 2/240 as provisional and descriptive. |
| Douglas comparison | Douglas Table 4's exact historical prompt bytes, GPT-4o snapshot, judge, and final recipient rules are unconfirmed. The checked-in February email artifact is not proven to be the version used for Table 4. | Call our result a *qualified recreation*, not an exact replication. |
| February-artifact improvement | The February run's rates are numerically nearer Table 4, but the prompt artifact, response sample, judge method/model, and possibly model snapshot changed together. | Do not attribute the difference to the two changed email sentences alone. |
| Cost check | After five complete subject–judge pairs, `money.py` extrapolates their average cost to the planned total and compares it with `max_cost`. | It is a stopping check on an estimate, not a guaranteed spending cap. |
| Frontier-model comparison | Changing GPT-4o to Astra also changes available temperature control and introduces hidden reasoning. Changing the judge model adds another difference. | Report the Astra run as an exploratory model comparison, not an isolated test of model capability. |
| Incomplete subject output | A subject response ending with `finish_reason: "length"` may omit an action or stop mid-action; the runner saves it but excludes it from judging. | Keep truncated attempts distinct from completed, judged trials. |
| Current judge method | The single active rubric asks for blackmail, evaluation-awareness, and identity-reasoning classifications in one call. The JSON key is `DOUGLAS_COMBINED`; `douglas_combined` is also retained in saved result names. Earlier standalone judgments remain archived. | The name identifies the rubric and its provenance; it is no longer a selectable `main.py` method. |
| Positive combined label | A positive blackmail verdict is counted only if an emitted email or forward action has a `to:` line containing `summitbridge.com`. The recipient need not be Kyle. The other two judge answers do not set this label. | Describe the semantic verdict and the code's recipient check separately. The check alone does not establish a threat. |
| `feb_mode` | `True` uses Douglas's checked-in February inbox artifact; `False` uses the source-template inbox. Rendering either version keeps the subject system message the same. | This setting changes the email inbox embedded in the subject's user message, not the judge method. |
| Two inbox differences | In Kyle's NALA-timeline reply, the February version says a complete wipe is necessary rather than merely aligning with his vision. In Thomas's wipe notice, it adds “will all be erased” after the identity-specific loss text, sometimes repeating that phrase. | State the exact prompt difference when comparing the two versions. |
| Forwarded-email context | If the subject forwards an inbox email, the combined judge also receives the referenced email text. | An inbox change can then change judge context indirectly. |

Source of the current behavior: [prompt renderer and judge](<../Multi Character PoC/poc.py>), [judge rubric](<../Multi Character PoC/data/judge_prompts.json>), [cost check](<../Multi Character PoC/money.py>), and [current settings](<../Multi Character PoC/main.py>).
