#!/usr/bin/env python3
"""Fail-closed consistency check for STATUS.md evidence claims.

PROVEN claims must carry a repository-relative markdown link to an evidence
file whose terminal EVIDENCE_STATUS is PROVEN.  Other terminal verdicts are
accepted for non-PROVEN status lines but are reported when they contradict a
claim's wording.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

VERDICTS = {"PROVEN", "OBSERVED", "CORROBORATED", "HYPOTHESIS", "UNPROVEN", "RETRACTED"}
BAD = {"UNPROVEN", "RETRACTED", "FAIL", "NOT_PROVEN", "NOT_RUN"}
LINK_RE = re.compile(r"\[[^]]+\]\(([^)]+)\)")
VERDICT_RE = re.compile(r"^EVIDENCE_STATUS\s*=\s*([A-Z_]+)\s*$", re.M)
# A status document is a snapshot, not a time-series log. Use scoped key names
# when two scopes need different verdicts.
KEY_RE = re.compile(r"^\s*([A-Z][A-Z0-9_]+)\s*=\s*(.*?)\s*$")


def evidence_status(path: Path) -> str | None:
    text = path.read_text(errors="replace")
    match = VERDICT_RE.findall(text)
    return match[-1] if match else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("status", nargs="?", default="STATUS.md")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    status_path = Path(args.status).resolve()
    root = status_path.parent
    lines = status_path.read_text(errors="replace").splitlines()
    in_proven = False
    errors: list[str] = []
    checks: list[dict[str, object]] = []
    key_values: dict[str, list[tuple[int, str]]] = {}
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        key_match = KEY_RE.match(line)
        if key_match:
            key, value = key_match.groups()
            key_values.setdefault(key, []).append((number, value))
        if re.match(r"^#{1,6}\s+PROVEN\s*:?.*$", stripped, re.I):
            in_proven = True
            continue
        if in_proven and re.match(r"^#{1,6}\s+", stripped):
            in_proven = False
        if not in_proven or not stripped.startswith("-"):
            continue
        links = LINK_RE.findall(line)
        record: dict[str, object] = {"line": number, "entry": stripped, "links": links}
        if not links:
            errors.append(f"line {number}: PROVEN entry has no evidence link")
            checks.append(record)
            continue
        target = links[0].split("#", 1)[0]
        target_path = (root / target).resolve()
        record["target"] = target
        if root not in target_path.parents and target_path != root:
            errors.append(f"line {number}: evidence escapes repository: {target}")
            checks.append(record)
            continue
        if not target_path.is_file():
            errors.append(f"line {number}: evidence target does not exist: {target}")
            checks.append(record)
            continue
        verdict = evidence_status(target_path)
        record["evidence_status"] = verdict
        if verdict != "PROVEN":
            errors.append(f"line {number}: target verdict is {verdict or 'MISSING'}, not PROVEN: {target}")
        if any(token in line.upper() for token in BAD):
            errors.append(f"line {number}: PROVEN entry contains contradictory verdict token")
        checks.append(record)
    conflicts = {
        key: records for key, records in key_values.items()
        if len({value for _, value in records}) > 1
    }
    for key, records in sorted(conflicts.items()):
        rendered = ", ".join(f"line {line}={value!r}" for line, value in records)
        errors.append(f"DUPLICATE_KEY_CONFLICT: {key}: {rendered}")
    result = {
        "STATUS_INTERNAL_CONSISTENCY": "PASS" if not conflicts else "FAIL",
        "STATUS_EVIDENCE_SYNC": "PASS" if not errors else "FAIL",
        "duplicate_key_conflicts": conflicts,
        "errors": errors,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
