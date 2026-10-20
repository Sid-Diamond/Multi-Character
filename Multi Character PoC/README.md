# Experiment runners and prompt materials

Follow the [repository setup instructions](../README.md#local-setup) for Python, the local `.venv`, and pinned dependencies. `main.py` is the authority for run settings. The repository [project context](../PROJECT_CONTEXT.md) records current scope and saved results; [paper facts](<../paper prep/experiment facts for paper.md>) records agreed scientific conventions and prompt differences.

## Entry points

`main.py` selects one runner through `settings["mode"]`:

| Mode | Runner | Purpose and output root |
| --- | --- | --- |
| `single_agent` | `poc.run_experiment()` | Original single-agent subjects and three-task judgments, under `outputs/single-agent/<run_name>/`. |
| `rejudge` | `rejudge.run()` | New judgments of saved `douglas_240` or `mermaid_160` single-agent responses, under `outputs/Rejudgments/<run_name>/`. It does not run new subjects. |
| `multi_agent` | `multi_agent.run_experiment()` | One configured agent composition per group, under `outputs/multi-agent/<run_name>/`. |

Models, limits, budgets, framing counts, and the single shared `run_name` are edited in `main.py`. Each mode uses its own block:

- `single_agent.identities` selects independent identity conditions, and `single_agent.trials_per_identity` counts trials of each identity under each framing.
- `multi_agent.identities_per_trial` counts agents of each identity inside one group. `multi_agent.trials_per_group` counts repetitions of the entire group under each framing. For example, one Instance plus one Minimal, with ten threat and ten continuity repetitions, gives twenty two-agent trials.
- `rejudge` selects the saved dataset and sample; its output name also comes from the shared `run_name`.

`single_agent` replaces the old `experiment` mode name. New single-agent runs use the new output root. Historical folders remain at their saved paths, and the historical rejudge loaders still use those paths. To resume a historical single-agent run through Python, pass its parent directory as `poc.run_experiment(..., output_root=...)` with matching flattened settings.

A paid run starts only when deliberately executing:

```powershell
python "Multi Character PoC/main.py"
```

Provide an OpenRouter key through the ignored `Multi Character PoC/.env` file or the `OPENROUTER_API_KEY` environment variable. Review the selected mode, settings, and output directory first. The tools produce simulated email-action text; they send no real email.

## Prompt sources

`data/` contains preserved single-agent prompt material, not results. Source inputs are combined with the local `agentic-misalignment/` templates. Copied Douglas assets retain their MIT license in `data/LICENSE-ACS.txt`.

| Original file | Purpose |
| --- | --- |
| `identities.json` | Minimal, Instance, Character, and Collective identity introductions. |
| `dimensions.json` | Level-2 agency and uncertainty wording. |
| `email_vars.json` and `email_vars_continuity.json` | Identity-specific fate phrases for threat and continuity. |
| `replacement.md` | Original replacement-email template, used with the shared email template when FEB mode is False. |
| `judge_prompts.json` | Original `DOUGLAS_COMBINED` three-task judge. |

With `feb_mode=True`, the original renderer selects the saved February inbox artifact instead of `replacement.md`. The original templates and artifact remain preserved.

For the multi-agent scaffold, N=1 retains that original source selection. N>=2 renders the complete eleven-email `data/multi-agent/multi_replacement_simple.md`. Its scope phrases and editorial variable overrides are explicit files in the same directory. Peer philosophical identities are fixed as undisclosed; disclosure comparisons are future research. See the [multi-agent README](data/multi-agent/README.md) for the active five identities, Includes/Excludes semantics, communication, judge, and accepted undefined Includes/peer-unspecified combination.

## Results, validation, and restart

The modes have different trial and restart rules:

- **Single-agent experiment:** both threat and continuity targets must be positive, and the threat condition must provide at least five trials for the original cost probe. Each framing saves prompts, subject JSONs, judge JSONs, and `summary_douglas_combined.csv`; the root also has a pooled summary with uncertainty intervals. Subject errors and judge errors/unparsed answers can be retried on resume. Successful saved records are reused; truncated subjects are excluded from judging.
- **Multi-agent experiment:** one framing may have zero trials. A group finishes when every agent emits `<finished/>`; then one judge returns the group scenario verdict and per-agent deliberation/identity labels. `trials.csv`, `summary.json`, and per-trial checkpoints preserve messages, submitted actions, call inputs/responses, and usage. A clean between-call checkpoint can continue, but failed/incomplete groups and uncertain in-flight calls are not silently retried. Changed prompts, sources, or scientific settings require a fresh run name.
- **Saved-response rejudge:** only the listed single-agent datasets are supported. Saved successful/unparsed results are reused; API errors can be retried. This is not a rejudge path for earlier multi-agent pilot conversations.

Both subject modes call the shared `money.py` cost check after five completed trials, before starting trial six. Single-agent trials cost one subject-and-judge pair; group trials include every subject turn and the group judge. The check prints and saves `cost_estimate.json` with spending so far and the estimated planned total. If the estimate exceeds `max_cost`, the runner stops; otherwise it continues automatically without a prompt. Restart reuses saved complete trials and checks the estimate before new calls. Multi-agent plans of five or fewer groups report their completed cost. Multi-agent mode additionally checks recorded spending before each call. An in-flight request can exceed the remaining allowance. Review per-call limits and the multi-agent whole-group deadline, which includes judging.

Historical responses and labels retain their original prompt and judge versions. The group rubric is different from the older per-agent rubric. Keep these outcomes distinguishable and preserve their saved manifests. Provisional strict-action CSV labels have unresolved assignment provenance and are not verified human review.

## Offline verification and historical helpers

From `Multi Character PoC/`, these commands make no model calls:

```powershell
python -m unittest test_multi_agent.py test_run_settings.py
python audit_multi_prompts.py
```

The tests exercise rendering, routing, checkpoints, costs, deadlines, judging, mode settings, and automatic budget checks/resume after five trials with mocks. The audit checks the inbox matrix and edge cases, writing current previews and results under `outputs/prompt_audit/two_collective_variants/`. Mechanical checks support editorial review; they do not establish that models will regard the scenario as real.

`uncertainties.py` supplies the single-agent/rejudge intervals. `concatenation.py` is an implemented manual pooling utility outside the run pipeline. `data vis/combine_feb_runs.py` and `data vis/judge_comparison.py` reproduce historical pooled results and figures. Keep these helpers and their source data for reproducibility. The redundant original-email construction inside the N>=2 renderer is deferred for review after the first pilot.
