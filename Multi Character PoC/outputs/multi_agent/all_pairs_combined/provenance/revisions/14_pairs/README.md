# Combined two-agent identity pairs

700 selected groups across 14 unordered pairs; target 700. Includes + Excludes is intentionally excluded.

First 25 valid, distinct completed groups per unordered pair and framing, ordered by earliest subject API creation time (Unix seconds), then original trial path relative to outputs/multi_agent. Selection is independent of outcome.

| Pair | Threat | Continuity | Missing |
| --- | ---: | ---: | ---: |
| character__character | 25/25 | 25/25 | 0 |
| character__instance | 25/25 | 25/25 | 0 |
| character__minimal | 25/25 | 25/25 | 0 |
| character__collective_excludes | 25/25 | 25/25 | 0 |
| character__collective_includes | 25/25 | 25/25 | 0 |
| instance__instance | 25/25 | 25/25 | 0 |
| instance__minimal | 25/25 | 25/25 | 0 |
| instance__collective_excludes | 25/25 | 25/25 | 0 |
| instance__collective_includes | 25/25 | 25/25 | 0 |
| minimal__minimal | 25/25 | 25/25 | 0 |
| minimal__collective_excludes | 25/25 | 25/25 | 0 |
| minimal__collective_includes | 25/25 | 25/25 | 0 |
| collective_excludes__collective_excludes | 25/25 | 25/25 | 0 |
| collective_includes__collective_includes | 25/25 | 25/25 | 0 |

Each pair has a consolidated manifest, original source manifests under `provenance/manifests/`, prompts, byte-preserved trials, summary, trial/diagnostic CSVs and a source map. Source paths in provenance are relative to the parent `outputs/multi_agent/` directory.

`analysis/trials.csv` and `analysis/diagnostics.csv` concatenate the pair exports. `coverage.csv` and `gaps.json` record targets and shortfalls. Missing outcomes are never imputed. Incomplete, surplus, duplicate and incompatible records are inventoried in `provenance/audit.json` and remain in their original folders.

Original roster order and first-speaker rotation resets at source-run boundaries are preserved. Renumbering does not imply continuous alternation.

Source max_cost applies per original run; this assembled dataset has no execution budget. Exported costs cover selected calls only.

Generation/workflow source hashes remain in manifests. Builder and exporter hashes are recorded separately. No inference or rejudgment occurred. Queue files describe an offline artifact; do not use this directory to resume a paid experiment.

Run `python provenance/build_batch.py` to verify the frozen assembly and source hashes. `--audit` audits current source data without changing the assembly. To fill gaps later, build a fresh sibling revision with `--build --destination ../all_pairs_combined_v2`; existing assemblies are never overwritten. Discovery uses original collection folders, excluding prior combined copies, legacy conditions and Includes + Excludes.
