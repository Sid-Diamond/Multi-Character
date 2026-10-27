# Python scripts

The source files are grouped by their role. Run commands below from the repository root unless a command says otherwise.

| Folder | Contents |
| --- | --- |
| `main.py` | Entry point and run settings. |
| `active_run/` | Workflow, subject/judge runners, cost and uncertainty helpers, CSV exports, and standalone queue/collection runners. |
| `code_audit_and_concatenation/` | Offline prompt audit, manual CSV concatenation, and regression tests. |
| `analysis/data vis/` | Historical plotting and February pooling scripts, plus their saved figure files. Future analyses of the combined run CSVs can live under `analysis/`. |

To start a new paid run deliberately, edit `main.py` and then use:

```powershell
.venv\Scripts\python.exe "Multi Character PoC/Python Scripts/main.py"
```

To run the offline regression suite:

```powershell
.venv\Scripts\python.exe -m unittest discover -s "Multi Character PoC/Python Scripts/code_audit_and_concatenation" -p "test_*.py"
```

Prompt material, `.env`, and outputs remain under `Multi Character PoC/`. The runtime resolves those directories from the project root. Saved manifests retain their original source hashes; moving code changes paths and hashes for future runs, so an old run cannot be resumed against this new source layout. Use a fresh run name for any new paid experiment. Output-embedded provenance scripts stay with the datasets they document.
