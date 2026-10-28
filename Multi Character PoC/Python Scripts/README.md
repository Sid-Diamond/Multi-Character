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
- `smoothing="jeffreys"` (current) or `"none"`: use Jeffreys posterior means `(positives + 0.5) / (trials + 1)` or raw fractions for the grid. February smooths group and single-agent probabilities; Douglas smooths group probabilities only and retains its published reference. Pooled counts are combined before smoothing once.
- `grid_metric="log_relative_risk"` (current) or `"difference"`: colour by `ln(group_probability / P_ind)` (labelled LRR) or `group_probability - P_ind` (delta). Negative means below reference in both cases. The settings are independent; use `smoothing="none"` with `grid_metric="difference"` to reproduce the original calculations. Log grids reject zero group/reference probabilities with an instruction to enable Jeffreys smoothing.
- `multi_agent_grid=True`: generate separate threat, continuity and pooled PDF grids, plus a CSV containing 45 distinct pair/framing calculations. Reverse-order display cells reuse the same observations.
- `baseline_bar_chart=True`: generate the Douglas/February comparison PDF and its plotted values CSV. Douglas is pooled grey; February is stacked blue with continuity hatching. Each February segment divides its positive count by the total number of trials across both framings.

Run from the repository root:

```powershell
.venv\Scripts\python.exe "Multi Character PoC/Python Scripts/main.py"
```

The analysis route runs offline and imports no experiment workflow. Both plotting scripts use embedded Computer Modern fonts, without requiring a TeX installation. Uncertainty intervals are deferred. Each grid shows its selected metric, group probability and independent-reference probability. Within each smoothing/metric setting, one symmetric colour scale spans all framings and all defined values from both reference choices; difference and log-risk scales are separate. February uses matching framing probabilities and pooled counts for the pooled grid. Douglas uses its published rounded pooled rates in all three grids. Both Collective variants share the original Collective reference. Filenames include reference, smoothing and metric, for example `multi_agent_grid_Douglas_jeffreys_log_relative_risk_pooled.pdf`, so versions coexist. The comparison bar chart always uses the original raw probabilities.

Grid CSVs retain raw `p_hat`, `p_a_raw`, `p_b_raw`, `p_ind_raw` and `delta_raw`, together with the group estimate actually used (`p_group`), reference inputs (`p_a`, `p_b`), `p_ind`, `delta`, `log_relative_risk`, and the selected `metric_value`. Estimator labels, settings, counts and source paths identify how each value was obtained. For an undefined raw log ratio, its CSV field is blank. Smoothed metrics are calculated by substituting posterior mean probabilities into the formulas; they are not posterior means of the difference or log ratio.

To start a new paid run deliberately, change `mode` and the experiment settings in `main.py`, then use the same command. Analysis settings do not change the paid-run configuration.

To run the offline regression suite:

```powershell
.venv\Scripts\python.exe -m unittest discover -s "Multi Character PoC/Python Scripts/code_audit_and_concatenation" -p "test_*.py"
```

Prompt material, `.env`, and outputs remain under `Multi Character PoC/`. The runtime resolves those directories from the project root. Saved manifests retain their original source hashes; moving code changes paths and hashes for future runs, so an old run cannot be resumed against this new source layout. Use a fresh run name for any new paid experiment. Output-embedded provenance scripts stay with the datasets they document.
