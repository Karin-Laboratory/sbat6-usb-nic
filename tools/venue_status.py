#!/usr/bin/env python3
"""Read-only summary of Venue inventory, current health, and recent reliability."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def main():
    profile = read_json(ROOT / "runtime/venue_profile.json", {})
    state = read_json(ROOT / "state/venue_guard.json", {})
    history = read_json(ROOT / "state/venue-health-history.json", [])
    recent = history[-288:]
    healthy = sum(1 for sample in recent if sample.get("ok"))
    result = {
        "target": "venue",
        "observed_at": state.get("updated_at"),
        "current_ok": not state.get("last_problems", []),
        "current_problems": state.get("last_problems", []),
        "inventory": profile.get("service_inventory", {}),
        "restart_policy": profile.get("restart_policy", {}),
        "reliability": {
            "window": "last 288 samples (approximately 24 hours at five-minute intervals)",
            "samples": len(recent),
            "healthy_samples": healthy,
            "unhealthy_samples": len(recent) - healthy,
            "health_fraction": healthy / len(recent) if recent else None,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
