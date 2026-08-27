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
HISTORY = ROOT / "state/venue-health-history.json"
EVENTS = ROOT / "state/venue-events.jsonl"
LOG = ROOT / "logs/venue_guard.log"
QUEUE = ROOT / "state/patrol_queue"

INTERVAL = 300
CONFIRM_SCANS = 2
MAX_NEWS_CACHE_AGE = 1800
MAX_HISTORY_SAMPLES = 2016

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

def service_details(name):
    p = subprocess.run(
        ["systemctl", "show", name, "--property=MainPID", "--property=ControlGroup"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5,
    )
    values = dict(line.split("=", 1) for line in p.stdout.splitlines() if "=" in line)
    try:
        main_pid = int(values.get("MainPID", "0"))
    except ValueError:
        main_pid = 0
    pids = []
    cgroup = values.get("ControlGroup", "")
    if cgroup:
        try:
            pids = [int(value) for value in open(
                "/sys/fs/cgroup" + cgroup + "/cgroup.procs", encoding="utf-8"
            ).read().split()]
        except (OSError, ValueError):
            pass
    if main_pid and main_pid not in pids:
        # Some user-session children move into delegated cgroups.  Preserve
        # service ownership correlation by following the fixed process tree.
        tree = {}
        ps = subprocess.run(
            ["ps", "-eo", "pid=,ppid="], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5,
        )
        for line in ps.stdout.splitlines():
            try:
                child, parent = (int(value) for value in line.split())
            except (ValueError, TypeError):
                continue
            tree.setdefault(parent, []).append(child)
        pending = [main_pid]
        pids = []
        while pending:
            current = pending.pop()
            if current in pids:
                continue
            pids.append(current)
            pending.extend(tree.get(current, []))
    return {"active": service(name), "main_pid": main_pid, "pids": pids}

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

def json_get(port, path):
    result = http_get(port, path)
    if result.get("status") != 200:
        return result
    try:
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        c.request("GET", path)
        r = c.getresponse()
        body = r.read(65536)
        c.close()
        result["json"] = json.loads(body.decode("utf-8"))
    except Exception as e:
        result["parse_error"] = type(e).__name__ + ": " + str(e)
    return result

def listeners():
    p = subprocess.run(
        ["sudo", "-n", "ss", "-lntpH"], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5,
    )
    found = {}
    for line in p.stdout.splitlines():
        match = re.search(r"127\.0\.0\.1:(\d+).*pid=(\d+)", line)
        if match:
            found[match.group(1)] = int(match.group(2))
    return found

def hardware():
    connected = []
    for path in __import__("glob").glob("/sys/class/drm/*/status"):
        try:
            if open(path, encoding="utf-8").read().strip() == "connected":
                connected.append(os.path.basename(os.path.dirname(path)))
        except OSError:
            pass
    try:
        inputs = open("/proc/bus/input/devices", encoding="utf-8").read()
    except OSError:
        inputs = ""
    try:
        pcm = open("/proc/asound/pcm", encoding="utf-8").read()
    except OSError:
        pcm = ""
    return {
        "connected_displays": sorted(connected),
        "touch_present": "Wacom HID 4801 Finger" in inputs,
        "audio_playback_present": "playback" in pcm,
    }

service_names = (
    "venue-kiosk.service",
    "venue-latest-tbs-news.service",
    "venue-bgm-manager.service",
    "venue-volume-api.service",
    "nginx.service",
)

out = {
    "services": {
        name: service_details(name)
        for name in service_names
    },
    "listeners": listeners(),
    "hardware": hardware(),
    "home": http_get(8080, "/"),
    "weather": http_get(8080, "/weather/"),
    "news": http_get(8080, "/news/"),
    "resolver": http_get(8091, "/"),
    "volume": json_get(8092, "/status"),
    "stream": json_get(8092, "/stream-status"),
    "bgm_health": json_get(8093, "/health"),
    "bgm_artists": json_get(8093, "/artists"),
    "kiosk_tabs": json_get(9222, "/json/list"),
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

# Retain only the facts needed by the local evaluator.  In particular, do not
# persist Chromium debugger URLs or complete application catalogues.
artists = out.get("bgm_artists", {}).get("json", {}).get("artists")
if isinstance(artists, list):
    out["bgm_artists"]["json"] = {
        "artist_count": len(artists),
        "artist_ids": [a.get("id") for a in artists if isinstance(a, dict) and a.get("id")],
    }
tabs = out.get("kiosk_tabs", {}).get("json")
if isinstance(tabs, list):
    out["kiosk_tabs"]["json"] = [
        {"type": tab.get("type"), "title": tab.get("title"), "url": tab.get("url")}
        for tab in tabs if isinstance(tab, dict) and tab.get("type") == "page"
    ]

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


def append_history(sample, path=HISTORY, limit=MAX_HISTORY_SAMPLES):
    try:
        history = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(history, list):
            history = []
    except (OSError, ValueError):
        history = []
    history.append(sample)
    history = history[-limit:]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


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

    for name, detail in snapshot["services"].items():
        status = detail.get("active") if isinstance(detail, dict) else detail
        if status != "active":
            problems.append(
                f"{name}={status or 'unknown'}"
            )

    expected_ports = {
        "venue-kiosk.service": (9222,),
        "venue-latest-tbs-news.service": (8091,),
        "venue-bgm-manager.service": (8093,),
        "venue-volume-api.service": (8092,),
        "nginx.service": (8080, 8082),
    }
    listeners = snapshot.get("listeners", {})
    for name, ports in expected_ports.items():
        detail = snapshot["services"].get(name, {})
        pids = detail.get("pids", []) if isinstance(detail, dict) else []
        if not pids:
            problems.append(f"{name} process ownership unavailable")
        for port in ports:
            listener_pid = listeners.get(str(port))
            if not listener_pid:
                problems.append(f"{name} listener {port} missing")
            elif pids and listener_pid not in pids:
                problems.append(f"{name} listener {port} owned by unexpected pid")

    hardware = snapshot.get("hardware", {})
    if not hardware.get("connected_displays"):
        problems.append("kiosk display not connected")
    if not hardware.get("touch_present"):
        problems.append("kiosk touch input not present")
    if not hardware.get("audio_playback_present"):
        problems.append("kiosk audio playback device not present")

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

    for key in ("volume", "stream", "bgm_health", "bgm_artists", "kiosk_tabs"):
        result = snapshot.get(key, {})
        if result.get("status") != 200 or "json" not in result:
            problems.append(f"{key} read-only state unavailable")

    volume = snapshot.get("volume", {}).get("json", {})
    if volume.get("ok") is not True or not isinstance(volume.get("volume"), (int, float)):
        problems.append("volume state invalid")

    stream = snapshot.get("stream", {}).get("json", {})
    if stream.get("ok") is not True or not isinstance(stream.get("streams"), list):
        problems.append("audio stream state invalid")

    bgm = snapshot.get("bgm_health", {}).get("json", {})
    if bgm.get("ok") is not True or bgm.get("worker") is not True:
        problems.append("BGM worker unhealthy")

    artist_count = snapshot.get("bgm_artists", {}).get("json", {}).get("artist_count")
    if not isinstance(artist_count, int) or artist_count < 1:
        problems.append("BGM catalogue empty or invalid")

    tabs = snapshot.get("kiosk_tabs", {}).get("json")
    if not isinstance(tabs, list) or not any(
        tab.get("type") == "page" and tab.get("url") == "http://127.0.0.1:8080/"
        for tab in tabs if isinstance(tab, dict)
    ):
        problems.append("kiosk home page not active")

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
    append_history({
        "observed_at": state["updated_at"],
        "ok": not problems,
        "problems": problems,
        "probe_succeeded": probe_error is None,
    })

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
