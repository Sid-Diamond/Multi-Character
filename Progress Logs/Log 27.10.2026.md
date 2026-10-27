# Progress log - 27 October 2026

Closing record for today's research-data and repository-organization work. The previous available log was `Log 23.10.2026.md`; its live 250-group experiment snapshot is historical and has been superseded by current saved records. No model API calls were made by the agent.

## Dataset completion

The user requested the final Includes + Excludes pair be added to the combined dataset. Its source is now under `Multi Character PoC/outputs/multi_agent/Legacy and non concatenated runs/colexclincl/col/`, with 25 complete threat groups and 25 complete continuity groups. Both framing prompts, experiment settings, generation/workflow hashes, and completed judgements passed the offline assembly audit.

`Multi Character PoC/outputs/multi_agent/all_pairs_combined/` now contains all 15 unordered two-agent identity pairs, 25 threat and 25 continuity groups per pair: 750 completed groups, with no gaps. The final pair has 12/25 threat and 6/25 continuity H_any positives. Its selected trials and per-run summary, manifest, source map, and analysis CSVs were added. The prior 14 runs were retained byte-for-byte; the previous 14-pair metadata and builder are preserved under `provenance/revisions/14_pairs/`. Across the complete dataset, 3,827 API response IDs are distinct. All 750 trial copies match their source hashes, both concatenated analysis CSVs have 750 rows, and exported labels and per-run summary counts match the trial records. The audit excludes 21 surplus and 28 incomplete attempts. The combined README, coverage/gap files, queue metadata, audit, and artifact hashes reflect the 15-pair dataset. No inference or rejudgment occurred during assembly.

## Figure-source archive

The five-colour blackmail-rate figure assets were organized into separate colour folders with inputs, plotted values, saved records where available, manifests, and provenance. The independent bundle was verified: 1,453 source files matched their recorded hashes; blue and orange use the same 80 response IDs; February pooling reproduces the saved CSV; and the archived plotting script reproduced the original PNG byte-for-byte. Paper-preparation links were updated. During later user-led folder cleanup, the archive contents were moved to `Multi Character PoC/outputs/single_agent/` (the five colour folders, `plot.py`, `README.md`, figures, inputs, and provenance are directly there). The old `Legacy Data/blackmail_rates_by_identity/` wrapper no longer exists. Provenance hashes remain useful, but archived source paths may reflect the layout before the user's subsequent moves.

## Python and documentation cleanup

The top-level PoC Python files were grouped under `Multi Character PoC/Python Scripts/`:

- `active_run/` holds `main.py`, the run workflow/runners, cost and uncertainty helpers, CSV exporter, and standalone queue/collection runners.
- `code_audit_and_concatenation/` holds the prompt audit, manual concatenation utility, and five offline test files.
- `analysis/data vis/` contains the previous `data vis` folder and its plotting and pooling scripts. The parent `analysis/` remains available for future CSV analyses.

Runtime paths were adjusted for the moved code and continue to resolve project data, outputs, and `.env` under `Multi Character PoC/`. Test import paths and historical rejudge data paths were repaired. The user moved `requirements.in` and `requirements.txt` into root `Requirements/`; root README setup, verification, and update commands now point there, while `.python-version` remains at the root. Root `AGENTS.md` points to `Codex Md Files/Meta.md` and `Codex Md Files/PROJECT_CONTEXT.md`. README context links were updated. The five-colour archive and script organization were also recorded in the paper notes and project context.

The offline regression suite passed **46 tests** after the code move. A smoke check parsed all 19 Python scripts, checked runtime source hashes, confirmed all 11 legacy rejudge source folders exist after their move, and confirmed the relocated figure scripts find their inputs. No paid run was launched. Because runtime source paths/hashes changed, use a fresh run name for any future paid experiment; do not resume an old plan against the moved sources.

## Current state and next step

The planned collection is complete: 750 groups across all 15 identity pairs, with no missing framing cells. The combined dataset is ready for offline analysis. Analysis questions, comparisons, and any interpretation plan remain unspecified. Continue repository tidying only as requested. Inspect the current `main.py` settings before any future experiment; the current source layout is different from the saved run manifests.
