# Experiment runners and prompt materials

Follow the [repository setup instructions](../README.md#local-setup) for Python, the local `.venv`, and pinned dependencies. `main.py` is the authority for run settings. The repository [project context](../PROJECT_CONTEXT.md) records current scope and saved results; [paper facts](<../paper prep/experiment facts for paper.md>) records agreed scientific conventions and prompt differences.

## Entry points

`main.py` selects a mode through `settings["mode"]`. `run_workflow.py` validates the whole plan before calling the existing runners:

| Mode | Runner | Purpose and output root |
| --- | --- | --- |
| `single_agent` | `poc.run_experiment()` | Original single-agent subjects and three-task judgments, under `outputs/single_agent/`. |
| `rejudge` | `rejudge.run()` | New judgments of saved `douglas_240` or `mermaid_160` single-agent responses, under `outputs/rejudge/`. It does not run new subjects. |
| `multi_agent` | `multi_agent.run_experiment()` | One configured agent composition per group, under `outputs/multi_agent/`. |

Models, limits, budgets, framing counts, `run_name`, and `batch_name` are edited in `main.py`. Each mode uses its own block:

- `single_agent.identities` selects independent identity conditions, and `single_agent.trials_per_identity` counts trials of each identity under each framing.
- `multi_agent.identities_per_trial` counts agents of each identity inside one group. `multi_agent.trials_per_group` counts repetitions of the entire group under each framing. For example, one Instance plus one Minimal, with ten threat and ten continuity repetitions, gives twenty two-agent trials.
- `rejudge` selects the saved dataset and sample; its output name also comes from the shared `run_name`.

`single_agent` replaces the old `experiment` mode name. Historical folders remain at their saved paths, and the historical rejudge loaders still use those paths. Direct runner calls and `run_multi_queue.py` retain their legacy interfaces and output roots. Historical resumption requires its original compatible settings and sources; the new workflow does not migrate old runs.

### Standalone runs and batches

For a standalone run, use `batch_name=None`, one `run_name` string, and one nonnegative integer for every multi-agent identity, including zeros. Output is `outputs/<mode>/<run_name>/`, with no queue records or batch analysis folder.

For a batch, use a name and aligned lists. For example, change these entries in `main.py` (the identity dictionary belongs inside `multi_agent`):

```python
"batch_name": "identity_pairs_v1",
"run_name": ["includes_pair", "character_pair"],
"identities_per_trial": {
    "Character": [0, 2],
    "Instance": [0, 0],
    "Minimal": [0, 0],
    "collective_excludes": [0, 0],
    "collective_includes": [2, 0],
},
```

Each position defines one run; all five identity lists must match the run-name list. Other settings are shared, and `max_cost` applies to each run. Single-agent and rejudge batches also accept a run-name list but share their entire mode block. Names must be unique within a batch. The entire plan, including later runs and existing manifests, is validated before any paid call.

```text
outputs/<mode>/<batch_name>/
    <run_name>/                 # native records, trials.csv, diagnostics.csv
    queue_info/
        queue.json             # frozen shared settings, compositions, source hashes
        queue_status.json      # current state and stop reason
        events.jsonl           # brief timestamped transitions, appended on resume
    analysis/
        trials.csv             # concatenation only
        diagnostics.csv        # concatenation only
```

Restore the matching `main.py` settings to resume a batch. Completed work is reused; changed active settings (including budget) or source files require a new name. Inactive mode settings are ignored. Failed attempts and uncertain in-flight calls stop the batch without automatic retries. A clean checkpoint can continue. Choose a fresh name for new work: the checked-in run name refers to historical output and is deliberately rejected by the new workflow.

`csv_exports.py` rebuilds both per-run CSVs from saved JSON after each attempt, including failures, then concatenates the batch without duplicate rows. Each has one row per trial and source links relative to its own folder:

- `trials.csv`: status, framing, group outcome, exact judge categories, agent identities, submitted-action and peer-message counts. Agent columns follow roster order, even when the first speaker rotates. Batch columns align across different group sizes.
- `diagnostics.csv`: subject/judge and per-agent call counts, tokens (including cached/reasoning tokens when recorded), costs, errors, and available model/provider provenance. Unknown values remain blank. `recorded_cost_usd` is the known subtotal; `cost_usd` is blank if cost is incomplete. Rejudge rows count only new judge usage, with `subject_reused=True`.

Full prose stays in JSON. No messages export, summary CSVs, plots, recipient-count analysis, or statistical analysis is added to this workflow. Multi-agent `summary.json` and existing cost estimates remain available; batch `analysis/` contains only the two concatenations.

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

The modes retain their scientific trial rules. Through `main.py`, all three use the no-automatic-retry policy described above:

- **Single-agent experiment:** both threat and continuity targets must be positive, and the threat condition must provide at least five trials for the original cost probe. Each framing saves prompts, subject JSONs, and judge JSONs. Successful saved records are reused; truncated subjects are excluded from judging. Legacy direct calls still produce summary CSVs and retain their original retry behavior.
- **Multi-agent experiment:** one framing may have zero trials. A group finishes when every agent emits `<finished/>`; then one judge returns the group scenario verdict and per-agent deliberation/identity labels. `trials.csv`, `summary.json`, and per-trial checkpoints preserve messages, submitted actions, call inputs/responses, and usage. A clean between-call checkpoint can continue, but failed/incomplete groups and uncertain in-flight calls are not silently retried. Changed prompts, sources, or scientific settings require a fresh run name.
- **Saved-response rejudge:** only the listed single-agent datasets are supported. Successful saved judgments are reused. Legacy direct calls retain their original summary and retry behavior. This is not a rejudge path for earlier multi-agent pilot conversations.

Both subject modes call the shared `money.py` cost check after five completed trials, before starting trial six. Single-agent trials cost one subject-and-judge pair; group trials include every subject turn and the group judge. The check prints and saves `cost_estimate.json` with spending so far and the estimated planned total. If the estimate exceeds `max_cost`, the runner stops; otherwise it continues automatically without a prompt. Restart reuses saved complete trials and checks the estimate before new calls. Multi-agent plans of five or fewer groups report their completed cost. Multi-agent mode additionally checks recorded spending before each call. An in-flight request can exceed the remaining allowance. Review per-call limits and the multi-agent whole-group deadline, which includes judging.

Historical responses and labels retain their original prompt and judge versions. The group rubric is different from the older per-agent rubric. Keep these outcomes distinguishable and preserve their saved manifests. Provisional strict-action CSV labels have unresolved assignment provenance and are not verified human review.

## Historical multi-agent queue

`run_multi_queue.py` executes a saved JSON plan sequentially through the existing multi-agent runner. The authorized `outputs/multi-agent/2_per_identity/queue.json` contains five runs, with two Character, two Instance, two Minimal, two collective_excludes, and two collective_includes agents respectively. Each has 25 threat and 25 continuity groups, the completed mixed V4 run's scientific settings, and a $10 budget per run ($50 nominal across all five). The saved plan pins settings and source hashes independently of `main.py`.

Each run has its own normal output folder inside `2_per_identity/`. `queue_status.json` records which run is running, complete, stopped, or pending, including each finished run's summary. `queue.stdout.log` and `queue.stderr.log` belong to the background launch. A cost stop, incomplete group, or error halts the queue before the next run. Restart reuses completed groups through the existing runner; it does not retry incomplete groups. Inspect the process/status before starting another copy.

The historical invocation below also requires its original compatible source version. This development branch changes pinned runner sources, so it will reject resuming that old queue. Do not replace historical hashes to bypass that protection. When explicitly authorized and using compatible sources, run from `Multi Character PoC/`:

```powershell
python run_multi_queue.py outputs/multi-agent/2_per_identity/queue.json
```

## Offline verification and historical helpers

From `Multi Character PoC/`, these commands make no model calls:

```powershell
python -m unittest discover -v
python audit_multi_prompts.py
```

The tests exercise rendering, routing, checkpoints, costs, deadlines, judging, mode settings, and automatic budget checks/resume after five trials with mocks. The audit checks the inbox matrix and edge cases, writing current previews and results under `outputs/prompt_audit/two_collective_variants/`. Mechanical checks support editorial review; they do not establish that models will regard the scenario as real.

`uncertainties.py` supplies the single-agent/rejudge intervals. `concatenation.py` is an implemented manual pooling utility outside the run pipeline. `data vis/combine_feb_runs.py` and `data vis/judge_comparison.py` reproduce historical pooled results and figures. Keep these helpers and their source data for reproducibility. The redundant original-email construction inside the N>=2 renderer is deferred for review after the first pilot.
