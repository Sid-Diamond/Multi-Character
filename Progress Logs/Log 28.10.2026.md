# Progress log - 28 October 2026

Closing record for today's uncertainty mathematics, offline analysis implementation and paper-fact consolidation. Repository instructions, current context and the requested 27 October log were read. No model API calls or paid experiments were started, resumed or rejudged by the agent. No agent commits or pushes were made.

## Uncertainty theory and agreed analysis

The user developed `paper prep/Uncertainties/Uncertainty_Appendix.pdf`, now nine pages. Discussion connected the Beta-binomial posterior to the Jeffreys prior and its Fisher-information geometry. The Beta posterior normaliser uses `B(alpha + k, beta + n - k)`. Fisher information supplies the local metric from a second-order divergence expansion; it is not the coordinate transformation itself.

The updated appendix's section 1.3 expresses the joint posterior calculation for arbitrary identity compositions. Section 1.4 reduces the group-rate integral to a complementary Beta CDF: general equation 43, shared-baseline equation 44 and distinct-baseline mixed-pair equation 45. The agreed procedure matches these expressions after applying the existing mapping of both Collective variants to the original Collective baseline.

The user requested an interview before coding and clarified that questions should be asked one at a time. Agreed choices:

- Use February single-agent counts only for uncertainty analysis, retaining uncertainty in both group and baseline rates.
- Start from raw positive and total counts and apply one Jeffreys prior per distinct rate. Existing smoothed point estimates are not new observations for this calculation.
- Produce threat, continuity and pooled grids. Pool positives and trials before fitting, matching the existing February calculation; do not average framing-specific sign probabilities.
- Report probability supporting the original unsmoothed difference's sign: `P(delta > 0)` for a positive difference and `P(delta < 0)` for a negative one.
- Keep blue for negative and orange for positive raw directions; stronger colour indicates greater posterior support. Print percentages only.
- Use a neutral cell with a dash when the exact raw difference is zero; do not assign an artificial 50% probability.
- Extend mixed pairs using `1 - (1 - p_a)(1 - p_b)`. Distinct baseline parameters require two numerical dimensions after evaluating the group tail. Repeated uses of a mapped baseline share one uncertain parameter and one dataset.
- Preserve the existing smoothing and log-relative-risk options. The user intends to consider empirical difference figures alongside the uncertainty grids for the paper.

All five homogeneous compositions and Excludes + Includes share one mapped baseline per pair. Nine other compositions use two distinct baseline parameters. Equal observed counts do not merge parameters belonging to different original identities.

No significance threshold was adopted. The displayed values are posterior direction probabilities, not p-values or formal exact-null model probabilities. A 95% directional-support threshold differs from exclusion of zero by a 95% equal-tailed credible interval, which requires more than 97.5% posterior mass on one side. Practical equivalence would require a separately chosen neighbourhood around zero; it was discussed but not implemented.

## Offline implementation and outputs

Added `Multi Character PoC/Python Scripts/analysis/uncertainty_grid.py`, integrated through the independent `analysis.uncertainty_grid` switch. It is enabled in `main.py` and requires `p_c_choice="feb_data"`. Existing point-estimate settings remain `smoothing="jeffreys"` and `grid_metric="log_relative_risk"`; the uncertainty calculation is independent of them. The script can also be run directly to regenerate only uncertainty outputs, without dispatching through the paid workflow.

Outputs are under `Multi Character PoC/outputs/multi_agent/all_pairs_combined/analysis/uncertainties/`:

- Three `multi_agent_uncertainty_feb_data_jeffreys_*.pdf` figures: threat, continuity and pooled.
- A 45-row `_values.csv` with full-precision positive/negative probabilities, support for the raw direction, counts, posterior parameters, exact-rational raw differences, mapped identities and numerical diagnostics.
- A `_manifest.json` with software versions, method settings and SHA-256 hashes for inputs, calculation sources and output files.

Gauss-Jacobi order doubles until two consecutive refinements change both tails by no more than `1e-10`; an adaptive algebraic-weight quadrature fallback handles slow endpoint convergence. The negative tail is evaluated directly for numerical stability and is mathematically the complement of the positive tail. Successive-order changes are diagnostics, not rigorous error bounds.

All 45 current calculations converged at orders 64, 128 or 256; the largest successive-order diagnostic was approximately `7.56e-11`. All cells agreed within `1e-9` with the second adaptive quadrature method. The full offline suite passed **62 tests**, including 16 uncertainty tests covering analytic integrals, shared versus distinct parameters, symmetry, zero counts, small tails, routing and the saved dataset. Input/source/output hashes and all three single-page PDFs were verified; figures were previewed and header spacing/font issues corrected.

A pre-existing workflow-test fixture inherited the current analysis mode from `main.py`, causing five errors and one failure in the first complete-suite run. Its intended mocked multi-agent mode is now explicit. That stale fixture temporarily regenerated some figures in the real analysis folder; the tracked comparison PDF was restored and four incidental generated files were moved to a temporary archive. Existing trial data and final pre-existing figures remain unchanged. Subsequent full-suite verification passed.

## Results discussed

- Thirteen of 15 pooled pairs have negative empirical differences from the February independence reference.
- Character + Character: 12/50 positive groups, 24% versus 3.31% reference, +20.69 percentage points; 99.58% posterior support for positivity.
- Instance + Character: 24% versus 14.78%, +9.22 points; 87.07% positive support.
- Instance + Instance: 8% versus 24.89%, -16.89 points; 98.23% negative support.
- Minimal + Excludes: 44% versus 62.42%, -18.42 points; 98.16% negative support.
- Minimal + Minimal changes direction across framings: threat +16 points, continuity -43 points, pooled -13.75 points. Pooled results do not establish a uniform framing-independent pattern.
- Minimal + Excludes threat is the single exact-zero raw difference: 16/25 groups and a 0.64 reference. Its posterior probabilities are approximately 47.3% positive and 52.7% negative; the figure is neutral because the raw estimate has no direction to support.
- Character + Excludes continuity has a positive raw difference but only 48.1% posterior support for positivity. This is retained and flagged rather than replaced with its larger complement.

Interpretation remains conditional on saved labels, priors, sampling assumptions and historical-baseline comparability. The results do not isolate communication effects. Shared baselines also mean cell summaries are not independent repetitions of baseline evidence. Robustness and noncommunicating controls remain follow-ups, not completed findings.

## Paper-fact audit and consolidation

At the user's request, audited `paper prep/paper prep.md` and `paper prep/experiment facts for paper.md` and consolidated their factual content into `paper prep/paper facts.md`. Its six sections follow the intended paper order: motivation; Douglas recreation; multi-agent extension; results; uncertainties; follow-up research. The user will choose which facts merit inclusion in the paper.

The consolidated file removes duplication, retains label/provenance limitations, distinguishes older pilots from the completed 750-group dataset, and includes the complete 15-pair count table. Inferred Douglas positive counts are not presented as verified; published percentages are retained. Superseded statements about no paid use of the group rubric and one Collective variant at a time are identified as historical. Relevant saved manifests, exports and current code were inspected read-only.

The final saved export records 1,311 peer-message sends, 1,040 receipts and 271 sends after the recipient finished; sends occurred in 650 groups, receipts in 542, and reciprocal receipts in 382. These are export counts, not a fresh message-body audit. The earlier two-send/no-receipt result belongs to the older stopped pilot batch and is kept separate.

The consolidation's 20 source links, all 45 framing/count entries, 15 pooled differences and saved communication totals passed checks when the document was created. `Meta.md` now directs future paper-fact updates to the consolidated document.

The two input documents were left intact by the consolidation. At session close, they are absent and `git status` reports their deletion; the agent did not delete or restore them. Some source references in `paper facts.md` consequently point to removed input files. The earlier standalone mathematical discussion Markdown is also absent; the appendix PDF remains. No deleted notes were recreated.

## Current state and next step

The uncertainty implementation and generated outputs are complete. The consolidated `paper facts.md` is the current fact reference. The 750-group collection remains complete, with no additional paid collection authorised by today's work.

Next: the user reviews the raw-difference and uncertainty figures and selects material from the fact document for the paper. Remaining research decisions are the robustness checks, exact design of the matched N=2 noncommunicating control, and any reporting threshold or practical-equivalence margin. The proposed control remains 15 compositions with 25 groups per framing, targeting 750 groups; it has not been collected. Its earlier budgeting reference is about USD 79.21 including the user's 10% allowance, not a guaranteed cost.

Documentation follow-up: if the old notes remain removed, replace their remaining source links in `paper facts.md` with suitable surviving provenance references. Preserve the user's current deletions. No code changes, commits or paid runs were made as part of this closing-log task.
