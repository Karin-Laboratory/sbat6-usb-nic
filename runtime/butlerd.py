#!/usr/bin/env python3

import json
import logging
import os
import shutil
import signal
import socket
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "runtime" / "config.json"
STATE_DIR = ROOT / "state"
LOG_DIR = ROOT / "logs"
EXPERIENCE_DIR = ROOT / "memory" / "experience"

RUNNING = True


def now():
    return datetime.now().astimezone()


def now_iso():
    return now().isoformat(timespec="seconds")


def load_json(path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def atomic_write_json(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def append_experience(title, seen, judgment="", action="", result="", remember=""):
    """
    人間が読める経験日記へ、意味のある出来事だけを書く。
    """
    EXPERIENCE_DIR.mkdir(parents=True, exist_ok=True)

    t = now()
    diary = EXPERIENCE_DIR / f"{t:%Y-%m-%d}.md"

    if not diary.exists():
        diary.write_text(
            f"# {t:%Y-%m-%d} ButlerX 経験日記\n\n",
            encoding="utf-8",
        )

    lines = [
        f"## {t:%H:%M} {title}",
        "",
        f"- 見たこと: {seen}",
    ]

    if judgment:
        lines.append(f"- 判断: {judgment}")
    if action:
        lines.append(f"- 行動: {action}")
    if result:
        lines.append(f"- 結果: {result}")
    if remember:
        lines.append(f"- 覚えておくこと: {remember}")

    lines.append("")

    with diary.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def read_uptime():
    try:
        return float(Path("/proc/uptime").read_text().split()[0])
    except Exception:
        return None


def read_load():
    try:
        a, b, c = os.getloadavg()
        return {
            "1m": round(a, 2),
            "5m": round(b, 2),
            "15m": round(c, 2),
        }
    except Exception:
        return None


def inspect_self():
    usage = shutil.disk_usage(ROOT)

    return {
        "observed_at": now_iso(),
        "hostname": socket.gethostname(),
        "uptime_seconds": read_uptime(),
        "load": read_load(),
        "project_disk": {
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "used_percent": round(usage.used / usage.total * 100, 1),
        },
        "codex_enabled": load_json(CONFIG_PATH).get("codex_enabled", False),
        "discord_enabled": load_json(CONFIG_PATH).get("discord_enabled", False),
    }


def append_change(change):
    path = STATE_DIR / "changes.jsonl"
    record = {
        "detected_at": now_iso(),
        **change,
    }
    with path.open("a", encoding="utf-8") as f:
        import json
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def detect_self_changes(previous, current):
    """
    前回観測との差から、意味のある変化だけを返す。
    小さなload変動などは騒がない。
    """
    if not previous:
        return []

    changes = []

    prev_disk = previous.get("project_disk", {})
    cur_disk = current.get("project_disk", {})

    prev_pct = prev_disk.get("used_percent")
    cur_pct = cur_disk.get("used_percent")

    if prev_pct is not None and cur_pct is not None:
        delta = round(cur_pct - prev_pct, 1)

        if abs(delta) >= 2.0:
            changes.append({
                "kind": "disk_usage_change",
                "summary": f"ディスク使用率が {prev_pct}% → {cur_pct}% に変化",
                "before": prev_pct,
                "after": cur_pct,
                "delta": delta,
            })

        thresholds = (50, 70, 80, 90, 95)
        for threshold in thresholds:
            if prev_pct < threshold <= cur_pct:
                changes.append({
                    "kind": "disk_threshold_up",
                    "summary": f"ディスク使用率が {threshold}% を超えた",
                    "threshold": threshold,
                    "value": cur_pct,
                })
            elif prev_pct >= threshold > cur_pct:
                changes.append({
                    "kind": "disk_threshold_down",
                    "summary": f"ディスク使用率が {threshold}% 未満へ戻った",
                    "threshold": threshold,
                    "value": cur_pct,
                })

    for key in ("codex_enabled", "discord_enabled"):
        before = previous.get(key)
        after = current.get(key)
        if before != after:
            changes.append({
                "kind": "config_change",
                "summary": f"{key}: {before} → {after}",
                "key": key,
                "before": before,
                "after": after,
            })

    # uptimeが大きく巻き戻ったら再起動とみなす
    prev_up = previous.get("uptime_seconds")
    cur_up = current.get("uptime_seconds")
    if (
        prev_up is not None
        and cur_up is not None
        and cur_up + 120 < prev_up
    ):
        changes.append({
            "kind": "host_reboot",
            "summary": "ホストのuptimeが巻き戻った。再起動した可能性が高い。",
            "before": prev_up,
            "after": cur_up,
        })

    # loadはかなり高い時だけ記録
    load = current.get("load") or {}
    load1 = load.get("1m")
    if load1 is not None and load1 >= 2.0:
        prev_load = (previous.get("load") or {}).get("1m", 0)
        if prev_load < 2.0:
            changes.append({
                "kind": "high_load",
                "summary": f"1分loadが高くなった: {load1}",
                "value": load1,
            })

    return changes


def queue_patrol_thought(changes, snapshot):
    config = load_json(CONFIG_PATH)

    if not config.get("codex_enabled", False):
        return

    import subprocess
    import time as _time

    queue_dir = STATE_DIR / "patrol_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)

    event = {
        "queued_at": now_iso(),
        "hostname": socket.gethostname(),
        "changes": changes,
        "current_snapshot": snapshot,
    }

    event_path = queue_dir / f"{_time.time_ns()}.json"
    atomic_write_json(event_path, event)

    subprocess.Popen(
        [
            "/usr/bin/python3",
            str(ROOT / "runtime" / "patrol_thinker.py"),
        ],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def queue_idle_curiosity(snapshot):
    config = load_json(CONFIG_PATH)

    if not config.get("codex_enabled", False):
        return False
    if not config.get("curiosity_enabled", False):
        return False

    import subprocess
    import time as _time

    queue_dir = STATE_DIR / "patrol_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)

    # 先に別の気づきが待っているなら、そちらを優先する。
    if any(queue_dir.glob("*.json")):
        return False

    event = {
        "event_type": "idle_curiosity",
        "queued_at": now_iso(),
        "hostname": socket.gethostname(),
        "reason": "一定時間、意味のある変化がなかったので自由探索を開始した。",
        "current_snapshot": snapshot,
    }

    event_path = queue_dir / f"{_time.time_ns()}.json"
    atomic_write_json(event_path, event)

    atomic_write_json(
        STATE_DIR / "curiosity.json",
        {
            "last_queued_at": now_iso(),
            "event_file": event_path.name,
        },
    )

    subprocess.Popen(
        [
            "/usr/bin/python3",
            str(ROOT / "runtime" / "patrol_thinker.py"),
        ],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    return True


def write_runtime_state(started_at, patrol_count):
    atomic_write_json(
        STATE_DIR / "runtime.json",
        {
            "status": "patrolling",
            "started_at": started_at,
            "last_patrol_at": now_iso(),
            "patrol_count": patrol_count,
            "pid": os.getpid(),
        },
    )


def handle_signal(signum, frame):
    global RUNNING
    logging.info("signal received: %s", signum)
    RUNNING = False


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    EXPERIENCE_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "butlerd.log"),
            logging.StreamHandler(),
        ],
    )

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    config = load_json(CONFIG_PATH)
    patrol_interval = int(config.get("patrol_interval_seconds", 60))
    inspect_interval = int(config.get("self_inspection_interval_seconds", 300))
    curiosity_interval = int(config.get("curiosity_interval_seconds", 900))

    started_at = now_iso()
    patrol_count = 0
    last_inspection = 0.0
    # 起動直後から探索を始める。
    # thinkerが処理中ならqueue側で重複を防止する。
    last_curiosity_activity = 0.0

    logging.info("ButlerX alpha started")
    logging.info("project root: %s", ROOT)
    logging.info("Codex: %s", "enabled" if config.get("codex_enabled", False) else "disabled")
    logging.info("Discord: %s", "enabled" if config.get("discord_enabled", False) else "disabled")

    append_experience(
        title="起動",
        seen=f"{socket.gethostname()} 上で起動した。",
        judgment="まだCodexもDiscordも使わない、最小構成での巡回段階。",
        action="自分の状態を確認しながら巡回を開始した。",
        remember="仕事がなくても終了せず、巡回へ戻る。",
    )

    disk_warning_written = False

    # 再起動前の観測結果も比較対象にする
    last_snapshot = load_json(STATE_DIR / "self.json")

    while RUNNING:
        patrol_count += 1
        write_runtime_state(started_at, patrol_count)

        current = time.monotonic()

        if current - last_inspection >= inspect_interval:
            snapshot = inspect_self()

            changes = detect_self_changes(last_snapshot, snapshot)

            for change in changes:
                append_change(change)
                logging.info(
                    "change detected: %s",
                    change.get("summary"),
                )

            if changes:
                queue_patrol_thought(changes, snapshot)
                # 変化について既に考えるので、自由探索時計はリセットする。
                last_curiosity_activity = current

            atomic_write_json(STATE_DIR / "self.json", snapshot)
            last_snapshot = snapshot

            disk_percent = snapshot["project_disk"]["used_percent"]

            logging.info(
                "self inspection: disk=%s%% load=%s",
                disk_percent,
                snapshot["load"],
            )

            if disk_percent >= 90 and not disk_warning_written:
                append_experience(
                    title="自分の部屋を見回した",
                    seen=f"ディスク使用率が {disk_percent}% だった。",
                    judgment="90%を超えており、平常として無視するには少々高い。",
                    action="まだ変更は行わず、気になる事項として記録した。",
                    result="現在の巡回には支障はない。",
                    remember="後でディスクを何が使っているか調べる価値がある。",
                )
                disk_warning_written = True

            last_inspection = current

        if (
            config.get("curiosity_enabled", False)
            and current - last_curiosity_activity >= curiosity_interval
        ):
            snapshot = load_json(STATE_DIR / "self.json")
            if queue_idle_curiosity(snapshot):
                logging.info("idle curiosity queued")
                last_curiosity_activity = current

        # 将来ここに追加する:
        # - inbox確認
        # - timer/event確認
        # - lightweight observation
        # - AIを起こす価値があるかの判定
        # - Codex invocation
        # - worker管理
        # - outbox配送
        # - memory consolidation
        # - AI budget管理

        time.sleep(patrol_interval)

    atomic_write_json(
        STATE_DIR / "runtime.json",
        {
            "status": "stopped",
            "started_at": started_at,
            "stopped_at": now_iso(),
            "patrol_count": patrol_count,
            "pid": os.getpid(),
        },
    )

    append_experience(
        title="停止",
        seen=f"{patrol_count}回巡回したところで停止シグナルを受けた。",
        judgment="異常終了ではなく、外部からの停止指示。",
        action="現在状態を保存して終了した。",
        result="巡回状態を帳面へ残した。",
    )

    logging.info("ButlerX alpha stopped")


if __name__ == "__main__":
    main()
