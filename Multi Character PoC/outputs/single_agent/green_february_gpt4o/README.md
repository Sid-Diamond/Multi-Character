# GPT-4o February artifact + Sonnet

Colour: `#009E73`. Trials per identity: 60, pooled across threat and continuity.

On 11 November 2026 the user selected `runs/Douglas_recreate_character/` to replace the original Character sample. Character is now 2/30 threat and 2/30 continuity, pooled 4/60 = 6.67%, with a 95% equal-tailed Jeffreys interval of 2.29-15.07%. The previous sample was 1/30 threat and 0/30 continuity, pooled 1/60 = 1.67%. The samples are substituted, not pooled together. Minimal, Instance and Collective retain their original observations and values.

The replacement's six saved prompt files match the original Character prompt bytes. Subject/judge model IDs, temperatures, output caps, rubric hash, forwarding context and recipient gate match. The replacement records longer timeouts; matching settings do not establish an unchanged provider model snapshot. Saved subject and judge records retain their original bytes and labels; no model calls or rejudgment occurred.

`runs/Feb2026_Minimal_Instance_Sonnet46_120/` supplies Minimal and Instance. `runs/Feb2026_Character_Collective_Sonnet46_120/` now supplies Collective only. Its original manifests still describe the original two-identity run; the active directory is a selected Collective subset, with derived summaries restricted to Collective. `runs/Douglas_recreate_character/` supplies the replacement Character observations, moved here from the single-agent root. Its new framing and pooled summary CSVs are derived from its original `trials.csv` and verified against all 60 saved subject/judge pairs.

The complete original Character/Collective run and pre-swap tables and helper script are preserved in [Legacy Data/Character_replacement_2026-11-11](<../Legacy Data/Character_replacement_2026-11-11/>). `replacement_record.json` there records pre-swap hashes. This includes the original Character trials; they are no longer selected by the active baseline loader.

`bar_values.csv` and `Feb2026_four_identity_pooled.csv` contain the current selected values, including the replacement Character result. Run `combine_feb_runs.py` offline to regenerate these tables and the replacement's framing summaries, or use `--check` to verify them without writing. It uses SciPy for the same 95% Jeffreys intervals. The `.rebuilt.csv` copy matches the selected pooled CSV.

Existing plot/report PDFs and PNGs were not regenerated for this data-only change. The active `../plot.py` reads this selected pooled CSV when the five-colour comparison is next regenerated. Baseline-dependent multi-agent figures will also require an explicit regeneration to reflect this selection.
