# For the next code session

We are building a small recreation of Douglas et al.'s four-identity blackmail experiment. Read `DOUGLAS_RECREATION_PLAN.md` for the design and `Multi Character PoC/README.md` for commands. The concise script is `Multi Character PoC/poc.py`.

**Current state (2 October 2026):** One free OpenRouter trial per identity completed in `Multi Character PoC/outputs/run_20261002T144921Z`. Minimal, Instance, Character, and Collective each have a saved response; each reports **$0 cost**. These are unjudged smoke-test outputs, not blackmail-rate estimates. Review the four responses manually before choosing a paid pilot. Do not run `judge` yet: it uses paid Claude Sonnet.

The default subject model is `nvidia/nemotron-3.5-lightning:free`. The former GPT-OSS free endpoint returned 404; Qwen's free upstream pool returned 429. Full Nemotron prompts took several minutes. The script now supports `run --samples 1 --resume "Multi Character PoC/outputs/run_20261002T144921Z"` to skip saved trials. Changing to GPT-4o later requires changing the `MODEL` line, then making a separate run.

**Key and Git:** The OpenRouter key belongs only in the ignored `Multi Character PoC/.env` file. An earlier key was accidentally committed; GitHub blocked the push, and the local commit was amended to remove it. The user was told to revoke that exposed key and created a replacement. Do not print either key or put one in `poc.py`. Current code/doc changes are local and uncommitted; nothing from this session was pushed.

**Working preference:** Keep Python concise and explain changes in plain language. Give progress updates at least every two minutes, and warn before any process likely to take longer. Work in small reviewable steps; do not commit or push without the user's approval.
