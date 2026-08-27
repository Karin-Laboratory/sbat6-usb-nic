#!/usr/bin/env python3
"""Item-level human review for growth proposals. Nothing here executes proposals."""
import fcntl
import hashlib
import json
import os
import re
from datetime import datetime

ITEM_STATUSES = {"pending", "approved", "rejected"}
AGGREGATE_STATUSES = {"pending", "partially_reviewed", "reviewed"}
RISKS = {"informational", "low", "medium", "high", "prohibited"}

class ReviewError(RuntimeError):
    pass

def now(): return datetime.now().astimezone().isoformat(timespec="seconds")
def safe_id(value): return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9._-]+", value) is not None
def object_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def canonical_hash(proposal): return object_hash(proposal)

def load_json(path):
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc: raise ReviewError(f"missing JSON: {path}") from exc
    except json.JSONDecodeError as exc: raise ReviewError(f"malformed JSON: {path}: {exc.msg}") from exc
    if not isinstance(value, dict): raise ReviewError(f"JSON root is not an object: {path}")
    return value

def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)

def validate_proposal(proposal, event_id=None, require_item_ids=True):
    if proposal.get("schema_version") != 1 or proposal.get("status") != "proposal": raise ReviewError("invalid proposal envelope")
    if proposal.get("proposal_is_not_authority") is not True: raise ReviewError("proposal authority boundary is missing")
    if not safe_id(proposal.get("event_id")) or not safe_id(proposal.get("target")): raise ReviewError("proposal event or target is unsafe")
    if event_id is not None and proposal["event_id"] != event_id: raise ReviewError("proposal event id mismatch")
    items = proposal.get("analysis", {}).get("proposals")
    if not isinstance(items, list): raise ReviewError("proposal items are malformed")
    seen = set()
    for item in items:
        if not isinstance(item, dict) or item.get("risk") not in RISKS: raise ReviewError("proposal item risk is invalid")
        if require_item_ids:
            proposal_id, item_hash = item.get("proposal_id"), item.get("item_hash")
            if not isinstance(proposal_id, str) or re.fullmatch(r"p-[0-9a-f]{16}", proposal_id) is None: raise ReviewError("proposal item id is invalid")
            if not isinstance(item_hash, str) or re.fullmatch(r"[0-9a-f]{64}", item_hash) is None: raise ReviewError("proposal item hash is invalid")
            semantic = {key: value for key, value in item.items() if key not in {"proposal_id", "item_hash"}}
            if object_hash(semantic) != item_hash or proposal_id in seen: raise ReviewError("proposal item identity mismatch or duplicate")
            seen.add(proposal_id)
    return proposal

def assign_item_identities(proposal):
    """Return a copy with code-owned stable IDs; AI output cannot choose identity."""
    validate_proposal(proposal, require_item_ids=False)
    enriched = json.loads(json.dumps(proposal, ensure_ascii=False))
    occurrence, ids = {}, set()
    for item in enriched["analysis"]["proposals"]:
        semantic = {key: value for key, value in item.items() if key not in {"proposal_id", "item_hash"}}
        item_hash = object_hash(semantic)
        index = occurrence.get(item_hash, 0); occurrence[item_hash] = index + 1
        proposal_id = "p-" + hashlib.sha256(f"{enriched['event_id']}\0{item_hash}\0{index}".encode()).hexdigest()[:16]
        if proposal_id in ids: raise ReviewError("proposal item id collision")
        ids.add(proposal_id); item.clear(); item.update(semantic, proposal_id=proposal_id, item_hash=item_hash)
    return validate_proposal(enriched)

def aggregate_status(items):
    statuses = [item["status"] for item in items.values()]
    if not statuses or all(status == "pending" for status in statuses): return "pending"
    if any(status == "pending" for status in statuses): return "partially_reviewed"
    return "reviewed"

def pending_review(proposal, created_at=None):
    validate_proposal(proposal)
    items = {item["proposal_id"]: {"item_hash": item["item_hash"], "status": "pending", "reviewed_at": None, "reviewed_by": None, "reason": None} for item in proposal["analysis"]["proposals"]}
    return {"schema_version": 2, "event_id": proposal["event_id"], "target": proposal["target"], "proposal_hash": canonical_hash(proposal), "aggregate_status": aggregate_status(items), "created_at": created_at or now(), "items": items}

def validate_review(review):
    required = {"schema_version", "event_id", "target", "proposal_hash", "aggregate_status", "created_at", "items"}
    if not isinstance(review, dict) or set(review) != required or review.get("schema_version") != 2: raise ReviewError("item review does not match closed schema v2")
    if not safe_id(review.get("event_id")) or not safe_id(review.get("target")): raise ReviewError("review event or target is unsafe")
    if re.fullmatch(r"[0-9a-f]{64}", review.get("proposal_hash", "")) is None: raise ReviewError("review proposal hash is invalid")
    if not isinstance(review.get("items"), dict): raise ReviewError("review items are invalid")
    item_required = {"item_hash", "status", "reviewed_at", "reviewed_by", "reason"}
    for proposal_id, item in review["items"].items():
        if re.fullmatch(r"p-[0-9a-f]{16}", proposal_id) is None or not isinstance(item, dict) or set(item) != item_required: raise ReviewError("review item does not match closed schema")
        if re.fullmatch(r"[0-9a-f]{64}", item.get("item_hash", "")) is None or item.get("status") not in ITEM_STATUSES: raise ReviewError("review item hash or status is invalid")
        if item["status"] == "pending":
            if any(item[key] is not None for key in ("reviewed_at", "reviewed_by", "reason")): raise ReviewError("pending item contains review fields")
        elif not all(isinstance(item[key], str) and item[key] for key in ("reviewed_at", "reviewed_by", "reason")): raise ReviewError("reviewed item fields are missing")
    derived = aggregate_status(review["items"])
    if review.get("aggregate_status") not in AGGREGATE_STATUSES or review["aggregate_status"] != derived: raise ReviewError("aggregate review status is not derived from items")
    return review

def validate_review_binding(review, proposal):
    validate_review(review); validate_proposal(proposal, review["event_id"])
    if review["target"] != proposal["target"] or review["proposal_hash"] != canonical_hash(proposal): raise ReviewError("review/proposal binding mismatch")
    proposal_items = {item["proposal_id"]: item for item in proposal["analysis"]["proposals"]}
    if set(review["items"]) != set(proposal_items): raise ReviewError("review/proposal item set mismatch")
    if any(review["items"][pid]["item_hash"] != item["item_hash"] for pid, item in proposal_items.items()): raise ReviewError("review/proposal item hash mismatch")
    return review

def read_audit(root):
    path = root / "state/growth_review_audit.jsonl"
    if not path.exists(): return []
    entries, previous_hash = [], None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try: entry = json.loads(line)
        except json.JSONDecodeError as exc: raise ReviewError(f"malformed review audit line {number}") from exc
        if not isinstance(entry, dict): raise ReviewError(f"invalid review audit line {number}")
        if "entry_hash" in entry:
            supplied = entry["entry_hash"]; payload = {key: value for key, value in entry.items() if key != "entry_hash"}
            if entry.get("previous_hash") != previous_hash or supplied != object_hash(payload): raise ReviewError(f"review audit hash chain mismatch at line {number}")
            previous_hash = supplied
        else: previous_hash = object_hash(entry)
        entries.append(entry)
    return entries

def append_audit(root, entry):
    path = root / "state/growth_review_audit.jsonl"; path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_audit(root)
    if any(row.get("audit_id") == entry["audit_id"] for row in existing): return False
    previous_hash = (existing[-1].get("entry_hash") or object_hash(existing[-1])) if existing else None
    chained = dict(entry, sequence=len(existing) + 1, previous_hash=previous_hash); chained["entry_hash"] = object_hash(chained)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try: os.write(fd, (json.dumps(chained, ensure_ascii=False, separators=(",", ":")) + "\n").encode()); os.fsync(fd)
    finally: os.close(fd)
    return True

def audit_entry(event_id, target, proposal_hash, old_status, new_status, actor, human_review_reason, proposal_item=None, action="item_review"):
    entry = {"timestamp": now(), "action": action, "event_id": event_id, "target": target, "proposal_hash": proposal_hash, "proposal_id": proposal_item.get("proposal_id") if proposal_item else None, "item_hash": proposal_item.get("item_hash") if proposal_item else None, "proposal_item": ({key: proposal_item.get(key) for key in ("kind", "name", "reason", "risk")} if proposal_item else None), "old_status": old_status, "new_status": new_status, "actor": actor, "human_review_reason": human_review_reason, "approval_is_not_execution_permission": True}
    entry["audit_id"] = object_hash(entry); return entry

def with_lock(root):
    path = root / "state/growth_review.lock"; path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+"); fcntl.flock(handle.fileno(), fcntl.LOCK_EX); return handle
def _journal_path(root, event_id): return root / "state/growth_review_journal" / f"{event_id}.json"

def _commit_review_change_locked(root, updated_review, entry, proposal=None, update_latest=False):
    journal_path = _journal_path(root, updated_review["event_id"])
    atomic_json(journal_path, {"schema_version": 2, "review": updated_review, "audit": entry, "proposal": proposal, "update_latest": update_latest})
    if proposal is not None:
        atomic_json(root / "state/growth_proposals/history" / f"{proposal['event_id']}.json", proposal)
        if update_latest: atomic_json(root / "state/growth_proposals" / f"{proposal['target']}.json", proposal)
    atomic_json(root / "state/growth_reviews" / f"{updated_review['event_id']}.json", updated_review)
    append_audit(root, entry); journal_path.unlink()

def _reconcile_locked(root):
    recovered = []
    for path in sorted((root / "state/growth_review_journal").glob("*.json")):
        journal = load_json(path)
        if journal.get("schema_version") != 2 or not isinstance(journal.get("audit"), dict): raise ReviewError(f"invalid review journal: {path}")
        review = validate_review(journal.get("review")); proposal = journal.get("proposal")
        if proposal is not None:
            validate_proposal(proposal, review["event_id"]); atomic_json(root / "state/growth_proposals/history" / f"{proposal['event_id']}.json", proposal)
            if journal.get("update_latest"): atomic_json(root / "state/growth_proposals" / f"{proposal['target']}.json", proposal)
        atomic_json(root / "state/growth_reviews" / f"{review['event_id']}.json", review); append_audit(root, journal["audit"]); path.unlink(); recovered.append(review["event_id"])
    read_audit(root); return recovered
def reconcile_review_journals(root):
    with with_lock(root): return _reconcile_locked(root)

def publish_proposal_with_pending_review(root, proposal):
    enriched = assign_item_identities(proposal); expected = pending_review(enriched)
    review_path = root / "state/growth_reviews" / f"{expected['event_id']}.json"
    with with_lock(root):
        _reconcile_locked(root)
        if review_path.exists():
            existing = validate_review(load_json(review_path)); validate_review_binding(existing, enriched); created = False
        else: existing, created = expected, True
        if created:
            entry = audit_entry(enriched["event_id"], enriched["target"], canonical_hash(enriched), None, "pending", "growth_worker", "validated proposal items created", action="proposal_items_created")
            _commit_review_change_locked(root, expected, entry, enriched, True)
        else:
            atomic_json(root / "state/growth_proposals/history" / f"{enriched['event_id']}.json", enriched); atomic_json(root / "state/growth_proposals" / f"{enriched['target']}.json", enriched)
        return existing, created

def load_current_proposal(root, event_id):
    if not safe_id(event_id): raise ReviewError("unsafe event id")
    return validate_proposal(load_json(root / "state/growth_proposals/history" / f"{event_id}.json"), event_id)

def transition_review(root, event_id, proposal_id, new_status, actor, reason):
    if new_status not in {"approved", "rejected"}: raise ReviewError("new status must be approved or rejected")
    if not safe_id(proposal_id): raise ReviewError("proposal item id is unsafe")
    if not isinstance(actor, str) or not actor.strip(): raise ReviewError("actor is required")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000: raise ReviewError("reason is required and must be at most 2000 characters")
    with with_lock(root):
        _reconcile_locked(root); proposal = load_current_proposal(root, event_id)
        review = validate_review_binding(load_json(root / "state/growth_reviews" / f"{event_id}.json"), proposal)
        proposal_items = {item["proposal_id"]: item for item in proposal["analysis"]["proposals"]}
        if proposal_id not in review["items"] or proposal_id not in proposal_items: raise ReviewError("unknown proposal item")
        proposal_item, current = proposal_items[proposal_id], review["items"][proposal_id]
        if current["item_hash"] != proposal_item["item_hash"]: raise ReviewError("proposal item hash mismatch")
        if new_status == "approved" and proposal_item["risk"] == "prohibited": raise ReviewError("a prohibited proposal item cannot be approved")
        if current["status"] != "pending":
            if current["status"] == new_status: return review, False
            raise ReviewError("a finalized item review cannot be overwritten")
        updated = json.loads(json.dumps(review, ensure_ascii=False)); updated["items"][proposal_id].update(status=new_status, reviewed_at=now(), reviewed_by=actor.strip(), reason=reason.strip()); updated["aggregate_status"] = aggregate_status(updated["items"])
        validate_review_binding(updated, proposal)
        entry = audit_entry(event_id, proposal["target"], canonical_hash(proposal), "pending", new_status, actor.strip(), reason.strip(), proposal_item)
        _commit_review_change_locked(root, updated, entry); return updated, True

def validate_legacy_review(review):
    required = {"schema_version", "event_id", "target", "proposal_hash", "status", "created_at", "reviewed_at", "reviewed_by", "reason"}
    if not isinstance(review, dict) or set(review) != required or review.get("schema_version") != 1: raise ReviewError("not a legacy event-level review")
    if review.get("status") not in ITEM_STATUSES: raise ReviewError("legacy review status is invalid")
    return review

def migrate_legacy_pending_review(root, event_id, actor):
    """Migrate only legacy pending. Final event decisions require explicit human handling."""
    with with_lock(root):
        _reconcile_locked(root); path = root / "state/growth_reviews" / f"{event_id}.json"; raw = load_json(path)
        if raw.get("schema_version") == 2: return validate_review(raw), False
        legacy = validate_legacy_review(raw)
        if legacy["status"] != "pending": raise ReviewError("legacy approved/rejected review requires explicit migration; no item decisions were inferred")
        old_proposal = validate_proposal(load_json(root / "state/growth_proposals/history" / f"{event_id}.json"), event_id, require_item_ids=False)
        if legacy["target"] != old_proposal["target"] or legacy["proposal_hash"] != canonical_hash(old_proposal): raise ReviewError("legacy review/proposal binding mismatch")
        enriched = assign_item_identities(old_proposal); migrated = pending_review(enriched, created_at=legacy["created_at"])
        latest_path = root / "state/growth_proposals" / f"{enriched['target']}.json"; update_latest = False
        if latest_path.exists():
            latest = load_json(latest_path); update_latest = latest.get("event_id") == event_id and canonical_hash(latest) == canonical_hash(old_proposal)
        entry = audit_entry(event_id, enriched["target"], canonical_hash(enriched), "pending_event_v1", "pending_items_v2", actor, "legacy pending review migrated without approving any item", action="legacy_pending_migration")
        _commit_review_change_locked(root, migrated, entry, enriched, update_latest); return migrated, True
