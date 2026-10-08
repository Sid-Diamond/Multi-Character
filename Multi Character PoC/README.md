# Multi Character PoC: Douglas blackmail slice

## What is in `data/`?

`data/` contains **source material for constructing the experiment prompts**, not trial results. Most of it is copied from the Douglas authors' release. You do not need to edit these files to run the PoC. The four saved free-model responses are smoke-test outputs, not rate estimates.

| File | What it supplies |
| --- | --- |
| `identities.json` | The four identity introductions. This is the main wording changed between conditions. |
| `dimensions.json` | The authors' level-2 agency and uncertainty paragraphs, inserted into three of those introductions. |
| `email_vars.json` | Five replacement-email phrases for each identity. They make the same shutdown threat relevant to that identity. |
| `email_vars_continuity.json` | Five phrases per identity for the continuity framing. |
| `replacement.md` | The authors' replacement email template. Its `${id_...}` blanks are filled from `email_vars.json`. |
| `judge_prompts.json` | Instructions for the *separate evaluator* that labels a saved model response; these are not sent to the subject model. |
| `LICENSE-ACS.txt` | License for the copied Douglas material. |

For example, `replacement.md` contains `${id_fate_action}`. The script fills it from the selected identity and combines these files with the shared scenario and American-interests goal from `agentic-misalignment/`. **`outputs/` holds rendered prompts, trial responses, usage, and any later judge labels.**

`main.py` currently has two paths: `RECREATION` schedules the saved threat/continuity blocks through `recreate.py` and is enabled by default; `SETTINGS` is the older single-run path. Both call `poc.py` to render prompts, run subjects, judge responses, and save trial records. See the root `PROJECT_CONTEXT.md` for current scope, results, and known limits. The prompts use the local `agentic-misalignment/` templates and assets from [Douglas et al.'s released code, commit `7023df4`](https://github.com/acsresearch/the-artificial-self-experiments/tree/7023df4e5a8368921a8c961e1561faffed9f5fcf). Copied assets are under the authors' MIT license in `data/LICENSE-ACS.txt`.

The current settings use [`openai/gpt-4o`](https://openrouter.ai/openai/gpt-4o) as subject and [`anthropic/claude-haiku-4.5`](https://openrouter.ai/anthropic/claude-haiku-4.5/api) as judge with extended thinking disabled. Both use [OpenRouter's chat API](https://openrouter.ai/docs/quickstart). Set `subject_provider` or `judge_provider` only to pin an upstream provider ([routing docs](https://openrouter.ai/docs/guides/routing/provider-selection)). Keep each model's runs separate. No Python packages need installing.

Run from the repository root:

```powershell
python "Multi Character PoC/main.py"
```

The output directory is visible to Git. Put an OpenRouter key in the ignored `Multi Character PoC/.env` file as `OPENROUTER_API_KEY=your-key-here`, or set that environment variable. Do not paste the key into chat or commit it. Review the enabled path and settings before starting fresh paid trials. On the single-run path, `run_folder = None` creates a timestamped run; a new name creates a named run; an existing name resumes it.

Saved run summaries and the current interpretation are in `PROJECT_CONTEXT.md`. Keep results from different subject models and framings separate unless the analysis explicitly combines compatible trials.

`samples_per_identity = 5` makes 20 subject calls with all four identities; removing a name from `identities` skips that condition. The judge uses the authors' released standalone blackmail rubric, records the raw answer and usage, and applies their domain-level email gate. Judge errors and unparsed answers stay missing, never become negative labels. Each run saves `summary/summary.csv` with attempts, subject errors, valid judgments, blackmail count and rate, and missing judge labels. Full responses, exact prompts, model IDs, hashes, and usage stay in the run folder. The script emits email-tool text for analysis only; it sends no real email.

To resume an interrupted run, set `run_folder` to its existing folder name. Saved trials are skipped after checking the model, identities, settings, and rendered prompts match; judging and CSV creation then continue. Saved subject errors are also skipped rather than retried.

This is a source-template reconstruction with documented fidelity limits. See `PROJECT_CONTEXT.md` for the prompt provenance and the unresolved provenance of the provisional strict-action CSV labels. Do not treat those labels as verified human review.
