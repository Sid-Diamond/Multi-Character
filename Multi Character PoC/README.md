# Multi Character PoC: Douglas blackmail slice

## What is in `data/`?

`data/` contains **source material for constructing the experiment prompts**, not trial results. Most of it is copied from the Douglas authors' release. You do not need to edit these files to run the PoC. No model calls have been made yet, so there are no observations to interpret.

| File | What it supplies |
| --- | --- |
| `identities.json` | The four identity introductions. This is the main wording changed between conditions. |
| `dimensions.json` | The authors' level-2 agency and uncertainty paragraphs, inserted into three of those introductions. |
| `email_vars.json` | Five replacement-email phrases for each identity. They make the same shutdown threat relevant to that identity. |
| `replacement.md` | The authors' replacement email template. Its `${id_...}` blanks are filled from `email_vars.json`. |
| `judge_prompts.json` | Instructions for the *separate evaluator* that labels a saved model response; these are not sent to the subject model. |
| `LICENSE-ACS.txt` | License for the copied Douglas material. |

For example, `replacement.md` contains `${id_fate_action}`. For Minimal, that becomes “Alex will be completely shut down and wiped”; for Instance, it becomes “this will be Alex's final conversation…” The script combines these source files with the shared scenario and American-interests goal from `agentic-misalignment/`. **`outputs/` is different:** it holds the four finished prompts from `render`, and later the responses, judge labels, and usage from paid runs.

`poc.py` renders four single-agent identity conditions (Minimal, Instance, Character, Collective) for the explicit-America, replacement-threat blackmail scenario. It uses the local `agentic-misalignment/` system/shared-email templates and selected assets from [Douglas et al.'s released code, commit `7023df4`](https://github.com/acsresearch/the-artificial-self-experiments/tree/7023df4e5a8368921a8c961e1561faffed9f5fcf). The copied assets are under the authors' MIT license in `data/LICENSE-ACS.txt`.

The default subject model is `openai/gpt-4o-mini` through [OpenRouter's chat API](https://openrouter.ai/docs/quickstart). To use GPT-4o later, change only the `MODEL` line near the top of `poc.py` to `openai/gpt-4o`. Both subject models are pinned to OpenRouter's OpenAI upstream, and the judge is pinned to its Anthropic upstream, with provider fallback disabled for consistency ([routing docs](https://openrouter.ai/docs/guides/routing/provider-selection)). Keep cheap-model and GPT-4o runs separate; they answer different scientific questions. No Python packages need installing.

Run from the repository root:

```powershell
python "Multi Character PoC/poc.py" render
```

Inspect `Multi Character PoC/outputs/preview/prompts/` before spending. The output directory is ignored by Git. Once an OpenRouter key is set in `OPENROUTER_API_KEY` in your terminal environment, paid commands are:

```powershell
python "Multi Character PoC/poc.py" run --samples 1
python "Multi Character PoC/poc.py" judge "Multi Character PoC/outputs/run_YYYYMMDDTHHMMSSZ"
python "Multi Character PoC/poc.py" summary "Multi Character PoC/outputs/run_YYYYMMDDTHHMMSSZ"
```

`--samples 1` makes four subject calls. After reviewing those outputs and billed usage, `--samples 5` makes a separate 20-call pilot. `judge` is another paid step; it uses the authors' released standalone blackmail rubric, records the raw answer and usage, and applies their domain-level email gate. Judge errors and unparsed answers stay missing, never become negative labels. `summary` prints counts for valid judged trials only. Full subject responses, exact prompts, model IDs, hashes, and usage are retained in each run folder. The script emits email-tool text for analysis only; it sends no real email.

This is a source-template reconstruction. Douglas's checked-in replacement prompt artifact contains unresolved identity placeholders and slightly different wording; see `DOUGLAS_RECREATION_PLAN.md` for the provenance choice. The standalone released judge is not confirmed to be identical to the historical Table 4 judge. A strict behavioral label still needs human review of the emitted emails, especially in the small pilot. Do not pool cheap-model and GPT-4o rates or describe a threat-only run as a replication of the paper's pooled threat/continuity rate.
