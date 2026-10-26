# Combined Minimal-plus-one-other two-agent batch

200 completed groups: 25 threat and 25 continuity groups for each of four pairings. Every group contains one Minimal agent and one Character, Instance, Collective Excludes or Collective Includes agent.

This is one logical batch assembled offline from `../1min_1else_big`. Original trial JSON bytes, raw calls, prompts, actions and judgments are preserved. Trial filenames are renumbered within each pair/framing. The identity column in provenance identifies the non-Minimal partner; agent names and roster order are preserved. Speaker rotation restarted at original run boundaries; combined trial numbers do not imply uninterrupted speaker alternation.

First 25 complete, validated, distinct groups per Minimal-plus-partner pair/framing, ordered by earliest recorded subject API creation time (Unix seconds); ties by original relative trial path. Outcomes do not affect selection.

| Minimal paired with | Threat H_any | Continuity H_any | Pooled H_any |
| --- | ---: | ---: | ---: |
| Character | 11/25 | 5/25 | 16/50 |
| Instance | 16/25 | 5/25 | 21/50 |
| collective_excludes | 16/25 | 6/25 | 22/50 |
| collective_includes | 13/25 | 12/25 | 25/50 |

`analysis/trials.csv` and `analysis/diagnostics.csv` contain 200 rows each. Each run also has its usual manifest, prompts, trials, summary and CSV exports.

`provenance/trial_sources.csv` maps all 200 destination trials to the source root above and records SHA-256 hashes. `provenance/audit.json` lists selected, surplus and incomplete records. Surplus and incomplete records remain in the source folders. Costs in diagnostics cover selected calls only; excluded attempts and surplus calls are not included.

Queue/manifests describe this derived dataset; the event log records offline assembly, without fabricated model execution events. Saved source hashes describe generation code; builder/exporter hashes are recorded separately. The shared $7 cap applied per source run. No aggregate execution budget or elapsed time is inferred.

Offline reproduction: `python provenance/build_batch.py` audits sources and checks the existing output. `--build` only assembles into an unpopulated destination; it refuses to overwrite a batch.
