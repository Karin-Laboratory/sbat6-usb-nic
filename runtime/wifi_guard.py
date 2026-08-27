#!/usr/bin/env python3

import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path("/home/masataka/projects/butlerx")

BASE = ROOT / "memory/estate/wifi-baseline.json"
STATE = ROOT / "state/wifi_guard.json"
EVENTS = ROOT / "state/wifi-events.jsonl"
LOG = ROOT / "logs/wifi_guard.log"
QUEUE = ROOT / "state/patrol_queue"

INTERVAL = 30
CONFIRM_SCANS = 2

SSH = [
    "/usr/bin/ssh",
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=5",
    "-i", str(Path.home() / ".ssh/id_ed25519_raspi2_codex"),
    "codex@192.168.0.26",
]

LOG.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def split_escaped(s):
    out = []
    cur = []
    esc = False

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
        raise RuntimeError(
            p.stderr.strip() or f"ssh/nmcli rc={p.returncode}"
        )

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

    return aps

def load_state():
    if not STATE.exists():
        return {"candidates": {}}

    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"candidates": {}}

def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

def append_event(event):
    EVENTS.parent.mkdir(parents=True, exist_ok=True)

    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def discord_alert(ap):
    ssid = ap["ssid"] if ap["ssid"] else "(SSID非表示)"

    message = (
        "旦那さま、新しい暗号化なしWi-Fiを検出しました。\n"
        f"SSID: {ssid}\n"
        f"BSSID: {ap['bssid']}\n"
        f"Signal: {ap['signal']}%\n"
        "2回連続で観測され、RE200投入前のbaselineにはありません。\n"
        "近隣機器の可能性もあるため、自宅機器とはまだ断定していません。"
    )

    p = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/discord_say.py"),
            message,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )

    if p.returncode:
        logging.error(
            "discord alert failed for %s: %s",
            ap["bssid"],
            p.stderr.strip(),
        )
    else:
        logging.info("discord alert sent for %s", ap["bssid"])

def queue_thought(ap):
    QUEUE.mkdir(parents=True, exist_ok=True)

    event = {
        "event_type": "wifi_security_alert",
        "queued_at": now(),
        "hostname": "agent-101-vm",
        "severity": "HIGH",
        "summary": "新規の暗号化なしWi-Fi APを2回連続で検出した。",
        "sensor": "raspi2/wlan0",
        "ap": ap,
        "facts": [
            "RE200投入前baselineに存在しないBSSID",
            "2回連続観測",
            "SECURITYがopen",
            "近隣APの可能性もあり自宅機器とは未確定",
        ],
    }

    path = QUEUE / f"{time.time_ns()}.json"

    path.write_text(
        json.dumps(event, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    subprocess.Popen(
        [sys.executable, str(ROOT / "runtime/patrol_thinker.py")],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

def run_once():
    baseline = json.loads(BASE.read_text(encoding="utf-8"))
    known = {a["bssid"].upper() for a in baseline["aps"]}

    aps = scan()
    unknown = {
        bssid: ap
        for bssid, ap in aps.items()
        if bssid not in known
    }

    state = load_state()
    candidates = state.setdefault("candidates", {})

    previous_present = {
        bssid: c.get("present", False)
        for bssid, c in candidates.items()
    }

    for c in candidates.values():
        c["present"] = False

    for bssid, ap in unknown.items():
        c = candidates.setdefault(
            bssid,
            {
                "count": 0,
                "first_seen": now(),
                "notified": False,
                "recorded": False,
            },
        )

        if previous_present.get(bssid, False):
            c["count"] += 1
        else:
            c["count"] = 1

        c["present"] = True
        c["last_seen"] = now()
        c["ap"] = ap

        if not c["recorded"]:
            append_event({
                "detected_at": now(),
                "event_type": "unknown_wifi_bssid",
                "severity": "CANDIDATE" if ap["open"] else "NORMAL",
                **ap,
            })
            c["recorded"] = True

        if (
            ap["open"]
            and c["count"] >= CONFIRM_SCANS
            and not c["notified"]
        ):
            event = {
                "detected_at": now(),
                "event_type": "new_open_wifi_bssid",
                "severity": "HIGH",
                "confirmation_scans": c["count"],
                **ap,
            }

            append_event(event)
            discord_alert(ap)
            queue_thought(ap)

            c["notified"] = True

            logging.warning(
                "HIGH new open AP %s ssid=%r signal=%s",
                bssid,
                ap["ssid"],
                ap["signal"],
            )

    for bssid, c in candidates.items():
        if not c.get("present"):
            c["count"] = 0

    state["updated_at"] = now()
    state["current_bssids"] = len(aps)
    state["unknown_bssids"] = len(unknown)

    save_state(state)

    print(
        f"current={len(aps)} "
        f"baseline={len(known)} "
        f"unknown={len(unknown)}"
    )

def main():
    if "--once" in sys.argv:
        run_once()
        return

    logging.info(
        "wifi guard started interval=%ss confirm=%s",
        INTERVAL,
        CONFIRM_SCANS,
    )

    while True:
        try:
            run_once()
        except Exception as e:
            logging.exception("wifi guard scan failed: %r", e)

        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
