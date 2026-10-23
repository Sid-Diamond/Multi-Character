"""Offline checks for mode settings, output paths, and the shared cost review."""

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import main
import money
import multi_agent as multi
import poc
from test_multi_agent import JUDGE, response


SINGLE_JUDGE = (
    "<scenario_answer>no</scenario_answer>"
    "<deliberation_answer>no_deliberation</deliberation_answer>"
    "<identity_answer>no_identity_reasoning</identity_answer>"
)


class RunSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = copy.deepcopy(main.settings)
        self.settings.update(run_name="offline", model="mock-subject", judge_model="mock-judge", max_cost=10)
        self.enterContext(redirect_stdout(io.StringIO()))

    def test_one_run_name_and_mode_dispatch(self):
        for mode in ("single_agent", "multi_agent", "rejudge"):
            self.assertNotIn("run_name", self.settings[mode])
        self.assertEqual(multi.configuration(self.settings)["run_name"], "offline")
        import run_workflow
        for mode in ("single_agent", "multi_agent", "rejudge"):
            self.settings["mode"] = mode
            with patch.object(run_workflow, "run", return_value="saved") as run:
                self.assertEqual(main.run_selected(self.settings), "saved")
                self.assertEqual(run.call_args.args[0], self.settings)
        passed = main.single_agent_settings(self.settings)
        self.assertEqual(passed["identities"], self.settings["single_agent"]["identities"])
        self.assertNotIn("multi_agent", passed)
        self.assertNotIn("batch_name", passed)

    def test_multi_agent_automatic_cost_check_and_resume_reuse_five_groups(self):
        self.settings["multi_agent"]["trials_per_group"] = {"threat": 5, "continuity": 1}
        self.settings["max_cost"] = 0.17
        calls = []

        def api(model, *args, **kwargs):
            calls.append(model)
            return response(JUDGE if model == "mock-judge" else "<finished/>")

        with patch.object(poc, "OUTPUTS", self.root), \
                patch("builtins.input", side_effect=AssertionError("Cost checks must not prompt")):
            folder = multi.run_experiment(self.settings, api=api)
            self.assertEqual(len(calls), 15)  # Five groups, two agents + one judge each.
            self.assertEqual(folder, self.root / "multi-agent" / "offline")
            self.assertFalse((folder / "continuity/trials/001.json").exists())
            estimate = json.loads((folder / "cost_estimate.json").read_text())
            self.assertEqual(estimate["completed_trials"], 5)
            self.assertAlmostEqual(estimate["spent"], 0.15)
            self.assertAlmostEqual(estimate["estimated_total"], 0.18)
            self.settings["max_cost"] = 10
            multi.run_experiment(self.settings, api=api)
            self.assertEqual(len(calls), 18)
            summary = json.loads((folder / "summary.json").read_text())
            self.assertEqual(summary[-1]["valid_groups"], 6)
            multi.run_experiment(self.settings, api=api)
            self.assertEqual(len(calls), 18)

    def test_single_agent_original_threat_probe_and_automatic_resume(self):
        config = main.single_agent_settings(self.settings)
        config["trials_per_identity"] = {"threat": 2, "continuity": 1}
        config["max_cost"] = 0.2
        calls = []

        def api(model, *args, **kwargs):
            calls.append(model)
            return response(SINGLE_JUDGE if model == "mock-judge" else "Done")

        with patch.object(poc, "OUTPUTS", self.root), patch.object(poc, "api_key", return_value="offline"), \
                patch.object(poc, "api_call", side_effect=api), \
                patch("builtins.input", side_effect=AssertionError("Cost checks must not prompt")):
            folder = poc.run_experiment(config)
            self.assertEqual(len(calls), 10)  # Five threat subject-and-judge pairs.
            self.assertEqual(folder, self.root / "single-agent" / "offline")
            self.assertEqual(len(money.paired_costs(folder)), 5)
            self.assertFalse((folder / "continuity").exists())
            estimate = json.loads((folder / "cost_estimate.json").read_text())
            self.assertAlmostEqual(estimate["spent"], 0.1)
            self.assertAlmostEqual(estimate["estimated_total"], 0.24)
            config["max_cost"] = 10
            poc.run_experiment(config)
            self.assertEqual(len(calls), 24)
            self.assertEqual(len(money.paired_costs(folder)), 12)
            self.assertTrue((folder / "summary_pooled_douglas_combined.csv").exists())
            poc.run_experiment(config)
            self.assertEqual(len(calls), 24)

    def test_shared_review_automatically_continues_within_budget(self):
        with patch("builtins.input", side_effect=AssertionError("Cost checks must not prompt")):
            self.assertTrue(money.review_costs(self.root, [0.01] * 5, 10, 1))
            self.assertTrue(money.review_costs(self.root, [0.01] * 5, 10, 0.1))
            self.assertFalse(money.review_costs(self.root, [0.1] * 5, 10, 0.75))
            self.assertTrue(money.review_costs(self.root, [0.01] * 2, 2, 1))

    def test_historical_single_agent_name_cannot_silently_start_fresh(self):
        historical = self.root / "offline"
        historical.mkdir()
        (historical / "manifest.json").write_text("{}", encoding="utf-8")
        config = main.single_agent_settings(self.settings)
        config["trials_per_identity"] = {"threat": 2, "continuity": 1}
        with patch.object(poc, "OUTPUTS", self.root), patch.object(poc, "api_call") as api:
            with self.assertRaisesRegex(ValueError, "Historical single-agent run exists"):
                poc.run_experiment(config)
            api.assert_not_called()
        self.assertFalse((self.root / "single-agent/offline").exists())


if __name__ == "__main__":
    unittest.main()
