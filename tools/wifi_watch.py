#!/usr/bin/env python3
import json, re, subprocess, sys
from datetime import datetime
from pathlib import Path

ROOT = Path("/home/masataka/projects/butlerx")
BASE = ROOT / "memory/estate/wifi-baseline.json"
CURRENT = ROOT / "state/wifi-current.json"
EVENTS = ROOT / "state/wifi-events.jsonl"

SSH = [
    "/usr/bin/ssh",
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=5",
    "-i", str(Path.home() / ".ssh/id_ed25519_raspi2_codex"),
    "codex@192.168.0.26",
]

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def split_escaped(s):
    out, cur, esc = [], [], False
    for c in s:
        if esc:
            cur.append(c)
            esc = False
        elif c == "\\":
            esc = True
        elif c == ":":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(c)
    out.append("".join(cur))
    return out

def scan():
    remote = (
        "sudo -n /usr/local/sbin/butlerx-wifi-rescan"
        " && sleep 2"
        " && nmcli -t -f BSSID,SSID,FREQ,CHAN,SIGNAL,SECURITY"
        " dev wifi list ifname wlan0"
    )

    p = subprocess.run(
        SSH + [remote],
        text=True,
        capture_output=True,
        timeout=25,
    )

    if p.returncode:
        raise SystemExit(p.stderr.strip())

    aps = {}
    for line in p.stdout.splitlines():
        f = split_escaped(line)
        if len(f) != 6:
            continue

        bssid, ssid, freq, chan, signal, security = f
        bssid = bssid.upper()

        ap = {
            "bssid": bssid,
            "ssid": ssid,
            "freq": freq,
            "chan": chan,
            "signal": int(signal or 0),
            "security": security,
            "open": security.strip() in ("", "--"),
        }

        if bssid not in aps or ap["signal"] > aps[bssid]["signal"]:
            aps[bssid] = ap

    return sorted(aps.values(), key=lambda x: x["bssid"])

aps = scan()

CURRENT.parent.mkdir(parents=True, exist_ok=True)
CURRENT.write_text(json.dumps({
    "observed_at": now(),
    "sensor": "raspi2/wlan0",
    "aps": aps,
}, ensure_ascii=False, indent=2) + "\n")

if "--init" in sys.argv:
    BASE.parent.mkdir(parents=True, exist_ok=True)
    BASE.write_text(json.dumps({
        "created_at": now(),
        "sensor": "raspi2/wlan0",
        "aps": aps,
    }, ensure_ascii=False, indent=2) + "\n")

    print(f"baseline: {len(aps)} BSSIDs")
    print("known open:")
    for ap in aps:
        if ap["open"]:
            print(f'  {ap["bssid"]}  SSID={ap["ssid"]!r}  signal={ap["signal"]}')
    raise SystemExit

baseline = json.loads(BASE.read_text())
known = {x["bssid"] for x in baseline["aps"]}
new = [x for x in aps if x["bssid"] not in known]

print(f"current={len(aps)} known={len(known)} new={len(new)}")

for ap in new:
    severity = "HIGH" if ap["open"] else "NORMAL"
    event = {
        "detected_at": now(),
        "event_type": "new_wifi_bssid",
        "severity": severity,
        **ap,
    }
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(
        f'{severity}: {ap["bssid"]} '
        f'SSID={ap["ssid"]!r} SECURITY={ap["security"]!r} '
        f'SIGNAL={ap["signal"]}'
    )
