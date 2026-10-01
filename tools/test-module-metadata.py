#!/usr/bin/env python3
"""Exercise the offline checker with published artifacts and invalid references."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / 'tools/check-module-metadata.py'
MODULE = ROOT / 'artifacts/t6a_usb_ncm_canonical_v6.ko'
MAP = ROOT / 'repro/t6a-vendor-Module.symvers'


class MetadataTests(unittest.TestCase):
    def run_check(self, module=MODULE, maps=None, extra=()):
        command = [sys.executable, str(CHECK), str(module)]
        for path in maps if maps is not None else [MAP]:
            command += ['--symvers', str(path)]
        result = subprocess.run(command + list(extra), capture_output=True, text=True)
        report = json.loads(result.stdout)
        self.assertEqual(report['load_authorization'], 'NOT_ESTABLISHED')
        return result.returncode, report

    def test_published_v6(self):
        code, report = self.run_check()
        self.assertEqual(code, 0)
        self.assertEqual(report['metadata_result'], 'MATCH')
        self.assertEqual(len(report['symbols']), 76)

    def test_wrong_release(self):
        code, report = self.run_check(extra=['--vermagic', 'different kernel'])
        self.assertEqual(code, 1)
        self.assertFalse(report['vermagic_match'])

    def test_missing_map_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'empty.symvers'
            path.write_text('')
            code, report = self.run_check(maps=[path])
            self.assertEqual(code, 1)
            self.assertTrue(all(x['status'] == 'UNKNOWN' for x in report['symbols']))

    def test_conflicting_maps(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'conflict.symvers'
            path.write_text('0x00000000 module_layout vmlinux EXPORT_SYMBOL\n')
            code, report = self.run_check(maps=[MAP, path])
            self.assertEqual(code, 2)
            self.assertIn('conflicting', report['error'])

    def test_wrong_crc(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'wrong.symvers'
            path.write_text(MAP.read_text().replace('0x3a3eb6e9', '0x00000000'))
            code, report = self.run_check(maps=[path])
            self.assertEqual(code, 1)
            self.assertEqual([x['symbol'] for x in report['symbols'] if x['status'] == 'MISMATCH'], ['module_layout'])

    def test_truncated_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'truncated.ko'
            path.write_bytes(MODULE.read_bytes()[:100])
            code, report = self.run_check(module=path)
            self.assertEqual(code, 2)
            self.assertEqual(report['metadata_result'], 'ERROR')


if __name__ == '__main__':
    unittest.main()
