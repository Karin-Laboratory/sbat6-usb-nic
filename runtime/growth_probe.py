#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path("/home/masataka/projects/butlerx")
CAPS = ROOT / "state/capabilities.json"
OUTDIR = ROOT / "state/growth_observations"

REMOTE_PY = r'''
import json
import os
import platform
import shutil
import socket
import subprocess
import time

def run(argv, timeout=8, limit=20000):
    try:
        p = subprocess.run(
            argv,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "rc": p.returncode,
            "stdout": p.stdout[:limit],
            "stderr": p.stderr[:4000],
        }
    except Exception as e:
        return {
            "rc": None,
            "stdout": "",
            "stderr": type(e).__name__ + ": " + str(e),
        }

def read_file(path, limit=12000):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except Exception as e:
        return type(e).__name__ + ": " + str(e)

disk = shutil.disk_usage("/")

out = {
    "probe_schema": 1,
    "hostname": socket.gethostname(),
    "platform": platform.platform(),
    "uname": run(["uname", "-a"]),
    "os_release": read_file("/etc/os-release"),
    "uptime_seconds": None,
    "root_disk": {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "used_percent": round(disk.used / disk.total * 100, 1),
    },
    "memory": read_file("/proc/meminfo", 8000),
    "systemd_failed": run([
        "systemctl", "--failed",
        "--no-legend", "--no-pager"
    ]),
    "running_services": run([
        "systemctl", "list-units",
        "--type=service",
        "--state=running",
        "--no-legend",
        "--no-pager"
    ], limit=30000),
    "listeners_tcp": run([
        "ss", "-lntH"
    ], limit=16000),
    "sudo_noninteractive": run([
        "sudo", "-n", "true"
    ]),
}

try:
    out["uptime_seconds"] = float(
        open("/proc/uptime").read().split()[0]
    )
except Exception:
    pass

print(json.dumps(out, ensure_ascii=False))
'''

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)

def capability_fingerprint(target, info):
    payload = {"target": target, "capability": info}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--event-id")
    args = ap.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.target):
        raise SystemExit("invalid target name")
    if args.event_id and not re.fullmatch(r"[A-Za-z0-9._-]+", args.event_id):
        raise SystemExit("invalid event id")

    caps = load(CAPS)
    info = caps.get("targets", {}).get(args.target)

    if not info:
        raise SystemExit("target is not registered")

    access = info.get("access", {})
    capability = access.get("capability", "")
    identity = access.get("identity", "")

    if "ssh" not in capability:
        raise SystemExit("target has no registered ssh capability")

    if not re.fullmatch(
        r"[A-Za-z0-9._-]+@[A-Za-z0-9._-]+",
        identity,
    ):
        raise SystemExit("unsafe or unsupported ssh identity")

    # 重要:
    # eventやAIからremote commandを受け取らない。
    # 実行内容はこのファイル内のREMOTE_PYだけ。
    result = {
        "observed_at": now(),
        "target": args.target,
        "role": info.get("role"),
        "trust": info.get("trust"),
        "access": access,
        "probe_kind": "fixed-read-only-linux-v1",
        "event_id": args.event_id,
        "capability_fingerprint": capability_fingerprint(args.target, info),
        "ok": False,
    }

    try:
        p = subprocess.run(
            [
                "/usr/bin/ssh",
                "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=8",
                identity,
                "python3", "-"
            ],
            input=REMOTE_PY,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=45,
        )
    except subprocess.TimeoutExpired:
        result["failure"] = {
            "code": "ssh_timeout",
            "scope": "observation_transport",
            "detail": "fixed probe timed out; target health is unknown",
        }
        OUTDIR.mkdir(parents=True, exist_ok=True)
        atomic(OUTDIR / f"{args.target}.json", result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    if p.returncode != 0:
        result["failure"] = {
            "code": "ssh_unavailable",
            "scope": "observation_transport",
            "detail": (p.stderr.strip() or f"ssh rc={p.returncode}")[:2000],
        }
    else:
        try:
            result["observation"] = json.loads(p.stdout)
            result["ok"] = True
        except Exception as e:
            result["failure"] = {
                "code": "malformed_probe_output",
                "scope": "probe_protocol",
                "detail": f"invalid fixed-probe output: {type(e).__name__}",
            }

    OUTDIR.mkdir(parents=True, exist_ok=True)
    atomic(
        OUTDIR / f"{args.target}.json",
        result,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result["ok"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
