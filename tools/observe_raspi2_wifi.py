#!/usr/bin/env python3

import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path("/home/masataka/projects/butlerx")
OUT = ROOT / "state" / "raspi2_wifi_capability.json"

SSH = [
    "/usr/bin/ssh",
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=5",
    "-o", "StrictHostKeyChecking=yes",
    "-i", str(Path.home() / ".ssh/id_ed25519_raspi2_codex"),
    "codex@192.168.0.26",
]

REMOTE = r'''
set -u

echo "=== HOST ==="
hostname

echo "=== LINKS ==="
ip -br link 2>/dev/null || true

echo "=== ADDRESSES ==="
ip -br addr 2>/dev/null || true

echo "=== IW DEV ==="
if command -v iw >/dev/null 2>&1; then
    iw dev 2>&1 || true
else
    echo "IW_NOT_FOUND"
fi

echo "=== RFKILL ==="
if command -v rfkill >/dev/null 2>&1; then
    rfkill list 2>&1 || true
else
    echo "RFKILL_NOT_FOUND"
fi

echo "=== WIFI TOOLS ==="
for x in iw nmcli wpa_cli iwlist; do
    printf "%s=" "$x"
    command -v "$x" 2>/dev/null || echo "NOT_FOUND"
done

echo "=== USB NETWORK DEVICES ==="
for d in /sys/class/net/*; do
    [ -e "$d/device" ] || continue
    dev="$(basename "$d")"
    path="$(readlink -f "$d/device" 2>/dev/null || true)"
    case "$path" in
        *usb*)
            echo "$dev $path"
            ;;
    esac
done
'''

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

p = subprocess.run(
    SSH + [REMOTE],
    text=True,
    capture_output=True,
    timeout=20,
)

result = {
    "observed_at": now(),
    "target": "raspi2",
    "address": "192.168.0.26",
    "ssh_user": "codex",
    "returncode": p.returncode,
    "stdout": p.stdout,
    "stderr": p.stderr,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps(result, ensure_ascii=False, indent=2))
