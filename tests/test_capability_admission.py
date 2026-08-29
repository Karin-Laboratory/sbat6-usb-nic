import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parents[1] / "runtime"))
from capability_admission import evaluate, summary, validate, write_reviews


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "state").mkdir()
        (self.root / "runtime").mkdir()
        (self.root / "state/capabilities.json").write_text(json.dumps({"targets": {
            "justnottoday": {"access": {"capability": "ssh-forced-command", "identity": "root@justnottoday"}, "allowed": ["inspect"], "forbidden": ["edit-config"]},
            "z4g4": {"access": {"capability": "discovery-presence-only", "identity": "z4g4@192.168.0.55"}, "allowed": [], "forbidden": ["ssh-login"]},
        }}))

    def tearDown(self):
        self.tmp.cleanup()

    def proposal(self, target="justnottoday"):
        return {"event_id": "e1", "target": target, "analysis": {"proposals": []}}

    def item(self, **values):
        base = {"kind": "health_check", "name": "read-only patrol", "reason": "observe status", "risk": "low", "requires_approval": False, "item_hash": "a" * 64}
        base.update(values)
        return base

    def test_forced_command_is_read_only_pass(self):
        record = evaluate(self.root, self.proposal(), self.item())
        self.assertEqual(record["result"], "PASS_READ_ONLY")
        self.assertIn("existing capability boundary only", record["mitigations"])

    def test_unknown_web_is_read_only_and_untrusted(self):
        record = evaluate(self.root, self.proposal(), self.item(name="Daily Estate Discovery Web GET", remote_input={"type": "web"}))
        self.assertEqual(record["result"], "PASS_READ_ONLY")
        self.assertTrue(record["remote_input"]["untrusted"])
        self.assertFalse(record["remote_input"]["command_execution_link"])

    def test_root_key_is_not_automatic_pass(self):
        record = evaluate(self.root, self.proposal(), self.item(name="new SSH root key", reason="add key", requires_approval=True))
        self.assertEqual(record["result"], "PASS_WITH_HUMAN_APPROVAL")
        self.assertTrue(record["approval_required"])

    def test_z4g4_unrestricted_ssh_is_rejected(self):
        record = evaluate(self.root, self.proposal("z4g4"), self.item(name="unrestricted general root SSH", reason="login"))
        self.assertEqual(record["result"], "REJECT")

    def test_write_without_rollback_is_revise(self):
        record = evaluate(self.root, self.proposal(), self.item(kind="restart_policy", name="restart service", reason="write and restart", requires_approval=True))
        self.assertEqual(record["result"], "REVISE")

    def test_write_with_rollback_is_human_approval(self):
        record = evaluate(self.root, self.proposal(), self.item(kind="restart_policy", name="restart service", reason="write and restart", requires_approval=True, rollback="snapshot and restore"))
        self.assertEqual(record["result"], "PASS_WITH_HUMAN_APPROVAL")

    def test_unknown_evidence_is_not_pass(self):
        record = evaluate(self.root, self.proposal(), self.item(evidence_status="unknown"))
        self.assertEqual(record["result"], "UNKNOWN")

    def test_secrets_are_not_stored(self):
        record = evaluate(self.root, self.proposal(), self.item(credentials={"type": "ssh", "token": "do-not-store"}))
        validate(record)
        self.assertNotIn("do-not-store", json.dumps(record))

    def test_write_reviews_and_human_summary(self):
        proposal = self.proposal()
        proposal["analysis"]["proposals"] = [self.item()]
        records = write_reviews(self.root, proposal)
        self.assertEqual(len(records), 1)
        self.assertIn("PASS_READ_ONLY", summary(records[0]))
        stored = next((self.root / "state/capability_reviews").glob("*.json"))
        self.assertEqual(json.loads(stored.read_text())["linked_growth_proposal"], "e1")


if __name__ == "__main__":
    unittest.main()
