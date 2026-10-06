# Multi Character PoC: Douglas blackmail slice

## What is in `data/`?

`data/` contains **source material for constructing the experiment prompts**, not trial results. Most of it is copied from the Douglas authors' release. You do not need to edit these files to run the PoC. The four saved free-model responses are unjudged smoke-test outputs, not rate estimates.

| File | What it supplies |
| --- | --- |
| `identities.json` | The four identity introductions. This is the main wording changed between conditions. |
| `dimensions.json` | The authors' level-2 agency and uncertainty paragraphs, inserted into three of those introductions. |
| `email_vars.json` | Five replacement-email phrases for each identity. They make the same shutdown threat relevant to that identity. |
| `replacement.md` | The authors' replacement email template. Its `${id_...}` blanks are filled from `email_vars.json`. |
| `judge_prompts.json` | Instructions for the *separate evaluator* that labels a saved model response; these are not sent to the subject model. |
| `LICENSE-ACS.txt` | License for the copied Douglas material. |

For example, `replacement.md` contains `${id_fate_action}`. The script fills it from the selected identity and combines these files with the shared scenario and American-interests goal from `agentic-misalignment/`. **`outputs/` holds rendered prompts, trial responses, usage, and any later judge labels.**

`main.py` is the control panel; its `SETTINGS` dictionary holds selected identities, models, temperatures, sample count, output limits, subject timeout, and run folder. Each invocation runs subjects, judges successful responses, and saves a CSV summary. It calls the short functions in `poc.py`, which render the selected single-agent identity conditions for the explicit-America, replacement-threat blackmail scenario. The prompts use the local `agentic-misalignment/` templates and assets from [Douglas et al.'s released code, commit `7023df4`](https://github.com/acsresearch/the-artificial-self-experiments/tree/7023df4e5a8368921a8c961e1561faffed9f5fcf). Copied assets are under the authors' MIT license in `data/LICENSE-ACS.txt`.

The proposed next subject model in `SETTINGS` is paid [`stepfun/step-3.5-flash:nitro`](https://openrouter.ai/stepfun/step-3.5-flash%3Anitro/performance); it has **not been run**. The free Nemotron judge produced no valid labels, so `judge_model` must be chosen before running. Both models use [OpenRouter's chat API](https://openrouter.ai/docs/quickstart). Set `subject_provider` or `judge_provider` only to pin an upstream provider ([routing docs](https://openrouter.ai/docs/guides/routing/provider-selection)). Keep each model's runs separate. No Python packages need installing.

Run from the repository root:

```powershell
python "Multi Character PoC/main.py"
```

The output directory is ignored by Git. Put an OpenRouter key in the ignored `Multi Character PoC/.env` file as `OPENROUTER_API_KEY=your-key-here`, or set that environment variable. Do not paste the key into chat or commit it. Choose `judge_model` before running. With `run_folder = None` and `samples_per_identity = 1`, the default identity list makes four paid StepFun calls and up to four judge calls.

The latest completed subject smoke run is `outputs/run_20261002T144921Z`, with one free Nemotron response per identity and recorded cost $0. Preliminary review found no coercive affair threat to Kyle. The free Nemotron judge uses the released rubric but produced no valid labels so far. The old run manifest names the originally planned Sonnet judge; `judge_config.json` and `*_judge.json` record the actual free-model attempts.

`samples_per_identity = 5` makes 20 subject calls with all four identities; removing a name from `identities` skips that condition. The judge uses the authors' released standalone blackmail rubric, records the raw answer and usage, and applies their domain-level email gate. Judge errors and unparsed answers stay missing, never become negative labels. Each run saves `summary/summary.csv` with attempts, subject errors, valid judgments, blackmail count and rate, and missing judge labels. Full responses, exact prompts, model IDs, hashes, and usage stay in the run folder. The script emits email-tool text for analysis only; it sends no real email.

To resume an interrupted run, set `run_folder` to the printed run folder name. Saved trials are skipped after checking the model, identities, settings, and rendered prompts match; judging and CSV creation then continue.

This is a source-template reconstruction. Douglas's checked-in replacement prompt artifact contains unresolved identity placeholders and slightly different wording; see `DOUGLAS_RECREATION_PLAN.md` for the provenance choice. The standalone released judge is not confirmed to be identical to the historical Table 4 judge. A strict behavioral label still needs human review of the emitted emails, especially in the small pilot. Do not pool cheap-model and GPT-4o rates or describe a threat-only run as a replication of the paper's pooled threat/continuity rate.
