#!/usr/bin/env python3
"""Offline-only extraction of the saved sbat6A ubus monitor transcript."""
from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "evidence/raw/sbat6a-20260831/ubus-monitor.log"
OUT = ROOT / "evidence/analysis/sbat6a-20260831"
OUT.mkdir(parents=True, exist_ok=True)
NOTIFY = re.compile(r"^\S+\s+.*notify: (\{.*\})$")
TARGETS = [
    "ril.unsol.nw.ecell",
    "ril.unsol.nw.signal",
    "ril.unsol.nw.ltethroughput",
    "ril.unsol.nw.nrthroughput",
]


def read_events():
    events = []
    for line_no, line in enumerate(SRC.open("r", encoding="latin1"), 1):
        m = NOTIFY.match(line.rstrip("\n"))
        if not m:
            continue
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        method = obj.get("method")
        if method in TARGETS:
            events.append({"line_no": line_no, "method": method,
                           "obj": obj, "raw_line": line.rstrip("\n")})
    return events


def value_type(value):
    if isinstance(value, bool): return "boolean"
    if value is None: return "null"
    if isinstance(value, int): return "integer"
    if isinstance(value, float): return "number"
    if isinstance(value, str): return "string"
    if isinstance(value, list): return "array"
    if isinstance(value, dict): return "object"
    return type(value).__name__


def write_event_files(events):
    grouped = defaultdict(list)
    for e in events:
        grouped[e["method"]].append(e)
    for method, rows in grouped.items():
        stem = method.removeprefix("ril.unsol.nw.")
        with (OUT / f"{stem}_raw.jsonl").open("w", encoding="utf-8") as f:
            for i, e in enumerate(rows, 1):
                payload = e["obj"]["data"]
                f.write(json.dumps({"event_index": i, "timestamp": None,
                                    "log_line": e["line_no"],
                                    "raw_ubus_payload": payload,
                                    "raw_monitor_line": e["raw_line"]},
                                   ensure_ascii=True, sort_keys=True) + "\n")
        if method == "ril.unsol.nw.ecell":
            fields = ["event_index", "timestamp", "log_line", "payload_keys",
                      "payload_types", "changed_from_previous", "constant_values",
                      "raw_ubus_payload"]
            with (OUT / "ecell_table.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
                previous = None
                for i, e in enumerate(rows, 1):
                    p = e["obj"]["data"]
                    keys = list(p.keys())
                    types = {k: value_type(v) for k, v in p.items()}
                    changed = {} if previous is None else {k: [previous.get(k), p.get(k)]
                              for k in set(previous) | set(p) if previous.get(k) != p.get(k)}
                    constants = {k: v for k, v in p.items() if all(x["obj"]["data"].get(k) == v for x in rows)}
                    w.writerow({"event_index": i, "timestamp": "unavailable in capture",
                                "log_line": e["line_no"], "payload_keys": json.dumps(keys),
                                "payload_types": json.dumps(types, sort_keys=True),
                                "changed_from_previous": json.dumps(changed, ensure_ascii=True),
                                "constant_values": json.dumps(constants, ensure_ascii=True),
                                "raw_ubus_payload": json.dumps(p, ensure_ascii=True, sort_keys=True)})
                    previous = p
        else:
            with (OUT / f"{stem}_table.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(["event_index", "timestamp", "log_line", "raw_ubus_payload"])
                for i, e in enumerate(rows, 1):
                    w.writerow([i, "unavailable in capture", e["line_no"],
                                json.dumps(e["obj"]["data"], ensure_ascii=True, sort_keys=True)])


def static_extract():
    files = ["ql_ril_service", "libqlril.so", "libmipc_msg.so"]
    patterns = re.compile(r"ecell|signal|throughput|earfcn|physical_cell|provider_id|rsrq|rsrp|tac|\\bta\\b|cid|rssnr|mac_throughput|ca_signal|nr_arfcn", re.I)
    lines = ["# Offline static extraction", "", "The files are stripped AArch64 ELF binaries.", ""]
    for name in files:
        path = SRC.parent / name
        lines.append(f"## {name}")
        lines.append(f"sha256: {subprocess.check_output(['sha256sum', str(path)], text=True).split()[0]}")
        out = subprocess.check_output(["strings", "-a", str(path)], text=True, errors="replace")
        hits = [x for x in out.splitlines() if patterns.search(x)]
        lines.extend(f"- `{x}`" for x in hits)
        lines.append("")
    (OUT / "binary_static_strings.md").write_text("\n".join(lines), encoding="utf-8")


def write_summary(events):
    counts = Counter(e["method"] for e in events)
    lines = ["# sbat6A passive ubus offline analysis", "", f"Source: `{SRC}`", "",
             "## Integrity and scope", "",
             "The transcript is ASCII/Latin-1 text emitted by `ubus monitor`; it has no timestamp field.",
             "Its `data` member is a JSON string containing only the visible prefix of a binary blob, not the declared `data_len` bytes.",
             "No device connection, AT/RIL/ubus request, setting change, or binary modification was performed.", "",
             "## Counts found in the saved transcript", "",
             "| notification | count | declared data_len | distinct visible payloads |", "|---|---:|---:|---:|"]
    for method in TARGETS:
        rows = [e for e in events if e["method"] == method]
        payloads = {json.dumps(e["obj"]["data"], ensure_ascii=True, sort_keys=True) for e in rows}
        lens = sorted({e["obj"]["data"].get("data_len") for e in rows})
        lines.append(f"| `{method}` | {len(rows)} | {', '.join(map(str,lens)) or '—'} | {len(payloads)} |")
    lines += ["", "## ecell payload as actually saved", "",
              "All 47 rows are in `ecell_table.csv` and `ecell_raw.jsonl`. Every saved payload has exactly these keys and types:",
              "`id: integer`, `result: integer`, `data_len: integer`, `data: string`.",
              "The values are constant across all 47 rows: `id=1447`, `result=0`, `data_len=2248`, `data=\\u0004`.",
              "No timestamp is present; `log_line` is retained as the only ordering locator.",
              "Therefore no event-to-event value changes are observable in the saved ecell payload.", "",
              "## Requested LTE fields", "",
              "| field | result from 47 ecell payloads | status |", "|---|---|---|"]
    for field in ["state", "provider_id", "cid/ECI", "EARFCN", "physical_cell_id/PCI", "TAC", "RSRP", "RSRQ", "TA"]:
        lines.append(f"| {field} | not present in visible ubus JSON; binary body unavailable | not determinable from this artifact |")
    lines += ["", "## signal and throughput", "",
              "All 355 signal rows have the same saved envelope: `id=1440`, `result=0`, `data_len=600`, `data=\\\"\\\"` (empty string). Thus RSRP, RSRQ, RSSI, SINR, and antenna values are not recoverable from this transcript.",
              "The saved transcript contains 120 LTE-throughput notifications, not 113. Every row has `id=1446`, `result=0`, `data_len=24`; the visible prefix varies, but the remaining binary payload is absent. DL, UL, unit, interval, and traffic correlation are therefore not safely decodable.",
              "NR throughput count is 0 in the saved transcript. This supports only: no NR-throughput notification was observed in this capture; it does not establish 5G non-support.", "",
              "## Static binary correlation", "",
              "The companion `binary_static_strings.md` records strings from all three copied binaries. `ql_ril_service` contains format strings naming LTE fields (`state`, `provider_id`, `cid`, `earfcn`, `physical_cell_id`, `tac`, `rsrp`, `rsrq`, `ta`), signal (`lte rssi`, `lte rssnr`), throughput (`mac_throughput_dl`, `mac_throughput_ul`), and CA/NR handlers. This confirms implementation capability and callback vocabulary, but not values in the truncated ubus capture, field offsets, signedness, units, or JSON serialization.", "",
              "## Evidence files", "",
              "- `ecell_table.csv`: all 47 ordered rows, types, differences, constants, and raw visible payload.",
              "- `ecell_raw.jsonl`: raw monitor line and raw visible JSON payload for every ecell event.",
              "- `signal_table.csv`, `ltethroughput_table.csv`: all ordered rows.",
              "- `binary_static_strings.md`: offline strings/format evidence and hashes.", "",
              "## Safe conclusions", "",
              "The earlier snapshot in the project records PLMN 440/51, LTE, TAC 39759, ECI 169774103, and RSRP -114 dBm, but those are not values extracted from these 47 ecell payloads. EARFCN is absent, so LTE band and DL/UL frequencies cannot be calculated and KDDI frequency consistency cannot be established. PCI/ECI/TAC constancy across these ecell payloads cannot be established beyond the fact that the visible envelope is constant.",
              "A future non-destructive NR observation should use an event capture that preserves timestamps and the complete binary/blob-to-JSON decoding path, then correlate ecell, signal, LTE throughput, and NR throughput without issuing requests or changing modem state."]
    (OUT / "analysis_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    events = read_events()
    write_event_files(events)
    static_extract()
    write_summary(events)
    print(f"wrote {len(events)} events to {OUT}")


if __name__ == "__main__":
    main()
