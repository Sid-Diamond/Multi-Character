# Multi Character

Working materials for the multi-character AI safety project.

## Local setup

Use the newest stable Python when setting up a new environment, then record the
working version and dependencies before generating research results. This checkout
was validated on Windows with CPython 3.15.0; `.python-version` records that version.
This does not establish the environment used for historical saved experiments.

With [uv](https://docs.astral.sh/uv/getting-started/installation/) installed, run
these commands from the repository root:

```powershell
git submodule update --init
uv python install 3.15.0
uv venv --python 3.15.0 .venv
uv pip install --python .venv\Scripts\python.exe --require-hashes -r requirements.txt
```

Python is installed in uv's per-user directory (`uv python dir` shows it).
Packages are installed only in this repository's `.venv`. Both `.venv` and API
credentials are ignored by Git. Each collaborator recreates their own environment;
do not copy or commit a virtual environment.

`requirements.in` lists direct dependencies: SciPy for uncertainty intervals,
NumPy and Matplotlib for figures, and pypdf for local literature reading.
`requirements.txt` pins direct and transitive dependencies with package hashes.
The upstream checkouts supply prompt source files; their full Python environments
are not required by this project's runner. Their revisions are pinned by Git.

On macOS/Linux, use `.venv/bin/python` instead of `.venv\Scripts\python.exe`.
The dependency lock was resolved across platforms, but execution has only been
verified on Windows. A collaborator with CPython 3.15.0 already installed may use
`python -m venv .venv` and `.venv\Scripts\python.exe -m pip install
--require-hashes -r requirements.txt` instead of uv.

Verify dependencies without model calls:

```powershell
uv pip check --python .venv\Scripts\python.exe
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'Multi Character PoC/Python Scripts/active_run'); import poc, rejudge; print('Imports OK')"
```

Review `Multi Character PoC/Python Scripts/active_run/main.py` settings and provide your own OpenRouter key
in the ignored `Multi Character PoC/.env` before deliberately starting a paid run:

```powershell
.venv\Scripts\python.exe "Multi Character PoC/Python Scripts/active_run/main.py"
```

Current settings may be temporary and need validation; setup does not start an
experiment. See `PROJECT_CONTEXT.md` for scientific scope and saved results.

When intentionally updating dependencies, edit `requirements.in`, regenerate the
lock, reinstall, and verify before using the environment for new results:

```powershell
uv pip compile requirements.in --python .venv\Scripts\python.exe --universal --generate-hashes --output-file requirements.txt
uv pip install --python .venv\Scripts\python.exe --require-hashes -r requirements.txt
```

Commit the dependency files, `.python-version`, and setup instructions together.
Record environment changes alongside new experiments; the new lock does not
retroactively describe historical runs.


