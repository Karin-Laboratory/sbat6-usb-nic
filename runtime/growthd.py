#!/usr/bin/env python3
"""Small queue daemon for safe ButlerX growth discovery and proposal notification."""
import argparse
import fcntl
import logging
import time
from pathlib import Path

from growth_pipeline import process_event
from growth_review import reconcile_review_journals


ROOT = Path("/home/masataka/projects/butlerx")
LOCK = ROOT / "state/growthd.lock"
LOG = ROOT / "logs/growthd.log"


def configure_logging():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.FileHandler(LOG), logging.StreamHandler()])


def run_once():
    recovered = reconcile_review_journals(ROOT)
    if recovered:
        logging.warning("reconciled review journals: %s", ",".join(recovered))
    for path in sorted((ROOT / "state/growth_queue").glob("*.json")):
        try:
            state = process_event(ROOT, path)
            logging.info("event=%s target=%s status=%s", state["event_id"], state["target"], state["status"])
        except Exception:
            logging.exception("unexpected growth event failure path=%s", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval", type=float, default=5.0)
    args = ap.parse_args()
    configure_logging()
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            logging.error("growthd already running")
            return 2
        while True:
            run_once()
            if args.once:
                return 0
            time.sleep(max(args.interval, 1.0))


if __name__ == "__main__":
    raise SystemExit(main())
