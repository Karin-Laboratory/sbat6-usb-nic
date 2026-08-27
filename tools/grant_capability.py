#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path("/home/masataka/projects/butlerx")
REGISTRY = ROOT / "state/capabilities.json"
QUEUE = ROOT / "state/growth_queue"
POLICY = ROOT / "runtime/growth_policy.json"
PROBE = ROOT / "runtime/growth_probe.py"
WORKER = ROOT / "runtime/growth_worker.py"


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--role", required=True)
    ap.add_argument("--capability", required=True)
    ap.add_argument("--identity", required=True)
    ap.add_argument("--trust", required=True)
    args = ap.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.target):
        raise SystemExit("invalid target name")

    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.role):
        raise SystemExit("invalid role")

    if not re.fullmatch(r"[A-Za-z0-9+._-]+", args.capability):
        raise SystemExit("invalid capability")

    if not re.fullmatch(r"[A-Za-z0-9._-]+@[A-Za-z0-9._-]+", args.identity):
        raise SystemExit("invalid identity")

    policy = load(POLICY, {})
    profiles = policy.get("trust_profiles", {})

    if args.trust not in profiles:
        raise SystemExit(
            f"unknown trust profile: {args.trust}"
        )

    protected = policy.get("protected_targets", {})
    required = protected.get(args.target)

    if required and args.trust != required:
        raise SystemExit(
            f"{args.target} is protected: "
            f"trust must be {required}"
        )

    registry = load(
        REGISTRY,
        {
            "schema_version": 1,
            "updated_at": None,
            "targets": {}
        },
    )

    targets = registry.setdefault("targets", {})
    previous = targets.get(args.target)

    profile = profiles[args.trust]

    current = {
        "role": args.role,
        "trust": args.trust,
        "access": {
            "capability": args.capability,
            "identity": args.identity
        },
        "allowed": profile.get("allowed", []),
        "forbidden": profile.get("forbidden", []),
        "registered_at": (
            previous.get("registered_at")
            if previous
            else now()
        ),
        "updated_at": now()
    }

    comparable_previous = None
    if previous:
        comparable_previous = {
            k: v for k, v in previous.items()
            if k not in ("registered_at", "updated_at")
        }

    comparable_current = {
        k: v for k, v in current.items()
        if k not in ("registered_at", "updated_at")
    }

    if comparable_previous == comparable_current:
        print(
            f"UNCHANGED {args.target}: "
            "capability already registered"
        )
        return

    targets[args.target] = current
    registry["updated_at"] = now()
    atomic_write(REGISTRY, registry)

    QUEUE.mkdir(parents=True, exist_ok=True)

    event = {
        "event_id": f"{time.time_ns()}-{args.target}",
        "event_type": (
            "new_capability"
            if previous is None
            else "capability_changed"
        ),
        "queued_at": now(),
        "target": args.target,
        "role": args.role,
        "trust": args.trust,
        "access": current["access"],
        "allowed": current["allowed"],
        "forbidden": current["forbidden"],
        "previous": previous,
        "reason":
            "新しい管理能力が登録されたため、"
            "対象を理解して安全な運用能力へ変換する。"
    }

    path = QUEUE / f"{event['event_id']}.json"
    atomic_write(path, event)

    print(f"REGISTERED {args.target}")
    print(f"QUEUED {path}")

    # Automatic discovery is deliberately a fixed, code-owned probe followed
    # by a local, read-only proposal worker.  Neither subprocess receives
    # event-provided remote commands and neither applies a proposal.
    probe = subprocess.run(
        [sys.executable, str(PROBE), "--target", args.target],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    if probe.returncode:
        print("FIXED_PROBE_FAILED: queued event will be recorded as probe_failed")
        if probe.stderr.strip():
            print(probe.stderr.strip(), file=sys.stderr)
    else:
        print("FIXED_PROBE_OK")

    worker = subprocess.run(
        [sys.executable, str(WORKER), "--once"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=330,
    )
    if worker.stdout.strip():
        print(worker.stdout.strip())
    if worker.returncode:
        print("GROWTH_WORKER_FAILED", file=sys.stderr)
        if worker.stderr.strip():
            print(worker.stderr.strip(), file=sys.stderr)
        raise SystemExit(worker.returncode)


if __name__ == "__main__":
    main()
