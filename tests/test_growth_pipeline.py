import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).parents[1] / "runtime"))
from growth_pipeline import load_json, process_event, register_event  # noqa: E402
from growth_review import publish_proposal_with_pending_review, transition_review  # noqa: E402
from growth_ticket import TicketError, create_ticket  # noqa: E402


def event(event_id="event-1"):
    return {
        "event_id": event_id, "event_type": "new_capability", "queued_at": "2026-08-27T00:00:00+09:00",
        "target": "venue", "role": "kitchen-terminal", "trust": "observe-only",
        "access": {"capability": "ssh", "identity": "codex@venue"},
        "allowed": ["inspect"], "forbidden": ["edit-config"], "previous": None,
        "capability_fingerprint": "a" * 64, "reason": "fixture",
    }


def proposal(event_id="event-1", risk="low", count=1):
    return {
        "schema_version": 1, "status": "proposal", "proposal_is_not_authority": True,
        "target": "venue", "event_id": event_id, "observed_at": "2026-08-27T00:00:00+09:00",
        "created_at": "2026-08-27T00:01:00+09:00",
        "risk_classes": ["informational", "low", "medium", "high", "prohibited"],
        "analysis": {"summary": "fixture", "known_facts": [], "knowledge_gaps": [], "proposals": [{
            "kind": "health_check", "name": "fixture", "reason": "fixture", "risk": risk,
            "requires_approval": risk != "low", "validation": ["accepted_by_code"],
        } for _ in range(count)]},
    }


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        policy = self.root / "runtime/growth_policy.json"
        policy.parent.mkdir(parents=True)
        policy.write_text(json.dumps({"growth_control": {"max_observation_age_seconds": 86400}}))
        self.event = event()
        self.path = register_event(self.root, self.event)
        self.calls = []
        self.notifications = []

    def tearDown(self):
        self.temp.cleanup()

    def write_observation(self, stale=False, mismatch=False):
        observed_at = datetime.now().astimezone() - (timedelta(days=2) if stale else timedelta())
        path = self.root / "state/growth_observations/venue.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "observed_at": observed_at.isoformat(timespec="seconds"), "target": "venue", "ok": True,
            "event_id": "wrong" if mismatch else self.event["event_id"],
            "capability_fingerprint": self.event["capability_fingerprint"], "observation": {},
        }))

    def runner(self, argv, **kwargs):
        self.calls.append(Path(argv[1]).name)
        if Path(argv[1]).name == "growth_probe.py":
            self.write_observation()
        elif Path(argv[1]).name == "growth_worker.py":
            publish_proposal_with_pending_review(self.root, proposal())
        return SimpleNamespace(returncode=0, stderr="")

    def notifier(self, root, event_value, proposal_value, runner):
        self.notifications.append((event_value["event_id"], len(proposal_value["analysis"]["proposals"])))
        return SimpleNamespace(returncode=0)

    def test_capability_event_starts_probe_then_worker(self):
        state = process_event(self.root, self.path, runner=self.runner, notifier=self.notifier)
        self.assertEqual(self.calls, ["growth_probe.py", "growth_worker.py"])
        self.assertEqual(state["status"], "review_pending")

    def test_probe_failure_does_not_run_worker(self):
        def failed_runner(argv, **kwargs):
            self.calls.append(Path(argv[1]).name)
            path = self.root / "state/growth_observations/venue.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"target": "venue", "event_id": "event-1", "capability_fingerprint": "a" * 64, "ok": False, "failure": {"scope": "observation_transport"}}))
            return SimpleNamespace(returncode=1, stderr="unavailable")
        state = process_event(self.root, self.path, runner=failed_runner, notifier=self.notifier)
        self.assertEqual(self.calls, ["growth_probe.py"])
        self.assertEqual(state["status"], "probe_failed")
        self.assertEqual(state["failure_domain"], "OBSERVATION_FAILURE")

    def test_duplicate_terminal_event_is_not_executed(self):
        process_event(self.root, self.path, runner=self.runner, notifier=self.notifier)
        duplicate = self.root / "state/growth_queue/event-1.json"
        duplicate.parent.mkdir(parents=True, exist_ok=True)
        duplicate.write_text(json.dumps(self.event))
        self.calls.clear()
        process_event(self.root, duplicate, runner=self.runner, notifier=self.notifier)
        self.assertEqual(self.calls, [])

    def test_stale_or_mismatched_observation_is_not_reused(self):
        for stale, mismatch in ((True, False), (False, True)):
            with self.subTest(stale=stale, mismatch=mismatch):
                self.write_observation(stale=stale, mismatch=mismatch)
                self.calls.clear()
                state = load_json(self.root / "state/growth_events/event-1.json")
                state["status"] = "registered"
                (self.root / "state/growth_events/event-1.json").write_text(json.dumps(state))
                if not self.path.exists():
                    self.path.write_text(json.dumps(self.event))
                process_event(self.root, self.path, runner=self.runner, notifier=self.notifier)
                self.assertEqual(self.calls[0], "growth_probe.py")

    def test_successful_proposal_is_notification_target(self):
        state = process_event(self.root, self.path, runner=self.runner, notifier=self.notifier)
        self.assertEqual(self.notifications, [("event-1", 1)])
        self.assertEqual(state["notification"]["status"], "sent")

    def test_discord_failure_keeps_proposal(self):
        def failed_notifier(root, event_value, proposal_value, runner):
            return SimpleNamespace(returncode=1)
        state = process_event(self.root, self.path, runner=self.runner, notifier=failed_notifier)
        self.assertEqual(state["status"], "review_pending")
        self.assertEqual(state["notification"]["status"], "failed")
        self.assertTrue((self.root / "state/growth_proposals/history/event-1.json").exists())


class TicketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def prepare(self, risk="low", count=1):
        value = proposal(risk=risk, count=count)
        publish_proposal_with_pending_review(self.root, value)
        stored = load_json(self.root / "state/growth_proposals/history/event-1.json")
        return stored

    def test_pending_and_rejected_cannot_create_ticket(self):
        value = self.prepare(); proposal_id = value["analysis"]["proposals"][0]["proposal_id"]
        with self.assertRaises(TicketError):
            create_ticket(self.root, "event-1", "tester", [proposal_id])
        transition_review(self.root, "event-1", proposal_id, "rejected", "tester", "reject")
        with self.assertRaises(TicketError):
            create_ticket(self.root, "event-1", "tester", [proposal_id])

    def test_approved_creates_non_executing_ticket(self):
        value = self.prepare(count=3); ids = [item["proposal_id"] for item in value["analysis"]["proposals"]]
        transition_review(self.root, "event-1", ids[0], "approved", "tester", "approve one")
        transition_review(self.root, "event-1", ids[1], "rejected", "tester", "reject one")
        ticket, created = create_ticket(self.root, "event-1", "tester", [ids[0]])
        self.assertTrue(created)
        self.assertEqual(ticket["status"], "ready")
        self.assertEqual(ticket["selected_proposal_ids"], [ids[0]])
        self.assertEqual(ticket["approved_proposal_items"], [value["analysis"]["proposals"][0]])
        self.assertNotIn(ids[1], ticket["selected_proposal_ids"]); self.assertNotIn(ids[2], ticket["selected_proposal_ids"])
        all_ticket, all_created = create_ticket(self.root, "event-1", "tester", all_approved=True)
        self.assertFalse(all_created); self.assertEqual(all_ticket["selected_proposal_ids"], [ids[0]])
        self.assertTrue(ticket["implementation_ticket_is_not_execution_authority"])
        self.assertNotIn("command", ticket)

    def test_prohibited_cannot_create_ticket(self):
        value = self.prepare(risk="prohibited"); proposal_id = value["analysis"]["proposals"][0]["proposal_id"]
        review_path = self.root / "state/growth_reviews/event-1.json"
        review = json.loads(review_path.read_text())
        review["items"][proposal_id].update(status="approved", reviewed_at="2026-08-27T01:00:00+09:00", reviewed_by="tamper", reason="tamper")
        review["aggregate_status"] = "reviewed"
        review_path.write_text(json.dumps(review))
        with self.assertRaises(TicketError):
            create_ticket(self.root, "event-1", "tester", [proposal_id])

    def test_ticket_module_has_no_execution_engine(self):
        source = (Path(__file__).parents[1] / "runtime/growth_ticket.py").read_text(encoding="utf-8")
        for forbidden in ("subprocess", "os.system", "ssh ", "sudo ", "systemctl", "git "):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
