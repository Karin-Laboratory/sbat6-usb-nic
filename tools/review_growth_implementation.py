#!/usr/bin/env python3
"""Explicit human lifecycle review for a non-executing growth ticket."""

import argparse
import getpass
import os
import sys
from pathlib import Path

ROOT = Path("/home/masataka/projects/butlerx")
sys.path.insert(0, str(ROOT / "runtime"))
from growth_implementation import ImplementationError, transition  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Record implementation evidence; no ticket work is executed")
    parser.add_argument("--ticket-id", required=True)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--implemented", action="store_true")
    choice.add_argument("--verified", action="store_true")
    choice.add_argument("--cancelled", action="store_true")
    parser.add_argument("--reason", required=True)
    parser.add_argument("--git-checkpoint", help="required with --implemented; explicit 7-64 digit Git object ID")
    parser.add_argument("--verification-summary", help="optional with --verified; defaults to --reason")
    args = parser.parse_args()
    status = "implemented" if args.implemented else "verified" if args.verified else "cancelled"
    actor = f"{getpass.getuser()} (uid={os.getuid()})"
    try:
        record = transition(
            ROOT, args.ticket_id, status, actor, args.reason,
            git_checkpoint=args.git_checkpoint,
            verification_summary=args.verification_summary,
        )
    except ImplementationError as exc:
        print(f"IMPLEMENTATION_REVIEW_REFUSED: {exc}", file=sys.stderr)
        return 1
    print(f"RECORDED {record['ticket_id']} status={record['status']}")
    print("STOP: this record is not execution authority and triggers no implementation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
