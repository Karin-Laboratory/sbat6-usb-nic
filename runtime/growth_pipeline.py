#!/usr/bin/env python3
"""Auditable growth event orchestration. It discovers and proposes; it never applies."""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from growth_review import canonical_hash, validate_proposal, validate_review


STAGES = {
    "registered", "probe_pending", "probe_failed", "observation_ready",
    "analysis_pending", "analysis_failed", "proposal_ready", "review_pending",
}
TERMINAL = {"review_pending"}
RISK_RANK = {"informational": 0, "low": 1, "medium": 2, "high": 3, "prohibited": 4}


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def lifecycle_path(root, event_id):
    return root / "state/growth_events" / f"{event_id}.json"


def new_lifecycle(event):
    stamp = now()
    return {
        "schema_version": 1, "event_id": event["event_id"], "target": event["target"],
        "capability_fingerprint": event["capability_fingerprint"], "status": "registered",
        "failure_domain": None, "failure": None, "retryable": True,
        "next_retry_at": None, "attempts": {"probe": 0, "analysis": 0},
        "notification": {"status": "not_attempted", "attempted_at": None, "error": None},
        "created_at": stamp, "updated_at": stamp,
        "history": [{"timestamp": stamp, "status": "registered", "failure_domain": None}],
        "proposal_is_not_authority": True, "approval_is_not_execution_permission": True,
    }


def register_event(root, event):
    event_path = root / "state/growth_queue" / f"{event['event_id']}.json"
    state_path = lifecycle_path(root, event["event_id"])
    if event_path.exists() or state_path.exists():
        raise RuntimeError("growth event already exists")
    # The queue file is the publication point. growthd cannot observe the
    # event until its bound lifecycle state is durable.
    atomic_json(state_path, new_lifecycle(event))
    atomic_json(event_path, event)
    return event_path


def transition(root, state, status, failure_domain=None, failure=None, retryable=True):
    if status not in STAGES:
        raise RuntimeError(f"invalid growth status: {status}")
    stamp = now()
    state.update(status=status, failure_domain=failure_domain, failure=failure, retryable=retryable, updated_at=stamp)
    state["history"].append({"timestamp": stamp, "status": status, "failure_domain": failure_domain, "failure": failure})
    atomic_json(lifecycle_path(root, state["event_id"]), state)


def retry_time(attempt):
    seconds = min(3600, 30 * (2 ** min(max(attempt - 1, 0), 7)))
    return (datetime.now().astimezone() + timedelta(seconds=seconds)).isoformat(timespec="seconds")


def retry_due(state):
    value = state.get("next_retry_at")
    if not value:
        return True
    try:
        return datetime.now(timezone.utc) >= datetime.fromisoformat(value).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return True


def observation_matches(root, event):
    path = root / "state/growth_observations" / f"{event['target']}.json"
    try:
        observation = load_json(path)
        policy = load_json(root / "runtime/growth_policy.json")
        observed = datetime.fromisoformat(observation["observed_at"]).astimezone(timezone.utc)
        maximum = policy["growth_control"]["max_observation_age_seconds"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return False
    return (
        observation.get("ok") is True
        and observation.get("event_id") == event["event_id"]
        and observation.get("target") == event["target"]
        and observation.get("capability_fingerprint") == event["capability_fingerprint"]
        and (datetime.now(timezone.utc) - observed).total_seconds() <= maximum
    )


def notify_discord(root, event, proposal, runner=subprocess.run):
    items = proposal["analysis"]["proposals"]
    risks = [item["risk"] for item in items if item.get("risk") in RISK_RANK]
    maximum = max(risks, key=RISK_RANK.get) if risks else "informational"
    message = (
        f"旦那さま、新しく{event['target']}を調べました。\n"
        f"成長提案を{len(items)}件作成しました。\n"
        f"最大risk: {maximum}\n未承認です。"
    )
    return runner(
        [sys.executable, str(root / "tools/discord_say.py"), message],
        cwd=root, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=30,
    )


def existing_pending_proposal(root, event):
    try:
        proposal = validate_proposal(load_json(root / "state/growth_proposals/history" / f"{event['event_id']}.json"), event["event_id"])
        review = validate_review(load_json(root / "state/growth_reviews" / f"{event['event_id']}.json"))
    except Exception:
        return None
    if (
        proposal["target"] != event["target"] or review["target"] != event["target"]
        or review["status"] != "pending" or review["proposal_hash"] != canonical_hash(proposal)
    ):
        return None
    return proposal


def finish_with_notification(root, event_path, event, state, proposal, runner, notifier):
    notification = state.get("notification", {})
    if notification.get("status") == "attempting":
        state["notification"] = {"status": "uncertain_after_crash", "attempted_at": notification.get("attempted_at"), "error": "delivery outcome unknown; not retried to avoid duplicate notification"}
    elif notification.get("status") not in {"sent", "failed", "uncertain_after_crash"}:
        state["notification"] = {"status": "attempting", "attempted_at": now(), "error": None}
        atomic_json(lifecycle_path(root, event["event_id"]), state)
        try:
            sent = notifier(root, event, proposal, runner=runner)
            if sent.returncode:
                raise RuntimeError("notification command failed")
            state["notification"] = {"status": "sent", "attempted_at": now(), "error": None}
        except Exception as exc:
            state["notification"] = {"status": "failed", "attempted_at": now(), "error": f"{type(exc).__name__}: {exc}"[:500]}
    atomic_json(lifecycle_path(root, event["event_id"]), state)
    transition(root, state, "review_pending")
    archive_event(root, event_path)
    return state
def archive_event(root, event_path):
    destination = root / "state/growth_queue/done" / event_path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(event_path, destination)


def process_event(root, event_path, runner=subprocess.run, notifier=notify_discord):
    event = load_json(event_path)
    state_path = lifecycle_path(root, event["event_id"])
    state = load_json(state_path) if state_path.exists() else new_lifecycle(event)
    if state["event_id"] != event["event_id"] or state["target"] != event["target"] or state["capability_fingerprint"] != event["capability_fingerprint"]:
        transition(root, state, "probe_failed", "BUTLERX_FAILURE", {"code": "event_state_mismatch", "detail": "event and lifecycle binding differ"}, False)
        return state
    if state["status"] in TERMINAL:
        archive_event(root, event_path)
        return state
    if state["status"] == "proposal_ready":
        proposal = existing_pending_proposal(root, event)
        if proposal is None:
            state["next_retry_at"] = retry_time(state["attempts"]["analysis"] or 1)
            transition(root, state, "analysis_failed", "ANALYSIS_FAILURE", {"code": "missing_valid_proposal", "detail": "proposal_ready state has no bound pending proposal"}, True)
            return state
        return finish_with_notification(root, event_path, event, state, proposal, runner, notifier)
    if state["status"] in {"probe_failed", "analysis_failed"} and not retry_due(state):
        return state

    if not observation_matches(root, event):
        transition(root, state, "probe_pending")
        state["attempts"]["probe"] += 1
        atomic_json(state_path, state)
        try:
            probe = runner(
                [sys.executable, str(root / "runtime/growth_probe.py"), "--target", event["target"], "--event-id", event["event_id"]],
                cwd=root, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            state["next_retry_at"] = retry_time(state["attempts"]["probe"])
            transition(root, state, "probe_failed", "BUTLERX_FAILURE", {"code": type(exc).__name__, "detail": "fixed probe process could not complete"}, True)
            return state
        if probe.returncode or not observation_matches(root, event):
            state["next_retry_at"] = retry_time(state["attempts"]["probe"])
            try:
                failed_observation = load_json(root / "state/growth_observations" / f"{event['target']}.json")
                bound_failure = failed_observation.get("event_id") == event["event_id"] and failed_observation.get("capability_fingerprint") == event["capability_fingerprint"] and failed_observation.get("ok") is False
            except (FileNotFoundError, json.JSONDecodeError, AttributeError):
                bound_failure = False
            domain = "OBSERVATION_FAILURE" if bound_failure else "BUTLERX_FAILURE"
            code = "fixed_probe_failed" if bound_failure else "probe_process_failed_without_bound_result"
            transition(root, state, "probe_failed", domain, {"code": code, "detail": "target health is unknown; ButlerX did not obtain a usable bound observation"}, True)
            return state
    state["next_retry_at"] = None
    transition(root, state, "observation_ready")
    transition(root, state, "analysis_pending")
    proposal = existing_pending_proposal(root, event)
    if proposal is None:
        state["attempts"]["analysis"] += 1
        atomic_json(state_path, state)
        try:
            worker = runner(
                [sys.executable, str(root / "runtime/growth_worker.py"), "--event-id", event["event_id"], "--keep-event"],
                cwd=root, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=330,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            state["next_retry_at"] = retry_time(state["attempts"]["analysis"])
            transition(root, state, "analysis_failed", "BUTLERX_FAILURE", {"code": type(exc).__name__, "detail": "growth worker process could not complete"}, True)
            return state
        if worker.returncode:
            state["next_retry_at"] = retry_time(state["attempts"]["analysis"])
            transition(root, state, "analysis_failed", "ANALYSIS_FAILURE", {"code": "growth_worker_failed", "detail": "proposal was not produced; capability registration remains valid"}, True)
            return state
        proposal = existing_pending_proposal(root, event)
    if proposal is None:
        state["next_retry_at"] = retry_time(state["attempts"]["analysis"])
        transition(root, state, "analysis_failed", "ANALYSIS_FAILURE", {"code": "missing_valid_proposal", "detail": "worker returned without a bound pending proposal"}, True)
        return state
    state["next_retry_at"] = None
    transition(root, state, "proposal_ready")
    return finish_with_notification(root, event_path, event, state, proposal, runner, notifier)
