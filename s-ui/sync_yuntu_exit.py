#!/usr/bin/env python3
"""Safely sync AaITR production clients to the YunTu pure-exit service."""

from __future__ import annotations

import fcntl
import hashlib
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from apply_desktop_direct_nodes import reconcile_desktop_nodes
from export_yuntu_exit import main as export_yuntu_exit_main
from reconcile_production_clients import reconcile_production_clients


ROOT = Path(__file__).resolve().parent
LOCK_FILE = ROOT / "yuntu-exit" / ".sync.lock"
LOCAL_CONFIG = ROOT / "yuntu-exit" / "config.json"
REMOTE = "root@154.23.242.22"
REMOTE_DIR = "/root/code/aaitr/yuntu-exit"
REMOTE_CONFIG = f"{REMOTE_DIR}/config.json"
REMOTE_NEXT = f"{REMOTE_DIR}/config.json.next"
REMOTE_BACKUPS = f"{REMOTE_DIR}/backups"
SSH_KEY = "/root/.ssh/yuntu_exit_sync_ed25519"
SING_BOX_IMAGE = (
    "ghcr.io/sagernet/sing-box:v1.13.0@"
    "sha256:d12357595495228bd673b4b3ef8d882c774ce7c4369bd22e89a2761029c53758"
)


def run(command: list[str], *, timeout: int = 60, input_text: str | None = None) -> str:
    result = subprocess.run(
        command,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        detail = stderr or stdout or f"exit {result.returncode}"
        raise RuntimeError(f"command failed: {command[0]}: {detail}")
    return result.stdout


def ssh_base() -> list[str]:
    return [
        "ssh",
        "-i",
        SSH_KEY,
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        "ConnectTimeout=10",
        REMOTE,
    ]


def scp_base() -> list[str]:
    return [
        "scp",
        "-i",
        SSH_KEY,
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        "ConnectTimeout=10",
    ]


def ssh_shell(script: str) -> list[str]:
    return ssh_base() + [f"bash -lc {shlex.quote(script)}"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def remote_sha256() -> str:
    output = run(
        ssh_shell(
            f"test -f {REMOTE_CONFIG!r} && sha256sum {REMOTE_CONFIG!r} | awk '{{print $1}}' || true"
        ),
        timeout=30,
    )
    return output.strip()


def render_local_config() -> None:
    # Reuse the existing renderer so the config schema stays in exactly one place.
    argv = sys.argv
    try:
        sys.argv = [
            "export_yuntu_exit.py",
            "--output",
            str(LOCAL_CONFIG),
        ]
        export_yuntu_exit_main()
    finally:
        sys.argv = argv


def sync_remote(local_hash: str) -> None:
    if not Path(SSH_KEY).exists():
        raise RuntimeError(f"SSH key is missing: {SSH_KEY}")
    run(ssh_base() + ["mkdir", "-p", REMOTE_DIR, REMOTE_BACKUPS], timeout=30)
    run(scp_base() + [str(LOCAL_CONFIG), f"{REMOTE}:{REMOTE_NEXT}"], timeout=60)
    remote_check = (
        f"set -euo pipefail; "
        f"chmod 600 {REMOTE_NEXT!r}; "
        f"docker run --rm "
        f"-v {REMOTE_NEXT!r}:/etc/sing-box/config.json:ro "
        f"-v {REMOTE_DIR!r}/cert:/etc/sing-box/cert:ro "
        f"{SING_BOX_IMAGE} check -c /etc/sing-box/config.json; "
        f"stamp=$(date -u +%Y%m%dT%H%M%SZ); "
        f"test -f {REMOTE_CONFIG!r} && cp -a {REMOTE_CONFIG!r} {REMOTE_BACKUPS!r}/config.json.$stamp.bak || true; "
        f"mv {REMOTE_NEXT!r} {REMOTE_CONFIG!r}; "
        f"chmod 600 {REMOTE_CONFIG!r}; "
        f"cd /root/code/aaitr; "
        f"docker compose restart yuntu-exit; "
        f"sleep 8; "
        f"test \"$(docker inspect -f '{{{{.State.Health.Status}}}}' yuntu-exit-sing-box)\" = healthy; "
        f"test \"$(sha256sum {REMOTE_CONFIG!r} | awk '{{print $1}}')\" = {local_hash!r}"
    )
    run(ssh_shell(remote_check), timeout=180)


def main() -> None:
    LOCK_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with LOCK_FILE.open("w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        reconcile_production_clients()
        reconcile_desktop_nodes()
        with tempfile.TemporaryDirectory(prefix="yuntu-exit-sync-", dir=str(ROOT)) as tmp:
            tmp_config = Path(tmp) / "config.json"
            render_local_config()
            shutil.copy2(LOCAL_CONFIG, tmp_config)
            local_hash = sha256(tmp_config)
            current_remote_hash = remote_sha256()
            if current_remote_hash == local_hash:
                print("YunTu exit config already up to date")
                return
            shutil.copy2(tmp_config, LOCAL_CONFIG)
            sync_remote(local_hash)
            print("YunTu exit config synced and yuntu-exit restarted")


if __name__ == "__main__":
    try:
        main()
    except BlockingIOError:
        print("another sync is already running")
    except Exception as exc:  # noqa: BLE001
        print(f"YunTu exit sync failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
