#!/usr/bin/env python3
"""Explicitly create a non-executing ticket from an approved growth review."""
import argparse
import getpass
import os
import sys
from pathlib import Path


ROOT = Path("/home/masataka/projects/butlerx")
sys.path.insert(0, str(ROOT / "runtime"))
from growth_ticket import TicketError, create_ticket  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Create an implementation candidate ticket; nothing is executed")
    ap.add_argument("--event-id", required=True)
    selection = ap.add_mutually_exclusive_group(required=True)
    selection.add_argument("--item", action="append", dest="items", help="approved stable proposal item ID; repeatable")
    selection.add_argument("--all-approved", action="store_true")
    args = ap.parse_args()
    actor = f"{getpass.getuser()} (uid={os.getuid()})"
    try:
        ticket, created = create_ticket(ROOT, args.event_id, actor, proposal_ids=args.items, all_approved=args.all_approved)
    except TicketError as exc:
        print(f"TICKET_REFUSED: {exc}", file=sys.stderr)
        return 1
    print(f"{'CREATED' if created else 'EXISTS'} {ticket['ticket_id']} status={ticket['status']}")
    print("STOP: this ticket is not execution authority and has no automatic consumer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
