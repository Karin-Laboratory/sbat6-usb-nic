import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime import openwrt_guard as guard


OBSERVATION = '''===== SYSTEM =====
{"hostname":"OpenWrt-Desktop","model":"ELECOM WRC-2533GHBK-I","system":"MediaTek MT7621","kernel":"6.12.94","release":{"version":"25.12.5","revision":"r33051-f5dae5ece4"}}
===== LAN =====
{"up":true,"device":"br-lan","proto":"dhcp","ipv4-address":[{"address":"192.168.1.42","mask":22}],"route":[{"target":"0.0.0.0","nexthop":"192.168.0.1"}],"dns-server":["192.168.0.1"],"data":{"dhcpserver":"192.168.0.88","ntpserver":"192.168.0.26"}}
===== BRIDGE PORTS =====
lan1
lan2
lan3
lan4
wan
phy0-ap0
phy0-ap1
phy1-ap0
===== WIRELESS =====
wireless.wifinet0 device=radio0 band=2g mode=ap ssid=justnottoday encryption=sae-mixed disabled=
wireless.wifinet1 device=radio1 band=5g mode=ap ssid=justnottoday encryption=sae-mixed disabled=
wireless.wifinet2 device=radio0 band=2g mode=ap ssid=infra2g encryption=sae-mixed disabled=
===== SERVICES =====
dropbear=running
uhttpd=running
Filesystem overlayfs:/overlay 1.9M 236.0K 1.6M 12% /
'''


class OpenWrtGuardTests(unittest.TestCase):
    def test_normal_probe_and_no_remote_command(self):
        def fake(args, **kwargs):
            self.assertEqual(args, guard.SSH)
            self.assertEqual(kwargs["capture_output"], True)
            return type("Result", (), {"returncode": 0, "stdout": OBSERVATION, "stderr": ""})()
        snapshot = guard.probe(fake)
        self.assertEqual(guard.evaluate(snapshot), [])

    def test_missing_radio_ssid_bridge_and_services(self):
        snapshot = guard.probe(lambda *a, **k: type("R", (), {"returncode": 0, "stdout": OBSERVATION.replace("radio1 band=5g mode=ap ssid=justnottoday", "radio1 band=5g mode=ap ssid=other").replace("phy1-ap0\n", "").replace("dropbear=running", "dropbear=stopped"), "stderr": ""})())
        problems = guard.evaluate(snapshot)
        self.assertTrue(any("5GHz" in p for p in problems)); self.assertTrue(any("bridge" in p for p in problems)); self.assertIn("dropbear not running", problems)

    def test_two_failures_alert_and_recovery(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(guard, "EVENTS", Path(directory) / "events.jsonl"), patch.object(guard, "QUEUE", Path(directory) / "queue"):
            state = Path(directory) / "state.json"
            failing = lambda *a, **k: (_ for _ in ()).throw(TimeoutError())
            _, problems, first = guard.run_once(failing, state)
            self.assertTrue(problems); self.assertEqual(first["bad_count"], 1); self.assertFalse(first.get("notified", False))
            _, _, second = guard.run_once(failing, state)
            self.assertTrue(second["notified"])
            healthy = lambda *a, **k: type("R", (), {"returncode": 0, "stdout": OBSERVATION, "stderr": ""})()
            _, problems, recovered = guard.run_once(healthy, state)
            self.assertFalse(problems); self.assertFalse(recovered["notified"])
            events = (Path(directory) / "events.jsonl").read_text()
            self.assertIn("openwrt_health_alert", events); self.assertIn("openwrt_health_recovered", events)

    def test_overlay_low_space(self):
        snapshot = guard.probe(lambda *a, **k: type("R", (), {"returncode": 0, "stdout": OBSERVATION.replace("12%", "92%"), "stderr": ""})())
        self.assertIn("overlay low-space", guard.evaluate(snapshot))


if __name__ == "__main__": unittest.main()
