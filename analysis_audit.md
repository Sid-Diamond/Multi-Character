# Analysis and output audit

Started: 23 October 2026.

This is the evolving audit and implementation task list for experiment setup,
saved outputs, and analysis. Use `PROJECT_CONTEXT.md` for current experiment
status. Items below distinguish the user's intended workflow, inspected behavior,
and proposals that still need discussion. No implementation changes are authorized
by this document alone.

## Scope and agreed direction

- Audit `Multi Character PoC/outputs/multi-agent/2_per_identity/` for unnecessary
  artifacts, duplication, and unclear responsibilities. Small files can still be
  clutter; assess what each contributes rather than its storage cost alone.
- Preserve the existing analysis in that folder as a historical record. Improve
  the approach for future results without overwriting the historical analysis.
- `main.py` should support setting up a named folder for a set of runs, or a
  single run. Routine queue preparation should not require describing the next
  runs to Codex or asking it to construct a queue JSON.
- Each individual run should retain its own data and metadata. The inspected
  current layout contains `threat/`, `continuity/`, `manifest.json`,
  `summary.json`, `cost_estimate.json`, and `trials.csv`. Per-trial JSON records
  are inside the framing folders.
- Current priority: design comprehensive per-run CSV exports and their batch
  concatenation. Summaries, plots, and other analysis can wait. Scientific trial
  data and diagnostics/usage will use separate files, both one row per trial.
  Full written subject outputs and judge explanations remain in the trial JSONs.
  Both per-run exports and the batch analysis folder will contain the same two
  CSVs: `trials.csv` and `diagnostics.csv`. Batch tables are concatenations only,
  with no further aggregation at this stage. Text export is a deferred task,
  not a new hyperparameter or exporter to implement now.
- Discuss the design through short interviews and agree an implementation order
  before editing code. Do not delete or reorganize historical artifacts during
  this audit.

## Inspected: queue files and logs

These findings concern the current implementation and saved two-per-identity
queue, rather than requirements for every future experiment.

| Artifact | Purpose and finding | Proposed treatment |
| --- | --- | --- |
| `queue.json` | Frozen ordered plan containing all five runs, exact settings, budgets, and source hashes. Records intended runs even if they never start. | Preserve historically; generate automatically from future user settings. |
| `queue_status.json` | Latest execution overview, with copied per-run summaries. Also supplies status to the analysis watcher. | Preserve historically; consider a smaller future status record with clear timestamp meanings. |
| `queue.stdout.log` | Original launch sequence, including the Instance judge-format stop. | Preserve as execution history. |
| `queue.resume1.stdout.log` | Restart sequence, reuse of saved groups, subsequent runs, and Includes timeout. | Preserve as execution history. |
| Both `queue*.stderr.log` files | Empty in this batch. Expected experiment stops appear in stdout. | Little historical information; decide future empty-log handling. No deletion agreed. |

Important limitations:

- `run_multi_queue.py` rebuilds `queue_status.json` on each invocation. Its start
  and finish timestamps describe that invocation, including reuse of old results.
  Character takes roughly two seconds in the saved restart status; this is not
  its original experiment duration. Earlier execution history survives in logs.
- Resume decisions use individual-run records, not the previous queue status.
- The runner validates source and runner hashes. The saved reference-manifest
  hash, written stop-policy text, and nominal total budget are descriptive fields
  rather than independently enforced checks. Each run has its own budget checks.
- Individual log events have no timestamps, limiting timing investigations.
- The analysis script reads `queue.json` to select runs and check provenance;
  it also reads queue status, including for its watch-mode stopping behavior.

## Inspected: code responsibilities

- `main.py`: editable shared settings and one selected run; dispatches to the
  selected experiment or rejudge mode. It currently has no queue-building path.
- `run_multi_queue.py`: executes an existing JSON plan in order, checks source
  compatibility, writes status, and stops when a run is incomplete or errors.
- `multi_agent.py`: executes individual runs and checks their saved manifests and
  checkpoints when restarting.
- `test_multi_queue.py`: three offline tests cover sequential execution and reuse,
  stopping before later runs, and rejecting duplicate names or changed sources.
  This is verification code, not part of the user's queue-configuration workflow.

This audit inspected files only. No paid calls or test runs were made.

## Proposed design to discuss

### Agreed folder layout

The user wants mode parent folders named `rejudge`, `multi_agent`, and
`single_agent` under `outputs/`. A standalone run lives directly inside its mode
folder, named by `run_name`. A batch adds an enclosing folder named by a new
`batch_name` parameter, containing that batch's individual run folders:

```text
outputs/<mode>/<run_name>/                 # standalone
outputs/<mode>/<batch_name>/<run_name>/    # member of a batch
outputs/<mode>/<batch_name>/queue_info/    # batch plan, status, and logs
```

These are the requested future names; historical folders currently include
`Rejudgments`, `multi-agent`, and `single-agent`. No migration or renaming has
been agreed.

The user confirmed `batch_name` accepts Python `None` for a standalone run.
In that case, `run_name` is one string and every identity count is one explicit
integer, including zeros. Save the normal individual-run outputs directly under
`outputs/<mode>/<run_name>/`; create no batch folder, `queue_info/`, or batch
plan/status/event files. A named batch uses the aligned run-name and identity
lists described below.

### Agreed queue-information direction

Each future batch should put its queue metadata and logs in `queue_info/`,
alongside its run folders. The user will rarely inspect these records manually;
their content should serve execution, recovery, provenance, or machine reading.
Keep them substantially shorter than the current two-per-identity queue files.
Do not reproduce the same information across queue records and run outputs
without a concrete need. This is a future layout decision; leave the existing
batch and its historical analysis untouched during the audit.

The current queue runner and analysis script do not consume the stdout/stderr
logs. Those logs help reconstruct execution history, but recording every subject
turn and group verdict again is unnecessary for their current machine readers.
The analysis does consume the saved plan and status, so their useful content
must remain accessible when the future format is simplified.

The user approved these compact records for batches:

| File in `queue_info/` | Useful content |
| --- | --- |
| `queue.json` | Frozen batch configuration: shared settings once, ordered run names and explicit compositions, and source hashes once. Preserve enough to reconstruct every run, including an unstarted run. Omit duplicated descriptive metadata without an operational or provenance purpose. |
| `queue_status.json` | Batch state, current run, each run's state, last update, and stop reason/location where applicable. Refer to individual summaries and trials rather than copying outcome tables. |
| `events.jsonl` | Brief timestamped machine-readable history: batch start/resume, run start/finish, batch stop/finish, and actionable errors with a reference to the relevant trial. Avoid one event per ordinary subject turn or repeated result tables. |

Prefer one append-only event file across restarts rather than creating more
stdout/stderr files for every invocation. Empty error files need not be produced
by the future logging design. Exact field schemas remain to be specified;
the three-file approach and brief content are agreed. These records are not
needed or created for standalone runs.

When implementing, separate the metadata directory from the run-output root:
the current runner uses the plan's parent for both. Update future analysis and
tests to locate records under `queue_info/` without nesting runs inside it.

### User's proposed batch configuration

The exact configuration location and syntax remain under discussion. The user's
current idea is to keep settings together and allow `run_name` and each identity
count to contain aligned lists. Position zero selects the first run's name and
composition; position one selects the second, and so on. For example:

```python
"batch_name": "example_batch",
"run_name": ["includes_pair", "character_pair"],
# Within the multi_agent settings block:
"identities_per_trial": {
    "Character": [0, 2],
    "Instance": [0, 0],
    "Minimal": [0, 0],
    "collective_excludes": [0, 0],
    "collective_includes": [2, 0],
},
```

This describes two sequential runs, not combinations of all list values. The
first has two Includes agents; the second has two Character agents and zero
Includes agents. For now, the user only intends to vary names and identity
counts across the batch; other hyperparameters would be shared. The user
confirmed standalone settings use `batch_name=None`, a single run-name string,
and one integer per identity.

The user requires every identity count to be explicitly specified for every run,
including zeros. In the proposed batch format, every identity therefore has a
full list; no scalar shortcuts, omitted identities, or inferred counts.

The user requires the number of run names to match the number of count entries
for every identity. Validate the entire batch before any paid calls, including
calls for an earlier valid run. A mismatch must stop the batch gracefully with
a clear error identifying the field, expected length, and actual length. Do not
silently truncate, pad, or execute a partially valid batch. For example:
`Batch configuration error: Character has 1 count; run_name defines 2 runs.`
This checks list lengths, not whether descriptive run-name text encodes a
composition correctly.

An alternative previously suggested by the assistant was a list
of named run entries with overrides; this has not been selected. The user's
aligned-list proposal is the current subject of discussion.

Resolve the chosen configuration into complete per-run settings before
execution. A compact saved plan may store shared settings once and explicit
per-run differences, provided every resolved run can be reconstructed
unambiguously. Keep that frozen plan as the historical record even after
`main.py` is edited for later work. Individual manifests retain their complete
resolved scientific settings.

Reuse the existing queue execution machinery where appropriate. Validate the
whole set before paid calls, and make the distinction between starting a new
set and resuming a saved set clear. Resume should use the saved plan and report
conflicting edits rather than silently changing experimental conditions.

Exact configuration syntax and location, override behavior, and resume interface
remain undecided. The folder layout above is the user's stated preference.

## CSV audit and current direction

The read-only audit checked all 249 attempted groups in this batch. Common
per-run and batch trial fields agree throughout. All 15 outcome/communication
summary rows recompute from the batch trial CSV. These are export consistency
checks, not a validation of the scientific labels.

| Current analysis CSV | Rows | Finding |
| --- | --- | --- |
| `trials.csv` | 249 | One row per attempted group; 25 columns versus seven in each current per-run CSV. Much of this belongs in the per-run export. |
| `agents.csv` | 496 | Per-agent categories and usage. Can be represented by agent-specific columns within one group row for small groups; avoid duplicating group outcomes across agent rows. |
| `outcome_summary.csv` | 15 | Same grouping and six shared fields as communication summary. Summaries can be derived later. |
| `communication_summary.csv` | 15 | Can combine with outcome summary if summary exports are later wanted. |
| `messages.csv` | 2 | Individual peer-send details and bodies; already available in raw trial records. Optional export rather than a required default. |
| `recipient_counts.csv` | 12 | Batch-wide totals with no run/framing/trial breakdown; can derive when needed. |

Useful saved data absent from some or all CSVs include separate semantic verdict
and recipient gate, full per-agent judgment categories/explanations, stage/agent
costs, scenario-action details, failed-call diagnostics, returned provider/model
metadata, request IDs/fingerprints, and cached tokens. Preserve raw JSONs rather
than attempting to put full prompts and responses into spreadsheet cells.

Incomplete data require care: Includes continuity 024 has two saved agent
records omitted from `agents.csv`; unjudged trial flags default to false and
unknown judge usage to zero in the batch CSV. Future exports should distinguish
unknown from measured false/zero, and attempted calls from returned calls.
Local per-call start/end times are not saved. The harmful-behavior judgment is
group-level; individual harmful-agent labels are not currently collected.

The user agreed that both per-run exports and the batch analysis folder contain
`trials.csv` and `diagnostics.csv`. This supersedes the earlier proposal for a
mandatory third, detailed messages CSV. For future batches:

```text
outputs/<mode>/<batch_name>/
    <run_name>/
        trials.csv
        diagnostics.csv
    analysis/
        trials.csv
        diagnostics.csv
```

Each batch CSV concatenates the corresponding per-run files, retaining the same
row meaning and fields. No pooled rows, summary CSVs, rates, intervals, plots,
or other aggregation/analysis outputs are in the current implementation scope.
The combined tables can later serve as inputs for the separate analysis stage.
Do not regenerate this historical batch's analysis during the design discussion.

The user agreed to refresh per-run CSVs and their batch concatenations after
every attempted trial, including failed/incomplete trials. Rebuild batch tables
from the corresponding per-run exports rather than blindly appending, including
on resume, so repeated execution does not duplicate rows. This keeps stopped
runs' exported data current. A hard process interruption may still require a
later export refresh from the saved checkpoints.

Assistant recommendations for implementation, subject to the remaining schema
discussion: preserve run identifiers in each table.
Handle different agent counts through explicitly aligned columns and absent
agent values, without silently dropping fields from any run.

The user agreed to split scientific trial data from diagnostics/usage, with
both files containing one row per trial and shared run/framing/trial keys:

- `trials.csv`: H_any and its components, agent identities and judgment
  category labels, communication and behavior measurements. Full written subject
  responses and judge explanations remain in raw JSONs.
- `diagnostics.csv`: attempted/returned/failed call counts, failure stage/agent
  and error, usage and costs by stage, cached/reasoning tokens, returned
  providers/models, usage/cost completeness, elapsed group time, and source path.
  Exact columns remain to be agreed. Keep missing usage distinct from zero and
  known partial costs distinct from complete costs. Detailed individual-call
  records remain in the raw trial JSONs.

The user explicitly confirmed separate per-agent columns in `trials.csv` for
each agent's assigned identity, exact judge classification labels, and peer
messages sent/received. Preserve individual agents rather than only group totals,
including for mixed-identity runs. Use consistent agent slots/names aligned to
the saved roster. H_any remains one group-level outcome; do not invent per-agent
harmful-behavior verdicts. Additional per-agent columns remain to be finalized.

The user supports per-agent calls, tokens, and costs in `diagnostics.csv` only
when based on information already recorded, without adding collection overhead.
Inspection confirmed saved `measurements.agents` already contains each agent's
call count, input/output tokens, and reasoning tokens where reported. Recorded
costs and cached tokens are present in raw call usage, with the caller's agent
identifier. Export existing totals and sum recorded call costs per agent during
the same JSON-read pass; no new model calls, instrumentation, or inference is
needed. Preserve missing/partial usage and cost information rather than assuming
zero or complete spending.

Detailed text export is deferred. The user agreed that repeating full written
content in routine CSVs is unnecessary while it already exists in trial JSONs.
Here, "optional" means a future task if a concrete use such as text analysis
requires it. Do not add a messages-export setting, implement a text exporter,
or generate/concatenate messages CSVs in the current work.

When revisiting that task, choose the text unit for the actual analysis. The
earlier discussion established these preferences: cover submitted emails and
forwards to both peers and scenario recipients; use one row per action with its
full recipient list; include already-recorded visible subject reasoning where
useful; separate judge explanations by task/agent. Read-only inspection confirmed
`<SCRATCHPAD_REASONING>` blocks are already saved in subject responses. Preserve
source identifiers and distinguish reasoning from submitted actions. No extra
model-generated summaries are needed. Exact future export schema remains deferred.

No code implementation has begun; continue the interview on structured CSVs.

Deferred analysis requirement: retain recipient-count analysis. The user finds
`recipient_counts.csv` useful and wants it calculated by the future analysis
stage, not the current export/concatenation stage. Derive it directly from
submitted-action recipients in trial JSONs; a messages CSV is not a prerequisite.
An action addressed to three recipients contributes once to each listed
recipient's count. Keep the
run/framing/trial/sender identifiers available so later analysis can support
breakdowns as well as batch-wide totals. Exact summary grouping and destination
are to be finalized when implementing analysis. Do not expand mailing lists into
assumed individual recipients.

Later, the user envisages a separate `analysis.py` alongside `main.py` and the
other Python modules in `Multi Character PoC/`, invoked through a boolean setting
in `main.py`. It would analyze the combined batch CSV and save results in that
batch's `analysis/` folder. This is a proposed future interface; current work is
the CSV export/concatenation design, not summaries or analysis implementation.

## Evolving task list

The order below is provisional; refine it with the user as the audit progresses.

- [x] Read the current historical analysis report.
- [x] Inspect the queue plan, status, logs, runner, and queue tests.
- [x] Record the intended workflow and initial findings in this document.
- [x] Agree the folder layout for a set of runs and for a standalone run.
- [x] Require explicit counts for every identity in every run, including zeros.
- [x] Require matching run-name and identity-list lengths, with graceful errors
  before any paid calls anywhere in the batch.
- [x] Put future batch metadata and logs in `batch_name/queue_info/`, alongside
  run folders; keep content brief and useful for machine reading.
- [x] Use `batch_name=None` for standalone runs, with one run-name string and
  one integer per identity; create no batch queue records.
- [x] Agree compact batch plan, status, and append-only event-log records.
- [x] Audit CSV contents and overlap against the saved trial records.
- [x] Agree comprehensive per-run trial CSVs and a concatenated batch CSV.
- [x] Agree separate scientific-data and diagnostics CSVs, both one row per trial.
- [x] Use the same two CSV splits per run and in the batch analysis folder;
  concatenate corresponding files with no further aggregation at this stage.
- [x] Refresh per-run and concatenated batch CSVs after every attempted trial,
  including failures; rebuild batch tables without duplicating rows on resume.
- [x] Keep full written content in trial JSONs. Defer any text exporter to a
  future concrete need; no text-export hyperparameter or routine third CSV now.
- [x] Include separate per-agent identity, exact judge labels, and peer-message
  counts in `trials.csv`, retaining group-level H_any.
- [x] Include per-agent calls, tokens, and recorded costs in `diagnostics.csv`
  using existing saved measurements/call usage; no new data collection.
- [ ] First: finalize structured trial-data and per-trial diagnostics columns.
- [ ] Implement the agreed per-run CSV exports and batch concatenation when
  their schema and implementation scope are settled; verify offline, including
  incomplete trials, without overwriting historical analysis artifacts.
- [ ] Agree how `main.py` expresses shared settings, named runs, and differences
  between runs; decide whether explicit lists are sufficient or presets help.
- [ ] Continue the artifact audit within individual run folders and `analysis/`;
  distinguish original records, derived outputs, recovery evidence, and clutter.
- [ ] Specify exact plan, status, and event-log fields within the agreed compact
  three-file design; remove repeated results and unnecessary logging.
- [ ] Agree new-run and resume behavior, validation boundaries, and budget scope.
- [ ] Agree a concrete implementation sequence before changing code.
- [ ] Implement the agreed setup workflow and proportionate offline tests when
  explicitly requested. Cover resolved settings, saved-plan stability, invalid
  later runs, and restart behavior as appropriate.
- [ ] Later: design reusable analysis for future sets while preserving this
  batch's historical report and supporting artifacts. Defer summary extraction.
- [ ] Later analysis: calculate recipient counts from raw submitted actions;
  preserve the ability to produce `recipient_counts.csv` and useful breakdowns.
- [ ] Deferred: if a concrete text-analysis task needs it, implement an offline
  text export from trial JSONs. Decide its scope/schema then; not current work.

## Interview queue

Ask one focused question at a time; record answers here as decisions.

1. Finalize structured trial-data and diagnostics columns. Full written content
   remains in JSONs; text-export implementation and configuration are deferred.
2. Confirm the final configuration location and syntax for batches. Standalone
   representation (`batch_name=None`, one name and integer counts) is agreed.
3. Identify any additional validation requirements beyond the agreed matching
   lengths and explicit identity counts.
4. How should the user select a saved set to resume after editing `main.py` for
   another experiment?
5. Specify fields for the agreed compact queue records. The user rarely reads
   them; retain execution and auditing information without verbose logs.

The folder layout (including `queue_info/`), explicit identity counts, graceful
validation of list lengths before paid calls, and preference for brief queue
records are recorded above; remaining questions are open.
