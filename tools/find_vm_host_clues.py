#!/usr/bin/env python3

import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
OUT = ROOT / "state" / "management_identity_clues.txt"

TERMS = [
    "agent-101-vm",
    "z2g3",
    "z4g4",
    "qm config",
    "qm resize",
    "VMID",
    "vm-308",
    "308.conf",
]


def run(cmd, timeout=90):
    try:
        p = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
        return p.stdout.strip()
    except Exception as e:
        return f"(failed: {e})"


def section(name, text):
    return f"\n===== {name} =====\n{text}\n"


def grep_tree(base):
    if not Path(base).exists():
        return "(not found)"

    pattern = "|".join(TERMS)

    return run([
        "grep",
        "-RInI",
        "-E",
        pattern,
        "--exclude-dir=.git",
        "--exclude-dir=build",
        "--exclude-dir=node_modules",
        "--exclude=*.img",
        "--exclude=*.iso",
        "--exclude=*.bin",
        "--exclude=*.tar",
        "--exclude=*.gz",
        str(base),
    ], timeout=120)


def main():
    parts = []

    parts.append(section(
        "OBSERVED AT",
        datetime.now().astimezone().isoformat(timespec="seconds"),
    ))

    parts.append(section(
        "DMI IDENTITY",
        run([
            "sh", "-c",
            """
for f in \
  product_name \
  product_uuid \
  product_serial \
  board_vendor \
  board_name \
  chassis_asset_tag
do
  printf '%s=' "$f"
  cat "/sys/class/dmi/id/$f" 2>/dev/null || true
done
"""
        ])
    ))

    parts.append(section(
        "CLOUD INIT IDENTITY",
        run([
            "sh", "-c",
            """
for f in \
 /var/lib/cloud/data/instance-id \
 /var/lib/cloud/instance/instance-id \
 /var/lib/cloud/instance/user-data.txt \
 /var/lib/cloud/instance/vendor-data.txt
do
  if [ -r "$f" ]; then
    echo "--- $f ---"
    sed -n '1,160p' "$f"
  fi
done
"""
        ])
    ))

    parts.append(section(
        "SSH DIRECTORY",
        run([
            "sh", "-c",
            "find ~/.ssh -maxdepth 1 -type f "
            "-printf '%f  %s bytes\\n' 2>/dev/null | sort"
        ])
    ))

    parts.append(section(
        "PROJECT REFERENCES",
        grep_tree(HOME / "projects")
    ))

    # Codex sessions are only searched for the strong host names.
    parts.append(section(
        "CODEX SESSION REFERENCES",
        run([
            "grep",
            "-RInI",
            "-E",
            "agent-101-vm|z2g3|z4g4|qm resize|qm config",
            str(HOME / ".codex" / "sessions"),
        ], timeout=120)
    ))

    parts.append(section(
        "SHELL HISTORY",
        run([
            "sh", "-c",
            """
grep -Ei \
'agent-101-vm|z2g3|z4g4|ssh .*root@|qm (list|config|resize)|pct ' \
~/.bash_history ~/.zsh_history 2>/dev/null | tail -n 200
"""
        ])
    ))

    text = "".join(parts)

    OUT.write_text(text, encoding="utf-8")

    print(text)


if __name__ == "__main__":
    main()
