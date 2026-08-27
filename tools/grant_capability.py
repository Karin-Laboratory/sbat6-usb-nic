#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path("/home/masataka/projects/butlerx")
REGISTRY = ROOT / "state/capabilities.json"
POLICY = ROOT / "runtime/growth_policy.json"
sys.path.insert(0, str(ROOT / "runtime"))
from growth_pipeline import register_event  # noqa: E402


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


def capability_fingerprint(target, info):
    payload = {"target": target, "capability": info}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


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
        "capability_fingerprint": capability_fingerprint(args.target, current),
        "reason":
            "新しい管理能力が登録されたため、"
            "対象を理解して安全な運用能力へ変換する。"
    }

    path = register_event(ROOT, event)

    print(f"REGISTERED {args.target}")
    print(f"QUEUED {path}")

    print("GROWTH_REGISTERED: growthd will run the fixed probe and analysis asynchronously")


if __name__ == "__main__":
    main()
