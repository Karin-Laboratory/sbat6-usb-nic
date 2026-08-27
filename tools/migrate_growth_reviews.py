#!/usr/bin/env python3
"""Explicitly migrate legacy pending event reviews to item-level pending reviews."""
import argparse
import getpass
import os
import sys
from pathlib import Path

ROOT = Path("/home/masataka/projects/butlerx")
sys.path.insert(0, str(ROOT / "runtime"))
from growth_review import ReviewError, migrate_legacy_pending_review  # noqa: E402

def main():
    ap = argparse.ArgumentParser(description="Migrate legacy pending reviews; final decisions are never expanded")
    ap.add_argument("--event-id", action="append", required=True)
    args = ap.parse_args(); actor = f"{getpass.getuser()} (uid={os.getuid()})"
    failed = False
    for event_id in args.event_id:
        try:
            review, changed = migrate_legacy_pending_review(ROOT, event_id, actor)
            print(f"{'MIGRATED' if changed else 'UNCHANGED'} {event_id} items={len(review['items'])} aggregate={review['aggregate_status']}")
        except ReviewError as exc:
            failed = True; print(f"MIGRATION_REFUSED {event_id}: {exc}", file=sys.stderr)
    return 1 if failed else 0

if __name__ == "__main__": raise SystemExit(main())
