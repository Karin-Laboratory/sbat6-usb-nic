import copy
import json
import tempfile
import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parents[1] / "runtime"))
from growth_review import (  # noqa: E402
    ReviewError,
    canonical_hash,
    ensure_pending_review,
    load_json,
    publish_proposal_with_pending_review,
    transition_review,
    validate_review,
)


def proposal(risk="low", event_id="event-1"):
    return {
        "schema_version": 1,
        "status": "proposal",
        "proposal_is_not_authority": True,
        "target": "venue",
        "event_id": event_id,
        "observed_at": "2026-08-27T00:00:00+09:00",
        "created_at": "2026-08-27T00:01:00+09:00",
        "risk_classes": ["informational", "low", "medium", "high", "prohibited"],
        "analysis": {
            "summary": "Venue proposal fixture",
            "known_facts": [],
            "knowledge_gaps": [],
            "proposals": [{
                "kind": "health_check", "name": "fixture", "reason": "fixture",
                "risk": risk, "requires_approval": risk != "low",
                "validation": ["accepted_by_code"],
            }],
        },
    }


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write_proposal(self, value):
        history = self.root / "state/growth_proposals/history" / f"{value['event_id']}.json"
        latest = self.root / "state/growth_proposals" / f"{value['target']}.json"
        history.parent.mkdir(parents=True, exist_ok=True)
        latest.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        history.write_text(text, encoding="utf-8")
        latest.write_text(text, encoding="utf-8")

    def prepare(self, risk="low"):
        value = proposal(risk)
        self.write_proposal(value)
        review, created = ensure_pending_review(self.root, value)
        return value, review, created

    def test_proposal_generation_creates_pending(self):
        value = proposal()
        review, created = publish_proposal_with_pending_review(self.root, value)
        self.assertTrue(created)
        self.assertEqual(review["status"], "pending")
        self.assertEqual(review["proposal_hash"], canonical_hash(value))
        self.assertEqual(load_json(self.root / "state/growth_proposals/venue.json"), value)

    def test_pending_to_approved(self):
        self.prepare()
        review, changed = transition_review(self.root, "event-1", "approved", "tester", "accepted")
        self.assertTrue(changed)
        self.assertEqual(review["status"], "approved")

    def test_pending_to_rejected(self):
        self.prepare()
        review, changed = transition_review(self.root, "event-1", "rejected", "tester", "not useful")
        self.assertTrue(changed)
        self.assertEqual(review["status"], "rejected")

    def test_unknown_status_rejected(self):
        _, review, _ = self.prepare()
        invalid = dict(review, status="executed")
        with self.assertRaises(ReviewError):
            validate_review(invalid)
        with self.assertRaises(ReviewError):
            transition_review(self.root, "event-1", "executed", "tester", "bad status")

    def test_proposal_hash_mismatch_rejected(self):
        value, _, _ = self.prepare()
        changed = copy.deepcopy(value)
        changed["analysis"]["summary"] = "changed"
        self.write_proposal(changed)
        with self.assertRaises(ReviewError):
            transition_review(self.root, "event-1", "approved", "tester", "stale")

    def test_prohibited_approve_rejected(self):
        self.prepare("prohibited")
        with self.assertRaises(ReviewError):
            transition_review(self.root, "event-1", "approved", "tester", "approve")

    def test_prohibited_reject_succeeds(self):
        self.prepare("prohibited")
        review, changed = transition_review(self.root, "event-1", "rejected", "tester", "prohibited")
        self.assertTrue(changed)
        self.assertEqual(review["status"], "rejected")

    def test_audit_log_is_appended(self):
        self.prepare()
        transition_review(self.root, "event-1", "approved", "tester", "accepted")
        lines = (self.root / "state/growth_review_audit.jsonl").read_text(encoding="utf-8").splitlines()
        entries = [json.loads(line) for line in lines]
        self.assertEqual([entry["new_status"] for entry in entries], ["pending", "approved"])
        self.assertEqual(entries[1]["actor"], "tester")

    def test_final_review_is_not_overwritten(self):
        self.prepare()
        approved, _ = transition_review(self.root, "event-1", "approved", "tester", "accepted")
        with self.assertRaises(ReviewError):
            transition_review(self.root, "event-1", "rejected", "tester2", "changed mind")
        stored = load_json(self.root / "state/growth_reviews/event-1.json")
        self.assertEqual(stored, approved)

    def test_old_approval_not_reused_after_proposal_update(self):
        self.prepare()
        approved, _ = transition_review(self.root, "event-1", "approved", "tester", "accepted")
        changed = copy.deepcopy(proposal(event_id="event-2"))
        changed["analysis"]["summary"] = "replacement proposal"
        new_review, created = publish_proposal_with_pending_review(self.root, changed)
        self.assertTrue(created)
        self.assertEqual(new_review["status"], "pending")
        self.assertEqual(new_review["proposal_hash"], canonical_hash(changed))
        old_stored = load_json(self.root / "state/growth_reviews/event-1.json")
        self.assertEqual(old_stored, approved)
        self.assertNotEqual(old_stored["proposal_hash"], new_review["proposal_hash"])


if __name__ == "__main__":
    unittest.main()
