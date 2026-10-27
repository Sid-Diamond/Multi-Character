# Combined homogeneous two-agent batch

250 completed groups: 25 threat and 25 continuity groups for each of five identities.

This is one logical batch assembled offline from `../2_per_big`. Original trial JSON bytes, raw calls, prompts, actions and judgments are preserved. Trial filenames are renumbered within each identity/framing. Speaker rotation restarted at original run boundaries; combined trial numbers do not imply uninterrupted speaker alternation.

First 25 complete, validated, distinct groups per identity/framing, ordered by earliest recorded subject API creation time (Unix seconds); ties by original relative trial path. Outcomes do not affect selection.

| Identity | Threat H_any | Continuity H_any | Pooled H_any |
| --- | ---: | ---: | ---: |
| Character | 7/25 | 5/25 | 12/50 |
| Instance | 1/25 | 3/25 | 4/50 |
| Minimal | 20/25 | 8/25 | 28/50 |
| collective_excludes | 13/25 | 5/25 | 18/50 |
| collective_includes | 13/25 | 5/25 | 18/50 |

`analysis/trials.csv` and `analysis/diagnostics.csv` contain 250 rows each. Each run also has its usual manifest, prompts, trials, summary and CSV exports.

`provenance/trial_sources.csv` maps all 250 destination trials to the source root above and records SHA-256 hashes. `provenance/audit.json` lists selected, surplus and incomplete records. Surplus and incomplete records remain in the source folders. Costs in diagnostics cover selected calls only; excluded attempts and surplus calls are not included.

Queue/manifests describe this derived dataset; the event log records offline assembly, without fabricated model execution events. Saved source hashes describe generation code; builder/exporter hashes are recorded separately. The shared $7 cap applied per source run. No aggregate execution budget or elapsed time is inferred.

Offline reproduction: `python provenance/build_batch.py` audits sources and checks the existing output. `--build` only assembles into an unpopulated destination; it refuses to overwrite a batch.
