#!/usr/bin/env python3
"""Read-only numbered listing of item-level growth reviews."""
import json
import sys
from pathlib import Path

ROOT = Path("/home/masataka/projects/butlerx")
sys.path.insert(0, str(ROOT / "runtime"))
from growth_review import ReviewError, load_json, validate_proposal, validate_review_binding  # noqa: E402

def main():
    for path in sorted((ROOT / "state/growth_reviews").glob("*.json")):
        try:
            raw = load_json(path)
            if raw.get("schema_version") != 2:
                print(f"EVENT {path.stem} LEGACY_REVIEW migration-required")
                continue
            proposal = validate_proposal(load_json(ROOT / "state/growth_proposals/history" / f"{raw['event_id']}.json"), raw["event_id"])
            review = validate_review_binding(raw, proposal)
            print(f"EVENT {review['event_id']} target={review['target']} aggregate={review['aggregate_status']}")
            for number, item in enumerate(proposal["analysis"]["proposals"], 1):
                decision = review["items"][item["proposal_id"]]
                name = " ".join(str(item.get("name", "")).split())[:100]
                print(f"  {number:>2} {item['proposal_id']} {decision['status']:<8} {item['risk']:<13} {name}")
        except (ReviewError, KeyError, TypeError, json.JSONDecodeError) as exc:
            print(f"EVENT {path.stem} INVALID {exc}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
