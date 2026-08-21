#!/usr/bin/env python3
"""Install or verify the AaITR-to-CStoneCloud synchronization timer."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED_ROOT = Path("/root/code/us-public/s-ui")
SYSTEMD_DIR = Path("/etc/systemd/system")
SERVICE = "yuntu-exit-sync.service"
TIMER = "yuntu-exit-sync.timer"
UNITS = (SERVICE, TIMER)


def run(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or str(result.returncode)
        raise RuntimeError(f"command failed: {command[0]}: {detail}")
    return result.stdout.strip()


def validate_sources() -> None:
    if ROOT != EXPECTED_ROOT:
        raise RuntimeError(f"run this script from the production checkout: {EXPECTED_ROOT}")
    for unit in UNITS:
        if not (ROOT / "systemd" / unit).is_file():
            raise RuntimeError(f"missing systemd unit: {unit}")
    for script in (
        "apply_desktop_direct_nodes.py",
        "export_yuntu_exit.py",
        "reconcile_production_clients.py",
        "sync_yuntu_exit.py",
    ):
        if not (ROOT / script).is_file():
            raise RuntimeError(f"missing synchronization script: {script}")


def verify_installation() -> None:
    validate_sources()
    for unit in UNITS:
        source = ROOT / "systemd" / unit
        installed = SYSTEMD_DIR / unit
        if not installed.is_file() or installed.read_bytes() != source.read_bytes():
            raise RuntimeError(f"installed systemd unit differs from the repository: {unit}")
    if run(["systemctl", "is-enabled", TIMER]) != "enabled":
        raise RuntimeError(f"systemd timer is not enabled: {TIMER}")
    if run(["systemctl", "is-active", TIMER]) != "active":
        raise RuntimeError(f"systemd timer is not active: {TIMER}")
    print("CStoneCloud exit synchronization timer: enabled and active")


def install() -> None:
    validate_sources()
    if os.geteuid() != 0:
        raise RuntimeError("installation must run as root")
    for unit in UNITS:
        destination = SYSTEMD_DIR / unit
        shutil.copyfile(ROOT / "systemd" / unit, destination)
        destination.chmod(0o644)
    run(["systemctl", "daemon-reload"])
    run(["systemctl", "enable", TIMER])
    run(["systemctl", "restart", TIMER])
    run(["systemctl", "start", SERVICE])
    verify_installation()
    print("CStoneCloud exit production users synchronized")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify installed units and timer state without changing the system",
    )
    args = parser.parse_args()
    if args.check:
        verify_installation()
    else:
        install()


if __name__ == "__main__":
    main()
