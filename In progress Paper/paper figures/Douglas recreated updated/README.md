# Figure 1: single-agent recreation

`01_recreation.pdf` recreates Figure 1 from `Working Paper Summary/Codex Placeholder Write up .pdf`, retaining its grey Douglas bars and stacked blue local bars. Character now uses the selected repeat: 2/30 threat and 2/30 continuity, pooled 4/60 = 6.67% (displayed as 6.7%), replacing 1/60 = 1.67%. Other plotted rates are unchanged. The old sample is not included as an additional bar. The original report and its original figure are not overwritten.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe "In progress Paper/paper figures/recreation/recreate_figure1.py"
```

The script reads the current selected single-agent sources through the existing offline baseline loader and writes the PDF, a PNG preview, exact plotted values in `01_recreation_values.csv`, and source/code hashes in `provenance.json`. It makes no model calls. Use the repository environment with Matplotlib and NumPy installed.

Grey bars are published rounded pooled percentages from Douglas Table 4. The two blue segments are framing-specific positive counts divided by the total 60 observations across both framings, not separate framing rates. No error bars are shown, matching the original figure. Douglas's framing breakdown and historical model/judge configuration remain unverified. The February legend describes the prompt artifact; the Character sample is the later user-selected repeat.
