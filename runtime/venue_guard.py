#!/usr/bin/env python3

import base64
import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path("/home/masataka/projects/butlerx")

STATE = ROOT / "state/venue_guard.json"
EVENTS = ROOT / "state/venue-events.jsonl"
LOG = ROOT / "logs/venue_guard.log"
QUEUE = ROOT / "state/patrol_queue"

INTERVAL = 300
CONFIRM_SCANS = 2
MAX_NEWS_CACHE_AGE = 1800

SSH = [
    "/usr/bin/ssh",
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=8",
    "venue",
]

REMOTE_PROBE = r'''
import datetime
import http.client
import json
import os
import re
import subprocess

CACHE = "/var/lib/venue-latest-tbs-news/latest.json"

def service(name):
    p = subprocess.run(
        ["systemctl", "is-active", name],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    return p.stdout.strip()

def http_get(port, path):
    try:
        c = http.client.HTTPConnection(
            "127.0.0.1", port, timeout=5
        )
        c.request("GET", path)
        r = c.getresponse()
        result = {
            "status": r.status,
            "location": r.getheader("Location"),
        }
        r.read(1024)
        c.close()
        return result
    except Exception as e:
        return {
            "status": 0,
            "error": type(e).__name__ + ": " + str(e),
        }

out = {
    "services": {
        name: service(name)
        for name in (
            "venue-kiosk.service",
            "venue-latest-tbs-news.service",
            "venue-bgm-manager.service",
            "venue-volume-api.service",
            "nginx.service",
        )
    },
    "home": http_get(8080, "/"),
    "weather": http_get(8080, "/weather/"),
    "news": http_get(8080, "/news/"),
    "resolver": http_get(8091, "/"),
    "cache": {},
}

try:
    st = os.stat(CACHE)

    with open(CACHE, encoding="utf-8") as f:
        cache = json.load(f)

    resolved = cache.get("resolved_at")
    age = None

    if resolved:
        dt = datetime.datetime.fromisoformat(resolved)
        now = datetime.datetime.now(dt.tzinfo)
        age = (now - dt).total_seconds()

    out["cache"] = {
        "exists": True,
        "mtime": st.st_mtime,
        "age_seconds": age,
        "video_id": cache.get("video_id"),
        "title": cache.get("title"),
        "source": cache.get("source"),
        "resolved_at": resolved,
    }

except Exception as e:
    out["cache"] = {
        "exists": False,
        "error": type(e).__name__ + ": " + str(e),
    }

print(json.dumps(out, ensure_ascii=False))
'''


LOG.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def now():
    return datetime.now().astimezone().isoformat(
        timespec="seconds"
    )


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "bad_count": 0,
            "notified": False,
        }


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)

    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(STATE)


def append_event(event):
    EVENTS.parent.mkdir(parents=True, exist_ok=True)

    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(event, ensure_ascii=False) + "\n"
        )


def probe():
    encoded = base64.b64encode(
        REMOTE_PROBE.encode("utf-8")
    ).decode("ascii")

    remote = (
        "python3 -c "
        "\"import base64;"
        "exec(base64.b64decode('"
        + encoded
        + "'))\""
    )

    p = subprocess.run(
        SSH + [remote],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=40,
    )

    if p.returncode:
        raise RuntimeError(
            p.stderr.strip()
            or f"venue ssh rc={p.returncode}"
        )

    return json.loads(p.stdout)


def evaluate(snapshot):
    problems = []

    for name, status in snapshot["services"].items():
        if status != "active":
            problems.append(
                f"{name}={status or 'unknown'}"
            )

    if snapshot["home"].get("status") != 200:
        problems.append(
            "home HTTP "
            + str(snapshot["home"].get("status"))
        )

    if snapshot["weather"].get("status") != 200:
        problems.append(
            "weather HTTP "
            + str(snapshot["weather"].get("status"))
        )

    news = snapshot["news"]

    if news.get("status") != 302:
        problems.append(
            "news HTTP "
            + str(news.get("status"))
        )
    elif "youtube.com/" not in (
        news.get("location") or ""
    ):
        problems.append(
            "news redirect is not YouTube"
        )

    resolver = snapshot["resolver"]

    if resolver.get("status") != 302:
        problems.append(
            "resolver HTTP "
            + str(resolver.get("status"))
        )
    elif "youtube.com/" not in (
        resolver.get("location") or ""
    ):
        problems.append(
            "resolver redirect is not YouTube"
        )

    cache = snapshot["cache"]

    if not cache.get("exists"):
        problems.append("news cache missing")
    else:
        video_id = cache.get("video_id") or ""

        if not re.fullmatch(
            r"[A-Za-z0-9_-]{11}", video_id
        ):
            problems.append(
                "news cache video_id invalid"
            )

        age = cache.get("age_seconds")

        if age is None:
            problems.append(
                "news cache resolved_at missing"
            )
        elif age > MAX_NEWS_CACHE_AGE:
            problems.append(
                f"news cache stale {int(age)}s"
            )

    return problems


def discord_say(message):
    p = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/discord_say.py"),
            message,
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )

    if p.returncode:
        logging.error(
            "discord alert failed: %s",
            p.stderr.strip(),
        )


def queue_thought(event):
    QUEUE.mkdir(parents=True, exist_ok=True)

    path = QUEUE / f"{time.time_ns()}.json"

    path.write_text(
        json.dumps(
            event,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "runtime/patrol_thinker.py"),
        ],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def run_once():
    state = load_state()

    try:
        snapshot = probe()
        problems = evaluate(snapshot)
        probe_error = None

    except Exception as e:
        snapshot = None
        problems = [
            "Venueへの巡回接続またはprobeに失敗: "
            + repr(e)
        ]
        probe_error = repr(e)

    previous_bad = state.get("bad_count", 0)

    if problems:
        state["bad_count"] = previous_bad + 1
        state["last_bad_at"] = now()
        state["last_problems"] = problems

        if (
            state["bad_count"] >= CONFIRM_SCANS
            and not state.get("notified")
        ):
            event = {
                "event_type": "venue_health_alert",
                "queued_at": now(),
                "hostname": "agent-101-vm",
                "target": "venue",
                "severity": "HIGH",
                "summary":
                    "Venue機能監視で異常を2回連続検出した。",
                "problems": problems,
                "snapshot": snapshot,
                "probe_error": probe_error,
            }

            append_event(event)
            queue_thought(event)

            discord_say(
                "旦那さま、Venueの巡回で異常を"
                "2回連続検出しました。\n"
                + "\n".join(
                    f"- {p}" for p in problems
                )
                + "\n現在は自動修復せず、"
                "状態を記録して調査対象にしています。"
            )

            state["notified"] = True
            state["notified_at"] = now()

            logging.warning(
                "venue confirmed unhealthy: %s",
                problems,
            )

    else:
        if state.get("notified"):
            event = {
                "event_type": "venue_health_recovered",
                "queued_at": now(),
                "hostname": "agent-101-vm",
                "target": "venue",
                "severity": "INFO",
                "summary": "Venue機能監視が正常へ復帰した。",
                "snapshot": snapshot,
            }

            append_event(event)
            queue_thought(event)

            discord_say(
                "旦那さま、Venueは巡回上"
                "正常状態へ復帰しました。"
            )

            logging.info("venue recovered")

        state["bad_count"] = 0
        state["notified"] = False
        state["last_ok_at"] = now()
        state["last_problems"] = []

    state["updated_at"] = now()
    state["snapshot"] = snapshot

    save_state(state)

    print(
        json.dumps(
            {
                "ok": not problems,
                "problems": problems,
                "bad_count": state["bad_count"],
                "snapshot": snapshot,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main():
    if "--once" in sys.argv:
        run_once()
        return

    logging.info(
        "venue guard started interval=%ss confirm=%s",
        INTERVAL,
        CONFIRM_SCANS,
    )

    while True:
        try:
            run_once()
        except Exception as e:
            logging.exception(
                "venue guard failed: %r", e
            )

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
