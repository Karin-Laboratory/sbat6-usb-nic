#!/usr/bin/env python3
"""Fixed-logic runtime selection controller for chrony's ZEN3 source.

The controller accepts only feeder health data and emits one of two fixed
selection profiles.  It deliberately has no arbitrary command interface.
"""
from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

FAILED = "ZEN3_FAILED"
NORMAL = "NORMAL_ZEN3"
RECOVERING = "ZEN3_RECOVERING"
FAIL_AFTER_SECONDS = 20.0
RECOVER_AFTER_SAMPLES = 3
REASSERT_INTERVAL = 30.0

NORMAL_COMMANDS = (("selectopts", "ZEN3", "+trust", "+prefer", "-noselect"), ("reselect",))
FAILED_COMMANDS = (("selectopts", "ZEN3", "+noselect", "-prefer", "-trust"), ("reselect",))


@dataclass
class Decision:
    state: str
    commands: tuple[tuple[str, ...], ...]
    transition: bool = False


def healthy(health: dict, now: float) -> bool:
    """Require feeder validity and freshness; accepted timestamp alone is insufficient."""
    accepted = health.get("last_accepted")
    packet_age = health.get("packet_age")
    return (health.get("valid_state") is True and accepted is not None and packet_age is not None
            and float(packet_age) <= FAIL_AFTER_SECONDS
            and now - float(accepted) <= FAIL_AFTER_SECONDS)


def decide(previous: dict | None, health: dict, now: float | None = None) -> Decision:
    previous = previous or {}
    now = time.time() if now is None else now
    is_healthy = healthy(health, now)
    accepted_recent = (health.get("last_accepted") is not None
                       and now - float(health["last_accepted"]) <= FAIL_AFTER_SECONDS)
    old = previous.get("state")
    valid_streak = int(previous.get("valid_streak", 0))
    valid_streak = valid_streak + 1 if is_healthy else 0

    if old == NORMAL and not is_healthy and accepted_recent:
        # Keep the current profile during the feeder's bounded invalidation
        # grace; do not claim a healthy source or emit a transition.
        return Decision(NORMAL, (), False)
    if old == FAILED:
        if valid_streak >= RECOVER_AFTER_SAMPLES:
            return Decision(NORMAL, NORMAL_COMMANDS, True)
        return Decision(RECOVERING, (), True)
    if old == RECOVERING:
        if not is_healthy:
            return Decision(FAILED, (), True)
        if valid_streak >= RECOVER_AFTER_SAMPLES:
            return Decision(NORMAL, NORMAL_COMMANDS, True)
        return Decision(RECOVERING, (), False)
    if not is_healthy:
        return Decision(FAILED, FAILED_COMMANDS, old != FAILED)
    return Decision(NORMAL, NORMAL_COMMANDS if old is None else (), old not in (None, NORMAL))


def apply_commands(commands, runner=subprocess.run) -> list[str]:
    """Run only the controller's compile-time command tuples."""
    output = []
    for command in commands:
        result = runner(["/usr/local/sbin/butlerx-zen3-ntp", "selection", *command], text=True, capture_output=True, check=False)
        if result.returncode:
            raise RuntimeError(f"fixed chrony operation failed: {command}: {result.stderr.strip()}")
        output.append(result.stdout.strip())
    return output


def step(previous: dict | None, health: dict, now: float | None = None, runner=subprocess.run) -> dict:
    now = time.time() if now is None else now
    decision = decide(previous, health, now)
    state = dict(previous or {})
    state.update({"state": decision.state, "valid_streak": int(previous.get("valid_streak", 0)) + 1 if healthy(health, now) else 0,
                  "last_accepted": health.get("last_accepted"), "packet_age": health.get("packet_age"),
                  "selection_options": "trust prefer selectable" if decision.state == NORMAL else "noselect no-prefer no-trust",
                  "controller_checked_at": now})
    # Reassert the fixed profile periodically. This repairs runtime chrony
    # state after chronyd restarts even when the controller process survives.
    reassert_due = ("last_reassert" in state
                    and now - float(state["last_reassert"]) >= REASSERT_INTERVAL)
    commands = decision.commands
    if not commands and decision.state in (NORMAL, FAILED) and reassert_due:
        commands = NORMAL_COMMANDS if decision.state == NORMAL else FAILED_COMMANDS
        state["reassert_reason"] = "periodic-runtime-profile-reassert"
    if commands:
        apply_commands(commands, runner)
        state["last_reassert"] = now
        if decision.state == FAILED:
            state["last_failover_timestamp"] = now
            state["failover_count"] = int(state.get("failover_count", 0)) + 1
        elif decision.state == NORMAL:
            state["last_recovery_timestamp"] = now
    return state


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    health_path = Path("/home/codex/zen3-ntp/zen3_health.json")
    state_path = Path("/home/codex/zen3-ntp/zen3_failover_state.json")
    while True:
        try:
            health = json.loads(health_path.read_text())
            previous = json.loads(state_path.read_text()) if state_path.exists() else {}
            current = step(previous, health)
            state_path.write_text(json.dumps(current, indent=2) + "\n")
            (root / "state" / "zen3_failover_last.json").parent.mkdir(parents=True, exist_ok=True)
            (root / "state" / "zen3_failover_last.json").write_text(json.dumps(current, indent=2) + "\n")
        except (FileNotFoundError, json.JSONDecodeError, RuntimeError, OSError) as exc:
            print(f"controller error: {exc}", flush=True)
        time.sleep(2)


if __name__ == "__main__":
    main()
