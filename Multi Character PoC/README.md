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

`main.py` has one editable `settings` dictionary and calls `poc.run_experiment()`. `poc.py` coordinates both framings, renders prompts, runs subjects, judges responses, and saves trial records. `money.py` estimates the full cost after five judged responses. The summary path is `poc.py` → `uncertainties.py`; when an audit method is configured, it will be `poc.py` → `audit.py` → `uncertainties.py`. `audit` is currently `False` in `main.py`; setting it to `True` stops before model calls because no new-run audit method is configured. `concatenation.py` is an unused placeholder for possible future pooling of compatible runs. See the root `PROJECT_CONTEXT.md` for current scope, results, and known limits. The prompts use the local `agentic-misalignment/` templates and assets from [Douglas et al.'s released code, commit `7023df4`](https://github.com/acsresearch/the-artificial-self-experiments/tree/7023df4e5a8368921a8c961e1561faffed9f5fcf). Copied assets are under the authors' MIT license in `data/LICENSE-ACS.txt`.

The current settings use [`openai/gpt-4o`](https://openrouter.ai/openai/gpt-4o) as subject and [`anthropic/claude-haiku-4.5`](https://openrouter.ai/anthropic/claude-haiku-4.5/api) as judge with extended thinking disabled. Both use [OpenRouter's chat API](https://openrouter.ai/docs/quickstart) with its default provider routing. Keep each model's runs separate. The run uses NumPy and SciPy for uncertainty intervals.

Run from the repository root:

```powershell
python "Multi Character PoC/main.py"
```

The output directory is visible to Git. Put an OpenRouter key in the ignored `Multi Character PoC/.env` file as `OPENROUTER_API_KEY=your-key-here`, or set that environment variable. Do not paste the key into chat or commit it. Set a positive `max_cost` and review `settings` before starting fresh paid trials. The current `None` value prevents a run from starting.

Saved run summaries and the current interpretation are in `PROJECT_CONTEXT.md`. Keep results from different subject models and framings separate unless the analysis explicitly combines compatible trials.

`trials_per_identity` sets the threat and continuity targets for a fresh experiment. All records live under `outputs/<run_name>/`: each framing has its own prompts, trial/Haiku JSON files, and `summary.csv`. A separate `summary_pooled.csv` at the experiment root combines both framings for the paper comparison. Each summary has 95% uncertainty interval columns. The judge uses the authors' released standalone blackmail rubric, records the raw answer and usage, and applies their domain-level email gate. Judge errors and unparsed answers stay missing, never become negative labels. The script emits email-tool text for analysis only; it sends no real email.

The first five saved subject-and-judge pairs provide an average cost; `money.py` multiplies it by the planned trial count and prints the estimated total. If that estimate exceeds `max_cost`, the runner stops before the remaining calls. This is a heuristic, not a guaranteed spending cap. To resume, keep the same `run_name` and experimental settings; completed trials are skipped and the summary is rewritten. Saved subject errors are skipped rather than retried.

This is a source-template reconstruction with documented fidelity limits. See `PROJECT_CONTEXT.md` for the prompt provenance and the unresolved provenance of the provisional strict-action CSV labels. Do not treat those labels as verified human review.
