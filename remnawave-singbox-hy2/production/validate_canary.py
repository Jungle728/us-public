#!/usr/bin/env python3
"""Validate a production HY2 canary without printing subscription credentials."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

from manage_canary import (
    Api,
    DEFAULT_BASE_URL,
    DEFAULT_TOKEN_FILE,
    ROOT,
    response,
    secure_write,
)


CLIENT_CONTAINER = "remnawave-hy2-canary-client"
CLIENT_CONFIG = ROOT / "runtime" / "canary-client.json"
CLIENT_PORT = 20882
HY2_ENDPOINTS = {
    "aaitr-hy2": 32443,
    "csc-hy2": 2443,
    "csc-aaitr-hy2": 443,
    "csc-aaitr-hy2-singbox-test": 444,
}
HY2_NODE_NAMES = {
    "aaitr-hy2": "Verizon HY2 sing-box",
    "csc-hy2": "CStoneCloud HY2 sing-box",
    "csc-aaitr-hy2": "Verizon HY2 sing-box",
    "csc-aaitr-hy2-singbox-test": "Verizon HY2 sing-box",
}
CLIENT_IMAGE = (
    "ghcr.io/sagernet/sing-box:v1.13.15@"
    "sha256:4aa30343cea6b5407960f99b36ffa653403d9ddcb1fc2800c9fb85a1bd77d6d8"
)


def docker(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", *args],
        check=check,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def get_user(api: Api, username: str) -> dict[str, Any]:
    return response(api.request("GET", f"/api/users/by-username/{urllib.parse.quote(username)}"))


def get_usage(user: dict[str, Any]) -> tuple[int, str | None]:
    traffic = user.get("userTraffic") or {}
    return int(traffic.get("usedTrafficBytes") or 0), traffic.get("lastConnectedNodeUuid")


def subscription_short_id(user: dict[str, Any]) -> str:
    path = urllib.parse.urlparse(user["subscriptionUrl"]).path.rstrip("/")
    value = path.split("/")[-1]
    if not value:
        raise RuntimeError("the user subscription URL has no short identifier")
    return value


def build_client_config(api: Api, user: dict[str, Any], tag: str) -> None:
    short_id = subscription_short_id(user)
    subscription = api.request("GET", f"/api/sub/{short_id}/singbox")
    outbound = next(
        (
            item
            for item in subscription.get("outbounds", [])
            if item.get("type") == "hysteria2" and item.get("tag") == tag
        ),
        None,
    )
    if outbound is None:
        raise RuntimeError(f"the sing-box subscription is missing {tag}")
    if outbound.get("server_port") != HY2_ENDPOINTS[tag]:
        raise RuntimeError(f"the {tag} subscription uses an unexpected UDP port")
    if not outbound.get("password"):
        raise RuntimeError("the canary subscription has no HY2 password")
    # The full generated subscription defines a DNS server named ``local``.
    # This single-outbound test client deliberately uses the container's
    # system resolver instead of copying the rest of the user's routing stack.
    outbound.pop("domain_resolver", None)

    config = {
        "log": {"level": "warn", "timestamp": True},
        "inbounds": [
            {
                "type": "socks",
                "tag": "socks-in",
                "listen": "127.0.0.1",
                "listen_port": CLIENT_PORT,
            }
        ],
        "outbounds": [outbound],
        "route": {"final": tag},
    }
    secure_write(CLIENT_CONFIG, json.dumps(config, separators=(",", ":")))


def curl_through(url: str, attempts: int = 1) -> None:
    command = [
        "curl",
        "--silent",
        "--show-error",
        "--fail",
        "--connect-timeout",
        "5",
        "--max-time",
        "20",
        "--socks5-hostname",
        f"127.0.0.1:{CLIENT_PORT}",
        "--output",
        "/dev/null",
        url,
    ]
    for _ in range(attempts):
        result = subprocess.run(
            command,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            raise RuntimeError("a request through the HY2 canary failed")


def wait_client(label: str = "HY2 canary") -> None:
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        try:
            curl_through("https://cp.cloudflare.com/generate_204")
            return
        except RuntimeError:
            time.sleep(2)
    raise RuntimeError(f"the {label} client did not become ready")


def wait_accounting(api: Api, username: str, baseline: int, node_uuid: str) -> int:
    deadline = time.monotonic() + 90
    latest_usage = baseline
    latest_node: str | None = None
    while time.monotonic() < deadline:
        latest_usage, latest_node = get_usage(get_user(api, username))
        if latest_usage > baseline and latest_node == node_uuid:
            return latest_usage
        time.sleep(2)
    raise RuntimeError(
        "Remnawave did not attribute increased usage to the managed sing-box node "
        f"within 90 seconds (usage_increased={latest_usage > baseline}, "
        f"node_matched={latest_node == node_uuid})"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument(
        "--tag",
        choices=tuple(HY2_ENDPOINTS),
        default="csc-aaitr-hy2-singbox-test",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-token-file", type=Path, default=DEFAULT_TOKEN_FILE)
    args = parser.parse_args()

    token = args.api_token_file.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError("API token file is empty")
    api = Api(args.base_url, token)
    node = next(
        (
            item
            for item in response(api.request("GET", "/api/nodes"))
            if item.get("name") == HY2_NODE_NAMES[args.tag]
        ),
        None,
    )
    if node is None:
        raise RuntimeError(f"the expected node {HY2_NODE_NAMES[args.tag]} was not found")
    versions = node.get("versions") or {}
    if (
        not node.get("isConnected")
        or versions.get("coreType") != "singbox"
        or not str(versions.get("singbox", "")).startswith("1.13.15")
    ):
        raise RuntimeError(f"the expected node {HY2_NODE_NAMES[args.tag]} is not ready")
    user = get_user(api, args.username)
    if user.get("status") != "ACTIVE":
        raise RuntimeError("the selected validation user is not active")

    baseline, _ = get_usage(user)
    build_client_config(api, user, args.tag)
    docker("rm", "-f", CLIENT_CONTAINER, check=False)
    try:
        docker(
            "run",
            "--detach",
            "--name",
            CLIENT_CONTAINER,
            "--network",
            "host",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--volume",
            f"{CLIENT_CONFIG}:/etc/sing-box/config.json:ro",
            CLIENT_IMAGE,
            "run",
            "-c",
            "/etc/sing-box/config.json",
        )
        wait_client()
        curl_through("https://speed.cloudflare.com/__down?bytes=524288", attempts=4)
        current = wait_accounting(api, args.username, baseline, node["uuid"])
    finally:
        docker("rm", "-f", CLIENT_CONTAINER, check=False)
        CLIENT_CONFIG.unlink(missing_ok=True)

    print(
        f"PASS production HY2 path {args.tag}: subscription handshake succeeded and "
        f"Remnawave attributed {current - baseline} bytes to the managed sing-box node"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
