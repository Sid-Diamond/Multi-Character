# Project agent entry point

Read `Meta.md` at the start of work in this repository. Follow its two-minute progress-update rule during active work. Use `PROJECT_CONTEXT.md` for current scope, status, and next steps. Load papers and source code selectively for the current task; do not preload them all.

Do not read or preload `Progress Logs/` during routine work. Read a specific log only if the user asks for it or a needed historical detail is unavailable from `PROJECT_CONTEXT.md` and the saved experiment records.

The user runs paid experiments in a separate terminal. Do not launch or resume `main.py`, `rejudge.py`, or any other command that makes model API calls unless the user explicitly asks the agent to execute the run. A request to prepare settings, fix resume behavior, audit outputs, or discuss finishing a run is not authorization to start it. Offline tests and read-only inspection are fine.
