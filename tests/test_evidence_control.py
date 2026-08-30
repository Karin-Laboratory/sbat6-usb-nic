import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parents[1] / "runtime"))
from evidence_control import (assert_action_allowed, audit_report, authorize_action,
    checkpoint_paths, compare_artifacts, evidence_record, historical_freshness,
    readiness, redact, validate_claim)


def record(source, digest="a" * 64, status="COLLECTED", timestamp="2026-08-30T10:00:00+09:00"):
    return evidence_record(audited_host="raspi2", asset="controller", source_type=source,
        path="/example", sha256=digest, collected_by="test", collection_status=status,
        evidence_timestamp=timestamp, reachability="reachable" if status == "COLLECTED" else "unreachable")


class EvidenceControlTests(unittest.TestCase):
    def test_zen3_backfill_records_required_identity_without_secrets(self):
        root = Path(__file__).parents[1]
        case = json.loads((root / "evidence/cases/zen3-2026-08-30.json").read_text())
        required = {"audited_host", "asset", "source_type", "path", "sha256", "git_commit",
            "mtime", "exec_start", "evidence_timestamp", "collected_by", "reachability",
            "collection_status", "notes"}
        self.assertTrue(case["artifacts"])
        self.assertTrue(all(set(item) == required for item in case["artifacts"]))
        self.assertFalse(case["authority_granted"])
        encoded = json.dumps(case).lower()
        self.assertNotIn("private key-----", encoded)
        self.assertNotIn("password=", encoded)

    def test_matching_repo_live_is_correct_target(self):
        identity = compare_artifacts(record("repository"), None, record("live"))
        self.assertEqual(identity["status"], "MATCH")
        self.assertEqual(validate_claim(evidence=[record("live")], target_identity=identity, corroborates=1), "CONFIRMED")

    def test_hash_mismatch_is_configuration_drift_and_wrong_target_claim(self):
        identity = compare_artifacts(record("repository"), None, record("live", "b" * 64))
        self.assertEqual(identity["status"], "CONFIGURATION_DRIFT")
        self.assertEqual(validate_claim(evidence=[record("repository")], target_identity=identity, corroborates=1), "WRONG_TARGET")

    def test_historical_fail_after_newer_deployment_is_stale(self):
        failure = record("historical_log", timestamp="2026-08-30T10:00:00+09:00")
        deployment = record("live", timestamp="2026-08-30T11:00:00+09:00")
        self.assertEqual(historical_freshness(failure, [deployment]), "STALE_EVIDENCE")

    def test_unreachable_live_is_unknown_not_fail(self):
        live = record("live", digest=None, status="UNREACHABLE")
        identity = compare_artifacts(record("repository"), None, live)
        self.assertEqual(identity["status"], "UNKNOWN")
        self.assertEqual(readiness(claim_verdicts=[], unreachable_targets=["raspi2"]), "UNKNOWN")

    def test_repository_only_cannot_decide_live(self):
        identity = compare_artifacts(record("repository"), None, None)
        self.assertEqual(identity["status"], "UNKNOWN")
        self.assertEqual(validate_claim(evidence=[record("repository")], target_identity=identity, corroborates=1), "UNKNOWN")

    def test_dynamic_test_omission_is_unknown(self):
        identity = compare_artifacts(record("repository"), None, record("live"))
        verdict = validate_claim(evidence=[record("live")], target_identity=identity,
            corroborates=1, required_dynamic_test=True, dynamic_test_performed=False)
        self.assertEqual(verdict, "UNKNOWN")

    def test_audit_cannot_start_implementation(self):
        with self.assertRaises(PermissionError):
            assert_action_allowed("AUDIT", "restart_service")
        assert_action_allowed("AUDIT", "collect_evidence")

    def test_finding_never_grants_authority(self):
        self.assertFalse(authorize_action({"verdict": "CONFIRMED"}))

    def test_credentials_are_not_saved(self):
        value = redact({"token": "abc", "note": "password=hunter2", "safe": "metadata"})
        encoded = json.dumps(value)
        self.assertNotIn("abc", encoded)
        self.assertNotIn("hunter2", encoded)
        self.assertEqual(value["safe"], "metadata")

    def test_strong_readiness_needs_provenance_or_reason(self):
        identity = compare_artifacts(record("repository"), None, None)
        with self.assertRaises(ValueError):
            audit_report(started_at="a", completed_at="b", audited_commit=None,
                audited_host="raspi2", identity=identity, unreachable_targets=["raspi2"],
                dynamic_tests_performed=[], dynamic_tests_not_performed=["restart"], findings=[],
                system_readiness="FAIL")

    def test_unrelated_worktree_changes_are_excluded_from_checkpoint(self):
        owned = ["runtime/evidence_control.py", "tests/test_evidence_control.py"]
        changed = owned + ["zen3-gnss-feeder.py", "runtime/discord_loop_v2.py"]
        self.assertEqual(checkpoint_paths(owned, changed), sorted(owned))


if __name__ == "__main__":
    unittest.main()
