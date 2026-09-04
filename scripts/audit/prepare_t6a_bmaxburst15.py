#!/usr/bin/env python3
"""Prepare (never install) the verified T6A NCM bMaxBurst candidate.

The guard is intentionally specific: this tool changes only the NCM bulk
companion byte identified by the 2026-09-04 static re-analysis.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

OFFSET = 0x10FD2
OLD = 0x00
NEW = 0x0F
CONTEXT_OFFSET = 0x10FD0
CONTEXT = bytes.fromhex("06 30 00 00 00 00 06 30 00 00 10 00")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("original", type=Path)
    ap.add_argument("candidate", type=Path)
    args = ap.parse_args()

    src = args.original.read_bytes()
    if src[:4] != b"\x7fELF":
        raise SystemExit("refusing non-ELF input")
    if len(src) <= OFFSET:
        raise SystemExit("input is shorter than verified offset")
    if src[CONTEXT_OFFSET:CONTEXT_OFFSET + len(CONTEXT)] != CONTEXT:
        raise SystemExit("verified NCM descriptor context is absent; refusing")
    if src[OFFSET] != OLD:
        raise SystemExit(f"offset 0x{OFFSET:x} is {src[OFFSET]:02x}, expected 00")

    out = bytearray(src)
    out[OFFSET] = NEW
    diffs = [i for i, (a, b) in enumerate(zip(src, out)) if a != b]
    if diffs != [OFFSET]:
        raise SystemExit(f"unexpected diff set: {diffs!r}")
    args.candidate.write_bytes(out)
    print(f"original_sha256 {sha256(src)}")
    print(f"candidate_sha256 {sha256(out)}")
    print(f"changed_offset 0x{OFFSET:x} {OLD:02x}->{NEW:02x}")
    print("changed_bytes 1")
    print("install_performed no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
