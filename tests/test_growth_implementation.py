import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from growth_implementation import ImplementationError, read_audit, transition  # noqa: E402
from growth_review import load_json, publish_proposal_with_pending_review, transition_review  # noqa: E402
from growth_ticket import create_ticket  # noqa: E402


def proposal():
    return {
        "schema_version": 1, "status": "proposal", "proposal_is_not_authority": True,
        "target": "venue", "event_id": "event-1", "observed_at": "2026-08-27T00:00:00+09:00",
        "created_at": "2026-08-27T00:01:00+09:00",
        "risk_classes": ["informational", "low", "medium", "high", "prohibited"],
        "analysis": {"summary": "fixture", "known_facts": [], "knowledge_gaps": [], "proposals": [
            {"kind": "health_check", "name": "check", "reason": "useful", "risk": "low",
             "requires_approval": False, "validation": ["accepted_by_code"]}
        ]},
    }


class ImplementationLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        publish_proposal_with_pending_review(self.root, proposal())
        stored = load_json(self.root / "state/growth_proposals/history/event-1.json")
        self.proposal_id = stored["analysis"]["proposals"][0]["proposal_id"]
        transition_review(self.root, "event-1", self.proposal_id, "approved", "reviewer", "approved")
        self.ticket, _ = create_ticket(self.root, "event-1", "creator", [self.proposal_id])

    def tearDown(self):
        self.temp.cleanup()

    def change(self, status, **kwargs):
        return transition(self.root, self.ticket["ticket_id"], status, "human (uid=1)", "reason", **kwargs)

    def test_ready_to_implemented_to_verified(self):
        record = self.change("implemented", git_checkpoint="9e662a9")
        self.assertEqual(record["status"], "implemented")
        self.assertEqual(record["implemented"]["git_checkpoint"], "9e662a9")
        record = self.change("verified", verification_summary="28 tests and Venue E2E passed")
        self.assertEqual(record["status"], "verified")
        self.assertEqual(record["approved_item_ids"], [self.proposal_id])
        ticket = load_json(self.root / "state/growth_implementation_queue" / f"{self.ticket['ticket_id']}.json")
        self.assertEqual(ticket["status"], "verified")

    def test_ready_to_verified_is_refused(self):
        with self.assertRaises(ImplementationError):
            self.change("verified")

    def test_verified_cannot_move_back_to_implemented(self):
        self.change("implemented", git_checkpoint="9e662a9")
        self.change("verified")
        with self.assertRaises(ImplementationError):
            self.change("implemented", git_checkpoint="abcdef0")

    def test_cancelled_only_from_ready_and_is_terminal(self):
        record = self.change("cancelled")
        self.assertEqual(record["status"], "cancelled")
        with self.assertRaises(ImplementationError):
            self.change("implemented", git_checkpoint="9e662a9")
        # A separate ticket may not be cancelled after implementation either.
        # Recreate a fixture root because ticket IDs are deterministic.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            publish_proposal_with_pending_review(root, proposal())
            stored = load_json(root / "state/growth_proposals/history/event-1.json")
            pid = stored["analysis"]["proposals"][0]["proposal_id"]
            transition_review(root, "event-1", pid, "approved", "reviewer", "approved")
            ticket, _ = create_ticket(root, "event-1", "creator", [pid])
            transition(root, ticket["ticket_id"], "implemented", "human", "done", git_checkpoint="9e662a9")
            with self.assertRaises(ImplementationError):
                transition(root, ticket["ticket_id"], "cancelled", "human", "cancel")

    def test_unknown_status_is_refused(self):
        with self.assertRaises(ImplementationError):
            self.change("unknown")

    def test_hash_and_review_binding_mismatch_is_refused(self):
        path = self.root / "state/growth_implementation_queue" / f"{self.ticket['ticket_id']}.json"
        ticket = json.loads(path.read_text())
        ticket["proposal_hash"] = "0" * 64
        path.write_text(json.dumps(ticket))
        with self.assertRaises(ImplementationError):
            self.change("implemented", git_checkpoint="9e662a9")

    def test_audit_is_appended_and_hash_chained(self):
        self.change("implemented", git_checkpoint="9e662a9")
        self.change("verified", verification_summary="passed")
        entries = read_audit(self.root)
        self.assertEqual([entry["new_status"] for entry in entries], ["implemented", "verified"])
        self.assertEqual(entries[1]["previous_hash"], entries[0]["entry_hash"])
        self.assertEqual(entries[0]["approved_item_ids"], [self.proposal_id])

    def test_lifecycle_module_has_no_execution_engine(self):
        source = (ROOT / "runtime/growth_implementation.py").read_text(encoding="utf-8")
        for forbidden in ("subprocess", "os.system", "ssh ", "sudo ", "systemctl", "git "):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
