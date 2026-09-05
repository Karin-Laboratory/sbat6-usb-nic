#!/usr/bin/env python3
"""Generate ABI gates from one manifest, failing closed on unknown offsets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--tu-header", type=Path)
    ap.add_argument("--elf-spec", type=Path)
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text())
    unknown: list[str] = []
    gates: list[dict[str, object]] = []
    rows = manifest.get("field_records") or manifest.get("fields", [])
    for row in rows:
        if row.get("CANDIDATE_DIRECT_ACCESS") != "yes":
            continue
        name = f"{row.get('STRUCT')}::{row.get('FIELD')}"
        vendor = row.get("VENDOR_OFFSET")
        if vendor in (None, "", "unknown", "UNKNOWN"):
            unknown.append(name)
            continue
        gates.append({"struct": row.get("STRUCT"), "field": row.get("FIELD"),
                      "vendor_offset": vendor,
                      "tu_assertion_required": row.get("TU_ASSERTION_REQUIRED") == "yes",
                      "final_elf_expected": row.get("FINAL_ELF_EXPECTED")})
    print(f"CANDIDATE_GATE_GENERATION={'FAIL' if unknown else 'PASS'}")
    print(f"DIRECT_ACCESS_FIELDS={len(gates) + len(unknown)}")
    print(f"UNKNOWN_VENDOR_OFFSET_COUNT={len(unknown)}")
    for item in unknown:
        print(f"UNKNOWN_VENDOR_OFFSET={item}")
    for group_name, group in manifest.get("unknown_groups", {}).items():
        print(f"{group_name}={group.get('struct', '')}")
        for field in group.get("fields", []):
            print(
                "FIELD_DETAIL="
                + json.dumps({"group": group_name, **field}, ensure_ascii=False, sort_keys=True)
            )
    if unknown:
        return 2
    if args.tu_header:
        lines = ["/* generated from ABI manifest; do not edit */", "#pragma once", ""]
        lines.extend(f"/* {g['struct']}::{g['field']} = {g['vendor_offset']} */" for g in gates)
        args.tu_header.write_text("\n".join(lines) + "\n")
    if args.elf_spec:
        args.elf_spec.write_text(json.dumps({"schema": "t6a-final-elf-gates-v1", "gates": gates}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
