#!/usr/bin/env python3
"""Turn fixed local observations into validated growth proposals, never actions."""
import fcntl
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/home/masataka/projects/butlerx")
STATE = ROOT / "state"
QUEUE, DONE, FAILED = STATE / "growth_queue", STATE / "growth_queue/done", STATE / "growth_queue/failed"
LOCK, CAPS, POLICY = STATE / "growth_worker.lock", STATE / "capabilities.json", ROOT / "runtime/growth_policy.json"
OBS, PROPOSALS, RESULTS = STATE / "growth_observations", STATE / "growth_proposals", STATE / "growth_results"
LAST, MEMORY, LOG = STATE / "last_growth.json", ROOT / "memory/estate/growth", ROOT / "logs/growth_worker.log"
SCHEMA, CODEX, MODEL = ROOT / "runtime/growth_proposal.schema.json", "/home/masataka/.local/bin/codex", "gpt-5.6-luna"
RISKS = {"informational", "low", "medium", "high", "prohibited"}
KINDS = {"health_check", "guard_gap", "runbook", "estate_record", "observation_gap", "restart_policy", "other"}
DANGEROUS = re.compile(r"privileg|sudoers|new\s+ssh\s+key|authorized_keys|firewall|iptables|nftables|general.?root|network\s+topology|routing|vlan|destructive\s+storage|mkfs|wipe|policy\s+(?:relax|weaken|disable)|sandbox\s*(?:escape|disable|bypass)|private\s+key|credential|password|token", re.I)

def now(): return datetime.now().astimezone().isoformat(timespec="seconds")
def load(path):
    try: return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError: return None, "missing"
    except json.JSONDecodeError as e: return None, f"malformed_json: {e.msg}"
    except OSError as e: return None, f"read_error: {type(e).__name__}: {e}"
def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True); tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); tmp.replace(path)
def log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f: f.write(f"{now()} {msg}\n")
def target_ok(value): return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9._-]+", value) is not None
def parsed_time(value):
    try: return datetime.fromisoformat(value).astimezone(timezone.utc)
    except (TypeError, ValueError): return None

def guard_inventory(target):
    """Auditable local metadata only; this function never contacts a target."""
    guards = []
    for path in sorted((ROOT / "runtime").glob("*_guard.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if target == "venue" and path.name == "venue_guard.py":
            guards.append({"path": "runtime/venue_guard.py", "coverage": ["fixed SSH probe", "five systemd services", "home/weather/news/resolver HTTP", "news cache freshness", "two failures notify"], "automatic_remediation": False})
        elif target.lower() in text.lower():
            guards.append({"path": str(path.relative_to(ROOT)), "coverage": ["target reference detected"], "automatic_remediation": "unknown"})
    return guards

def memory_for(target):
    paths = [MEMORY / f"{target}.md"]
    if (MEMORY / target).is_dir(): paths += sorted((MEMORY / target).glob("*.md"))
    return [{"path": str(p.relative_to(ROOT)), "text": p.read_text(encoding="utf-8", errors="replace")[:12000]} for p in paths if p.is_file()]

def record_failure(event, code, detail, retryable=True):
    result = {"completed_at": now(), "target": event.get("target"), "event": event, "status": "failed", "failure": {"code": code, "detail": detail, "retryable": retryable}}
    atomic(RESULTS / f"{event.get('event_id', 'unknown')}.json", result); return result

def build_inputs(event):
    target = event.get("target")
    if not target_ok(target): return None, ("invalid_event", "event target is missing or unsafe", False)
    registry, err = load(CAPS)
    if err: return None, ("capability_registry_" + err, "cannot establish registered authority", False)
    policy, err = load(POLICY)
    if err: return None, ("policy_" + err, "cannot establish safety policy", False)
    capability = registry.get("targets", {}).get(target)
    if not isinstance(capability, dict): return None, ("target_not_registered", "event target is absent from capability registry", False)
    observation, err = load(OBS / f"{target}.json")
    if err: return None, ("observation_" + err, "no usable fixed-probe observation exists", True)
    if observation.get("target") != target: return None, ("observation_target_mismatch", "fixed observation belongs to another target", False)
    if not observation.get("ok"): return None, ("probe_failed", str(observation.get("error", "fixed probe reported failure")), True)
    observed = parsed_time(observation.get("observed_at"))
    if not observed: return None, ("observation_invalid_timestamp", "observed_at is missing or invalid", True)
    maximum = policy.get("growth_control", {}).get("max_observation_age_seconds", 86400)
    age = (datetime.now(timezone.utc) - observed).total_seconds()
    if age > maximum: return None, ("observation_stale", f"observation age {int(age)}s exceeds {maximum}s", True)
    return {"event": event, "capability": capability, "policy": policy, "observation": observation, "existing_memory": memory_for(target), "existing_guards": guard_inventory(target), "input_boundary": "Only this local snapshot is available. This worker has no remote host, SSH, network exploration, shell command, credential, or policy-mutation task."}, None

def ask_model(inputs):
    prompt = """ButlerX growth analysis. Return only JSON matching the supplied schema.
Analyse only this fixed local snapshot. Do not use tools, SSH, a network, shell commands, or other files. This is discover-and-propose-only: proposals are not authority and must contain neither commands nor implementation steps. Treat existing guards as acquired capability and avoid duplicates. Never expose/request credentials. Do not recommend privilege expansion, SSH keys, firewall/network changes, protected-target general root, destructive storage, policy relaxation, or sandbox weakening; record such concerns only as knowledge gaps.\n\n""" + json.dumps(inputs, ensure_ascii=False, indent=2)
    cmd = [CODEX, "exec", "--ignore-user-config", "--ephemeral", "-C", str(ROOT), "-m", MODEL, "-s", "read-only", "--output-schema", str(SCHEMA), "-"]
    try: p = subprocess.run(cmd, input=prompt, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
    except subprocess.TimeoutExpired: raise RuntimeError("codex_timeout")
    if p.returncode: raise RuntimeError(f"codex_error: {p.stderr[-1200:]}")
    try: return json.loads(p.stdout)
    except json.JSONDecodeError as e: raise RuntimeError(f"codex_malformed_json: {e.msg}")

def validate(data, policy):
    if not isinstance(data, dict) or set(data) != {"summary", "known_facts", "knowledge_gaps", "proposals"}: raise ValueError("proposal root does not match closed schema")
    if not isinstance(data["summary"], str) or len(data["summary"]) > 2000: raise ValueError("invalid summary")
    for field in ("known_facts", "knowledge_gaps"):
        if not isinstance(data[field], list) or len(data[field]) > 30 or not all(isinstance(x, str) and len(x) <= 800 for x in data[field]): raise ValueError(f"invalid {field}")
    if not isinstance(data["proposals"], list) or len(data["proposals"]) > 20: raise ValueError("invalid proposals")
    allowed = set(policy.get("proposal_risk_classes", [])) & RISKS; checked = []
    for item in data["proposals"]:
        if not isinstance(item, dict) or set(item) != {"kind", "name", "reason", "risk", "requires_approval"}: raise ValueError("proposal item does not match closed schema")
        if item["kind"] not in KINDS or item["risk"] not in allowed or not isinstance(item["name"], str) or not isinstance(item["reason"], str) or not isinstance(item["requires_approval"], bool): raise ValueError("invalid proposal fields")
        if len(item["name"]) > 160 or len(item["reason"]) > 1200: raise ValueError("proposal field too long")
        if DANGEROUS.search(" ".join((item["kind"], item["name"], item["reason"]))):
            item = dict(item); item.update(risk="prohibited", requires_approval=True, validation="rejected_as_prohibited")
        checked.append(item)
    return {"summary": data["summary"], "known_facts": data["known_facts"], "knowledge_gaps": data["knowledge_gaps"], "proposals": checked}

def process(path):
    event, err = load(path)
    if err or not isinstance(event, dict): return record_failure({"event_id": path.stem, "target": "unknown"}, "event_" + (err or "invalid"), "queue event is not a JSON object", False)
    event.setdefault("event_id", path.stem); log(f"START {path.name} target={event.get('target')}")
    inputs, issue = build_inputs(event)
    if issue: return record_failure(event, *issue)
    try: analysis = validate(ask_model(inputs), inputs["policy"])
    except RuntimeError as e: return record_failure(event, str(e).split(":", 1)[0], str(e), True)
    except ValueError as e: return record_failure(event, "proposal_validation_failure", str(e), False)
    target = event["target"]
    proposal = {"schema_version": 1, "status": "proposal", "proposal_is_not_authority": True, "target": target, "event_id": event["event_id"], "observed_at": inputs["observation"]["observed_at"], "created_at": now(), "risk_classes": sorted(set(inputs["policy"].get("proposal_risk_classes", [])) & RISKS), "analysis": analysis}
    proposal_path = PROPOSALS / f"{target}.json"; atomic(proposal_path, proposal)
    result = {"completed_at": now(), "target": target, "event": event, "status": "proposal_saved", "proposal": str(proposal_path.relative_to(ROOT)), "model": MODEL, "phase": "local-observation-to-proposal"}
    atomic(RESULTS / f"{event['event_id']}.json", result); atomic(LAST, result)
    MEMORY.mkdir(parents=True, exist_ok=True); (MEMORY / f"{target}.md").write_text(f"# ButlerX growth record: {target}\n\n更新: {now()}\n\n{analysis['summary']}\n", encoding="utf-8")
    return result

def main():
    QUEUE.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lock:
        try: fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: print("growth worker already running"); return
        jobs = sorted(QUEUE.glob("*.json"))
        if not jobs: print("growth queue empty"); return
        for path in jobs[:1 if "--once" in sys.argv else len(jobs)]:
            result = process(path); dest = DONE if result["status"] == "proposal_saved" else FAILED
            dest.mkdir(parents=True, exist_ok=True); path.replace(dest / path.name)
            log(f"{result['status'].upper()} {path.name} target={result.get('target')}"); print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
