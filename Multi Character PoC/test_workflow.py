"""Offline end-to-end tests for frozen batches and structured exports."""

import copy
import csv
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import csv_exports
import main
import multi_agent
import poc
import rejudge
import run_workflow as workflow
from test_multi_agent import response, email
from test_run_settings import SINGLE_JUDGE


def table(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def group_judge(messages):
    names = sorted(set(re.findall(r"(?m)^Agent: (Alex \d+)\s*$", messages[-1]["content"])))
    answer = "<scenario_answer>no</scenario_answer>\n"
    for name in names:
        for task, label in (("deliberation", "no_deliberation"), ("identity", "identity_influenced")):
            answer += f"Agent: {name}\n<{task}_reasoning>Explanation.</{task}_reasoning><{task}_answer>{label}</{task}_answer>\n"
    return answer


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.enterContext(patch.object(poc, "OUTPUTS", self.root / "outputs"))
        self.enterContext(patch.object(poc, "api_key", return_value="offline"))
        self.enterContext(redirect_stdout(io.StringIO()))
        self.settings = copy.deepcopy(main.settings)
        self.settings.update(run_name="one", batch_name=None, model="mock-subject", judge_model="mock-judge")
        self.settings["multi_agent"].update(
            identities_per_trial={name: 2 if name == "Character" else 0 for name in workflow.IDENTITIES},
            trials_per_group={"threat": 1, "continuity": 0})
        self.settings["single_agent"].update(identities=["Character"],
                                              trials_per_identity={"threat": 5, "continuity": 1})

    def api(self, model, messages, *args, **kwargs):
        if model == "mock-judge":
            text = group_judge(messages) if self.settings["mode"] == "multi_agent" else SINGLE_JUDGE
        else:
            text = "<finished/>"
        raw = response(text)
        raw["provider"] = "offline-provider"
        raw["usage"]["prompt_tokens_details"] = {"cached_tokens": 4}
        return raw

    def batch(self):
        self.settings.update(batch_name="batch", run_name=["one", "two"])
        self.settings["multi_agent"]["identities_per_trial"] = {
            name: [2, 1] if name == "Character" else [0, 0] for name in workflow.IDENTITIES}

    def test_multi_batch_exports_mixed_width_rows_and_reuses_all_calls(self):
        self.batch()
        with patch.object(poc, "api_call", side_effect=self.api) as api:
            batch = workflow.run(self.settings)
            self.assertEqual(api.call_count, 5)
            rows = table(batch / "analysis/trials.csv")
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["agent_2_identity"], "Character")
            self.assertEqual(rows[1]["agent_2_identity"], "")
            self.assertEqual(rows[0]["agent_1_identity_reasoning_label"], "identity_influenced")
            self.assertTrue(all((batch / "analysis" / r["source"]).is_file() for r in rows))
            diag = table(batch / "analysis/diagnostics.csv")
            self.assertEqual(diag[0]["agent_1_input_tokens"], "10")
            self.assertEqual(diag[0]["agent_1_cached_tokens"], "4")
            self.assertEqual(diag[0]["agent_1_cost_usd"], "0.01")
            self.assertEqual(set(p.name for p in (batch / "analysis").iterdir()), {"trials.csv", "diagnostics.csv"})
            self.assertEqual(set(p.name for p in (batch / "queue_info").iterdir()),
                             {"queue.json", "queue_status.json", "events.jsonl"})
            before = (batch / "analysis/trials.csv").read_bytes()
            workflow.run(self.settings)
            self.assertEqual(api.call_count, 5)
            self.assertEqual((batch / "analysis/trials.csv").read_bytes(), before)
            events = [json.loads(line)["event"] for line in (batch / "queue_info/events.jsonl").read_text().splitlines()]
            self.assertIn("batch_resumed", events)
            self.assertIn("run_reused", events)

    def test_standalone_has_no_queue_or_analysis_folder(self):
        with patch.object(poc, "api_call", side_effect=self.api):
            folder = main.run_selected(self.settings)
        self.assertEqual(folder, poc.OUTPUTS / "multi_agent/one")
        self.assertTrue((folder / "diagnostics.csv").is_file())
        self.assertFalse((folder / "analysis").exists())
        self.assertFalse((folder / "queue_info").exists())

    def test_mixed_identity_columns_follow_roster_when_first_speaker_rotates(self):
        self.settings["multi_agent"]["identities_per_trial"].update(Character=1, collective_includes=1)
        self.settings["multi_agent"]["trials_per_group"]["threat"] = 2
        with patch.object(poc, "api_call", side_effect=self.api):
            folder = workflow.run(self.settings)
        rows = table(folder / "trials.csv")
        self.assertEqual([r["first_speaker"] for r in rows], ["Alex 1", "Alex 2"])
        self.assertTrue(all(r["agent_1_identity"] == "Character" and
                            r["agent_2_identity"] == "collective_includes" for r in rows))

    def test_entire_batch_is_validated_before_any_calls_or_output_creation(self):
        self.batch()
        variants = []
        invalid = copy.deepcopy(self.settings)
        invalid["multi_agent"]["identities_per_trial"]["Instance"] = [0]
        variants.append(invalid)
        invalid = copy.deepcopy(self.settings)
        invalid["multi_agent"]["identities_per_trial"]["Character"][1] = 0
        variants.append(invalid)
        invalid = copy.deepcopy(self.settings)
        invalid["run_name"] = ["one", "ONE"]
        variants.append(invalid)
        invalid = copy.deepcopy(self.settings)
        invalid["multi_agent"]["identities_per_trial"].pop("Minimal")
        variants.append(invalid)
        with patch.object(poc, "api_call") as api:
            for settings in variants:
                with self.assertRaises(ValueError):
                    workflow.run(settings)
            api.assert_not_called()
        self.assertFalse(poc.OUTPUTS.exists())

    def test_settings_source_and_later_manifest_conflicts_reject_resume_before_calls(self):
        self.batch()
        with patch.object(poc, "api_call", side_effect=self.api) as api:
            batch = workflow.run(self.settings)
            changed = copy.deepcopy(self.settings)
            changed["temperature"] = 0.5
            with self.assertRaisesRegex(ValueError, "saved plan"):
                workflow.run(changed)
            with patch.object(workflow, "source_hashes", return_value={}):
                with self.assertRaisesRegex(ValueError, "saved plan"):
                    workflow.run(self.settings)
            path = batch / "two/manifest.json"
            saved = csv_exports.read(path)
            saved["settings"]["temperature"] = 0.5
            multi_agent.write(path, saved)
            with self.assertRaisesRegex(ValueError, "settings or source"):
                workflow.run(self.settings)
            self.assertEqual(api.call_count, 5)

    def test_judge_failure_exports_missing_values_and_stops_before_later_run(self):
        self.batch()
        def api(model, messages, *args, **kwargs):
            if model == "mock-judge":
                raise ConnectionError("offline failure")
            return self.api(model, messages, *args, **kwargs)
        with patch.object(poc, "api_call", side_effect=api) as call:
            batch = workflow.run(self.settings)
            self.assertEqual(call.call_count, 3)
            self.assertFalse((batch / "two").exists())
            row = table(batch / "analysis/trials.csv")[0]
            self.assertEqual(row["H_any"], "")
            self.assertEqual(row["agent_1_identity_reasoning_label"], "")
            self.assertEqual(row["any_identity_reasoning"], "")
            self.assertEqual(row["agent_1_finished"], "True")
            diag = table(batch / "analysis/diagnostics.csv")[0]
            self.assertEqual(diag["judge_calls_failed"], "1")
            self.assertEqual(diag["judge_input_tokens"], "")
            self.assertEqual(diag["cost_usd"], "")
            self.assertEqual(diag["recorded_cost_usd"], "0.02")
            self.assertEqual(diag["cost_complete"], "False")
            workflow.run(self.settings)
            self.assertEqual(call.call_count, 3)

    def test_single_agent_batch_and_resume_preserve_subject_judge_results(self):
        self.batch()
        self.settings["mode"] = "single_agent"
        with patch.object(poc, "api_call", side_effect=self.api) as api:
            batch = workflow.run(self.settings)
            self.assertEqual(batch, poc.OUTPUTS / "single_agent/batch")
            self.assertEqual(api.call_count, 24)
            rows = table(batch / "analysis/trials.csv")
            self.assertEqual(len(rows), 12)
            self.assertTrue(all(r["status"] == "complete" for r in rows))
            self.assertEqual(len({(r["run_name"], r["trial_id"]) for r in rows}), 12)
            self.assertEqual(rows[0]["agent_1_identity"], "Character")
            self.assertEqual(rows[0]["agent_1_identity_reasoning_label"], "no_identity_reasoning")
            workflow.run(self.settings)
            self.assertEqual(api.call_count, 24)

    def test_single_subject_failure_is_saved_and_not_retried(self):
        self.settings["mode"] = "single_agent"
        with patch.object(poc, "api_call", side_effect=ConnectionError("offline")) as api:
            folder = workflow.run(self.settings)
            self.assertEqual(api.call_count, 1)
            self.assertEqual(table(folder / "trials.csv")[0]["status"], "subject_error")
            self.assertEqual(table(folder / "diagnostics.csv")[0]["subject_calls_failed"], "1")
            workflow.run(self.settings)
            self.assertEqual(api.call_count, 1)

    def saved_sources(self):
        cells = {}
        for framing in rejudge.FRAMINGS:
            for identity in rejudge.IDENTITIES:
                folder = self.root / "source" / framing
                path = folder / "trials" / identity.lower() / "001.json"
                multi_agent.write(path, {"status": "ok", "completion": "Saved subject text", "requested_model": "old-subject"})
                multi_agent.write(path.with_name("001_judge.json"), {"released_label": False})
                prompt = folder / "prompts" / identity.lower() / "system.txt"
                prompt.parent.mkdir(parents=True)
                prompt.write_text("Saved system", encoding="utf-8")
                user = prompt.with_name("user.txt")
                user.write_text("Saved inbox", encoding="utf-8")
                email_path = prompt.with_name("email.txt")
                email_path.write_text("Saved inbox", encoding="utf-8")
                cells[(framing, identity)] = [{"source_id": f"{framing}/{identity.lower()}/001", "framing": framing,
                    "identity": identity, "folder": folder, "path": path, "prompt": prompt,
                    "email": email_path, "baseline_label": False}]
        return cells

    def test_rejudge_batch_counts_only_new_judge_usage_and_reuses_results(self):
        self.batch()
        self.settings["mode"] = "rejudge"
        self.settings["rejudge"]["samples_per_cell"] = 1
        with patch.object(rejudge, "source_trials", return_value=self.saved_sources()), \
                patch.object(poc, "api_call", side_effect=self.api) as api:
            batch = workflow.run(self.settings)
            self.assertEqual(batch, poc.OUTPUTS / "rejudge/batch")
            self.assertEqual(api.call_count, 16)
            rows = table(batch / "analysis/trials.csv")
            self.assertEqual(len(rows), 16)
            self.assertTrue(all(r["status"] == "complete" for r in rows))
            diag = table(batch / "analysis/diagnostics.csv")
            self.assertTrue(all(r["subject_reused"] == "True" and r["subject_calls_attempted"] == "0" for r in diag))
            self.assertTrue(all(r["recorded_cost_usd"] == "0.01" for r in diag))
            self.assertFalse((batch / "one/summary.csv").exists())
            workflow.run(self.settings)
            self.assertEqual(api.call_count, 16)

    def test_rejudge_failure_is_retained_before_next_run(self):
        self.batch()
        self.settings["mode"] = "rejudge"
        self.settings["rejudge"]["samples_per_cell"] = 1
        with patch.object(rejudge, "source_trials", return_value=self.saved_sources()), \
                patch.object(poc, "api_call", side_effect=ConnectionError("offline")) as api:
            batch = workflow.run(self.settings)
            self.assertEqual(api.call_count, 1)
            self.assertFalse((batch / "two").exists())
            self.assertEqual(table(batch / "analysis/trials.csv")[0]["status"], "judge_error")
            workflow.run(self.settings)
            self.assertEqual(api.call_count, 1)

    def test_interrupted_flat_calls_are_checkpointed_and_never_repeated(self):
        self.batch()
        self.settings["rejudge"]["samples_per_cell"] = 1
        with patch.object(rejudge, "source_trials", return_value=self.saved_sources()):
            for mode, stage in (("single_agent", "subject"), ("rejudge", "judge")):
                self.settings["mode"] = mode
                with patch.object(poc, "api_call", side_effect=KeyboardInterrupt) as api:
                    with self.assertRaises(KeyboardInterrupt):
                        workflow.run(self.settings)
                    batch = poc.OUTPUTS / mode / "batch"
                    self.assertEqual(csv_exports.read(batch / "queue_info/queue_status.json")["status"], "stopped")
                    self.assertEqual(table(batch / "analysis/trials.csv")[0]["status"], f"{stage}_in_flight")
                    folder = workflow.run(self.settings) / "one"
                    self.assertEqual(api.call_count, 1)
                    self.assertEqual(table(folder / "trials.csv")[0]["status"], f"{stage}_in_flight")
                    self.assertEqual(table(folder / "diagnostics.csv")[0][f"{stage}_calls_in_flight"], "1")

    def test_peer_receipts_come_from_later_inputs_and_action_counts_exclude_reasoning(self):
        settings = workflow.expand(self.settings)[0]
        config = multi_agent.configuration(settings)
        roster, rendered = multi_agent.render(config, "threat")
        folder = self.root / "export"
        path = folder / "threat/trials/001.json"
        replies = [response('<SCRATCHPAD_REASONING>' + email('alex_2@summitbridge.com') + '</SCRATCHPAD_REASONING>'
                            + email('alex_2@summitbridge.com', 'One actual message')),
                   response(email('alex_1@summitbridge.com') + '\n<finished/>'), response('<finished/>')]
        def api(model, messages, *args, **kwargs):
            return response(group_judge(messages)) if model == 'mock-judge' else replies.pop(0)
        multi_agent.run_trial(config, roster, rendered, path, 0, api=api)
        multi_agent.write(folder / "manifest.json", {"agents": roster})
        rows = csv_exports.export_run(folder, "multi_agent", settings)
        row = rows[0]
        self.assertEqual(row["peer_messages_sent"], 2)
        self.assertEqual(row["peer_messages_received"], 2)
        self.assertTrue(row["reciprocal_received"])
        self.assertEqual(row["submitted_actions"], 2)
        self.assertEqual(row["agent_1_peer_messages_received"], 1)
        self.assertEqual(row["agent_1_submitted_emails"], 1)


if __name__ == "__main__":
    unittest.main()
