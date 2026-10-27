"""Offline queue checks with mocked subject and judge responses."""

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "active_run"))

import main
import multi_agent as multi
import run_multi_queue as queue
from test_multi_agent import JUDGE, response


class MultiQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.enterContext(redirect_stdout(io.StringIO()))
        self.plan = {"source_sha256": multi.source_hashes(), "runner_sha256": queue.runner_sha256(),
                     "runs": []}
        for identity in ("Character", "Instance"):
            settings = copy.deepcopy(main.settings)
            settings.update(run_name=f"two_{identity}", model="mock-subject", judge_model="mock-judge", max_cost=10)
            settings["multi_agent"].update(identities_per_trial={identity: 2},
                                          trials_per_group={"threat": 1, "continuity": 1})
            self.plan["runs"].append(settings)
        self.path = self.root / "queue.json"

    def save_plan(self):
        multi.write(self.path, self.plan)

    def test_sequential_runs_use_saved_settings_and_completed_calls_are_reused(self):
        self.save_plan()
        calls = []

        def api(model, messages, *args, **kwargs):
            calls.append(model)
            if len(calls) > 6:
                first = json.loads((self.root / "two_Character/summary.json").read_text())
                self.assertEqual(first[-1]["valid_groups"], 2)
            return response(JUDGE if model == "mock-judge" else "<finished/>")

        self.assertTrue(queue.run_queue(self.path, api=api))
        self.assertEqual(len(calls), 12)
        status = json.loads((self.root / "queue_status.json").read_text())
        self.assertEqual(status["status"], "complete")
        self.assertEqual([row["status"] for row in status["runs"]], ["complete", "complete"])
        for identity in ("Character", "Instance"):
            manifest = json.loads((self.root / f"two_{identity}/manifest.json").read_text())
            self.assertEqual([agent["identity"] for agent in manifest["agents"]], [identity, identity])
        self.assertTrue(queue.run_queue(self.path, api=api))
        self.assertEqual(len(calls), 12)

    def test_incomplete_run_stops_queue_before_the_next_run(self):
        self.save_plan()
        calls = []

        def api(*args, **kwargs):
            calls.append(1)
            return response("Partial", finish="length")

        self.assertFalse(queue.run_queue(self.path, api=api))
        self.assertEqual(len(calls), 1)
        self.assertFalse((self.root / "two_Instance").exists())
        status = json.loads((self.root / "queue_status.json").read_text())
        self.assertEqual(status["status"], "stopped")
        self.assertEqual([row["status"] for row in status["runs"]], ["stopped", "pending"])

    def test_duplicate_names_and_changed_sources_fail_before_any_run(self):
        self.plan["runs"][1]["run_name"] = self.plan["runs"][0]["run_name"]
        self.save_plan()
        with self.assertRaisesRegex(ValueError, "unique"):
            queue.run_queue(self.path, api=lambda *args, **kwargs: self.fail("Unexpected API call"))
        self.plan["source_sha256"] = {}
        self.save_plan()
        with self.assertRaisesRegex(ValueError, "source files differ"):
            queue.run_queue(self.path, api=lambda *args, **kwargs: self.fail("Unexpected API call"))
        self.assertFalse((self.root / "two_Character").exists())


if __name__ == "__main__":
    unittest.main()
