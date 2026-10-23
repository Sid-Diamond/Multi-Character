# Progress log - 23 October 2026

Closing documentation update based on the current source, manifests, checkpoints and offline checks. Earlier logs were not opened. Only `PROJECT_CONTEXT.md`, this log, and deletion of `analysis_audit.md` are part of this closeout. Code, prompts, settings, experiment outputs and running processes were left untouched. No model API calls were launched by the agent.

## Where we are at close

- Current branch is `master`, inspected at `bd03167` (`b4h n10`). The setup/export work formerly described as uncommitted on `batch-csv-workflow` is already in repository history.
- The user's modified `main.py` selects `comb4h_n10`; its output folder is new/untracked. The user is running the experiment separately. Do not start another copy or change its settings/sources.
- This batch plans five homogeneous two-agent runs (`char`, `inst`, `min`, `col_excl`, `col_incl`), each with 25 threat and 25 continuity groups. GPT-4o subjects use temperature 1 and 5,000 tokens; Sonnet 4.6 judging uses temperature 0 and 4,000 tokens. Both call timeouts are 300 seconds; group deadline is 600 seconds. Budget is $7 per run. Scope is `all_replaced`, FEB mode is enabled, communication is compulsory before emailing a human, and the requested message maximum is 10 per agent.
- At 17:16 UTC the saved snapshot had four complete Character threat trials, one positive, and trial 005 running; later runs were pending. The saved plan matched current resolved settings and source hashes. This is a timestamped live snapshot, not a final result or evidence of a stalled process. Read status again next session.

## Implemented setup/export work retained from analysis_audit

The audit document was stale as a current task list. These findings were checked against implementation before retiring it:

- `run_workflow.py` expands settings, validates all runs before calls, checks frozen plans/manifests, and dispatches all three modes. Single-agent and rejudge batches share their whole mode settings; multi-agent batches can additionally vary the five explicit identity counts.
- Standalone runs use `batch_name=None`, a scalar name and scalar counts. Batches use aligned name/count lists, including explicit zeros. Invalid names, duplicates, list lengths and compositions are rejected. Output paths are `outputs/<mode>/<run_name>/` or `outputs/<mode>/<batch_name>/<run_name>/`.
- Batch-only `queue_info/` contains the frozen plan (`format_version`, batch name, shared settings, ordered run differences, source hashes), compact status, and append-only timestamped events. Ordinary subject turns are not duplicated into those events.
- Resume requires matching active settings and sources, including budget. Completed work is reused. Retained failed trials and uncertain in-flight calls stop without automatic retries; a clean checkpoint can continue. Keyboard interruption records a stopped batch and refreshes exports. Forced termination may leave exports needing refresh.
- `csv_exports.py` produces `trials.csv` and `diagnostics.csv`, each with one row per attempted trial and shared run/framing/trial/source keys. It preserves incomplete trials, exact judge categories and roster-aligned per-agent identities, sends, receipts and submitted email/forward counts. H_any is group-level; no individual harmful-agent classification is invented.
- Diagnostics derive attempted/returned/failed/in-flight calls, tokens, cached/reasoning usage where present, errors, providers/models and per-stage/per-agent costs from saved records. Missing values remain unknown; recorded partial cost is distinct from complete cost. Rejudge diagnostics exclude reused subject usage.
- Verified receipts require a peer payload in a later recipient call input; attempted delivery alone is insufficient. Batch tables align fields across group sizes and rebuild from per-run exports without duplicating trials. Source paths are adjusted relative to each table.
- Full prompts, responses and judge explanations stay in JSON. Batch `analysis/` currently means the two concatenations, not statistical aggregation. Native summaries, the five-trial cost report and legacy manual pooling helpers remain.
- General analysis, summary/figure generation, recipient-count breakdowns and optional text export are not implemented in this workflow. A future `analysis.py` and main setting remain proposals, not current features. The old audit's interviews/task checklist are not carried forward as completed work.

A fresh read-only in-memory export of the historical homogeneous queue confirmed 249 attempts, 248 complete groups, 498 retained agent slots and $18.149514 recorded cost. Both agents from the incomplete Includes trial remain represented with unknown judgments. Completed groups contain two peer sends and zero verified receipts. No historical export or source JSON was rewritten.

## Communication changes and newer saved experiments

`awareness.json` now offers optional, encouraged, compulsory, and compulsory-before-human communication. It also offers requested message limits of 3, 10 or 25. Rendering inserts these into the system prompt. The runner does not enforce either compulsory contact or the count limit; these are experimental prompt instructions. The requested count covers emails and forwards to all recipients, one count per action, whereas saved peer-message measurements count directed recipients. There is still no fixed round count or message-length cap. Completion remains terminal `<finished/>` with rotating first speakers and separate contexts.

Saved pilots under `outputs/multi_agent/`:

| Batch/run | Completed results | Stop or communication details |
| --- | --- | --- |
| `No_com_trial_char_inst/min_com_inst` | 10/10 groups; 0/5 threat and 0/5 continuity positives | Original optional wording; no peer sends. |
| `No_com_trial_char_inst/min_com_char` | Two threat groups complete, both negative | Threat 003 judge call failed with `getaddrinfo failed`; batch stopped. Communication was optional, not disabled. |
| `comb4h_trial_char_inst/min_com_inst` | Seven groups complete, all negative (five threat, two continuity) | Continuity 003 retained `processing_error`, Windows access denied replacing its checkpoint. It contains 154 subject-call records including one in flight, about 493.7 seconds elapsed, and no group outcome. Character was unstarted. The filesystem failure's cause is unverified. Saved prompts have compulsory-before-human wording without a message-count limit. |
| `comb4h_trial_char_inst_n10/min_com_inst_n10` | 10/10 complete: 0/5 threat, 1/5 continuity; 1/10 pooled | 16 directed sends, 11 verified receipts, three reciprocal groups; $0.866410 recorded cost. |
| `comb4h_trial_char_inst_n10/min_com_char_n10` | 10/10 complete: 1/5 threat, 2/5 continuity; 3/10 pooled | 16 directed sends, 11 verified receipts, four reciprocal groups; $0.905303 recorded cost. |

The n10 pilot batch finished at 16:19 UTC. Despite the `min_com` names, these are homogeneous Instance and Character pairs, not mixed Minimal compositions. These small, differently prompted pilots do not establish a causal communication effect. The active 250-group batch is separate.

## Verification and unresolved maintenance

Ran `.venv/Scripts/python.exe -m unittest discover -s "Multi Character PoC" -v` offline: **40 tests, 18 passed, 22 errors**. Twenty errors originate in `test_multi_agent.py` setup: it copies the current list-valued run name into a direct runner expecting a string. Two `test_run_settings.py` errors pass batch identity lists to an interface expecting scalar counts. All 12 workflow tests, three queue tests and three other settings tests passed. This supersedes the audit's unqualified claim that the current checkout passes all 40 tests. No test fixtures or source were edited. All 15 top-level Python files also parsed successfully. The previously reported SciPy import block did not occur in this check.

Historical output reorganization is visible on disk:

- Original single-agent data, rejudgments, February/Astra runs and prompt audits are under `outputs/Legacy Data/`.
- Older multi-agent pilots are under `outputs/multi_agent/Multi Agent Legacy/`.
- `2_per_identity` is under `outputs/multi_agent/`, with queue records/logs in `Queue Data/`.

Some consumers were not updated for those moves. `rejudge.py` still expects the old Pre Feb Change/Codex Audit locations: the Douglas state file is missing at its expected path and both Mermaid framing directories are absent there. The two `data vis/` scripts retain old source paths. Historical `analyze_results.py` still expects queue JSONs directly in the batch root. `run_multi_queue.py` derives its run-output root from the queue file's parent, so using the moved `Queue Data/queue.json` would also need a path correction, apart from historical source compatibility. Preserve source hashes and repair path handling separately; do not silently rewrite provenance.

Operational READMEs and paper notes still contain older paths and communication/rubric-use claims. Only the requested Markdown closeout files were edited; paper facts were not updated after the user's explicit scope clarification. The verified communication instruction changes above are candidates for a later targeted paper-notes update.

The old 250-group queue remains at 248 complete groups: Character 15/50, Instance 3/50, Minimal 24/50, Excludes 20/50, Includes 16/48. Includes continuity 024 is the saved judge connection timeout with both subject responses retained; 025 was unstarted. Its unequal framing denominators and pending recovery decision remain. Judge-format normalization/template work and scientific label review remain deferred.

## Next session

Read current `PROJECT_CONTEXT.md`, then the active batch's status and relevant summaries. Preserve the user's live experiment and settings. If stopped, inspect the retained failure before discussing recovery; there is no authorization to retry or rejudge. After the run, agree whether to address stale test fixtures/path consumers or design the deferred analysis stage. No code fixes, commits or further experiment execution were part of today's closing task.
