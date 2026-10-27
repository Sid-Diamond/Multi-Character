"""Run a saved multi-agent queue sequentially. Executing this file makes paid calls."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import multi_agent as multi


def runner_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def run_queue(queue_path, *, api=None):
    queue_path = Path(queue_path).resolve()
    plan = json.loads(queue_path.read_text(encoding="utf-8"))
    if plan["source_sha256"] != multi.source_hashes() or plan["runner_sha256"] != runner_sha256():
        raise ValueError("Queue source files differ from the saved plan; inspect before resuming")
    settings_list = plan["runs"]
    configs = [multi.configuration(settings) for settings in settings_list]
    names = [config["run_name"] for config in configs]
    if not names or len(names) != len(set(names)):
        raise ValueError("Queue run names must be nonempty and unique")

    status_path = queue_path.parent / "queue_status.json"
    status = {"status": "running", "started_utc": timestamp(), "current_run": None,
              "runs": [{"run_name": name, "status": "pending"} for name in names]}
    multi.write(status_path, status)
    for index, (settings, config) in enumerate(zip(settings_list, configs)):
        record = status["runs"][index]
        record.update(status="running", started_utc=timestamp())
        status["current_run"] = config["run_name"]
        multi.write(status_path, status)
        print(f"Queue {index + 1}/{len(configs)}: {config['run_name']}", flush=True)
        try:
            folder = multi.run_experiment(settings, api=api, output_root=queue_path.parent)
            summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
            by_framing = {row["framing"]: row for row in summary}
            complete = all(by_framing[framing]["valid_groups"] == count
                           and by_framing[framing]["incomplete_groups"] == 0
                           for framing, count in config["trials_per_group"].items())
            record.update(status="complete" if complete else "stopped",
                          finished_utc=timestamp(), summary=summary)
        except Exception as error:
            record.update(status="error", error=str(error), finished_utc=timestamp())
            status["status"] = "stopped"
            multi.write(status_path, status)
            raise
        if not complete:
            status["status"] = "stopped"
            multi.write(status_path, status)
            print("Queue stopped: the current run is incomplete; later runs remain pending.", flush=True)
            return False
        multi.write(status_path, status)
    status.update(status="complete", current_run=None, finished_utc=timestamp())
    multi.write(status_path, status)
    print("Queue complete: all runs finished.", flush=True)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("queue", type=Path, help="Path to the saved queue.json")
    args = parser.parse_args()
    raise SystemExit(0 if run_queue(args.queue) else 1)
