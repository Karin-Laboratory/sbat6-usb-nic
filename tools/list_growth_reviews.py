#!/usr/bin/env python3
"""Read-only compact listing of growth proposal reviews."""
import json
import sys
from pathlib import Path


ROOT = Path("/home/masataka/projects/butlerx")
sys.path.insert(0, str(ROOT / "runtime"))
from growth_review import canonical_hash, ReviewError, load_json, validate_proposal, validate_review  # noqa: E402


RANK = {"informational": 0, "low": 1, "medium": 2, "high": 3, "prohibited": 4}


def main():
    print("EVENT\tTARGET\tSTATUS\tMAX_RISK\tSUMMARY")
    for path in sorted((ROOT / "state/growth_reviews").glob("*.json")):
        try:
            review = validate_review(load_json(path))
            proposal = validate_proposal(load_json(ROOT / "state/growth_proposals/history" / f"{review['event_id']}.json"), review["event_id"])
            if review["proposal_hash"] != canonical_hash(proposal) or review["target"] != proposal["target"]:
                raise ReviewError("review/proposal binding mismatch")
            risks = [p.get("risk") for p in proposal["analysis"]["proposals"] if isinstance(p, dict) and p.get("risk") in RANK]
            maximum = max(risks, key=RANK.get) if risks else "informational"
            summary = " ".join(proposal["analysis"].get("summary", "").split())[:160]
            print(f"{review['event_id']}\t{review['target']}\t{review['status']}\t{maximum}\t{summary}")
        except (ReviewError, KeyError, TypeError, json.JSONDecodeError) as exc:
            print(f"{path.stem}\t?\tINVALID\t?\t{exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
