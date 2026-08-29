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
    read_audit,
    validate_review_binding,
)


class TicketError(RuntimeError):
    pass


def validate_ticket(ticket):
    required = {
        "schema_version", "ticket_id", "event_id", "target", "proposal_hash", "review_hash",
        "created_at", "created_by", "status", "selected_proposal_ids", "approved_proposal_items",
        "implementation_ticket_is_not_execution_authority", "approval_is_not_execution_permission",
    }
    if not isinstance(ticket, dict) or set(ticket) != required or ticket.get("schema_version") != 1:
        raise TicketError("ticket does not match closed schema")
    if ticket.get("status") not in {"ready", "implemented", "verified", "cancelled"}:
        raise TicketError("invalid ticket status")
    if ticket.get("implementation_ticket_is_not_execution_authority") is not True or ticket.get("approval_is_not_execution_permission") is not True:
        raise TicketError("ticket authority boundary is missing")
    selected = ticket.get("selected_proposal_ids")
    items = ticket.get("approved_proposal_items")
    if not isinstance(selected, list) or not selected or len(selected) != len(set(selected)):
        raise TicketError("ticket item selection is invalid")
    if not isinstance(items, list) or [item.get("proposal_id") for item in items if isinstance(item, dict)] != selected:
        raise TicketError("ticket proposal items are malformed")
    if any(item.get("risk") == "prohibited" for item in items): raise TicketError("ticket contains prohibited item")
    return ticket


def create_ticket(root, event_id, actor, proposal_ids=None, all_approved=False):
    if not isinstance(actor, str) or not actor.strip():
        raise TicketError("ticket creator is required")
    try:
        proposal = load_current_proposal(root, event_id)
        review = validate_review_binding(load_json(root / "state/growth_reviews" / f"{event_id}.json"), proposal)
    except ReviewError as exc:
        raise TicketError(str(exc)) from exc
    proposal_hash = canonical_hash(proposal)
    # Admission is a design gate, not execution permission.  Legacy roots
    # without admission records remain migratable; once records exist every
    # selected candidate must have passed the fixed gate.
    admission_dir = root / "state/capability_reviews"
    admission = []
    if admission_dir.exists():
        from capability_admission import validate
        for path in admission_dir.glob("*.json"):
            try:
                record = validate(load_json(path))
            except (ValueError, OSError):
                continue
            if record.get("linked_growth_proposal") == event_id:
                admission.append(record)
    if not isinstance(proposal_ids, (list, tuple, type(None))): raise TicketError("proposal item selection must be a list")
    proposal_items = {item["proposal_id"]: item for item in proposal["analysis"]["proposals"]}
    if all_approved and proposal_ids:
        raise TicketError("choose explicit items or all approved, not both")
    if all_approved:
        selected_ids = [item["proposal_id"] for item in proposal["analysis"]["proposals"] if review["items"][item["proposal_id"]]["status"] == "approved"]
    else:
        selected_ids = list(dict.fromkeys(proposal_ids or []))
    if not selected_ids:
        raise TicketError("select at least one approved proposal item")
    if any(proposal_id not in proposal_items or proposal_id not in review["items"] for proposal_id in selected_ids):
        raise TicketError("unknown proposal item selected")
    for proposal_id in selected_ids:
        item, decision = proposal_items[proposal_id], review["items"][proposal_id]
        if decision["item_hash"] != item["item_hash"] or decision["status"] != "approved":
            raise TicketError("only hash-bound approved items may enter a ticket")
        if item["risk"] == "prohibited":
            raise TicketError("prohibited proposal items cannot become implementation tickets")
        if admission:
            matching = [row for row in admission if row.get("evidence", {}).get("item_hash") == item["item_hash"]]
            if len(matching) != 1 or matching[0]["result"] not in {"PASS_READ_ONLY", "PASS_WITH_HUMAN_APPROVAL"}:
                raise TicketError("capability admission did not pass; no ticket may be created")
    try:
        audit = read_audit(root)
    except ReviewError as exc:
        raise TicketError(str(exc)) from exc
    for proposal_id in selected_ids:
        decision, item = review["items"][proposal_id], proposal_items[proposal_id]
        audited = any(
            row.get("event_id") == event_id and row.get("proposal_hash") == proposal_hash
            and row.get("proposal_id") == proposal_id and row.get("item_hash") == item["item_hash"]
            and row.get("new_status") == "approved" and row.get("actor") == decision["reviewed_by"]
            and row.get("human_review_reason") == decision["reason"] for row in audit
        )
        if not audited: raise TicketError(f"approved item has no matching valid audit record: {proposal_id}")
    review_hash = object_hash(review)
    selection_hash = object_hash(selected_ids)
    ticket_id = f"growth-{event_id}-{selection_hash[:12]}"
    ticket = {
        "schema_version": 1, "ticket_id": ticket_id, "event_id": event_id,
        "target": proposal["target"], "proposal_hash": proposal_hash,
        "review_hash": review_hash, "created_at": now(), "created_by": actor.strip(),
        "status": "ready", "selected_proposal_ids": selected_ids,
        "approved_proposal_items": [proposal_items[proposal_id] for proposal_id in selected_ids],
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
