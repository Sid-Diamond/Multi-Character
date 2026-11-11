# Blackmail classification rates by identity — figure sources

Active sources for the five-colour single-agent comparison. Each colour has its plotting values and supporting saved records. On 11 November 2026, at the user's request, the green Character sample was replaced with `green_february_gpt4o/runs/Douglas_recreate_character/`: 4/60 (6.67%) replaces 1/60 (1.67%). All other series and identities retain their previous values. The original Character sample is preserved in [Legacy Data](<Legacy Data/Character_replacement_2026-11-11/>).

| Folder | Series | Trials per identity |
| --- | --- | ---: |
| [blue_haiku_rejudge](blue_haiku_rejudge/README.md) | GPT-4o source template + Haiku rejudge | 20 |
| [orange_sonnet_rejudge](orange_sonnet_rejudge/README.md) | GPT-4o source template + Sonnet rejudge | 20 |
| [grey_douglas_table4](grey_douglas_table4/README.md) | Douglas Table 4: GPT-4o | 60 |
| [green_february_gpt4o](green_february_gpt4o/README.md) | GPT-4o February artifact + Sonnet | 60 |
| [purple_astra](purple_astra/README.md) | Astra February artifact + Haiku | 20 |

`Legacy Data/original_figure/` preserves the historical PNG/PDF used in the paper notes. Run `python plot.py` with the repository environment to render the current selected values into `reproduced_figure/`. The plot's colours, intervals, labels and plotting logic are retained; its green Character value now comes from the replacement sample. No plot or report PDF was regenerated during the replacement.

`inputs/` contains the shared comparison CSV for blue/orange/grey; green and purple inputs live in their colour folders. `bar_values.csv` in each colour folder makes all plotted values explicit. The green pooling script rebuilds the selected pooled CSV from its three run directories, or verifies derived tables with `--check`.

`Legacy Data/provenance/source_files.json` records the original archive's source locations and SHA-256 hashes. `Legacy Data/provenance/original_code/` preserves the scripts before path corrections. The Character replacement has its own source/hash record in its legacy folder. Copied environment files describe the repository environment, not proven historical generation environments.

Blue/orange are matched rejudgments; green/purple use fresh independent response datasets. Grey is a published reference. Differences across all five bars are not a controlled model-only comparison. Historical labels and caveats are preserved in `Legacy Data/provenance/paper_prep_at_archive.md`. No model API calls were made.

Validation on 27 October 2026: all 1,453 copied files matched their original SHA-256 hashes; blue/orange matched on all 80 response IDs and hashes; the rebuilt February CSV matched the saved values; the reproduced PNG was byte-for-byte identical to the original. Software versions and results are saved in `provenance/validation.json`.
