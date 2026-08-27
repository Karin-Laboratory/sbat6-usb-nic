#!/usr/bin/env python3
"""Create non-executing implementation tickets from explicitly approved reviews."""
import fcntl
from pathlib import Path

from growth_review import (
    ReviewError,
    atomic_json,
    canonical_hash,
    load_current_proposal,
    load_json,
    now,
    object_hash,
    proposal_is_prohibited,
    read_audit,
    validate_review,
)


class TicketError(RuntimeError):
    pass


def validate_ticket(ticket):
    required = {
        "schema_version", "ticket_id", "event_id", "target", "proposal_hash", "review_hash",
        "created_at", "created_by", "status", "approved_proposal_items",
        "implementation_ticket_is_not_execution_authority", "approval_is_not_execution_permission",
    }
    if not isinstance(ticket, dict) or set(ticket) != required or ticket.get("schema_version") != 1:
        raise TicketError("ticket does not match closed schema")
    if ticket.get("status") not in {"ready", "cancelled"}:
        raise TicketError("invalid ticket status")
    if ticket.get("implementation_ticket_is_not_execution_authority") is not True or ticket.get("approval_is_not_execution_permission") is not True:
        raise TicketError("ticket authority boundary is missing")
    if not isinstance(ticket.get("approved_proposal_items"), list):
        raise TicketError("ticket proposal items are malformed")
    return ticket


def create_ticket(root, event_id, actor):
    if not isinstance(actor, str) or not actor.strip():
        raise TicketError("ticket creator is required")
    try:
        proposal = load_current_proposal(root, event_id)
        review = validate_review(load_json(root / "state/growth_reviews" / f"{event_id}.json"))
    except ReviewError as exc:
        raise TicketError(str(exc)) from exc
    proposal_hash = canonical_hash(proposal)
    if review["event_id"] != event_id or review["target"] != proposal["target"] or review["proposal_hash"] != proposal_hash:
        raise TicketError("review/proposal binding mismatch")
    if review["status"] != "approved":
        raise TicketError("implementation ticket requires an approved review")
    if proposal_is_prohibited(proposal):
        raise TicketError("prohibited proposals cannot become implementation tickets")
    try:
        audited = any(
            row.get("event_id") == event_id and row.get("proposal_hash") == proposal_hash
            and row.get("new_status") == "approved" and row.get("actor") == review["reviewed_by"]
            and row.get("reason") == review["reason"]
            for row in read_audit(root)
        )
    except ReviewError as exc:
        raise TicketError(str(exc)) from exc
    if not audited:
        raise TicketError("approved review has no matching valid audit record")
    review_hash = object_hash(review)
    ticket_id = f"growth-{event_id}-{proposal_hash[:12]}"
    ticket = {
        "schema_version": 1, "ticket_id": ticket_id, "event_id": event_id,
        "target": proposal["target"], "proposal_hash": proposal_hash,
        "review_hash": review_hash, "created_at": now(), "created_by": actor.strip(),
        "status": "ready", "approved_proposal_items": proposal["analysis"]["proposals"],
        "implementation_ticket_is_not_execution_authority": True,
        "approval_is_not_execution_permission": True,
    }
    validate_ticket(ticket)
    directory = root / "state/growth_implementation_queue"
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = root / "state/growth_ticket.lock"
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        path = directory / f"{ticket_id}.json"
        if path.exists():
            existing = validate_ticket(load_json(path))
            comparable = dict(ticket)
            comparable["created_at"] = existing.get("created_at")
            if existing != comparable:
                raise TicketError("existing ticket differs; refusing overwrite")
            return existing, False
        atomic_json(path, ticket)
    return ticket, True
