#!/usr/bin/env python3

import os
import shutil
import socket
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPERIENCE = ROOT / "memory" / "experience"


def run(cmd):
    try:
        p = subprocess.run(
            cmd,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return p.stdout.strip()
    except Exception:
        return ""


def diary(title, seen, judgment="", remember=""):
    t = datetime.now().astimezone()
    path = EXPERIENCE / f"{t:%Y-%m-%d}.md"

    if not path.exists():
        path.write_text(
            f"# {t:%Y-%m-%d} ButlerX 経験日記\n\n",
            encoding="utf-8",
        )

    with path.open("a", encoding="utf-8") as f:
        f.write(f"## {t:%H:%M} {title}\n\n")
        f.write(f"- 見たこと: {seen}\n")
        if judgment:
            f.write(f"- 判断: {judgment}\n")
        if remember:
            f.write(f"- 覚えておくこと: {remember}\n")
        f.write("\n")


def main():
    EXPERIENCE.mkdir(parents=True, exist_ok=True)

    diary(
        "自分の部屋の探索を始めた",
        "agent VMについて、変更を加えず読み取りだけで調べることにした。",
        "まだ他の機械へは入らず、まず自分の部屋を知る。",
    )

    # OS
    os_name = run(". /etc/os-release 2>/dev/null; echo \"$PRETTY_NAME\"")
    kernel = run("uname -r")
    diary(
        "自分の足元を確認した",
        f"OSは {os_name or '不明'}、kernelは {kernel or '不明'}。",
        remember="自分が動いている基盤として覚えておく。",
    )

    # Disk
    usage = shutil.disk_usage(ROOT)
    pct = usage.used / usage.total * 100
    diary(
        "ディスクを確認した",
        f"プロジェクトのあるファイルシステムは {pct:.1f}% 使用されている。",
        "かなり高い。原因を調査する候補にしておく。" if pct >= 90 else "今すぐ問題になる水準ではない。",
        "90%を超えた状態が続くなら、何が容量を使っているか調べたい。" if pct >= 90 else "",
    )

    # Projects
    projects = []
    parent = ROOT.parent
    try:
        projects = sorted(
            p.name for p in parent.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        )
    except Exception:
        pass

    diary(
        "隣の作業場所を眺めた",
        "projectsには "
        + (", ".join(projects[:20]) if projects else "確認できるディレクトリがなかった")
        + "。",
        "名前だけを確認した。中身は必要になったら調べる。",
    )

    # Available tools
    wanted = [
        "codex", "ssh", "git", "python3", "curl",
        "jq", "docker", "podman", "systemctl", "nmap"
    ]
    found = [x for x in wanted if shutil.which(x)]

    diary(
        "道具箱を確認した",
        "使えそうな道具として " + ", ".join(found) + " を見つけた。",
        "何ができるかを判断する材料になる。",
        "特にCodexとSSHは今後重要になりそう。",
    )

    # SSH config
    ssh_dir = Path.home() / ".ssh"
    config = ssh_dir / "config"
    known_hosts = ssh_dir / "known_hosts"

    config_hosts = []
    if config.exists():
        for line in config.read_text(errors="ignore").splitlines():
            s = line.strip()
            if s.lower().startswith("host "):
                config_hosts.extend(s.split()[1:])

    kh_lines = 0
    if known_hosts.exists():
        try:
            kh_lines = len(known_hosts.read_text(errors="ignore").splitlines())
        except Exception:
            pass

    diary(
        "鍵束を眺めた",
        (
            f"SSH configには {', '.join(config_hosts[:20])} が記載されている。"
            if config_hosts
            else "SSH configから明示的なHost名は見つからなかった。"
        )
        + f" known_hostsには約{kh_lines}件の記録がある。",
        "既にこの部屋から訪れたことのある機械がありそう。",
        "まだ接続は試さない。次の探索候補として覚えておく。",
    )

    # Running services
    services = run(
        "systemctl --no-pager --no-legend --state=running "
        "--type=service 2>/dev/null | awk '{print $1}' | head -30"
    )
    svc = [x for x in services.splitlines() if x]

    diary(
        "部屋で動いているものを確認した",
        "稼働中serviceとして "
        + (", ".join(svc[:15]) if svc else "特に取得できなかった")
        + "。",
        "用途不明のものは後で必要に応じて調べる。",
    )

    # Listening sockets
    sockets = run(
        "ss -lnt 2>/dev/null | awk 'NR>1 {print $4}' | sort -u | head -20"
    )
    ports = [x for x in sockets.splitlines() if x]

    diary(
        "部屋の扉を確認した",
        "TCP待受として "
        + (", ".join(ports) if ports else "確認できるものはなかった")
        + "。",
        "localhostサービスや管理用サービスが存在する可能性がある。",
    )

    diary(
        "最初の部屋探索を終えた",
        "自分の環境、道具、鍵の手掛かり、稼働サービスを一通り確認した。",
        "変更は行っていない。",
        "次は得た情報から、どこを調べる価値があるか考えたい。",
    )


if __name__ == "__main__":
    main()
