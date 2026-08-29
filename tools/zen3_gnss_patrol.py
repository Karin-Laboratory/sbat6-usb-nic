#!/usr/bin/env python3
"""Read-only Zen3 patrol with persistent, bounded offset classification."""
from __future__ import annotations
import json, re, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state/zen3_gnss_patrol.json"
HISTORY = ROOT / "state/zen3_gnss_history.jsonl"
MAX_HISTORY = 500
WARN_OFFSET, ALERT_OFFSET, CRITICAL_OFFSET, PERSISTENCE = 1.0, 2.0, 5.0, 3
REMOTE = r'''set +e
echo __USB__; lsusb | grep -i '0b05:4dae\|ASUS_Z012DA'
echo __ADB__; adb devices 2>/dev/null
echo __SERVICE__; systemctl is-active zen3-gnss-time.service
echo __SOCKET__; ss -lun 2>/dev/null | grep ':40123 '
echo __JOURNAL__; journalctl -u zen3-gnss-time.service --since '3 min ago' --no-pager 2>/dev/null | tail -30
echo __SOURCES__; chronyc sources -v
echo __STATS__; chronyc sourcestats -v
echo __TRACKING__; chronyc tracking
'''

def classify(offset: float | None, consecutive: int = 0) -> str:
    if offset is None: return "unavailable"
    value = abs(offset)
    if value > CRITICAL_OFFSET and consecutive >= PERSISTENCE: return "critical"
    if value > ALERT_OFFSET and consecutive >= PERSISTENCE: return "alert"
    if value > WARN_OFFSET and consecutive >= PERSISTENCE: return "warn"
    return "normal"

def parse_snapshot(raw: str) -> dict:
    source = next((x for x in raw.splitlines() if " ZEN3 " in x), "")
    rows = re.findall(r"accept.*?offset=([+-]?\d+(?:\.\d+)?).*?age=([0-9.]+).*?(?:sat|satellites)=([0-9]+).*?cn0=([0-9.]+)", raw)
    current = None
    match = re.search(r"([+-]\d+)(ms|us|ns)\[", source)
    if match: current = float(match.group(1)) / {"ms": 1e3, "us": 1e6, "ns": 1e9}[match.group(2)]
    state = re.search(r"#([+x~?\-])\s+ZEN3\s+\S+\s+(\d+)\s+(\d+)\s+(\d+)", source)
    selected = re.search(r"(?:\^|#)\*\s+([^\s]+)", raw)
    last = rows[-1] if rows else None
    return {"timestamp": time.time(), "usb_present": "0b05:4dae" in raw,
            "adb_present": "GCAZCY05P824JAW\\tdevice" in raw,
            "sender_service": "active" in raw.split("__SERVICE__",1)[-1].split("__SOCKET__",1)[0],
            "udp_listener": ":40123" in raw, "accepted_packets": len(rows),
            "satellites": int(last[2]) if last else None, "mean_cn0": float(last[3]) if last else None,
            "packet_age": float(last[1]) if last else None, "feeder_offsets": [float(x[0]) for x in rows[-20:]],
            "feeder_accept": len(rows), "feeder_reject": len(re.findall(r"reject", raw)),
            "chrony_state": state.group(1) if state else "?",
            "reach": int(state.group(3)) if state else 0, "last_rx": int(state.group(4)) if state else None,
            "offset": current, "internet_ntp_healthy": bool(re.search(r"\^\*|\^\+", raw)),
            "selected_source": selected.group(1) if selected else None,
            "expected_primary": "ZEN3",
            "unexpected_fallback": bool(selected and selected.group(1) != "ZEN3"),
            "zen3_usable": bool(state and state.group(1) in "*+~" and int(state.group(3)) > 0)}

def next_state(observation: dict, previous: dict | None = None) -> dict:
    previous = previous or {}; offset = observation.get("offset")
    bad = offset is None or abs(offset) > WARN_OFFSET
    count = int(previous.get("consecutive_warning", 0)) + 1 if bad else 0
    state = classify(offset, count); old = previous.get("classification", "unknown")
    notify = state != old and (state in {"warn", "alert", "critical"} or old in {"warn", "alert", "critical"})
    return dict(observation, consecutive_warning=count, classification=state, notify=notify)

def collect() -> str:
    return subprocess.check_output(["ssh", "raspi2", REMOTE], text=True, timeout=30, stderr=subprocess.STDOUT)

def save(observation: dict) -> dict:
    previous = json.loads(STATE.read_text()) if STATE.exists() else {}
    current = next_state(observation, previous); STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n")
    with HISTORY.open("a", encoding="utf-8") as stream: stream.write(json.dumps(current, ensure_ascii=False) + "\n")
    lines = HISTORY.read_text(encoding="utf-8").splitlines()[-MAX_HISTORY:]
    HISTORY.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return current

def notify(current: dict) -> None:
    if not current.get("notify"): return
    offset = current.get("offset")
    if current["classification"] == "normal":
        message = f"旦那さま、Zen3 GNSS時刻源が通常状態へ戻り、主時刻源へ復帰しました。現在offset {offset:+.2f}秒です。"
    else:
        message = (f"旦那さま、Zen3 GNSS時刻の誤差が通常範囲を超えています。"
                   f"現在offset {offset:+.2f}秒、判定は{current['classification'].upper()}です。"
                   "Internet NTPは正常のため、raspi2の時刻同期自体は維持されています。")
    subprocess.run(["/usr/bin/python3", str(ROOT / "tools/discord_say.py"), message], cwd=ROOT, timeout=30, check=False)

if __name__ == "__main__":
    result = save(parse_snapshot(collect()))
    notify(result)
    if result["notify"]: print(json.dumps(result, ensure_ascii=False))
