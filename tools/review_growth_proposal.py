#!/usr/bin/env python3
"""Explicit human CLI for reviewing proposals. This tool never executes them."""
import argparse
import getpass
import os
import sys
from pathlib import Path


ROOT = Path("/home/masataka/projects/butlerx")
sys.path.insert(0, str(ROOT / "runtime"))
from growth_review import ReviewError, transition_review  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Review a growth proposal; approval is not execution permission")
    ap.add_argument("--event-id", required=True)
    ap.add_argument("--item", required=True, help="stable proposal item ID from list_growth_reviews.py")
    choice = ap.add_mutually_exclusive_group(required=True)
    choice.add_argument("--approve", action="store_true")
    choice.add_argument("--reject", action="store_true")
    ap.add_argument("--reason", required=True)
    args = ap.parse_args()
    actor = f"{getpass.getuser()} (uid={os.getuid()})"
    try:
        review, changed = transition_review(ROOT, args.event_id, args.item, "approved" if args.approve else "rejected", actor, args.reason)
    except ReviewError as exc:
        print(f"REVIEW_REFUSED: {exc}", file=sys.stderr)
        return 1
    print(f"{'REVIEWED' if changed else 'UNCHANGED'} {review['event_id']} {args.item} {review['items'][args.item]['status']} aggregate={review['aggregate_status']}")
    print("Approval records candidacy only; it is not execution permission.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
