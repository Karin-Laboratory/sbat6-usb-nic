#!/usr/bin/env python3
"""Read-only health guard for the justnottoday OpenWrt AP.

The SSH invocation intentionally has no remote command or user supplied
arguments.  OpenWrt's authorized_keys forced-command is therefore the only
observation path this guard can use.
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = "justnottoday"
SSH_ALIAS = "justnottoday"
STATE = ROOT / "state" / "justnottoday_guard.json"
HISTORY = ROOT / "state" / "justnottoday-health-history.json"
EVENTS = ROOT / "state" / "justnottoday-events.jsonl"
QUEUE = ROOT / "state" / "patrol_queue"
LOG = ROOT / "logs" / "justnottoday_guard.log"
INTERVAL = 300
CONFIRM_SCANS = 2
EXPECTED_PORTS = {"lan1", "lan2", "lan3", "lan4", "wan", "phy0-ap0", "phy0-ap1", "phy1-ap0"}

SSH = ["/usr/bin/ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", SSH_ALIAS]


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {} if default is None else default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _json_section(text, heading):
    match = re.search(r"===== " + re.escape(heading) + r" =====\n(.*?)(?=\n===== |\Z)", text, re.S)
    if not match:
        return None
    try:
        # SYSTEM is followed by the human-readable uptime/load line before
        # the next section; decode only the first JSON value.
        value, _ = json.JSONDecoder().raw_decode(match.group(1).lstrip())
        return value
    except json.JSONDecodeError:
        return None


def probe(ssh_runner=None):
    """Run only the authorized forced command and parse bounded output."""
    runner = ssh_runner or subprocess.run
    try:
        result = runner(SSH, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"reachable": False, "error": type(exc).__name__}
    raw = result.stdout or ""
    system = _json_section(raw, "SYSTEM") or {}
    lan = _json_section(raw, "LAN") or {}
    identity = re.search(r"===== IDENTITY =====\n.*?\n(.*? up .*load average: .*?)\n", raw, re.S)
    load_line = identity.group(1).strip() if identity else ""
    load = None
    load_match = re.search(r"load average: ([0-9.]+), ([0-9.]+), ([0-9.]+)", load_line)
    if load_match:
        load = {"1m": float(load_match.group(1)), "5m": float(load_match.group(2)), "15m": float(load_match.group(3))}
    uptime = None
    up_match = re.search(r"\n\s*([0-9.]+) up ", raw)
    if up_match:
        uptime = float(up_match.group(1)) * 60
    memory = {}
    mem_match = re.search(r"Mem:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", raw)
    if mem_match:
        memory = {"total_kb": int(mem_match.group(1)), "used_kb": int(mem_match.group(2)), "free_kb": int(mem_match.group(3)), "available_kb": int(mem_match.group(6))}
    overlay = {}
    fs_match = re.search(r"overlayfs:/overlay\s+(\S+)\s+(\S+)\s+(\S+)\s+(\d+)%", raw)
    if fs_match:
        overlay = {"size": fs_match.group(1), "used": fs_match.group(2), "available": fs_match.group(3), "used_percent": int(fs_match.group(4))}
    ports = set()
    port_start = raw.find("===== BRIDGE PORTS =====")
    if port_start >= 0:
        port_text = raw[port_start:].split("===== WIRELESS =====", 1)[0]
        ports = {line.strip() for line in port_text.splitlines()[1:] if line.strip()}
    wireless = []
    wireless_start = raw.find("===== WIRELESS =====")
    if wireless_start >= 0:
        wireless_text = raw[wireless_start:].split("===== SERVICES =====", 1)[0]
        for line in wireless_text.splitlines()[1:]:
            match = re.search(r"device=(\S+) band=(\S+) mode=(\S+) ssid=(\S+) encryption=(\S+)", line)
            if match:
                wireless.append({"device": match.group(1), "band": match.group(2), "mode": match.group(3), "ssid": match.group(4), "encryption": match.group(5), "disabled": "disabled=1" in line})
    services = {}
    service_match = re.search(r"dropbear=(\S+)\s+uhttpd=(\S+)", raw)
    if service_match:
        services = {"dropbear": service_match.group(1), "uhttpd": service_match.group(2)}
    return {"reachable": result.returncode == 0 or bool(system or lan), "identity": {"hostname": system.get("hostname"), "model": system.get("model"), "hardware": system.get("system"), "kernel": system.get("kernel"), "release": system.get("release")}, "uptime_seconds": uptime, "load": load, "memory": memory, "overlay": overlay, "lan": lan, "bridge_ports": sorted(ports), "wireless": wireless, "services": services, "stderr": (result.stderr or "")[-500:]}


def evaluate(snapshot):
    problems = []
    if not snapshot.get("reachable"): return ["SSH observation failed"]
    identity, lan = snapshot.get("identity", {}), snapshot.get("lan", {})
    release = identity.get("release") or {}
    if identity.get("model") != "ELECOM WRC-2533GHBK-I": problems.append("hardware/model mismatch")
    if release.get("version") != "25.12.5" or release.get("revision") != "r33051-f5dae5ece4": problems.append("OpenWrt version/revision changed")
    if not lan.get("up") or lan.get("device") != "br-lan": problems.append("br-lan down or unexpected device")
    addresses = {x.get("address") for x in lan.get("ipv4-address", [])}
    if not addresses: problems.append("management IPv4 missing")
    routes = lan.get("route", [])
    if not any(x.get("target") == "0.0.0.0" and x.get("nexthop") == "192.168.0.1" for x in routes): problems.append("default gateway missing")
    if "192.168.0.1" not in set(lan.get("dns-server", [])): problems.append("DNS missing")
    if lan.get("data", {}).get("dhcpserver") != "192.168.0.88": problems.append("DHCP server mismatch")
    if lan.get("data", {}).get("ntpserver") != "192.168.0.26": problems.append("NTP server mismatch")
    missing = EXPECTED_PORTS - set(snapshot.get("bridge_ports", []))
    if missing: problems.append("bridge ports missing: " + ",".join(sorted(missing)))
    aps = snapshot.get("wireless", [])
    for band, label in (("2g", "justnottoday 2.4GHz"), ("5g", "justnottoday 5GHz")):
        if not any(x.get("ssid") == "justnottoday" and x.get("band") == band and x.get("mode") == "ap" and x.get("encryption") == "sae-mixed" and not x.get("disabled") for x in aps): problems.append(label + " missing or invalid")
    if not any(x.get("ssid") == "infra2g" and x.get("band") == "2g" and x.get("mode") == "ap" and x.get("encryption") == "sae-mixed" and not x.get("disabled") for x in aps): problems.append("infra2g 2.4GHz missing or invalid")
    for service in ("dropbear", "uhttpd"):
        if snapshot.get("services", {}).get(service) != "running": problems.append(service + " not running")
    if snapshot.get("overlay", {}).get("used_percent", 0) >= 80: problems.append("overlay low-space")
    return problems


def _record_event(event):
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as handle: handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _notify(message):
    if not load_json(ROOT / "runtime" / "config.json", {}).get("discord_enabled", False):
        return
    try:
        subprocess.run(["/usr/bin/python3", str(ROOT / "tools/discord_say.py"), message], cwd=ROOT, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        logging.exception("Discord notification failed")


def run_once(ssh_runner=None, state_path=STATE):
    state = load_json(state_path, {})
    snapshot = probe(ssh_runner)
    problems = evaluate(snapshot)
    previous = state.get("last_problems", [])
    if problems:
        state["bad_count"] = state.get("bad_count", 0) + 1
        state["last_problems"] = problems
        if state["bad_count"] >= CONFIRM_SCANS and not state.get("notified"):
            event = {"event_type": "openwrt_health_alert", "target": TARGET, "severity": "HIGH", "created_at": now(), "problems": problems, "snapshot": snapshot, "automatic_remediation": False}
            _record_event(event); state["notified"] = True; state["notified_at"] = event["created_at"]
            QUEUE.mkdir(parents=True, exist_ok=True); save_json(QUEUE / ("openwrt-" + str(time.time_ns()) + ".json"), event)
            _notify("旦那さま、justnottodayの読み取り専用巡回で異常を2回連続検出しました。\n" + "\n".join("- " + p for p in problems) + "\n自動修復は行っていません。")
    else:
        if state.get("notified"):
            event = {"event_type": "openwrt_health_recovered", "target": TARGET, "severity": "INFO", "created_at": now(), "snapshot": snapshot}
            _record_event(event)
            _notify("旦那さま、justnottodayは読み取り専用巡回で正常状態へ復帰しました。")
        state.update({"bad_count": 0, "notified": False, "last_problems": [], "last_ok_at": now()})
    state.update({"updated_at": now(), "snapshot": snapshot})
    save_json(state_path, state)
    return snapshot, problems, state


def main():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=LOG, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if "--once" in sys.argv:
        snapshot, problems, state = run_once()
        print(json.dumps({"ok": not problems, "problems": problems, "bad_count": state.get("bad_count", 0), "target": TARGET}, ensure_ascii=False))
        return
    while True:
        run_once(); time.sleep(INTERVAL)


if __name__ == "__main__": main()
