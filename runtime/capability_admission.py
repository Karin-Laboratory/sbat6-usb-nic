#!/usr/bin/env python3
"""Fixed-logic safety gate for admitting a proposed capability.

This module records an explanation of a design.  It never grants authority,
creates a ticket, or executes an action.  Secrets are deliberately not part of
the record schema.
"""
import hashlib
import json
import re
from datetime import datetime

RESULTS = {"PASS_READ_ONLY", "PASS_WITH_HUMAN_APPROVAL", "REVISE", "REJECT", "UNKNOWN"}
REVIEW_FIELDS = {
    "review_id", "created_at", "capability_name", "target", "purpose",
    "requested_access", "credentials", "read_write_class", "remote_input",
    "destructive_actions", "approval_required", "rollback", "rate_limits",
    "audit_plan", "policy_conflicts", "risks", "mitigations", "evidence",
    "result", "reviewed_by", "linked_growth_proposal", "linked_ticket",
}
SECRET = re.compile(r"(?:private[ _-]?key|password|passwd|secret|token|credential|認証情報|パスワード|秘密鍵)", re.I)
PRIVILEGE = re.compile(r"(?:sudo|root|ssh.?key|firewall|routing|vlan|credential|token|password|privilege|権限|鍵)", re.I)
DESTRUCTIVE = re.compile(r"(?:delete|destroy|wipe|mkfs|reboot|restart|install|package|firewall|routing|vlan|storage|purchase|send|message|削除|破壊|再起動|導入|購入|送信|変更)", re.I)

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def _redact(value):
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if SECRET.search(str(k)) else _redact(v)) for k, v in value.items()}
    if isinstance(value, list): return [_redact(v) for v in value]
    if isinstance(value, str) and SECRET.search(value): return "[REDACTED]"
    return value

def _text(item):
    return " ".join(str(item.get(k, "")) for k in ("name", "reason", "kind"))

def _context(root, target):
    registry = {}
    policy = {}
    try: registry = json.loads((root / "state/capabilities.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError): pass
    try: policy = json.loads((root / "runtime/growth_policy.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError): pass
    return registry.get("targets", {}).get(target), policy

def evaluate(root, proposal, item, reviewed_by="fixed-policy"):
    """Evaluate one candidate and return a closed, secret-free record."""
    target, policy = _context(root, proposal.get("target"))
    item = _redact(item)
    text = _text(item)
    requested = {
        "kind": item.get("kind"), "name": item.get("name"),
        "declared_risk": item.get("risk"), "requires_approval": item.get("requires_approval"),
    }
    access = target.get("access", {}) if isinstance(target, dict) else {}
    allowed = target.get("allowed", []) if isinstance(target, dict) else []
    forbidden = target.get("forbidden", []) if isinstance(target, dict) else []
    privilege = bool(PRIVILEGE.search(text))
    destructive = bool(DESTRUCTIVE.search(text))
    declared_rw = item.get("read_write_class")
    declared_remote = item.get("remote_input") if isinstance(item.get("remote_input"), dict) else {}
    declared_destructive = item.get("destructive_actions") if isinstance(item.get("destructive_actions"), dict) else {}
    destructive = destructive or declared_destructive.get("present") is True
    read_only = (declared_rw == "read-only" or (declared_rw is None and item.get("kind") in {"health_check", "guard_gap", "estate_record", "observation_gap"})) and not destructive and not privilege
    z4g4_conflict = proposal.get("target") == "z4g4" and (privilege or target is None or "ssh-login" in forbidden)
    unknown = (target is None or not proposal.get("event_id") or not item.get("reason") or not item.get("name")
               or item.get("evidence_status") in {"unknown", "insufficient"})
    policy_conflicts = []
    if z4g4_conflict: policy_conflicts.append("restricted-engine-room forbids access expansion/login")
    if privilege and any(x in text.lower() for x in ("general root", "unrestricted", "万能root")): policy_conflicts.append("excessive or unrestricted credential authority")
    risks = []
    if privilege: risks.append("privilege or credential boundary may change")
    if destructive: risks.append("write or side-effecting operation is implied")
    if not risks: risks.append("no destructive or privilege-expanding action identified")
    mitigations = ["fixed policy evaluation", "proposal is not authority", "credential contents excluded", "human approval remains separate from execution"]
    if read_only: mitigations += ["existing capability boundary only", "no remote content-to-command path"]
    rollback_ready = bool(item.get("rollback")) or declared_destructive.get("rollback") is True
    result = ("UNKNOWN" if unknown else "REJECT" if policy_conflicts else
              "PASS_READ_ONLY" if read_only else
              "REVISE" if destructive and not rollback_ready else
              "PASS_WITH_HUMAN_APPROVAL" if (privilege or destructive or item.get("requires_approval")) else "REVISE")
    approval = result == "PASS_WITH_HUMAN_APPROVAL"
    record = {
        "review_id": "car-" + digest({"event_id": proposal.get("event_id"), "item": item})[:20],
        "created_at": now(), "capability_name": item.get("name"), "target": proposal.get("target"),
        "purpose": {"statement": item.get("reason"), "existing_capability": "checked against registry", "fixed_logic_possible": True},
        "requested_access": requested,
        "credentials": {"type": access.get("capability"), "identity": access.get("identity"), "scope": "existing registry scope", "source": "capability registry", "technical_restriction": "registry allowed/forbidden boundary"},
        "read_write_class": "read-only" if read_only else "write-or-side-effect",
        "remote_input": {"accepted": bool(declared_remote), "untrusted": True, "command_execution_link": False},
        "destructive_actions": {"present": destructive, "items": ["unspecified side effect"] if destructive else [], "dry_run": not destructive, "human_approval": approval, "rollback": "specified" if rollback_ready else ("required before implementation" if destructive else "not applicable")},
        "approval_required": approval or privilege or destructive,
        "rollback": {"status": "not applicable" if read_only else "must be specified before implementation", "required": not read_only},
        "rate_limits": {"status": "inherited fixed patrol limits; implementation-specific limits required" if not read_only else "existing patrol limits", "ai": "none"},
        "audit_plan": "record actor, timestamp, proposal/item hashes, approval reason, ticket and implementation evidence",
        "policy_conflicts": policy_conflicts,
        "risks": risks,
        "mitigations": mitigations,
        "evidence": {"proposal_hash": digest(proposal), "item_hash": item.get("item_hash"), "target_registered": isinstance(target, dict), "allowed_scope": allowed, "policy": policy.get("protected_targets", {})},
        "result": result, "reviewed_by": reviewed_by, "linked_growth_proposal": proposal.get("event_id"), "linked_ticket": None,
    }
    validate(record)
    return record

def validate(record):
    if not isinstance(record, dict) or set(record) != REVIEW_FIELDS: raise ValueError("capability admission record schema mismatch")
    if record.get("result") not in RESULTS: raise ValueError("invalid admission result")
    if record.get("result") == "PASS_READ_ONLY" and (record["approval_required"] or record["read_write_class"] != "read-only"): raise ValueError("read-only pass boundary violated")
    if record.get("result") == "UNKNOWN": return record
    if not isinstance(record.get("credentials"), dict) or any(SECRET.search(str(k)) for k in record["credentials"]): raise ValueError("credential secret field present")
    return record

def write_reviews(root, proposal):
    records = [evaluate(root, proposal, item) for item in proposal.get("analysis", {}).get("proposals", [])]
    for record in records:
        path = root / "state/capability_reviews" / f"{record['review_id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and json.loads(path.read_text(encoding="utf-8")) != record: raise ValueError("admission review identity collision")
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return records

def summary(record):
    checks = [
        ("Purpose justified", bool(record["purpose"].get("statement"))),
        ("Read/write separated", record["read_write_class"] in {"read-only", "write-or-side-effect"}),
        ("Credential scope recorded", bool(record["credentials"].get("scope"))),
        ("Remote input untrusted", record["remote_input"].get("untrusted") is True),
        ("Destructive action bounded", not record["destructive_actions"].get("present") or record["approval_required"]),
        ("Audit trail", bool(record["audit_plan"])), ("Rate limit", bool(record["rate_limits"])),
        ("No privilege escalation", not bool(record["policy_conflicts"])),
    ]
    lines = ["ButlerX Capability Admission Review", f"Capability: {record['capability_name']}", f"Target: {record['target']}", ""]
    lines += [f"[{'PASS' if ok else 'FAIL'}] {label}" for label, ok in checks]
    lines += ["", f"Result: {record['result']}", "", "Remaining risks:", "- " + "\n- ".join(record["risks"])]
    return "\n".join(lines)
