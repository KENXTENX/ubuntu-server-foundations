"""Command line interface for the Linux System Audit project."""

import argparse
import json
import sys
from .audit import collect_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only Linux health audit. Check output for host details before sharing."
    )
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report")
    parser.add_argument("--disk-path", default="/", help="Disk mount or path to inspect (default: /)")
    parser.add_argument("--disk-warn", type=int, default=85, help="Disk warning threshold 1-100 (default: 85)")
    parser.add_argument("--memory-warn", type=int, default=90, help="Memory warning threshold 1-100 (default: 90)")
    parser.add_argument("--require-ssh", action="store_true", help="Warn if systemd ssh service is not active")
    parser.add_argument("--require-network", action="store_true", help="Warn if a default IPv4 route is not verified")
    args = parser.parse_args(argv)
    try:
        report = collect_report(args.disk_path, args.disk_warn, args.memory_warn,
                                args.require_ssh, args.require_network)
    except (OSError, ValueError) as exc:
        print(f"Audit error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        disk = report["disk"]
        memory = report["memory"]
        print(f"Linux audit: {report['status'].upper()}")
        print(f"OS: {report['operating_system']} | Kernel: {report['kernel']}")
        print(f"Host: {report['hostname']} (local; redact before sharing)")
        print(f"Disk {disk['path']}: {disk['used_percent']}% used | Free: {disk['free_bytes'] // (1024**3)} GiB")
        print(f"Memory: {memory['used_percent']}% used" if memory['used_percent'] is not None else "Memory: unavailable")
        print(f"SSH: {report['ssh_service_state']} | Default IPv4 route: {report['default_ipv4_route_present']}")
        for alert in report["alerts"]:
            print(f"WARNING: {alert}")
    return 1 if report["alerts"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
