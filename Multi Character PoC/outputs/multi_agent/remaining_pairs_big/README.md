# Remaining six two-agent compositions

Authorized on 26 October 2026: collect 25 valid threat and 25 valid continuity
groups for each of Character + Instance, Character + Excludes, Character +
Includes, Instance + Excludes, Instance + Includes, and Excludes + Includes.
Reverse roster assignments are not separate conditions. Existing homogeneous
and Minimal-plus-partner samples are retained in their own datasets.

`multi_agent/` contains normal, separately named execution batches. Each new
attempt targets only the missing valid groups for one pair. Source batches and
failed records are preserved. First-speaker rotation restarts at each batch.

`supervision/plan.json` freezes scientific settings, generation/workflow source
hashes, rendered prompt hashes, the target counts, and attempt history.
`supervision/configs/` records every submitted batch configuration.
`supervision/calls/` records an entry before each network submission and the
returned response ID/cost or failure afterward. The supervisor's hash is saved
with each attempt; generation source hashes describe the unchanged pipeline.

The original $7 per-run cap remains. A separate API wrapper checks the $21
aggregate recorded-spend stopping threshold before each submission, including
returned costs from failed attempts. One final call may exceed the threshold.
Unknown charges, payment/authentication failures, budget stops and repeated
failures require review. The wrapper forwards model parameters unchanged.

`supervision/status.json` is refreshed when an attempt ends. During a run,
inspect queue status and saved trials or use the read-only audit command from
the repository root:

```powershell
& '.venv/Scripts/python.exe' 'Multi Character PoC/collect_remaining_pairs.py' --audit
```

The supervisor uses one new Python process per attempt. `--run-next` makes paid
calls and must never run concurrently with another collection invocation.
The existing collection lock blocks concurrent invocations; inspect a stale
lock and process state before recovery. A `running` call during an active
process is expected and does not by itself mean an abandoned request.

Final combination must validate settings, source hashes, rendered prompts,
unique response IDs, completed judgments and source-byte preservation, using
the established chronological selection and provenance method.
