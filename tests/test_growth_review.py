import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1] / "runtime"))
import growth_review  # noqa: E402
from growth_review import (  # noqa: E402
    ReviewError, assign_item_identities, canonical_hash, load_json,
    migrate_legacy_pending_review, publish_proposal_with_pending_review,
    transition_review, validate_review_binding,
)

def proposal(count=7, event_id="event-1", prohibited_index=None):
    items = []
    for index in range(count):
        risk = "prohibited" if index == prohibited_index else ("medium" if index % 3 == 2 else "low")
        items.append({"kind": "health_check", "name": f"proposal {index + 1}", "reason": f"reason {index + 1}", "risk": risk, "requires_approval": risk != "low", "validation": ["accepted_by_code"]})
    return {"schema_version": 1, "status": "proposal", "proposal_is_not_authority": True, "target": "venue", "event_id": event_id, "observed_at": "2026-08-27T00:00:00+09:00", "created_at": "2026-08-27T00:01:00+09:00", "risk_classes": ["informational", "low", "medium", "high", "prohibited"], "analysis": {"summary": "fixture", "known_facts": [], "knowledge_gaps": [], "proposals": items}}

class ItemReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()

    def publish(self, value=None):
        value = value or proposal(); review, created = publish_proposal_with_pending_review(self.root, value)
        stored = load_json(self.root / f"state/growth_proposals/history/{value['event_id']}.json")
        return stored, review, created

    def test_seven_items_create_seven_pending_reviews_with_stable_ids(self):
        stored, review, created = self.publish()
        self.assertTrue(created); self.assertEqual(len(review["items"]), 7)
        self.assertTrue(all(item["status"] == "pending" for item in review["items"].values()))
        self.assertEqual(review["aggregate_status"], "pending")
        self.assertEqual([item["proposal_id"] for item in stored["analysis"]["proposals"]], [item["proposal_id"] for item in assign_item_identities(proposal())["analysis"]["proposals"]])

    def test_item_approve_reject_and_remaining_pending(self):
        stored, _, _ = self.publish(); ids = [item["proposal_id"] for item in stored["analysis"]["proposals"]]
        review, _ = transition_review(self.root, "event-1", ids[0], "approved", "tester", "useful")
        self.assertEqual(review["aggregate_status"], "partially_reviewed")
        review, _ = transition_review(self.root, "event-1", ids[1], "rejected", "tester", "duplicate")
        self.assertEqual(review["items"][ids[0]]["status"], "approved")
        self.assertEqual(review["items"][ids[1]]["status"], "rejected")
        self.assertTrue(all(review["items"][pid]["status"] == "pending" for pid in ids[2:]))

    def test_all_items_reviewed_derives_reviewed(self):
        stored, _, _ = self.publish(); ids = [item["proposal_id"] for item in stored["analysis"]["proposals"]]
        review = None
        for index, proposal_id in enumerate(ids):
            review, _ = transition_review(self.root, "event-1", proposal_id, "approved" if index % 2 else "rejected", "tester", "decision")
        self.assertEqual(review["aggregate_status"], "reviewed")

    def test_item_hash_mismatch_and_unknown_item_are_rejected(self):
        stored, _, _ = self.publish(); proposal_id = stored["analysis"]["proposals"][0]["proposal_id"]
        stored["analysis"]["proposals"][0]["name"] = "tampered"
        (self.root / "state/growth_proposals/history/event-1.json").write_text(json.dumps(stored))
        with self.assertRaises(ReviewError): transition_review(self.root, "event-1", proposal_id, "approved", "tester", "bad")
        clean_root = Path(tempfile.mkdtemp(dir=self.root)); publish_proposal_with_pending_review(clean_root, proposal(event_id="event-2"))
        with self.assertRaises(ReviewError): transition_review(clean_root, "event-2", "p-0000000000000000", "approved", "tester", "bad")

    def test_prohibited_approve_refused_reject_allowed(self):
        stored, _, _ = self.publish(proposal(prohibited_index=0)); proposal_id = stored["analysis"]["proposals"][0]["proposal_id"]
        with self.assertRaises(ReviewError): transition_review(self.root, "event-1", proposal_id, "approved", "tester", "no")
        review, _ = transition_review(self.root, "event-1", proposal_id, "rejected", "tester", "prohibited")
        self.assertEqual(review["items"][proposal_id]["status"], "rejected")

    def test_item_audit_contains_proposal_snapshot_and_chain(self):
        stored, _, _ = self.publish(); item = stored["analysis"]["proposals"][0]
        transition_review(self.root, "event-1", item["proposal_id"], "approved", "tester", "teacher reason")
        entries = growth_review.read_audit(self.root); entry = entries[-1]
        self.assertEqual(entry["proposal_id"], item["proposal_id"]); self.assertEqual(entry["proposal_item"]["name"], item["name"])
        self.assertEqual(entry["human_review_reason"], "teacher reason"); self.assertIsNotNone(entry["entry_hash"])

    def test_crash_journal_reconciles_item_review(self):
        stored, _, _ = self.publish(); proposal_id = stored["analysis"]["proposals"][0]["proposal_id"]
        with mock.patch.object(growth_review, "append_audit", side_effect=RuntimeError("crash")):
            with self.assertRaises(RuntimeError): transition_review(self.root, "event-1", proposal_id, "approved", "tester", "accepted")
        self.assertEqual(growth_review.reconcile_review_journals(self.root), ["event-1"])
        review = load_json(self.root / "state/growth_reviews/event-1.json")
        self.assertEqual(review["items"][proposal_id]["status"], "approved")

    def test_legacy_pending_migrates_but_final_refuses(self):
        raw = proposal(); enriched = assign_item_identities(raw)
        history = self.root / "state/growth_proposals/history/event-1.json"; history.parent.mkdir(parents=True); history.write_text(json.dumps(raw))
        latest = self.root / "state/growth_proposals/venue.json"; latest.parent.mkdir(parents=True, exist_ok=True); latest.write_text(json.dumps(raw))
        review_path = self.root / "state/growth_reviews/event-1.json"; review_path.parent.mkdir(parents=True)
        legacy = {"schema_version": 1, "event_id": "event-1", "target": "venue", "proposal_hash": canonical_hash(raw), "status": "pending", "created_at": "old", "reviewed_at": None, "reviewed_by": None, "reason": None}
        review_path.write_text(json.dumps(legacy)); migrated, changed = migrate_legacy_pending_review(self.root, "event-1", "tester")
        self.assertTrue(changed); self.assertEqual(len(migrated["items"]), 7); self.assertEqual(migrated["aggregate_status"], "pending")
        self.assertEqual(load_json(latest), enriched)
        raw2 = proposal(event_id="event-2"); history2 = self.root / "state/growth_proposals/history/event-2.json"; history2.write_text(json.dumps(raw2))
        legacy.update(event_id="event-2", proposal_hash=canonical_hash(raw2), status="approved", reviewed_at="time", reviewed_by="human", reason="legacy")
        (self.root / "state/growth_reviews/event-2.json").write_text(json.dumps(legacy))
        with self.assertRaises(ReviewError): migrate_legacy_pending_review(self.root, "event-2", "tester")

if __name__ == "__main__": unittest.main()
