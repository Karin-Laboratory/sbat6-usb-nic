#!/usr/bin/env python3
"""Human review state for growth proposals. Approval is never execution authority."""
import fcntl
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path


STATUSES = {"pending", "approved", "rejected"}
RISKS = {"informational", "low", "medium", "high", "prohibited"}


class ReviewError(RuntimeError):
    pass


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def safe_id(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9._-]+", value) is not None


def canonical_hash(proposal):
    encoded = json.dumps(proposal, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def object_hash(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReviewError(f"missing JSON: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReviewError(f"malformed JSON: {path}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ReviewError(f"JSON root is not an object: {path}")
    return value


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def validate_proposal(proposal, event_id=None):
    if proposal.get("schema_version") != 1 or proposal.get("status") != "proposal":
        raise ReviewError("invalid proposal envelope")
    if proposal.get("proposal_is_not_authority") is not True:
        raise ReviewError("proposal authority boundary is missing")
    if not safe_id(proposal.get("event_id")) or not safe_id(proposal.get("target")):
        raise ReviewError("proposal event or target is unsafe")
    if event_id is not None and proposal["event_id"] != event_id:
        raise ReviewError("proposal event id mismatch")
    items = proposal.get("analysis", {}).get("proposals")
    if not isinstance(items, list):
        raise ReviewError("proposal items are malformed")
    if any(not isinstance(item, dict) or item.get("risk") not in RISKS for item in items):
        raise ReviewError("proposal item risk is invalid")
    return proposal


def validate_review(review):
    required = {"schema_version", "event_id", "target", "proposal_hash", "status", "created_at", "reviewed_at", "reviewed_by", "reason"}
    if not isinstance(review, dict) or set(review) != required:
        raise ReviewError("review does not match closed schema")
    if review["schema_version"] != 1 or review["status"] not in STATUSES:
        raise ReviewError("review schema version or status is invalid")
    if not safe_id(review["event_id"]) or not safe_id(review["target"]):
        raise ReviewError("review event or target is unsafe")
    if not isinstance(review["proposal_hash"], str) or re.fullmatch(r"[0-9a-f]{64}", review["proposal_hash"]) is None:
        raise ReviewError("review proposal hash is invalid")
    if review["status"] == "pending":
        if any(review[key] is not None for key in ("reviewed_at", "reviewed_by", "reason")):
            raise ReviewError("pending review contains final review fields")
    elif not all(isinstance(review[key], str) and review[key] for key in ("reviewed_at", "reviewed_by", "reason")):
        raise ReviewError("final review fields are missing")
    return review


def read_audit(root):
    path = root / "state/growth_review_audit.jsonl"
    if not path.exists():
        return []
    entries = []
    previous_hash = None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ReviewError(f"malformed review audit line {number}") from exc
        if not isinstance(entry, dict):
            raise ReviewError(f"invalid review audit line {number}")
        if "entry_hash" in entry:
            supplied = entry["entry_hash"]
            payload = {key: value for key, value in entry.items() if key != "entry_hash"}
            if entry.get("previous_hash") != previous_hash or supplied != object_hash(payload):
                raise ReviewError(f"review audit hash chain mismatch at line {number}")
            previous_hash = supplied
        else:
            # Pre-chain records remain valid as an explicit legacy anchor.
            previous_hash = object_hash(entry)
        entries.append(entry)
    return entries


def append_audit(root, entry):
    path = root / "state/growth_review_audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_audit(root)
    if any(row.get("audit_id") == entry["audit_id"] for row in existing):
        return False
    previous_hash = (existing[-1].get("entry_hash") or object_hash(existing[-1])) if existing else None
    chained = dict(entry, sequence=len(existing) + 1, previous_hash=previous_hash)
    chained["entry_hash"] = object_hash(chained)
    line = json.dumps(chained, ensure_ascii=False, separators=(",", ":")) + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, line.encode())
        os.fsync(fd)
    finally:
        os.close(fd)
    return True


def audit_entry(event_id, target, proposal_hash, old_status, new_status, actor, reason):
    entry = {
        "timestamp": now(), "event_id": event_id, "target": target,
        "proposal_hash": proposal_hash, "old_status": old_status,
        "new_status": new_status, "actor": actor, "reason": reason,
        "approval_is_not_execution_permission": True,
    }
    entry["audit_id"] = object_hash(entry)
    return entry


def with_lock(root):
    path = root / "state/growth_review.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def _journal_path(root, event_id):
    return root / "state/growth_review_journal" / f"{event_id}.json"


def _commit_review_change_locked(root, updated_review, entry):
    review_path = root / "state/growth_reviews" / f"{updated_review['event_id']}.json"
    journal_path = _journal_path(root, updated_review["event_id"])
    journal = {"schema_version": 1, "review": updated_review, "audit": entry}
    atomic_json(journal_path, journal)
    atomic_json(review_path, updated_review)
    append_audit(root, entry)
    journal_path.unlink()


def _reconcile_locked(root):
    recovered = []
    journal_dir = root / "state/growth_review_journal"
    for path in sorted(journal_dir.glob("*.json")):
        journal = load_json(path)
        if journal.get("schema_version") != 1 or not isinstance(journal.get("audit"), dict):
            raise ReviewError(f"invalid review journal: {path}")
        review = validate_review(journal.get("review"))
        if path.stem != review["event_id"]:
            raise ReviewError(f"review journal event mismatch: {path}")
        atomic_json(root / "state/growth_reviews" / f"{review['event_id']}.json", review)
        append_audit(root, journal["audit"])
        path.unlink()
        recovered.append(review["event_id"])
    read_audit(root)
    return recovered


def reconcile_review_journals(root):
    with with_lock(root):
        return _reconcile_locked(root)


def pending_review(proposal):
    validate_proposal(proposal)
    return {
        "schema_version": 1, "event_id": proposal["event_id"], "target": proposal["target"],
        "proposal_hash": canonical_hash(proposal), "status": "pending", "created_at": now(),
        "reviewed_at": None, "reviewed_by": None, "reason": None,
    }


def ensure_pending_review(root, proposal):
    """Create once. Never overwrite an existing review, even after proposal drift."""
    expected = pending_review(proposal)
    path = root / "state/growth_reviews" / f"{expected['event_id']}.json"
    with with_lock(root):
        _reconcile_locked(root)
        if path.exists():
            existing = validate_review(load_json(path))
            if existing["target"] != expected["target"] or existing["proposal_hash"] != expected["proposal_hash"]:
                raise ReviewError("existing review is bound to different proposal content")
            return existing, False
        entry = audit_entry(expected["event_id"], expected["target"], expected["proposal_hash"], None, "pending", "growth_worker", "validated proposal created")
        _commit_review_change_locked(root, expected, entry)
        return expected, True


def publish_proposal_with_pending_review(root, proposal):
    """Atomically serialize proposal publication against human review operations."""
    expected = pending_review(proposal)
    review_path = root / "state/growth_reviews" / f"{expected['event_id']}.json"
    latest_path = root / "state/growth_proposals" / f"{expected['target']}.json"
    history_path = root / "state/growth_proposals/history" / f"{expected['event_id']}.json"
    with with_lock(root):
        _reconcile_locked(root)
        if review_path.exists():
            existing = validate_review(load_json(review_path))
            if existing["target"] != expected["target"] or existing["proposal_hash"] != expected["proposal_hash"]:
                raise ReviewError("existing review is bound to different proposal content")
            created = False
        else:
            existing = expected
            created = True
        atomic_json(latest_path, proposal)
        atomic_json(history_path, proposal)
        if created:
            entry = audit_entry(expected["event_id"], expected["target"], expected["proposal_hash"], None, "pending", "growth_worker", "validated proposal created")
            _commit_review_change_locked(root, expected, entry)
        return existing, created


def load_current_proposal(root, event_id):
    if not safe_id(event_id):
        raise ReviewError("unsafe event id")
    history = validate_proposal(load_json(root / "state/growth_proposals/history" / f"{event_id}.json"), event_id)
    latest = validate_proposal(load_json(root / "state/growth_proposals" / f"{history['target']}.json"))
    if latest.get("event_id") != event_id or canonical_hash(latest) != canonical_hash(history):
        raise ReviewError("proposal is no longer the current proposal for target")
    return history


def proposal_is_prohibited(proposal):
    return any(item.get("risk") == "prohibited" for item in proposal["analysis"]["proposals"] if isinstance(item, dict))


def transition_review(root, event_id, new_status, actor, reason):
    if new_status not in {"approved", "rejected"}:
        raise ReviewError("new status must be approved or rejected")
    if not isinstance(actor, str) or not actor.strip():
        raise ReviewError("actor is required")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
        raise ReviewError("reason is required and must be at most 2000 characters")
    path = root / "state/growth_reviews" / f"{event_id}.json"
    with with_lock(root):
        _reconcile_locked(root)
        proposal = load_current_proposal(root, event_id)
        proposal_hash = canonical_hash(proposal)
        review = validate_review(load_json(path))
        if review["event_id"] != event_id or review["target"] != proposal["target"] or review["proposal_hash"] != proposal_hash:
            raise ReviewError("review/proposal binding mismatch")
        if new_status == "approved" and proposal_is_prohibited(proposal):
            raise ReviewError("a proposal containing prohibited risk cannot be approved")
        if review["status"] != "pending":
            if review["status"] == new_status:
                return review, False
            raise ReviewError("a finalized review cannot be overwritten")
        updated = dict(review)
        updated.update(status=new_status, reviewed_at=now(), reviewed_by=actor.strip(), reason=reason.strip())
        validate_review(updated)
        entry = audit_entry(event_id, proposal["target"], proposal_hash, "pending", new_status, actor.strip(), reason.strip())
        _commit_review_change_locked(root, updated, entry)
        return updated, True
