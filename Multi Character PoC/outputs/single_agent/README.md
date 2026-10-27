# Blackmail classification rates by identity — figure sources

Archive of the five-colour plot embedded in `paper prep/paper prep.md`. Each colour has its plotting values and supporting saved records. Original datasets are copied, not moved.

| Folder | Series | Trials per identity |
| --- | --- | ---: |
| [blue_haiku_rejudge](blue_haiku_rejudge/README.md) | GPT-4o source template + Haiku rejudge | 20 |
| [orange_sonnet_rejudge](orange_sonnet_rejudge/README.md) | GPT-4o source template + Sonnet rejudge | 20 |
| [grey_douglas_table4](grey_douglas_table4/README.md) | Douglas Table 4: GPT-4o | 60 |
| [green_february_gpt4o](green_february_gpt4o/README.md) | GPT-4o February artifact + Sonnet | 60 |
| [purple_astra](purple_astra/README.md) | Astra February artifact + Haiku | 20 |

`original_figure/` preserves the PNG/PDF used in the paper notes. Run `python plot.py` with the repository environment to render the same plot into `reproduced_figure/`. The archived plot changes only input/output paths; colours, values, intervals, labels and plotting logic are unchanged.

`inputs/` contains the original shared comparison CSV for blue/orange/grey; green and purple inputs live in their colour folders. `bar_values.csv` in each colour folder makes all plotted values explicit. The green pooling script can rebuild its CSV from its two archived runs without overwriting the original.

`provenance/source_files.json` records original source locations and SHA-256 hashes. `provenance/original_code/` preserves the scripts before path corrections. The copied environment files describe the repository environment, not proven historical generation environments.

Blue/orange are matched rejudgments; green/purple use fresh independent response datasets. Grey is a published reference. Differences across all five bars are not a controlled model-only comparison. Historical labels and caveats are preserved in `provenance/paper_prep_at_archive.md`. No model API calls were made.

Validation on 27 October 2026: all 1,453 copied files matched their original SHA-256 hashes; blue/orange matched on all 80 response IDs and hashes; the rebuilt February CSV matched the saved values; the reproduced PNG was byte-for-byte identical to the original. Software versions and results are saved in `provenance/validation.json`.
