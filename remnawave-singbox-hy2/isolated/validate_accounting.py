#!/usr/bin/env python3
"""End-to-end checks for sing-box HY2 per-user accounting and lifecycle events."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable

from bootstrap_lab import ADMIN_ENV, DEFAULT_BASE_URL, PROXY_HEADERS, STATE, Api, read_env


def wait_for(label: str, predicate: Callable[[], Any], timeout: int = 90) -> Any:
    deadline = time.monotonic() + timeout
    last: Any = None
    while time.monotonic() < deadline:
        try:
            last = predicate()
            if last:
                return last
        except Exception as error:
            last = error
        time.sleep(2)
    raise RuntimeError(f"timed out waiting for {label}; last result: {last}")


def curl_through(port: int, count: int = 1, expect_success: bool = True) -> None:
    command = [
        "curl",
        "--silent",
        "--show-error",
        "--fail",
        "--connect-timeout",
        "3",
        "--max-time",
        "8",
        "--socks5-hostname",
        f"127.0.0.1:{port}",
        "--output",
        "/dev/null",
        "--header",
        "X-Forwarded-For: 127.0.0.1",
        "--header",
        "X-Forwarded-Proto: https",
        "--header",
        "X-Remnawave-Client-Type: browser",
        "http://hy2-panel:3000/",
    ]
    successes = 0
    for _ in range(count):
        result = subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        successes += result.returncode == 0
    if expect_success and successes != count:
        raise RuntimeError(f"only {successes}/{count} HY2 requests succeeded on SOCKS port {port}")
    if not expect_success and successes:
        raise RuntimeError(f"disabled user still completed {successes}/{count} HY2 requests")


def restart_lab_client(service: str) -> None:
    result = subprocess.run(
        ["docker", "compose", "--profile", "client", "restart", service],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise RuntimeError(f"failed to restart isolated client service {service}")


def get_user(api: Api, user_id: int) -> dict[str, Any]:
    return api.request("GET", f"/api/users/{user_id}")["response"]


def usage(api: Api, user_id: int) -> int:
    return int(get_user(api, user_id)["userTraffic"]["usedTrafficBytes"])


def reset_user_traffic(api: Api, user_id: int) -> None:
    api.request("POST", f"/api/users/{user_id}/actions/reset-traffic")
    wait_for(f"usage for user {user_id} to reset", lambda: usage(api, user_id) == 0, 60)
    if get_user(api, user_id)["status"] != "ACTIVE":
        api.request("POST", f"/api/users/{user_id}/actions/enable")
        wait_for(
            f"user {user_id} to become active",
            lambda: get_user(api, user_id)["status"] == "ACTIVE",
            60,
        )


def wait_usage(api: Api, user_id: int, baseline: int, timeout: int = 75) -> int:
    def increased_usage() -> int:
        current = usage(api, user_id)
        return current if current > baseline else 0

    return int(
        wait_for(
            f"usage for user {user_id} to exceed {baseline}",
            increased_usage,
            timeout,
        )
    )


def fetch_subscription(base_url: str, short_uuid: str, suffix: str = "") -> str:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/sub/{short_uuid}{suffix}",
        headers={
            "Accept": "text/plain",
            "User-Agent": "hy2-accounting-validator",
            **PROXY_HEADERS,
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def validate_subscriptions(base_url: str, user: dict[str, Any]) -> None:
    expected_password = user["vlessUuid"]

    singbox = json.loads(fetch_subscription(base_url, user["shortUuid"], "/singbox"))
    singbox_hy2 = next(
        (item for item in singbox.get("outbounds", []) if item.get("type") == "hysteria2"),
        None,
    )
    if not singbox_hy2:
        raise RuntimeError("sing-box subscription is missing the Hysteria2 outbound")
    if (
        singbox_hy2.get("server") != "127.0.0.1"
        or singbox_hy2.get("server_port") != 35443
        or singbox_hy2.get("password") != expected_password
        or (singbox_hy2.get("tls") or {}).get("server_name") != "verizon.bigpandas.top"
    ):
        raise RuntimeError("sing-box Hysteria2 subscription fields do not match the managed host")

    mihomo = fetch_subscription(base_url, user["shortUuid"], "/mihomo")
    for marker in (
        "type: hysteria2",
        "server: 127.0.0.1",
        "port: 35443",
        f"password: {expected_password}",
        "sni: verizon.bigpandas.top",
    ):
        if marker not in mihomo:
            raise RuntimeError(f"Mihomo Hysteria2 subscription is missing marker: {marker}")

    encoded_links = fetch_subscription(base_url, user["shortUuid"]).strip()
    decoded_links = base64.b64decode(encoded_links + "=" * (-len(encoded_links) % 4)).decode(
        "utf-8"
    )
    matching_links = [line for line in decoded_links.splitlines() if line.startswith("hysteria2://")]
    if len(matching_links) != 1:
        raise RuntimeError("base64 subscription does not contain exactly one Hysteria2 share link")
    share_link = matching_links[0]
    for marker in (
        expected_password,
        "@127.0.0.1:35443/",
        "sni=verizon.bigpandas.top",
        "#hy2-accounting-lab",
    ):
        if marker not in share_link:
            raise RuntimeError("Hysteria2 share link fields do not match the managed host")

    print("PASS sing-box, Mihomo and share-link subscription output")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    state = json.loads(STATE.read_text(encoding="utf-8"))
    admin = read_env(ADMIN_ENV)
    api = Api(args.base_url)
    api.authenticate(admin["ADMIN_USERNAME"], admin["ADMIN_PASSWORD"])
    node_uuid = state["nodeUuid"]
    user_a, user_b = state["users"]

    def online_node() -> dict[str, Any] | None:
        node = api.request("GET", f"/api/nodes/{node_uuid}")["response"]
        versions = node.get("versions") or {}
        if (
            node.get("isConnected")
            and versions.get("coreType") == "singbox"
            and str(versions.get("singbox", "")).startswith("1.13.15")
        ):
            return node
        return None

    wait_for("sing-box node 1.13.15 to be connected", online_node, 120)
    validate_subscriptions(args.base_url, user_a)
    reset_user_traffic(api, user_a["id"])
    reset_user_traffic(api, user_b["id"])
    restart_lab_client("hy2-client-a")
    restart_lab_client("hy2-client-b")
    time.sleep(2)
    curl_through(20880)
    curl_through(20881)

    before_a = usage(api, user_a["id"])
    before_b = usage(api, user_b["id"])
    curl_through(20880, count=18)
    curl_through(20881, count=4)
    after_a = wait_usage(api, user_a["id"], before_a)
    after_b = wait_usage(api, user_b["id"], before_b)
    delta_a = after_a - before_a
    delta_b = after_b - before_b
    if delta_a <= delta_b * 2:
        raise RuntimeError(f"per-user deltas are not isolated as expected: A={delta_a}, B={delta_b}")
    print(f"PASS per-user accounting: A={delta_a} bytes, B={delta_b} bytes")

    reload_baseline = usage(api, user_a["id"])
    curl_through(20880, count=5)
    api.request("POST", f"/api/nodes/{node_uuid}/actions/restart", {"forceRestart": True})
    wait_for("node reconnect after core restart", online_node, 120)
    reload_usage = wait_usage(api, user_a["id"], reload_baseline)
    print(f"PASS reload preservation: {reload_usage - reload_baseline} bytes retained")

    api.request("POST", f"/api/users/{user_b['id']}/actions/disable")
    wait_for(
        "user B to become disabled",
        lambda: get_user(api, user_b["id"])["status"] == "DISABLED",
        60,
    )
    time.sleep(4)
    curl_through(20881, expect_success=False)
    api.request("POST", f"/api/users/{user_b['id']}/actions/enable")
    wait_for(
        "user B to become active",
        lambda: get_user(api, user_b["id"])["status"] == "ACTIVE",
        60,
    )
    restart_lab_client("hy2-client-b")
    time.sleep(2)
    curl_through(20881)
    print("PASS dynamic disable and re-enable")

    reset_user_traffic(api, user_b["id"])
    quota_baseline = usage(api, user_b["id"])
    curl_through(20881, count=10)
    wait_usage(api, user_b["id"], quota_baseline)
    wait_for(
        "1 MiB quota to limit user B",
        lambda: get_user(api, user_b["id"])["status"] == "LIMITED",
        90,
    )
    time.sleep(4)
    restart_lab_client("hy2-client-b")
    time.sleep(2)
    curl_through(20881, expect_success=False)
    print("PASS Remnawave quota enforcement from sing-box HY2 usage")
    return 0


if __name__ == "__main__":
    sys.exit(main())
