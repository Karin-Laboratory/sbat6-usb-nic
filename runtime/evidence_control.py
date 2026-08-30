#!/usr/bin/env python3
"""Evidence identity and configuration-control primitives for ButlerX.

This module is deliberately read-only with respect to audited targets.  It
describes observations and validates claims; it never deploys, repairs, grants
authority, or turns an audit result into an implementation action.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

SOURCE_TYPES = {"live", "repository", "git_checkpoint", "historical_log", "generated_report"}
COLLECTION_STATUSES = {"COLLECTED", "UNREACHABLE", "NOT_FOUND", "ERROR", "UNKNOWN"}
IDENTITY_STATUSES = {"MATCH", "CONFIGURATION_DRIFT", "UNKNOWN", "WRONG_TARGET"}
CLAIM_VERDICTS = {"CONFIRMED", "PARTIALLY_CONFIRMED", "REFUTED", "STALE_EVIDENCE", "WRONG_TARGET", "UNKNOWN"}
READINESS_VERDICTS = {"PASS", "PASS_WITH_RESIDUAL_RISK", "FAIL", "UNKNOWN"}
MODES = {"IMPLEMENTATION", "AUDIT", "REVIEW_DECISION"}
SECRET_KEY = re.compile(r"(?:password|passwd|secret|token|private[_ -]?key|credential|api[_ -]?key)", re.I)
SECRET_VALUE = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:password|passwd|secret|token|api[_ -]?key)\s*[:=]\s*\S+)", re.I
)


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def redact(value: Any) -> Any:
    """Remove credential material while retaining useful evidence metadata."""
    if isinstance(value, dict):
        return {str(key): "[REDACTED]" if SECRET_KEY.search(str(key)) else redact(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str) and SECRET_VALUE.search(value):
        return "[REDACTED]"
    return value


def evidence_record(*, audited_host: str, asset: str, source_type: str,
                    path: str | None, collected_by: str,
                    collection_status: str = "COLLECTED", sha256: str | None = None,
                    git_commit: str | None = None, mtime: str | None = None,
                    exec_start: str | None = None, evidence_timestamp: str | None = None,
                    reachability: str = "reachable", notes: list[str] | None = None) -> dict[str, Any]:
    if source_type not in SOURCE_TYPES:
        raise ValueError("invalid evidence source_type")
    if collection_status not in COLLECTION_STATUSES:
        raise ValueError("invalid collection status")
    record = {
        "audited_host": audited_host, "asset": asset, "source_type": source_type,
        "path": path, "sha256": sha256, "git_commit": git_commit, "mtime": mtime,
        "exec_start": exec_start, "evidence_timestamp": evidence_timestamp or now(),
        "collected_by": collected_by, "reachability": reachability,
        "collection_status": collection_status, "notes": notes or [],
    }
    return redact(record)


def collect_local_file(path: Path, *, audited_host: str, asset: str,
                       source_type: str, collected_by: str,
                       git_commit: str | None = None, exec_start: str | None = None) -> dict[str, Any]:
    """Collect identity for a local artifact without reading its content into the record."""
    try:
        stat = path.stat()
        return evidence_record(
            audited_host=audited_host, asset=asset, source_type=source_type,
            path=str(path), sha256=sha256_file(path), git_commit=git_commit,
            mtime=datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
            exec_start=exec_start, collected_by=collected_by,
        )
    except FileNotFoundError:
        return evidence_record(
            audited_host=audited_host, asset=asset, source_type=source_type,
            path=str(path), collected_by=collected_by, collection_status="NOT_FOUND",
            reachability="reachable", notes=["artifact not found"],
        )
    except OSError as exc:
        return evidence_record(
            audited_host=audited_host, asset=asset, source_type=source_type,
            path=str(path), collected_by=collected_by, collection_status="ERROR",
            reachability="unknown", notes=[type(exc).__name__],
        )


def compare_artifacts(repository: dict[str, Any], deployed: dict[str, Any] | None,
                      live: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve repository -> deployed -> live identity without guessing."""
    records = [repository, deployed, live]
    if live is not None and live.get("source_type") != "live":
        return {"status": "WRONG_TARGET", "repo_live_match": None,
                "reason": "claimed live evidence is not a live source", "chain": records}
    required = [repository, live]
    if any(not item or item.get("collection_status") != "COLLECTED" or not item.get("sha256")
           for item in required):
        return {"status": "UNKNOWN", "repo_live_match": None,
                "reason": "repository/live identity is incomplete", "chain": records}
    match = repository["sha256"] == live["sha256"]
    return {"status": "MATCH" if match else "CONFIGURATION_DRIFT",
            "repo_live_match": match,
            "reason": "repository and live hashes match" if match else "repository and live hashes differ",
            "chain": records}


def historical_freshness(evidence: dict[str, Any], deployments: Iterable[dict[str, Any]]) -> str:
    """Return STALE_EVIDENCE when a successful collection/deployment is newer."""
    if evidence.get("source_type") != "historical_log" or not evidence.get("evidence_timestamp"):
        return "UNKNOWN"
    timestamp = evidence["evidence_timestamp"]
    newer = any(item.get("collection_status") == "COLLECTED"
                and item.get("evidence_timestamp")
                and item["evidence_timestamp"] > timestamp for item in deployments)
    return "STALE_EVIDENCE" if newer else "CURRENT_AT_OBSERVED_TIME"


def validate_claim(*, evidence: list[dict[str, Any]], target_identity: dict[str, Any] | None,
                   corroborates: int = 0, contradicts: int = 0,
                   required_dynamic_test: bool = False, dynamic_test_performed: bool = False,
                   historical_status: str | None = None) -> str:
    """Validate a claim separately from system readiness and authority."""
    if not evidence or any(item.get("collection_status") != "COLLECTED" for item in evidence):
        return "UNKNOWN"
    if not target_identity or target_identity.get("status") == "UNKNOWN":
        return "UNKNOWN"
    if target_identity.get("status") in {"WRONG_TARGET", "CONFIGURATION_DRIFT"}:
        return "WRONG_TARGET"
    if historical_status == "STALE_EVIDENCE":
        return "STALE_EVIDENCE"
    if required_dynamic_test and not dynamic_test_performed:
        return "UNKNOWN"
    if corroborates and contradicts:
        return "PARTIALLY_CONFIRMED"
    if contradicts and not corroborates:
        return "REFUTED"
    return "CONFIRMED" if corroborates else "UNKNOWN"


def readiness(*, claim_verdicts: list[str], dynamic_tests_required: bool = False,
              dynamic_tests_performed: bool = False, unreachable_targets: list[str] | None = None) -> str:
    unreachable_targets = unreachable_targets or []
    if unreachable_targets or "UNKNOWN" in claim_verdicts or (dynamic_tests_required and not dynamic_tests_performed):
        return "UNKNOWN"
    if any(item in {"CONFIRMED", "PARTIALLY_CONFIRMED"} for item in claim_verdicts):
        return "FAIL"
    if any(item in {"STALE_EVIDENCE", "WRONG_TARGET"} for item in claim_verdicts):
        return "PASS_WITH_RESIDUAL_RISK"
    return "PASS"


def authorize_action(*_args: Any, **_kwargs: Any) -> bool:
    """Evidence never grants authority; callers must use the authority subsystem."""
    return False


def assert_action_allowed(mode: str, action_kind: str) -> None:
    if mode not in MODES:
        raise ValueError("invalid role mode")
    if mode == "AUDIT" and action_kind not in {"read", "collect_evidence", "write_audit_report"}:
        raise PermissionError("AUDIT mode is read-only; implementation action refused")


def audit_report(*, started_at: str, completed_at: str, audited_commit: str | None,
                 audited_host: str, identity: dict[str, Any], unreachable_targets: list[str],
                 dynamic_tests_performed: list[str], dynamic_tests_not_performed: list[str],
                 findings: list[dict[str, Any]], system_readiness: str,
                 strong_verdict_reason: str | None = None) -> dict[str, Any]:
    if system_readiness not in READINESS_VERDICTS:
        raise ValueError("invalid readiness verdict")
    live = next((x for x in identity.get("chain", []) if x and x.get("source_type") == "live"), None)
    repo = next((x for x in identity.get("chain", []) if x and x.get("source_type") == "repository"), None)
    incomplete = (not audited_commit or not live or not live.get("sha256") or not repo or not repo.get("sha256"))
    if incomplete and system_readiness in {"PASS", "FAIL"} and not strong_verdict_reason:
        raise ValueError("strong readiness verdict requires provenance or an explicit reason")
    return redact({
        "audit_started_at": started_at, "audit_completed_at": completed_at,
        "audited_commit": audited_commit, "audited_host": audited_host,
        "live_artifact_hash": live.get("sha256") if live else None,
        "repository_artifact_hash": repo.get("sha256") if repo else None,
        "live_repo_identity": identity.get("status"),
        "unreachable_targets": unreachable_targets,
        "dynamic_tests_performed": dynamic_tests_performed,
        "dynamic_tests_not_performed": dynamic_tests_not_performed,
        "findings": findings, "system_readiness": system_readiness,
        "strong_verdict_reason": strong_verdict_reason,
        "authority_granted": False, "implementation_action_started": False,
    })


def checkpoint_paths(owned_paths: Iterable[str], worktree_changes: Iterable[str]) -> list[str]:
    """Return only explicitly owned changes for an isolated Git checkpoint."""
    owned = set(owned_paths)
    return sorted(path for path in worktree_changes if path in owned)


def dump(record: dict[str, Any]) -> str:
    return json.dumps(redact(record), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
