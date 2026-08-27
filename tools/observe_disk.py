#!/usr/bin/env python3

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
EXPERIENCE = ROOT / "memory" / "experience"


def now():
    return datetime.now().astimezone()


def human(n):
    n = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PiB"


def run(cmd, timeout=120):
    try:
        p = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
        return p.stdout.strip()
    except Exception:
        return ""


def can_sudo():
    try:
        p = subprocess.run(
            ["sudo", "-n", "true"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        return p.returncode == 0
    except Exception:
        return False


def du_level1(path, sudo=False):
    cmd = ["du", "-x", "-B1", "-d1", str(path)]
    if sudo:
        cmd = ["sudo", "-n"] + cmd

    out = run(cmd)

    rows = []
    for line in out.splitlines():
        try:
            size, name = line.split("\t", 1)
            rows.append((int(size), name))
        except ValueError:
            pass

    return sorted(rows, reverse=True)


def append_diary(title, seen, judgment, action, result, remember):
    t = now()
    diary = EXPERIENCE / f"{t:%Y-%m-%d}.md"

    if not diary.exists():
        diary.write_text(
            f"# {t:%Y-%m-%d} ButlerX 経験日記\n\n",
            encoding="utf-8",
        )

    with diary.open("a", encoding="utf-8") as f:
        f.write(f"## {t:%H:%M} {title}\n\n")
        f.write(f"- 見たこと: {seen}\n")
        f.write(f"- 判断: {judgment}\n")
        f.write(f"- 行動: {action}\n")
        f.write(f"- 結果: {result}\n")
        f.write(f"- 覚えておくこと: {remember}\n\n")


def main():
    sudo = can_sudo()
    usage = shutil.disk_usage(ROOT)

    # まず同一ファイルシステムの最上位を確認
    root_usage = du_level1("/", sudo=sudo)

    # home と projects も少し詳しく見る
    home_usage = du_level1(Path.home(), sudo=False)
    project_usage = du_level1(Path.home() / "projects", sudo=False)

    # systemd journal
    journal = run(["journalctl", "--disk-usage"])

    # 大きなファイル
    bigfiles_raw = run([
        "find", str(Path.home()),
        "-xdev",
        "-type", "f",
        "-size", "+500M",
        "-printf", "%s\t%p\n",
    ])

    bigfiles = []
    for line in bigfiles_raw.splitlines():
        try:
            size, name = line.split("\t", 1)
            bigfiles.append((int(size), name))
        except ValueError:
            pass
    bigfiles.sort(reverse=True)

    data = {
        "observed_at": now().isoformat(timespec="seconds"),
        "filesystem": {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "used_percent": round(usage.used / usage.total * 100, 1),
        },
        "root_top": [
            {"bytes": n, "path": p}
            for n, p in root_usage[:12]
        ],
        "home_top": [
            {"bytes": n, "path": p}
            for n, p in home_usage[:12]
        ],
        "projects_top": [
            {"bytes": n, "path": p}
            for n, p in project_usage[:12]
        ],
        "large_home_files": [
            {"bytes": n, "path": p}
            for n, p in bigfiles[:10]
        ],
        "journal": journal,
        "used_sudo_readonly": sudo,
    }

    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / "disk_observation.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    root_children = [
        (n, p) for n, p in root_usage
        if p != "/"
    ][:4]

    root_text = ", ".join(
        f"{p} {human(n)}" for n, p in root_children
    ) or "十分な内訳を取得できなかった"

    biggest_file = (
        f"{bigfiles[0][1]} ({human(bigfiles[0][0])})"
        if bigfiles else
        "500MiBを超えるファイルは自分のhome内では見つからなかった"
    )

    append_diary(
        title="気になっていたディスクを調べた",
        seen=(
            f"使用率は {data['filesystem']['used_percent']}%。"
            f" 同一ファイルシステムの主な使用先は {root_text}。"
        ),
        judgment=(
            "最初の思考で自分が調べたいと選んだため、"
            "変更を加えず容量の内訳だけ確認した。"
        ),
        action=(
            "du、find、journalctlを使って読み取り調査を行った。"
            " 削除や設定変更はしていない。"
        ),
        result=f"大きなファイルについては、{biggest_file}。",
        remember=(
            "この観測結果を使って、次に対処が必要か、"
            "それとも別の探索へ移るかを判断する。"
        ),
    )

    print("===== DISK OBSERVATION =====")
    print(f"Filesystem used: {data['filesystem']['used_percent']}%")
    print()
    print("Largest top-level directories:")
    for n, p in root_children[:8]:
        print(f"  {human(n):>10}  {p}")

    print()
    print("Largest projects:")
    for n, p in project_usage:
        if p != str(Path.home() / "projects"):
            print(f"  {human(n):>10}  {p}")

    print()
    print("Large files in home:")
    if bigfiles:
        for n, p in bigfiles[:10]:
            print(f"  {human(n):>10}  {p}")
    else:
        print("  none over 500 MiB")

    print()
    print("Journal:")
    print(" ", journal or "unknown")


if __name__ == "__main__":
    main()
