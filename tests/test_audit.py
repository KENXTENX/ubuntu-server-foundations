"""Deterministic unit tests; no real SSH failures or network scans required."""
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory

from linux_audit.audit import (
    assess, has_default_ipv4_route, parse_meminfo, parse_os_release, used_percent,
)
from linux_audit.__main__ import main


class ParsingTests(unittest.TestCase):
    def test_os_release(self):
        data = 'NAME=Ubuntu\nPRETTY_NAME="Ubuntu 24.04 LTS"\n# ignored\n'
        self.assertEqual(parse_os_release(data)["PRETTY_NAME"], "Ubuntu 24.04 LTS")

    def test_memory_parser(self):
        data = 'MemTotal:  8192000 kB\nMemAvailable: 4096000 kB\nBad: X kB'
        self.assertEqual(parse_meminfo(data)["MemAvailable"], 4096000)
        self.assertNotIn("Bad", parse_meminfo(data))

    def test_memory_percent(self):
        self.assertEqual(used_percent(1000, 250), 75.0)

    def test_invalid_amounts(self):
        with self.assertRaises(ValueError):
            used_percent(0, 0)
        with self.assertRaises(ValueError):
            used_percent(100, 101)


class AssessmentTests(unittest.TestCase):
    def test_clean_health(self):
        self.assertEqual(assess(20, 30, 85, 90, "active", True, True, True), [])

    def test_disk_warning_at_threshold(self):
        result = assess(85, 10, 85, 90, "active", False, True, False)
        self.assertTrue(any("Disk usage" in message for message in result))

    def test_memory_warning(self):
        result = assess(10, 95, 85, 90, "active", False, True, False)
        self.assertTrue(any("Memory usage" in message for message in result))

    def test_ssh_required(self):
        self.assertTrue(any("SSH" in m for m in assess(10, 10, 85, 90, "inactive", True, True, False)))

    def test_route_required(self):
        self.assertTrue(any("route" in m for m in assess(10, 10, 85, 90, "active", False, False, True)))

    def test_route_parse(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "route"
            path.write_text("Iface Destination Gateway Flags RefCnt Use Metric Mask MTU Window IRTT\n"
                            "ens33 00000000 0101A8C0 0003 0 0 0 00000000 0 0 0\n", encoding="utf-8")
            self.assertTrue(has_default_ipv4_route(path))


class CommandTests(unittest.TestCase):
    @patch("linux_audit.__main__.collect_report")
    def test_json_exit_ok(self, mock_collect):
        mock_collect.return_value = {"alerts": [], "status": "ok"}
        with patch("builtins.print") as mocked_print:
            self.assertEqual(main(["--json"]), 0)
        self.assertTrue(mocked_print.called)

    @patch("linux_audit.__main__.collect_report")
    def test_json_exit_warning(self, mock_collect):
        mock_collect.return_value = {"alerts": ["Disk usage is high"], "status": "warning"}
        with patch("builtins.print"):
            self.assertEqual(main(["--json"]), 1)

    @patch("linux_audit.__main__.collect_report", side_effect=ValueError("bad threshold"))
    def test_error_exit_two(self, mock_collect):
        with patch("builtins.print"):
            self.assertEqual(main([]), 2)


if __name__ == "__main__":
    unittest.main()
