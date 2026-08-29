#!/usr/bin/env python3
"""Create or inspect a fixed-logic Capability Admission Review."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
from capability_admission import evaluate, summary, write_reviews  # noqa: E402

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proposal", type=Path, help="proposal JSON to review")
    ap.add_argument("--backfill", action="store_true", help="review current major capability records")
    args = ap.parse_args()
    if args.backfill:
        registry = json.loads((ROOT / "state/capabilities.json").read_text(encoding="utf-8"))
        count = 0
        targets = set(registry.get("targets", {})) | {"raspi2-observation", "receipt", "daily-estate-discovery", "zen3-gnss-patrol", "growth-subsystem", "z4g4-restricted-policy"}
        for target in sorted(targets):
            proposal = {"event_id": f"retrospective-{target}", "target": target, "analysis": {"proposals": [{"kind": "health_check", "name": f"{target} current capability", "reason": "Retrospective read-only visibility of the registered capability.", "risk": "low", "requires_approval": False, "item_hash": "retrospective"}]}}
            write_reviews(ROOT, proposal); count += 1
        print(f"BACKFILLED {count} capability reviews")
        return 0
    if not args.proposal: ap.error("--proposal or --backfill is required")
    proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
    records = write_reviews(ROOT, proposal)
    for record in records: print(summary(record)); print()
    return 0

if __name__ == "__main__": raise SystemExit(main())
