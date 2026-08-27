#!/usr/bin/env python3

import os
import re
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
OUT = ROOT / "state" / "management_clues.txt"

PATTERN = re.compile(
    r"proxmox|pve|pveversion|qm\s|pct\s|"
    r"vmid|agent-101-vm|qemu|kvm|virt",
    re.IGNORECASE,
)


def section(title, text):
    return f"\n===== {title} =====\n{text.strip()}\n"


def read_file(path, max_bytes=2_000_000):
    try:
        if not path.exists():
            return ""
        if path.stat().st_size > max_bytes:
            return ""
        return path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except Exception:
        return ""


def interesting_lines(text, limit=100):
    rows = []
    for line in text.splitlines():
        if PATTERN.search(line):
            rows.append(line[:1000])
        if len(rows) >= limit:
            break
    return "\n".join(rows)


def shell_history():
    result = []

    for name in (
        ".bash_history",
        ".zsh_history",
    ):
        path = HOME / name
        text = read_file(path)

        for line in text.splitlines():
            # 管理・SSHに関係しそうな過去コマンドだけ
            if re.search(
                r"\b(ssh|scp|rsync|qm|pct|pve|proxmox)\b",
                line,
                re.IGNORECASE,
            ):
                result.append(line[:1200])

    return "\n".join(result[-200:])


def ssh_config():
    parts = []

    for name in (
        "config",
        "known_hosts",
    ):
        path = HOME / ".ssh" / name
        text = read_file(path)

        if text:
            parts.append(
                f"--- ~/.ssh/{name} ---\n{text}"
            )

    return "\n".join(parts)


def project_search():
    """
    巨大なbuild/.git/vendor等を掘らず、
    projects内の比較的小さいテキストだけ検索する。
    """
    base = HOME / "projects"
    result = []

    if not base.exists():
        return ""

    excluded = {
        ".git",
        "build",
        "node_modules",
        "vendor",
        "__pycache__",
    }

    checked = 0

    for path in base.rglob("*"):
        if not path.is_file():
            continue

        if any(part in excluded for part in path.parts):
            continue

        try:
            size = path.stat().st_size
        except OSError:
            continue

        # 大物やバイナリを避ける
        if size > 512 * 1024:
            continue

        checked += 1

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except Exception:
            continue

        matches = interesting_lines(text, limit=10)

        if matches:
            try:
                rel = path.relative_to(HOME)
            except ValueError:
                rel = path

            result.append(
                f"--- {rel} ---\n{matches}"
            )

        if len(result) >= 80:
            break

    return (
        f"scanned_files={checked}\n\n"
        + "\n\n".join(result)
    )


def command(cmd):
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
        )
        return p.stdout
    except Exception as e:
        return f"(failed: {e})"


def main():
    parts = []

    parts.append(section(
        "OBSERVED AT",
        datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
    ))

    parts.append(section(
        "HOST",
        command([
            "sh", "-c",
            "hostname; "
            "systemd-detect-virt 2>/dev/null || true; "
            "cat /sys/class/dmi/id/product_name "
            "2>/dev/null || true"
        ]),
    ))

    parts.append(section(
        "/etc/hosts",
        read_file(Path("/etc/hosts")),
    ))

    parts.append(section(
        "SSH CONFIG AND KNOWN HOSTS",
        ssh_config(),
    ))

    parts.append(section(
        "SHELL HISTORY CLUES",
        shell_history(),
    ))

    parts.append(section(
        "PROJECT CLUES",
        project_search(),
    ))

    parts.append(section(
        "ROUTING",
        command(["ip", "route"]),
    ))

    parts.append(section(
        "NEIGHBOUR CACHE",
        command(["ip", "neigh"]),
    ))

    text = "".join(parts)

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    OUT.write_text(
        text,
        encoding="utf-8",
    )

    print(text)


if __name__ == "__main__":
    main()
