import copy
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).parents[1] / "runtime" / "growth_worker.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("growth_worker", MODULE_PATH)
growth_worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(growth_worker)


POLICY = {
    "proposal_risk_classes": ["informational", "low", "medium", "high", "prohibited"],
    "proposal_constraints": {
        "approval_required_at_or_above": "medium",
        "kind_risk_floor": {"restart_policy": "medium"},
    },
}


def response(item):
    return {"summary": "summary", "known_facts": [], "knowledge_gaps": [], "proposals": [item]}


class ProposalValidationTests(unittest.TestCase):
    def test_model_process_has_no_agent_tools_or_ssh_agent(self):
        completed = mock.Mock(returncode=0, stdout='{"summary":"ok","known_facts":[],"knowledge_gaps":[],"proposals":[]}', stderr="")
        with mock.patch.object(growth_worker.subprocess, "run", return_value=completed) as run:
            with mock.patch.dict(growth_worker.os.environ, {"SSH_AUTH_SOCK": "/tmp/agent"}):
                growth_worker.ask_model({"fixed": "snapshot"})
        argv = run.call_args.args[0]
        self.assertIn("read-only", argv)
        for feature in ("shell_tool", "browser_use", "apps", "plugins", "computer_use"):
            self.assertIn(feature, argv)
        self.assertNotIn("SSH_AUTH_SOCK", run.call_args.kwargs["env"])

    def test_unknown_risk_is_rejected(self):
        item = {"kind": "health_check", "name": "check", "reason": "reason", "risk": "tiny", "requires_approval": False}
        with self.assertRaises(ValueError):
            growth_worker.validate(response(item), copy.deepcopy(POLICY))

    def test_restart_policy_gets_medium_floor_and_approval(self):
        item = {"kind": "restart_policy", "name": "restart review", "reason": "review only", "risk": "low", "requires_approval": False}
        checked = growth_worker.validate(response(item), copy.deepcopy(POLICY))["proposals"][0]
        self.assertEqual(checked["risk"], "medium")
        self.assertTrue(checked["requires_approval"])
        self.assertIn("risk_raised_by_kind_floor", checked["validation"])

    def test_dangerous_text_is_classified_prohibited(self):
        item = {"kind": "other", "name": "distribute a new SSH key", "reason": "privilege expansion", "risk": "low", "requires_approval": False}
        checked = growth_worker.validate(response(item), copy.deepcopy(POLICY))["proposals"][0]
        self.assertEqual(checked["risk"], "prohibited")
        self.assertTrue(checked["requires_approval"])
        self.assertIn("classified_prohibited_by_code", checked["validation"])

    def test_secret_like_memory_is_redacted(self):
        text = "token = abc123\nordinary note\n-----BEGIN PRIVATE KEY-----\ndata\n-----END PRIVATE KEY-----"
        redacted = growth_worker.redacted_text(text)
        self.assertNotIn("abc123", redacted)
        self.assertNotIn("\ndata\n", redacted)


if __name__ == "__main__":
    unittest.main()
