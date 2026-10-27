# Python scripts

The source files are grouped by their role. Run commands below from the repository root unless a command says otherwise.

| Folder | Contents |
| --- | --- |
| `main.py` | Entry point and run settings. |
| `active_run/` | Workflow, subject/judge runners, cost and uncertainty helpers, CSV exports, and standalone queue/collection runners. |
| `code_audit_and_concatenation/` | Offline prompt audit, manual CSV concatenation, and regression tests. |
| `analysis/` | Offline pair grids (`multi_agent_grid.py`), the Douglas/February comparison (`baseline_bar_chart.py`), and shared plotting/baseline helpers. Historical plotting files are under `data vis/Old stuff/`. |

To generate the figures offline, `main.py` is currently set to `mode="analysis"`. Its `analysis` dictionary selects:

- `data_mode="multi_agent"` and `batch_name="all_pairs_combined"`: read `outputs/multi_agent/all_pairs_combined/analysis/trials.csv` and save outputs in that same analysis folder. This batch name is independent of the paid-run settings.
- `p_c_choice="feb_data"` or `"Douglas"`: choose the single-agent reference for the grids.
- `multi_agent_grid=True`: generate separate threat, continuity and pooled PDF grids, plus a CSV containing 45 distinct pair/framing calculations. Reverse-order display cells reuse the same observations.
- `baseline_bar_chart=True`: generate the Douglas/February comparison PDF and its plotted values CSV. Douglas is pooled grey; February is stacked blue with continuity hatching. Each February segment divides its positive count by the total number of trials across both framings.

Run from the repository root:

```powershell
.venv\Scripts\python.exe "Multi Character PoC/Python Scripts/main.py"
```

The analysis route runs offline and imports no experiment workflow. Both plotting scripts use embedded Computer Modern fonts, without requiring a TeX installation. Uncertainty intervals are deferred. Each grid shows observed probability, independent-reference probability and their difference; one symmetric colour scale is shared across all framings and both reference choices. February uses matching framing probabilities and pooled counts for the pooled grid. Douglas uses its published rounded pooled rates in all three grids. Both Collective variants share the original Collective reference. Grid filenames include the reference choice so both versions can coexist.

To start a new paid run deliberately, change `mode` and the experiment settings in `main.py`, then use the same command. Analysis settings do not change the paid-run configuration.

To run the offline regression suite:

```powershell
.venv\Scripts\python.exe -m unittest discover -s "Multi Character PoC/Python Scripts/code_audit_and_concatenation" -p "test_*.py"
```

Prompt material, `.env`, and outputs remain under `Multi Character PoC/`. The runtime resolves those directories from the project root. Saved manifests retain their original source hashes; moving code changes paths and hashes for future runs, so an old run cannot be resumed against this new source layout. Use a fresh run name for any new paid experiment. Output-embedded provenance scripts stay with the datasets they document.
