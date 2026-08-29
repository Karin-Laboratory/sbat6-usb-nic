import unittest
from tools import zen3_gnss_patrol as patrol

class Zen3PatrolTests(unittest.TestCase):
    def test_thresholds_and_grace(self):
        self.assertEqual(patrol.classify(.3, 10), "normal")
        self.assertEqual(patrol.classify(.8, 10), "normal")
        self.assertEqual(patrol.classify(1.5, 1), "normal")
        self.assertEqual(patrol.classify(1.5, 3), "warn")
        self.assertEqual(patrol.classify(3, 3), "alert")
        self.assertEqual(patrol.classify(6, 3), "critical")

    def test_recovery(self):
        result = patrol.next_state({"offset": .32}, {"classification": "warn", "consecutive_warning": 4})
        self.assertEqual(result["classification"], "normal")
        self.assertEqual(result["consecutive_warning"], 0)
        self.assertTrue(result["notify"])

    def test_parse(self):
        raw = """__USB__\n0b05:4dae ASUS_Z012DA\n__ADB__\nGCAZCY05P824JAW\\tdevice\n__SERVICE__\nactive\n__SOCKET__\n0.0.0.0:40123\n__JOURNAL__\naccept peer=x offset=-0.2216 age=0.09 sat=12 cn0=26.6\n__SOURCES__\n#x ZEN3 0 2 252 7 +195ms[ +195ms] +/- 32ms\n^* internet 2 10 377 7 -1us[ -1us] +/- 2ms\n"""
        result = patrol.parse_snapshot(raw)
        self.assertTrue(result["usb_present"])
        self.assertEqual(result["accepted_packets"], 1)
        self.assertEqual(result["reach"], 252)
        self.assertAlmostEqual(result["offset"], .195)
        self.assertTrue(result["internet_ntp_healthy"])
        self.assertEqual(result["selected_source"], "internet")
        self.assertEqual(result["expected_primary"], "ZEN3")
        self.assertTrue(result["unexpected_fallback"])
