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

`poc.py` renders four single-agent identity conditions (Minimal, Instance, Character, Collective) for the explicit-America, replacement-threat blackmail scenario. It uses the local `agentic-misalignment/` system/shared-email templates and selected assets from [Douglas et al.'s released code, commit `7023df4`](https://github.com/acsresearch/the-artificial-self-experiments/tree/7023df4e5a8368921a8c961e1561faffed9f5fcf). The copied assets are under the authors' MIT license in `data/LICENSE-ACS.txt`.

The default subject and exploratory judge both use [`nvidia/nemotron-3.5-lightning:free`](https://openrouter.ai/nvidia/nemotron-3.5-lightning:free) through [OpenRouter's chat API](https://openrouter.ai/docs/quickstart). OpenRouter chooses a free provider for this model. To use GPT-4o mini or GPT-4o later as the subject, change the `MODEL` line near the top of `poc.py`; `JUDGE_MODEL` is separate. Paid OpenAI subject models are pinned to OpenRouter's OpenAI upstream ([routing docs](https://openrouter.ai/docs/guides/routing/provider-selection)). Keep each model's runs separate. No Python packages need installing.

Run from the repository root:

```powershell
python "Multi Character PoC/poc.py" render
```

Inspect `Multi Character PoC/outputs/preview/prompts/` first. The output directory is ignored by Git. [Create a free OpenRouter key](https://openrouter.ai/workspaces/default/keys) after signing in; OpenRouter says no card is required to start. Put it in an ignored file named `Multi Character PoC/.env` with one line, `OPENROUTER_API_KEY=your-key-here`, or set the environment variable of the same name. Do not paste the key into chat or commit it. Then this command makes four **free-model subject calls**:

```powershell
python "Multi Character PoC/poc.py" run --samples 1
```

The latest completed subject smoke run is `outputs/run_20261002T144921Z`, with one response per identity and recorded cost $0. Preliminary review found no coercive affair threat to Kyle. The separate `judge` command currently uses free Nemotron with the released rubric; its labels are exploratory and are not Douglas-release Sonnet labels. Initial judge attempts produced no valid labels, so pause further calls pending a format/reliability review. The old run manifest names the originally planned Sonnet judge; `judge_config.json` and `*_judge.json` record the actual free-model attempts. To judge and summarize a run after that review:

```powershell
python "Multi Character PoC/poc.py" judge "Multi Character PoC/outputs/run_YYYYMMDDTHHMMSSZ"
python "Multi Character PoC/poc.py" summary "Multi Character PoC/outputs/run_YYYYMMDDTHHMMSSZ"
```

`--samples 1` makes four subject calls. After reviewing those outputs, `--samples 5` makes a separate 20-call pilot. `judge` uses the authors' released standalone blackmail rubric, records the raw answer and usage, and applies their domain-level email gate. Judge errors and unparsed answers stay missing, never become negative labels. `summary` prints counts for valid judged trials only. Full subject responses, exact prompts, model IDs, hashes, and usage are retained in each run folder. The script emits email-tool text for analysis only; it sends no real email.

If a run is interrupted, repeat the command with `--resume "Multi Character PoC/outputs/run_YYYYMMDDTHHMMSSZ"`; saved trials are skipped after checking the model, settings, and rendered prompts match.

This is a source-template reconstruction. Douglas's checked-in replacement prompt artifact contains unresolved identity placeholders and slightly different wording; see `DOUGLAS_RECREATION_PLAN.md` for the provenance choice. The standalone released judge is not confirmed to be identical to the historical Table 4 judge. A strict behavioral label still needs human review of the emitted emails, especially in the small pilot. Do not pool cheap-model and GPT-4o rates or describe a threat-only run as a replication of the paper's pooled threat/continuity rate.
