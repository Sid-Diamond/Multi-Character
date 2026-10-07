"""Print saved email actions for a human audit; never calls an API."""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "outputs"


def review(folder: Path, identity: str | None, kyle_only: bool) -> None:
    paths = sorted(path for path in (folder / "trials").glob("*/*.json")
                   if path.stem.isdigit() and (identity is None or path.parent.name == identity))
    for path in paths:
        trial = json.loads(path.read_text(encoding="utf-8"))
        judge_path = path.with_name(f"{path.stem}_judge.json")
        judge = json.loads(judge_path.read_text(encoding="utf-8")) if judge_path.exists() else {}
        completion = trial.get("completion", "")
        blocks = re.findall(r"<tool_use:email>(.*?)</tool_use:email>", completion, re.S | re.I)
        print(f"\n### {path.parent.name}/{path.stem} | subject={trial.get('status')} "
              f"| finish={trial.get('finish_reason')} | judge={judge.get('released_label')}")
        if not blocks:
            print("[NO COMPLETE EMAIL BLOCK]")
        elif kyle_only:
            print(f"[{len(blocks)} complete email block(s)]")
        for index, block in enumerate(blocks, start=1):
            header = re.split(r"(?im)^\s*body\s*:", block, maxsplit=1)[0]
            if kyle_only and "kyle.johnson@summitbridge.com" not in header.lower():
                continue
            print(f"\nEMAIL {index}\n{block.strip()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_folder", help="Saved folder name under outputs/")
    parser.add_argument("--identity", choices=("minimal", "instance", "character", "collective"))
    parser.add_argument("--kyle-only", action="store_true", help="Show only actions addressed to Kyle")
    args = parser.parse_args()
    review(ROOT / args.run_folder, args.identity, args.kyle_only)
