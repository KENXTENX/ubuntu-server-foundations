"""Regression tests use synthetic data, not owner's VM results."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from linux_audit.__main__ import main
from linux_audit.audit import assess, collect_report, get_ssh_state, has_default_ipv4_route, parse_meminfo


class RegressionTests(unittest.TestCase):
    def test_route_requires_zero_mask_and_up_flag(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'route'
            for mask, flags, expected in [('000000FF', '0001', False), ('00000000', '0000', False), ('00000000', 'bad-hex', False), ('00000000', '0003', True)]:
                with self.subTest(mask=mask, flags=flags):
                    path.write_text('Iface Destination Gateway Flags RefCnt Use Metric Mask\n'
                                    f'eth0 00000000 00000000 {flags} 0 0 0 {mask}\n')
                    self.assertEqual(has_default_ipv4_route(path), expected)
            self.assertIsNone(has_default_ipv4_route(Path(tmp) / 'missing'))

    @patch('linux_audit.audit.subprocess.run')
    def test_service_states_and_timeout(self, run):
        for output, rc, expected in [('active\n', 0, 'active'), ('inactive\n', 3, 'inactive'), ('active\n', 1, 'unknown'), ('unrecognized', 0, 'unknown')]:
            with self.subTest(output=output, rc=rc):
                run.return_value = SimpleNamespace(stdout=output, returncode=rc)
                self.assertEqual(get_ssh_state(), expected)
        args, kwargs = run.call_args
        self.assertEqual(args[0], ['systemctl', 'is-active', 'ssh'])
        self.assertEqual(kwargs['timeout'], 5)
        self.assertFalse(kwargs.get('shell', False))
        for error in (FileNotFoundError(), subprocess.TimeoutExpired('systemctl', 5)):
            run.side_effect = error
            self.assertEqual(get_ssh_state(), 'unknown')

    def fixture_read(self, path, **kwargs):
        return {'/etc/os-release': 'PRETTY_NAME="Synthetic Ubuntu"\n',
                '/proc/meminfo': 'MemTotal: 1000 kB\nMemAvailable: 500 kB\n',
                '/proc/uptime': '1234.56 500.00\n'}[str(path)]

    def fixture_cli(self, argv, reader=None):
        with patch('linux_audit.audit.platform.system', return_value='Linux'), \
             patch('linux_audit.audit.platform.release', return_value='synthetic-kernel'), \
             patch('linux_audit.audit.socket.gethostname', return_value='synthetic-host'), \
             patch('linux_audit.audit.shutil.disk_usage', return_value=SimpleNamespace(total=1000, free=500)), \
             patch('linux_audit.audit.Path.read_text', autospec=True, side_effect=reader or self.fixture_read), \
             patch('linux_audit.audit.get_ssh_state', return_value='active'), \
             patch('linux_audit.audit.has_default_ipv4_route', return_value=True), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            code = main(argv)
        return code, output.getvalue()

    def test_end_to_end_synthetic_json_success(self):
        code, output = self.fixture_cli(['--json', '--require-ssh', '--require-network'])
        report = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(report['status'], 'ok')
        self.assertEqual(report['disk']['used_percent'], 50.0)
        self.assertEqual(report['memory']['used_percent'], 50.0)
        self.assertEqual(report['uptime_seconds'], 1234)
        self.assertEqual(report['hostname'], 'synthetic-host')

    def test_end_to_end_exact_threshold_warning(self):
        code, output = self.fixture_cli(['--json', '--disk-warn', '50'])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output)['status'], 'warning')

    def test_missing_memory_is_warning(self):
        def reader(path, **kwargs):
            if str(path) == '/proc/meminfo':
                raise PermissionError('synthetic unreadable proc')
            return self.fixture_read(path, **kwargs)
        code, output = self.fixture_cli(['--json'], reader)
        report = json.loads(output)
        self.assertEqual(code, 1)
        self.assertIsNone(report['memory']['used_percent'])
        self.assertIn('Memory usage could not be verified.', report['alerts'])

    def test_invalid_memory_text_output(self):
        def reader(path, **kwargs):
            if str(path) == '/proc/meminfo':
                return 'MemTotal: 1000 kB\nMemAvailable: 2000 kB\n'
            return self.fixture_read(path, **kwargs)
        code, output = self.fixture_cli([], reader)
        self.assertEqual(code, 1)
        self.assertIn('Memory: unavailable', output)

    @patch('linux_audit.audit.platform.system', return_value='Linux')
    def test_invalid_thresholds_before_disk_reads(self, system):
        for option in ('disk_warn', 'memory_warn'):
            for value in (0, 101):
                with self.subTest(option=option, value=value), patch('linux_audit.audit.shutil.disk_usage') as disk:
                    with self.assertRaises(ValueError):
                        collect_report(**{option: value})
                    disk.assert_not_called()

    @patch('linux_audit.audit.platform.system', return_value='Linux')
    @patch('linux_audit.audit.shutil.disk_usage', side_effect=FileNotFoundError('synthetic missing path'))
    def test_missing_disk_cli_error(self, disk, system):
        with contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(main(['--json', '--disk-path', '/synthetic-missing']), 2)
        self.assertIn('Audit error:', error.getvalue())

    @patch('linux_audit.audit.platform.system', return_value='Darwin')
    def test_non_linux_is_explicit_error(self, system):
        with contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(main(['--json']), 2)
        self.assertIn('requires Linux', error.getvalue())

    def test_memory_requires_kib_units(self):
        self.assertEqual(parse_meminfo('MemTotal: 1000 MB\nHugePages_Total: 0\nMemAvailable: 500 kB\n'), {'MemAvailable': 500})

    def test_unknown_required_checks_warn(self):
        self.assertEqual(len(assess(20, 30, 85, 90, 'unknown', True, None, True)), 2)

    def test_unknown_optional_checks_are_not_requirements(self):
        self.assertEqual(assess(20, 30, 85, 90, 'unknown', False, None, False), [])


if __name__ == '__main__':
    unittest.main()
