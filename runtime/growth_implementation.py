#!/usr/bin/env python3
"""Human-recorded implementation lifecycle. This module executes no ticket work."""

import fcntl
import json
import os
import re

from growth_review import (
    ReviewError,
    atomic_json,
    canonical_hash,
    load_current_proposal,
    load_json,
    now,
    object_hash,
    validate_review_binding,
)
from growth_ticket import TicketError, validate_ticket

STATUSES = {"ready", "implemented", "verified", "cancelled"}
TRANSITIONS = {"ready": {"implemented", "cancelled"}, "implemented": {"verified"}}


class ImplementationError(RuntimeError):
    pass


def _safe_id(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9._-]+", value) is not None


def _ticket_path(root, ticket_id):
    if not _safe_id(ticket_id):
        raise ImplementationError("unsafe ticket id")
    return root / "state/growth_implementation_queue" / f"{ticket_id}.json"


def validate_binding(root, ticket):
    """Fail closed if the immutable proposal/review/item evidence has changed."""
    try:
        validate_ticket(ticket)
        proposal = load_current_proposal(root, ticket["event_id"])
        review = validate_review_binding(
            load_json(root / "state/growth_reviews" / f"{ticket['event_id']}.json"),
            proposal,
        )
    except (ReviewError, TicketError) as exc:
        raise ImplementationError(str(exc)) from exc
    if ticket["target"] != proposal["target"] or ticket["proposal_hash"] != canonical_hash(proposal):
        raise ImplementationError("ticket/proposal binding mismatch")
    if ticket["review_hash"] != object_hash(review):
        raise ImplementationError("ticket/review binding mismatch")
    proposal_items = {item["proposal_id"]: item for item in proposal["analysis"]["proposals"]}
    if [item.get("proposal_id") for item in ticket["approved_proposal_items"]] != ticket["selected_proposal_ids"]:
        raise ImplementationError("ticket item ordering mismatch")
    for proposal_id, ticket_item in zip(ticket["selected_proposal_ids"], ticket["approved_proposal_items"]):
        item = proposal_items.get(proposal_id)
        decision = review["items"].get(proposal_id)
        if item != ticket_item or not decision or decision["status"] != "approved":
            raise ImplementationError("ticket contains an unbound or unapproved item")
        if decision["item_hash"] != item["item_hash"] or item["risk"] == "prohibited":
            raise ImplementationError("ticket item hash/risk binding mismatch")
    return proposal, review


def validate_record(record):
    required = {
        "schema_version", "ticket_id", "event_id", "target", "proposal_hash",
        "review_hash", "approved_item_ids", "status", "implemented", "verification",
        "cancelled", "implementation_is_human_authorized",
        "implementation_record_is_not_execution_authority",
    }
    if not isinstance(record, dict) or set(record) != required or record.get("schema_version") != 1:
        raise ImplementationError("implementation record does not match closed schema")
    if record.get("status") not in STATUSES - {"ready"}:
        raise ImplementationError("implementation record status is invalid")
    if record.get("implementation_is_human_authorized") is not True:
        raise ImplementationError("human authorization marker is missing")
    if record.get("implementation_record_is_not_execution_authority") is not True:
        raise ImplementationError("record authority boundary is missing")
    if not _safe_id(record.get("ticket_id")) or not _safe_id(record.get("event_id")) or not _safe_id(record.get("target")):
        raise ImplementationError("record identity is unsafe")
    if re.fullmatch(r"[0-9a-f]{64}", record.get("proposal_hash", "")) is None or re.fullmatch(r"[0-9a-f]{64}", record.get("review_hash", "")) is None:
        raise ImplementationError("record hash is invalid")
    if not isinstance(record.get("approved_item_ids"), list) or not record["approved_item_ids"]:
        raise ImplementationError("record approved item ids are invalid")
    if record["status"] in {"implemented", "verified"}:
        implemented = record.get("implemented")
        if not _valid_action(implemented) or re.fullmatch(r"[0-9a-f]{7,64}", implemented.get("git_checkpoint", "")) is None:
            raise ImplementationError("implemented evidence is invalid")
    elif record.get("implemented") is not None:
        raise ImplementationError("cancelled record contains implementation evidence")
    if record["status"] == "verified":
        verification = record.get("verification")
        if not _valid_action(verification) or not isinstance(verification.get("summary"), str) or not verification["summary"].strip():
            raise ImplementationError("verification evidence is invalid")
    elif record.get("verification") is not None:
        raise ImplementationError("non-verified record contains verification evidence")
    if record["status"] == "cancelled":
        if not _valid_action(record.get("cancelled")):
            raise ImplementationError("cancellation evidence is invalid")
    elif record.get("cancelled") is not None:
        raise ImplementationError("active record contains cancellation evidence")
    return record


def _valid_action(value):
    return isinstance(value, dict) and all(
        isinstance(value.get(key), str) and value[key].strip()
        for key in ("actor", "timestamp", "human_reason")
    )


def read_audit(root):
    path = root / "state/growth_implementation_audit.jsonl"
    if not path.exists():
        return []
    entries, previous_hash = [], None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ImplementationError(f"malformed implementation audit line {number}") from exc
        supplied = entry.get("entry_hash") if isinstance(entry, dict) else None
        payload = {key: value for key, value in entry.items() if key != "entry_hash"} if isinstance(entry, dict) else {}
        if entry.get("previous_hash") != previous_hash or supplied != object_hash(payload):
            raise ImplementationError(f"implementation audit hash chain mismatch at line {number}")
        previous_hash = supplied
        entries.append(entry)
    return entries


def _append_audit(root, entry):
    path = root / "state/growth_implementation_audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = read_audit(root)
    if any(row.get("audit_id") == entry["audit_id"] for row in entries):
        return False
    chained = dict(entry, sequence=len(entries) + 1,
                   previous_hash=entries[-1]["entry_hash"] if entries else None)
    chained["entry_hash"] = object_hash(chained)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, (json.dumps(chained, ensure_ascii=False, separators=(",", ":")) + "\n").encode())
        os.fsync(fd)
    finally:
        os.close(fd)
    return True


def _commit_locked(root, ticket, record, audit):
    journal = root / "state/growth_implementation_journal" / f"{ticket['ticket_id']}.json"
    atomic_json(journal, {"schema_version": 1, "ticket": ticket, "record": record, "audit": audit})
    atomic_json(_ticket_path(root, ticket["ticket_id"]), ticket)
    atomic_json(root / "state/growth_implementation_records" / f"{ticket['ticket_id']}.json", record)
    _append_audit(root, audit)
    journal.unlink()


def _reconcile_locked(root):
    directory = root / "state/growth_implementation_journal"
    recovered = []
    for path in sorted(directory.glob("*.json")):
        journal = load_json(path)
        if journal.get("schema_version") != 1 or not isinstance(journal.get("audit"), dict):
            raise ImplementationError(f"invalid implementation journal: {path}")
        ticket = validate_ticket(journal.get("ticket"))
        record = validate_record(journal.get("record"))
        validate_binding(root, ticket)
        expected = (ticket["ticket_id"], ticket["event_id"], ticket["target"], ticket["proposal_hash"],
                    ticket["review_hash"], ticket["selected_proposal_ids"], ticket["status"])
        actual = (record["ticket_id"], record["event_id"], record["target"], record["proposal_hash"],
                  record["review_hash"], record["approved_item_ids"], record["status"])
        if actual != expected:
            raise ImplementationError("journal record/ticket binding mismatch")
        atomic_json(_ticket_path(root, ticket["ticket_id"]), ticket)
        atomic_json(root / "state/growth_implementation_records" / f"{ticket['ticket_id']}.json", record)
        _append_audit(root, journal["audit"])
        path.unlink()
        recovered.append(ticket["ticket_id"])
    read_audit(root)
    return recovered


def transition(root, ticket_id, new_status, actor, reason, git_checkpoint=None, verification_summary=None):
    if new_status not in STATUSES - {"ready"}:
        raise ImplementationError("unknown implementation status")
    if not isinstance(actor, str) or not actor.strip():
        raise ImplementationError("actor is required")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
        raise ImplementationError("reason is required and must be at most 2000 characters")
    if new_status != "implemented" and git_checkpoint is not None:
        raise ImplementationError("Git checkpoint is accepted only for implemented")
    if new_status != "verified" and verification_summary is not None:
        raise ImplementationError("verification summary is accepted only for verified")
    lock_path = root / "state/growth_implementation.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        _reconcile_locked(root)
        ticket = validate_ticket(load_json(_ticket_path(root, ticket_id)))
        validate_binding(root, ticket)
        old_status = ticket["status"]
        if new_status not in TRANSITIONS.get(old_status, set()):
            raise ImplementationError(f"invalid lifecycle transition: {old_status} -> {new_status}")
        timestamp, actor, reason = now(), actor.strip(), reason.strip()
        record_path = root / "state/growth_implementation_records" / f"{ticket_id}.json"
        record = load_json(record_path) if record_path.exists() else {
            "schema_version": 1, "ticket_id": ticket_id, "event_id": ticket["event_id"],
            "target": ticket["target"], "proposal_hash": ticket["proposal_hash"],
            "review_hash": ticket["review_hash"], "approved_item_ids": ticket["selected_proposal_ids"],
            "status": new_status, "implemented": None, "verification": None, "cancelled": None,
            "implementation_is_human_authorized": True,
            "implementation_record_is_not_execution_authority": True,
        }
        if record_path.exists():
            validate_record(record)
            expected = (ticket_id, ticket["event_id"], ticket["target"], ticket["proposal_hash"],
                        ticket["review_hash"], ticket["selected_proposal_ids"])
            actual = (record["ticket_id"], record["event_id"], record["target"], record["proposal_hash"],
                      record["review_hash"], record["approved_item_ids"])
            if actual != expected or record["status"] != old_status:
                raise ImplementationError("implementation record/ticket binding mismatch")
        record = json.loads(json.dumps(record, ensure_ascii=False))
        record["status"] = new_status
        action = {"actor": actor, "timestamp": timestamp, "human_reason": reason}
        if new_status == "implemented":
            if not isinstance(git_checkpoint, str) or re.fullmatch(r"[0-9a-f]{7,64}", git_checkpoint) is None:
                raise ImplementationError("implemented requires an explicit hexadecimal Git checkpoint")
            record["implemented"] = dict(action, git_checkpoint=git_checkpoint)
        elif new_status == "verified":
            summary = verification_summary if verification_summary is not None else reason
            if not isinstance(summary, str) or not summary.strip() or len(summary) > 4000:
                raise ImplementationError("verification summary is required and must be at most 4000 characters")
            record["verification"] = dict(action, summary=summary.strip())
        else:
            record["cancelled"] = action
        validate_record(record)
        updated_ticket = dict(ticket, status=new_status)
        implemented_evidence = record.get("implemented") or {}
        verification_evidence = record.get("verification") or {}
        audit = {
            "timestamp": timestamp, "action": "implementation_lifecycle_review",
            "ticket_id": ticket_id, "event_id": ticket["event_id"], "target": ticket["target"],
            "proposal_hash": ticket["proposal_hash"], "review_hash": ticket["review_hash"],
            "approved_item_ids": ticket["selected_proposal_ids"], "old_status": old_status,
            "new_status": new_status, "actor": actor, "human_reason": reason,
            "git_checkpoint": git_checkpoint if new_status == "implemented" else implemented_evidence.get("git_checkpoint"),
            "verification_summary": verification_evidence.get("summary"),
            "implementation_is_human_authorized": True,
            "implementation_record_is_not_execution_authority": True,
        }
        audit["audit_id"] = object_hash(audit)
        _commit_locked(root, updated_ticket, record, audit)
        return record


def reconcile(root):
    lock_path = root / "state/growth_implementation.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        return _reconcile_locked(root)
