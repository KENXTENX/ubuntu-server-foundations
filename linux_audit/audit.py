"""Collect and assess basic Linux host health using Python's standard library.

No privileges, system changes, open ports, or third-party packages are required.
The report includes local hostname metadata: review before publicly sharing it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import platform
import shutil
import socket
import subprocess
from typing import Any


def parse_os_release(contents: str) -> dict[str, str]:
    """Parse the key/value subset of os-release without evaluating shell code."""
    values: dict[str, str] = {}
    for raw in contents.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if not key.isidentifier():
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def parse_meminfo(contents: str) -> dict[str, int]:
    """Read /proc/meminfo fields expressed in KiB, ignoring malformed lines."""
    metrics: dict[str, int] = {}
    for line in contents.splitlines():
        if ":" not in line:
            continue
        name, raw = line.split(":", 1)
        parts = raw.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1] == "kB":
            metrics[name.strip()] = int(parts[0])
    return metrics


def used_percent(total: int, available: int) -> float:
    if total <= 0:
        raise ValueError("total must be positive")
    if available < 0 or available > total:
        raise ValueError("available must be between zero and total")
    return round(100 * (total - available) / total, 1)


def get_ssh_state() -> str:
    """Report the systemd ssh service state without making changes."""
    try:
        process = subprocess.run(
            ["systemctl", "is-active", "ssh"],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    value = process.stdout.strip()
    if value == "active" and process.returncode != 0:
        return "unknown"
    return value if value in {"active", "inactive", "failed", "activating", "deactivating"} else "unknown"


def has_default_ipv4_route(path: Path = Path("/proc/net/route")) -> bool | None:
    """Returns None when the route table cannot be inspected."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[1:]
    except OSError:
        return None
    for line in lines:
        parts = line.split()
        if len(parts) >= 8 and parts[1] == "00000000" and parts[7] == "00000000":
            try:
                if int(parts[3], 16) & 0x1:
                    return True
            except ValueError:
                pass
    return False


def assess(
    disk_percent: float,
    memory_percent: float | None,
    disk_warn: int,
    memory_warn: int,
    ssh_state: str,
    require_ssh: bool,
    route_exists: bool | None,
    require_network: bool,
) -> list[str]:
    alerts = []
    if disk_percent >= disk_warn:
        alerts.append(f"Disk usage is {disk_percent}% (threshold: {disk_warn}%).")
    if memory_percent is not None and memory_percent >= memory_warn:
        alerts.append(f"Memory usage is {memory_percent}% (threshold: {memory_warn}%).")
    if memory_percent is None:
        alerts.append("Memory usage could not be verified.")
    if require_ssh and ssh_state != "active":
        alerts.append(f"SSH service is not active (state: {ssh_state}).")
    if require_network and route_exists is not True:
        alerts.append("No active default IPv4 route was verified.")
    return alerts


def collect_report(
    disk_path: str = "/",
    disk_warn: int = 85,
    memory_warn: int = 90,
    require_ssh: bool = False,
    require_network: bool = False,
) -> dict[str, Any]:
    """Inspect local system only. Does not modify data or need sudo."""
    if platform.system() != "Linux":
        raise ValueError("this audit requires Linux; run it inside the Ubuntu guest")
    for name, value in (("disk_warn", disk_warn), ("memory_warn", memory_warn)):
        if not 1 <= value <= 100:
            raise ValueError(f"{name} must be between 1 and 100")
    disk = shutil.disk_usage(disk_path)
    disk_percent = used_percent(disk.total, disk.free)
    try:
        os_release = parse_os_release(Path("/etc/os-release").read_text(encoding="utf-8"))
    except OSError:
        os_release = {}
    try:
        mem = parse_meminfo(Path("/proc/meminfo").read_text(encoding="utf-8"))
    except OSError:
        mem = {}
    mem_total = mem.get("MemTotal")
    mem_available = mem.get("MemAvailable")
    memory_percent = (
        used_percent(mem_total, mem_available)
        if mem_total is not None and mem_available is not None and 0 <= mem_available <= mem_total and mem_total > 0
        else None
    )
    try:
        uptime_seconds = int(float(Path("/proc/uptime").read_text(encoding="utf-8").split()[0]))
    except (OSError, IndexError, ValueError):
        uptime_seconds = None
    ssh_state = get_ssh_state()
    default_route = has_default_ipv4_route()
    alerts = assess(disk_percent, memory_percent, disk_warn, memory_warn, ssh_state,
                    require_ssh, default_route, require_network)
    return {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hostname": socket.gethostname(),
        "operating_system": os_release.get("PRETTY_NAME", platform.system()),
        "kernel": platform.release(),
        "uptime_seconds": uptime_seconds,
        "disk": {"path": disk_path, "total_bytes": disk.total, "free_bytes": disk.free,
                 "used_percent": disk_percent},
        "memory": {"total_kib": mem_total, "available_kib": mem_available,
                   "used_percent": memory_percent},
        "ssh_service_state": ssh_state,
        "default_ipv4_route_present": default_route,
        "alerts": alerts,
        "status": "warning" if alerts else "ok",
    }
