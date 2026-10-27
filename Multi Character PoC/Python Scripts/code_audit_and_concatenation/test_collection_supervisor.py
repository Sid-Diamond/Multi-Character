"""Offline checks for spending and uncertainty across separate batch invocations."""
import socket
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "active_run"))

import collect_remaining_pairs as supervisor


class SupervisorTests(unittest.TestCase):
    def test_threshold_persists_across_batches_and_counts_final_call(self):
        with tempfile.TemporaryDirectory() as d:
            control = Path(d)
            sent = []
            def api(*args, **kwargs):
                sent.append(args)
                return {"id": f"response-{len(sent)}", "usage": {"cost": 0.6}}
            supervisor.GuardedAPI(api, 1.0, "batch1", control)("model", [])
            supervisor.GuardedAPI(api, 1.0, "batch2", control)("model", [])
            with self.assertRaisesRegex(ValueError, "threshold"):
                supervisor.GuardedAPI(api, 1.0, "batch3", control)("model", [])
            self.assertEqual(len(sent), 2)
            self.assertAlmostEqual(supervisor.ledger_state(control)["recorded_cost_usd"], 1.2)

    def test_unknown_remote_error_blocks_new_batch(self):
        with tempfile.TemporaryDirectory() as d:
            control = Path(d)
            def api(*args):
                raise TimeoutError("Remote result unknown")
            with self.assertRaises(TimeoutError):
                supervisor.GuardedAPI(api, 21, "batch1", control)("model", [])
            with self.assertRaisesRegex(ValueError, "uncertain"):
                supervisor.GuardedAPI(lambda *a: self.fail("Must not submit"), 21, "batch2", control)("model", [])
            self.assertEqual(supervisor.ledger_state(control)["uncertain_calls"], [1])

    def test_missing_cost_blocks_next_call(self):
        with tempfile.TemporaryDirectory() as d:
            control = Path(d)
            guarded = supervisor.GuardedAPI(lambda *a: {"id": "one", "usage": {}}, 21, "batch", control)
            guarded("model", [])
            with self.assertRaisesRegex(ValueError, "uncertain"):
                guarded("model", [])

    def test_crashed_inflight_entry_blocks_calls(self):
        with tempfile.TemporaryDirectory() as d:
            control = Path(d)
            supervisor.write(control / "calls/000001.json", {"id": 1, "status": "in_flight"})
            with self.assertRaisesRegex(ValueError, "uncertain"):
                supervisor.GuardedAPI(lambda *a: self.fail("Must not submit"), 21, "batch", control)("model", [])

    def test_known_rejections_distinguish_payment_and_rate_limit(self):
        for code, expected in [(402, (True, False)), (429, (True, True)), (500, (False, False))]:
            with HTTPError("url", code, "test", {}, None) as error:
                self.assertEqual(supervisor.rejection_kind(error), expected)
        self.assertEqual(supervisor.rejection_kind(URLError(socket.gaierror("DNS"))), (True, True))

    def test_remaining_config_preserves_shared_settings_and_roster_order(self):
        plan = {"settings": {"mode": "multi_agent", "model": "fixed-model", "max_cost": 7,
                             "multi_agent": {"n_messages": 10, "trials_per_group": {"threat": 25, "continuity": 25}}}}
        config = supervisor.config_for(plan, "char_inst", {"threat": 0, "continuity": 6}, "fresh")
        self.assertEqual(config["model"], "fixed-model")
        self.assertEqual(config["max_cost"], 7)
        self.assertEqual(config["multi_agent"]["trials_per_group"], {"threat": 0, "continuity": 6})
        self.assertEqual(list(config["multi_agent"]["identities_per_trial"]), list(supervisor.IDENTITIES))
        self.assertEqual(config["multi_agent"]["identities_per_trial"]["Character"], [1])
        self.assertEqual(config["multi_agent"]["identities_per_trial"]["Instance"], [1])
        self.assertEqual(plan["settings"]["multi_agent"]["trials_per_group"]["threat"], 25)


if __name__ == "__main__":
    unittest.main()
