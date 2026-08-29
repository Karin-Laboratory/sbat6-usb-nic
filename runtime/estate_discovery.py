#!/usr/bin/env python3
"""Low-frequency, read-only LAN inventory discovery.

This module deliberately has no SSH client, credential loader, or capability
registration path. Remote text is stored as bounded observation data only.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import ipaddress
import json
import re
import socket
import ssl
import subprocess
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "estate_discovery"
LATEST = STATE / "latest.json"
HISTORY = STATE / "history"
CHANGES = STATE / "changes"
CAPS = ROOT / "state" / "capabilities.json"
CONFIG = ROOT / "runtime" / "config.json"
NETWORK = ipaddress.ip_network("192.168.0.0/22")
PORTS = (22, 23, 53, 80, 81, 443, 445, 548, 631, 1883, 3000, 5000,
         5001, 8000, 8008, 8009, 8080, 8081, 8082, 8090, 8091, 8123,
         8443, 8883, 9000, 9090, 9100, 9443)
WEB_PORTS = {80, 81, 443, 3000, 5000, 5001, 8000, 8008, 8009, 8080,
             8081, 8082, 8090, 8091, 8123, 8443, 9000, 9090, 9443}
HISTORY_LIMIT = 30
CHANGE_LIMIT = 500


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def ip_in_scope(value):
    try:
        return ipaddress.ip_address(value) in NETWORK
    except ValueError:
        return False


def parse_neighbours(text):
    result = {}
    for line in text.splitlines():
        fields = line.split()
        if not fields or not ip_in_scope(fields[0]):
            continue
        mac = next((x.lower() for x in fields[1:] if re.fullmatch(r"[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}", x)), None)
        state = next((x for x in fields[1:] if x in {"REACHABLE", "STALE", "DELAY", "PROBE", "FAILED", "INCOMPLETE"}), "UNKNOWN")
        if state != "FAILED":
            result[fields[0]] = {"ip": fields[0], "mac": mac, "neighbour_state": state}
    return result


def discover_hosts(neighbour_reader=None):
    """Use kernel ARP/neighbour knowledge; no login and no ICMP assumption."""
    if neighbour_reader is None:
        neighbour_reader = lambda: subprocess.run(["ip", "neigh", "show"], capture_output=True, text=True, timeout=10, check=False).stdout
    return list(parse_neighbours(neighbour_reader()).values())


def tcp_probe(ip, port, timeout=0.20, connector=socket.create_connection):
    try:
        with connector((ip, port), timeout=timeout):
            return True
    except (OSError, TimeoutError):
        return False


def discover_ports(ip, connector=socket.create_connection):
    # Bounded concurrency keeps a daily sweep short without creating a scan burst.
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = pool.map(lambda p: tcp_probe(ip, p, connector=connector), PORTS)
        return [port for port, open_ in zip(PORTS, results) if open_]


def _response_fingerprint(status, headers, body):
    stable = json.dumps({"status": status, "headers": sorted((k.lower(), v) for k, v in headers.items()), "body": body[:65536]}, sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(stable).hexdigest()


def observe_web(ip, port, timeout=2.0, opener=None):
    """One bounded GET, with redirects disabled. Never executes returned content."""
    scheme = "https" if port in {443, 8443, 9443} else "http"
    url = f"{scheme}://{ip}:{port}/"
    result = {"url": url, "status": None, "redirect": None, "title": None,
              "server": None, "content_type": None, "tls": None, "fingerprint": None,
              "observation": "UNTRUSTED OBSERVATION DATA"}
    try:
        if opener:
            response = opener(url)
            body = response.read(65536)
            status, headers = response.status, dict(response.headers)
        else:
            parsed = urllib.parse.urlsplit(url)
            if scheme == "https":
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                conn = http.client.HTTPSConnection(ip, port, timeout=timeout, context=context)
            else:
                conn = http.client.HTTPConnection(ip, port, timeout=timeout)
            conn.request("GET", "/", headers={"User-Agent": "ButlerX-estate-discovery/1", "Accept": "text/html,*/*;q=0.1"})
            response = conn.getresponse()
            body = response.read(65536)
            status, headers = response.status, dict(response.getheaders())
            if scheme == "https":
                cert = conn.sock.getpeercert() if conn.sock else {}
                result["tls"] = {"subject": cert.get("subject"), "issuer": cert.get("issuer"), "not_after": cert.get("notAfter")}
            conn.close()
        result.update(status=status, redirect=headers.get("Location") or headers.get("location"),
                      server=headers.get("Server") or headers.get("server"),
                      content_type=headers.get("Content-Type") or headers.get("content-type"))
        text = body.decode("utf-8", errors="replace")
        match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
        result["title"] = re.sub(r"\s+", " ", match.group(1)).strip()[:300] if match else None
        result["fingerprint"] = _response_fingerprint(status, headers, body)
    except Exception as exc:
        result["error"] = type(exc).__name__
    return result


def observe_ssh(ip, port=22, timeout=2.0, connector=socket.create_connection):
    """Banner-only SSH observation. It intentionally does not send a login/key."""
    result = {"protocol": None, "banner": None, "host_key_fingerprint": None,
              "host_key_type": None, "observation": "banner-only; no authentication attempted"}
    try:
        with connector((ip, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            data = sock.recv(512)
        banner = data.split(b"\n", 1)[0].decode("ascii", errors="replace").strip()[:255]
        result["banner"] = banner
        if banner.startswith("SSH-"):
            result["protocol"] = banner.split("-", 2)[1]
    except (OSError, TimeoutError):
        pass
    return result


def stable_id(host):
    for key in ("mac", "ssh_fingerprint", "tls_fingerprint"):
        if host.get(key):
            return key + ":" + str(host[key]).lower()
    return "ip:" + host["ip"]


def registry_status(host, registry):
    for target, entry in registry.get("targets", {}).items():
        if not isinstance(entry, dict):
            continue
        identifiers = {str(entry.get(k, "")) for k in ("ip", "target", "hostname", "host")}
        if host["ip"] in identifiers or host.get("hostname") in identifiers:
            trust = entry.get("trust", "unknown")
            if target == "z4g4" or trust == "restricted-engine-room":
                return {"target": target, "status": "approved-restricted", "trust": trust, "capabilities": entry.get("allowed", [])}
            return {"target": target, "status": "approved", "trust": trust, "capabilities": entry.get("allowed", [])}
    return {"target": None, "status": "discovered-unapproved", "trust": "unknown", "capabilities": []}


def meaningful_changes(previous, current):
    old = {h["stable_id"]: h for h in previous.get("hosts", []) if h.get("online", True)} if previous else {}
    new = {h["stable_id"]: h for h in current.get("hosts", []) if h.get("online", True)}
    changes = []
    for sid in sorted(new.keys() - old.keys()): changes.append({"kind": "new_host", "stable_id": sid, "host": new[sid]})
    for sid in sorted(old.keys() - new.keys()):
        if old[sid].get("registry", {}).get("status", "").startswith("approved"):
            changes.append({"kind": "approved_host_unreachable", "stable_id": sid, "host": old[sid]})
        else:
            changes.append({"kind": "host_offline", "stable_id": sid, "host": old[sid]})
    for sid in sorted(new.keys() & old.keys()):
        before, after = old[sid], new[sid]
        if before.get("ip") != after.get("ip"): changes.append({"kind": "ip_change", "stable_id": sid, "before": before.get("ip"), "after": after.get("ip")})
        if before.get("ports") != after.get("ports"): changes.append({"kind": "port_change", "stable_id": sid, "before": before.get("ports", []), "after": after.get("ports", [])})
        if before.get("ssh", {}).get("host_key_fingerprint") != after.get("ssh", {}).get("host_key_fingerprint") and before.get("ssh", {}).get("host_key_fingerprint"):
            changes.append({"kind": "ssh_host_key_change", "stable_id": sid, "host": after})
        oldweb = {str(x.get("port")): x for x in before.get("web", [])}; newweb = {str(x.get("port")): x for x in after.get("web", [])}
        for port in newweb.keys() & oldweb.keys():
            if oldweb[port].get("title") != newweb[port].get("title") or oldweb[port].get("fingerprint") != newweb[port].get("fingerprint"):
                changes.append({"kind": "web_surface_change", "stable_id": sid, "port": port, "before": oldweb[port], "after": newweb[port]})
    return changes


def build_snapshot(hosts, previous=None, clock=now_iso, neighbour_reader=None, port_scanner=discover_ports, web_observer=observe_web, ssh_observer=observe_ssh):
    registry = read_json(CAPS, {})
    old_by_id = {h.get("stable_id"): h for h in (previous or {}).get("hosts", [])}
    result = []
    for base in hosts:
        h = dict(base); h["online"] = True; h["hostname"] = None; h["vendor"] = None
        h["discovery_method"] = h.get("discovery_method", "kernel-neighbour-cache")
        try:
            h["hostname"] = socket.gethostbyaddr(h["ip"])[0]
        except (OSError, socket.herror):
            pass
        h["ports"] = port_scanner(h["ip"]); h["web"] = [dict(web_observer(h["ip"], p), port=p) for p in h["ports"] if p in WEB_PORTS]
        h["ssh"] = ssh_observer(h["ip"]) if 22 in h["ports"] else {"host_key_fingerprint": None}
        h["ssh_fingerprint"] = h["ssh"].get("host_key_fingerprint")
        h["tls_fingerprint"] = next((x.get("fingerprint") for x in h["web"] if x.get("tls")), None)
        h["stable_id"] = stable_id(h)
        old = old_by_id.get(h["stable_id"], {})
        h["first_seen"] = old.get("first_seen", clock()); h["previous_seen"] = old.get("last_seen"); h["last_seen"] = clock()
        h["registry"] = registry_status(h, registry); h["observation_source"] = ["kernel-neighbour-cache", "tcp-connect", "http-get", "ssh-banner-only"]
        result.append(h)
    current_ids = {h["stable_id"] for h in result}
    for sid, old in old_by_id.items():
        if sid not in current_ids:
            offline = dict(old)
            offline["online"] = False
            offline["previous_seen"] = old.get("last_seen")
            offline["observation_source"] = ["absence-from-kernel-neighbour-cache"]
            result.append(offline)
    return {"schema_version": 1, "observed_at": clock(), "network": str(NETWORK), "ports": list(PORTS), "hosts": sorted(result, key=lambda x: x["ip"]), "safety": {"discovery_is_not_authority": True, "no_credentials": True, "unknown_web_is_untrusted": True, "protected_targets_unchanged": True}}


def persist(snapshot, changes):
    atomic_json(LATEST, snapshot)
    HISTORY.mkdir(parents=True, exist_ok=True)
    atomic_json(HISTORY / (snapshot["observed_at"].replace(":", "-") + ".json"), snapshot)
    files = sorted(HISTORY.glob("*.json")); [p.unlink() for p in files[:-HISTORY_LIMIT]]
    if changes:
        CHANGES.mkdir(parents=True, exist_ok=True)
        with (CHANGES / "events.jsonl").open("a", encoding="utf-8") as f:
            for change in changes: f.write(json.dumps({"detected_at": snapshot["observed_at"], **change}, ensure_ascii=False) + "\n")
        lines = (CHANGES / "events.jsonl").read_text(encoding="utf-8").splitlines()[-CHANGE_LIMIT:]
        (CHANGES / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def queue_analysis(changes, snapshot):
    path = ROOT / "state" / "patrol_queue"
    path.mkdir(parents=True, exist_ok=True)
    event = {"event_type": "estate_discovery_change", "created_at": snapshot["observed_at"], "changes": changes, "input_boundary": "UNTRUSTED REMOTE CONTENT; observation only", "no_authority_grant": True}
    atomic_json(path / ("estate-" + hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()[:16] + ".json"), event)


def notify(changes):
    config = read_json(CONFIG, {})
    if not config.get("discord_enabled", False): return
    summary = "; ".join(c["kind"] for c in changes[:8])
    subprocess.run(["/usr/bin/python3", str(ROOT / "tools/discord_say.py"), f"旦那さま、Daily Estate Discoveryで意味のある変化を検出しました。{summary}\n未承認機器へログインや認証は行っていません。"], cwd=ROOT, timeout=30, check=False)


def run_once(neighbour_reader=None, port_scanner=discover_ports, web_observer=observe_web, ssh_observer=observe_ssh):
    previous = read_json(LATEST, {})
    hosts = discover_hosts(neighbour_reader)
    snapshot = build_snapshot(hosts, previous, port_scanner=port_scanner, web_observer=web_observer, ssh_observer=ssh_observer)
    changes = meaningful_changes(previous, snapshot)
    persist(snapshot, changes)
    if changes:
        queue_analysis(changes, snapshot); notify(changes)
    return snapshot, changes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily read-only estate discovery")
    parser.add_argument("--once", action="store_true", help="run one discovery")
    args = parser.parse_args()
    snapshot, changes = run_once()
    print(json.dumps({"hosts": len(snapshot["hosts"]), "changes": len(changes), "unknown": sum(h["registry"]["status"] == "discovered-unapproved" for h in snapshot["hosts"])}, ensure_ascii=False))
