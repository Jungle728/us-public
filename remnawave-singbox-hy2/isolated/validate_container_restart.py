#!/usr/bin/env python3
"""Prove that pending sing-box HY2 usage survives a full Node container restart."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from bootstrap_lab import ADMIN_ENV, DEFAULT_BASE_URL, ROOT, STATE, Api, read_env
from validate_accounting import (
    curl_through,
    get_user,
    reset_user_traffic,
    restart_lab_client,
    usage,
    wait_for,
)


PANEL_CONTAINER = "remnawave-hy2-lab-panel"
NODE_CONTAINER = "remnawave-hy2-lab-node"
STATE_PATH = ROOT / "runtime" / "node-state" / "singbox-stats.json"


def docker(*args: str) -> None:
    subprocess.run(
        ["docker", *args],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def pending_state_size() -> int:
    try:
        return STATE_PATH.stat().st_size
    except FileNotFoundError:
        return 0


def wait_empty_state(timeout: int = 45) -> None:
    wait_for("pending stats file to be empty", lambda: pending_state_size() <= 2, timeout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    state = json.loads(STATE.read_text(encoding="utf-8"))
    admin = read_env(ADMIN_ENV)
    api = Api(args.base_url)
    api.authenticate(admin["ADMIN_USERNAME"], admin["ADMIN_PASSWORD"])
    user = state["users"][0]
    node_uuid = state["nodeUuid"]

    reset_user_traffic(api, user["id"])
    restart_lab_client("hy2-client-a")
    time.sleep(2)
    wait_empty_state()

    paused = threading.Event()
    watcher_error: list[BaseException] = []
    captured_size = 0

    def pause_on_snapshot() -> None:
        nonlocal captured_size
        try:
            deadline = time.monotonic() + 75
            while time.monotonic() < deadline:
                size = pending_state_size()
                if size > 2:
                    docker("pause", PANEL_CONTAINER)
                    captured_size = size
                    paused.set()
                    return
                time.sleep(0.02)
            raise RuntimeError("timed out waiting for a persisted pending stats snapshot")
        except BaseException as error:
            watcher_error.append(error)
            paused.set()

    watcher = threading.Thread(target=pause_on_snapshot, daemon=True)
    watcher.start()

    action_error: list[BaseException] = []

    def generate_and_restart_core() -> None:
        try:
            curl_through(20880, count=6)
            api.request(
                "POST",
                f"/api/nodes/{node_uuid}/actions/restart",
                {"forceRestart": True},
            )
        except BaseException as error:
            action_error.append(error)

    action = threading.Thread(target=generate_and_restart_core, daemon=True)
    action.start()
    paused.wait(80)
    if watcher_error:
        raise watcher_error[0]
    if not paused.is_set() or captured_size <= 2:
        raise RuntimeError("Panel was not paused with a pending stats snapshot")

    try:
        before_restart = pending_state_size()
        if before_restart <= 2:
            raise RuntimeError("pending stats were consumed before the container restart")
        docker("restart", NODE_CONTAINER)
        after_restart = pending_state_size()
        if after_restart != before_restart:
            raise RuntimeError(
                f"pending stats file changed across restart: {before_restart} -> {after_restart}"
            )
    finally:
        docker("unpause", PANEL_CONTAINER)

    action.join(timeout=5)
    if action_error:
        # Pausing the panel can terminate the in-flight admin request after the
        # Node has already persisted the snapshot. The persisted state and
        # restored accounting below are the authoritative checks.
        action_error.clear()

    def restored_usage() -> int:
        node = api.request("GET", f"/api/nodes/{node_uuid}")["response"]
        current = usage(api, user["id"])
        return current if node.get("isConnected") and current > 0 else 0

    restored = int(wait_for("restored usage after Node container restart", restored_usage, 240))
    if get_user(api, user["id"])["status"] != "ACTIVE":
        raise RuntimeError("test user is no longer active after restored accounting")

    print(
        "PASS container restart persistence: "
        f"state={before_restart} bytes, restored_usage={restored} bytes"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
