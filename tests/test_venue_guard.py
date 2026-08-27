import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "runtime/venue_guard.py"
SPEC = importlib.util.spec_from_file_location("venue_guard", MODULE_PATH)
venue_guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(venue_guard)


def healthy_snapshot():
    services = {
        "venue-kiosk.service": {"active": "active", "main_pid": 9, "pids": [9, 10]},
        "venue-latest-tbs-news.service": {"active": "active", "main_pid": 11, "pids": [11]},
        "venue-bgm-manager.service": {"active": "active", "main_pid": 12, "pids": [12]},
        "venue-volume-api.service": {"active": "active", "main_pid": 13, "pids": [13]},
        "nginx.service": {"active": "active", "main_pid": 14, "pids": [14, 15]},
    }
    return {
        "services": services,
        "listeners": {"9222": 10, "8091": 11, "8093": 12, "8092": 13,
                      "8080": 15, "8082": 15},
        "hardware": {"connected_displays": ["card0-DSI-1"],
                     "touch_present": True, "audio_playback_present": True},
        "home": {"status": 200}, "weather": {"status": 200},
        "news": {"status": 302, "location": "https://www.youtube.com/embed/x"},
        "resolver": {"status": 302, "location": "https://www.youtube.com/watch?v=x"},
        "cache": {"exists": True, "video_id": "5Dfumn4ibHc", "age_seconds": 10},
        "volume": {"status": 200, "json": {"ok": True, "volume": 20}},
        "stream": {"status": 200, "json": {"ok": True, "streams": []}},
        "bgm_health": {"status": 200, "json": {"ok": True, "worker": True}},
        "bgm_artists": {"status": 200, "json": {"artist_count": 1, "artist_ids": ["ive"]}},
        "kiosk_tabs": {"status": 200, "json": [
            {"type": "page", "url": "http://127.0.0.1:8080/"}
        ]},
    }


class VenueGuardTests(unittest.TestCase):
    def test_enhanced_snapshot_is_healthy(self):
        self.assertEqual(venue_guard.evaluate(healthy_snapshot()), [])

    def test_service_listener_correlation_detects_wrong_owner(self):
        snapshot = healthy_snapshot()
        snapshot["listeners"]["8093"] = 999
        self.assertIn(
            "venue-bgm-manager.service listener 8093 owned by unexpected pid",
            venue_guard.evaluate(snapshot),
        )

    def test_user_facing_state_is_checked(self):
        snapshot = healthy_snapshot()
        snapshot["hardware"]["touch_present"] = False
        snapshot["kiosk_tabs"]["json"] = []
        problems = venue_guard.evaluate(snapshot)
        self.assertIn("kiosk touch input not present", problems)
        self.assertIn("kiosk home page not active", problems)

    def test_history_is_bounded_and_atomic_result_is_valid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            for number in range(5):
                venue_guard.append_history({"number": number}, path=path, limit=3)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                [{"number": 2}, {"number": 3}, {"number": 4}],
            )
            self.assertFalse(path.with_suffix(".tmp").exists())

    def test_restart_policy_is_documentation_only(self):
        profile_path = MODULE_PATH.with_name("venue_profile.json")
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        policy = profile["restart_policy"]
        self.assertFalse(policy["automatic_restart_by_butlerx"])
        self.assertTrue(policy["policy_is_documentation_not_execution_authority"])


if __name__ == "__main__":
    unittest.main()
