#!/usr/bin/env python3
"""Emit a conservative direct-access inventory for T6A compatibility work.

This is intentionally lexical and fail-closed: an access not mapped to a
vendor offset is emitted as UNKNOWN. It never turns a guessed offset into a
layout claim and is only an input to the actual-TU/final-ELF gates.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ACCESS = re.compile(r"\b(?:net|netdev|ncm->netdev)->([A-Za-z_]\w*)")
PRIV = re.compile(r"\bnetdev_priv\s*\(")
KNOWN = {
    "netdev_ops": ("0x1f8", "PROVEN"),
    "ethtool_ops": ("0x200", "PROVEN"),
    "dev_addr": ("0x318", "PROVEN"),
    "dev": ("0x510", "PROVEN"),
    "min_mtu": ("0x22c", "PROVEN"),
    "max_mtu": ("0x230", "PROVEN"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sources", nargs="+", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    records: dict[str, dict[str, object]] = {}
    for source in args.sources:
        for line_no, line in enumerate(source.read_text(errors="replace").splitlines(), 1):
            for field in ACCESS.findall(line):
                row = records.setdefault(field, {
                    "FIELD": field, "CANDIDATE_OFFSET": "UNKNOWN",
                    "VENDOR_EXPECTED_OFFSET": KNOWN.get(field, ("UNKNOWN",))[0],
                    "EVIDENCE_CLASS": KNOWN.get(field, ("UNKNOWN", "UNKNOWN"))[1],
                    "DIRECT_READ_COUNT": 0, "DIRECT_WRITE_COUNT": 0,
                    "ACCESS_SITES": [],
                })
                row["ACCESS_SITES"].append(f"{source}:{line_no}")
                # A lexical line-level approximation; final ELF is authoritative.
                if re.search(r"\b(?:=|\+=|-=|\+\+|--)", line):
                    row["DIRECT_WRITE_COUNT"] += 1
                else:
                    row["DIRECT_READ_COUNT"] += 1
    payload = {
        "schema": "t6a-direct-access-inventory-v1",
        "classification": "lexical-preaudit; UNKNOWN requires resolution",
        "fields": sorted(records.values(), key=lambda row: str(row["FIELD"])),
        "netdev_priv_call_count": sum(len(PRIV.findall(s.read_text(errors="replace"))) for s in args.sources),
        "unknown_field_count": sum(row["EVIDENCE_CLASS"] == "UNKNOWN" for row in records.values()),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FIELD\tCANDIDATE_OFFSET\tVENDOR_EXPECTED_OFFSET\tEVIDENCE_CLASS\tDIRECT_READ_COUNT\tDIRECT_WRITE_COUNT")
        for row in payload["fields"]:
            print("\t".join(str(row[key]) for key in ("FIELD", "CANDIDATE_OFFSET", "VENDOR_EXPECTED_OFFSET", "EVIDENCE_CLASS", "DIRECT_READ_COUNT", "DIRECT_WRITE_COUNT")))
        print(f"UNKNOWN_FIELD_COUNT={payload['unknown_field_count']}")
        print(f"NETDEV_PRIV_CALL_COUNT={payload['netdev_priv_call_count']}")
    return 0 if payload["unknown_field_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
