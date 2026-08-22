#!/usr/bin/env python3
"""Validate production Reality/TLS paths and their Remnawave node attribution."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from manage_canary import Api, DEFAULT_BASE_URL, DEFAULT_TOKEN_FILE, response, secure_write
from validate_canary import (
    CLIENT_CONTAINER,
    CLIENT_PORT,
    curl_through,
    docker,
    get_usage,
    get_user,
    subscription_short_id,
    wait_accounting,
    wait_client,
)

XRAY_CLIENT_CONFIG = Path(__file__).resolve().parent / "runtime" / "xray-client.json"
XRAY_CLIENT_IMAGE = "local/remnawave-node:3.3.2-singbox-hy2"

XRAY_ENDPOINTS = {
    "aaitr-reality": (24443, "Verizon"),
    "aaitr-tls": (443, "Verizon"),
    "csc-reality": (24444, "CStoneCloud"),
    "csc-tls": (443, "CStoneCloud"),
    "csc-aaitr-reality": (24445, "Verizon"),
    "csc-aaitr-tls": (443, "Verizon"),
}


def build_client_config(api: Api, user: dict, tag: str) -> None:
    short_id = subscription_short_id(user)
    subscription = api.request("GET", f"/api/sub/{short_id}/singbox")
    outbound = next(
        (
            item
            for item in subscription.get("outbounds", [])
            if item.get("type") == "vless" and item.get("tag") == tag
        ),
        None,
    )
    if outbound is None:
        raise RuntimeError(f"the sing-box subscription is missing {tag}")
    if outbound.get("server_port") != XRAY_ENDPOINTS[tag][0]:
        raise RuntimeError(f"the {tag} subscription uses an unexpected TCP port")
    tls = outbound.get("tls") or {}
    utls = tls.get("utls") or {}
    reality = tls.get("reality") or {}
    if reality.get("enabled"):
        security = "reality"
        security_settings = {
            "realitySettings": {
                "serverName": tls.get("server_name"),
                "fingerprint": utls.get("fingerprint", "chrome"),
                "publicKey": reality.get("public_key"),
                "shortId": reality.get("short_id"),
                "spiderX": "/",
            }
        }
    else:
        security = "tls"
        security_settings = {
            "tlsSettings": {
                "serverName": tls.get("server_name"),
                "fingerprint": utls.get("fingerprint", "chrome"),
                "alpn": tls.get("alpn", ["h2", "http/1.1"]),
            }
        }
    config = {
        "log": {"loglevel": "warning"},
        "inbounds": [
            {
                "tag": "socks-in",
                "listen": "127.0.0.1",
                "port": CLIENT_PORT,
                "protocol": "socks",
                "settings": {"udp": True},
            }
        ],
        "outbounds": [
            {
                "tag": tag,
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {
                            "address": outbound.get("server"),
                            "port": outbound.get("server_port"),
                            "users": [
                                {
                                    "id": outbound.get("uuid"),
                                    "encryption": "none",
                                    "flow": outbound.get("flow", ""),
                                }
                            ],
                        }
                    ]
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": security,
                    **security_settings,
                },
            }
        ],
    }
    secure_write(XRAY_CLIENT_CONFIG, json.dumps(config, separators=(",", ":")))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--tag", choices=tuple(XRAY_ENDPOINTS), required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-token-file", type=Path, default=DEFAULT_TOKEN_FILE)
    args = parser.parse_args()

    token = args.api_token_file.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError("API token file is empty")
    api = Api(args.base_url, token)
    expected_name = XRAY_ENDPOINTS[args.tag][1]
    node = next(
        (
            item
            for item in response(api.request("GET", "/api/nodes"))
            if item.get("name") == expected_name
        ),
        None,
    )
    versions = (node or {}).get("versions") or {}
    if (
        node is None
        or not node.get("isConnected")
        or versions.get("coreType") != "xray"
        or not str(versions.get("xray", "")).startswith("26.6.27")
    ):
        raise RuntimeError(f"the expected Xray node {expected_name} is not ready")

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
            f"{XRAY_CLIENT_CONFIG}:/etc/xray/config.json:ro",
            "--entrypoint",
            "/usr/local/bin/xray",
            XRAY_CLIENT_IMAGE,
            "run",
            "-c",
            "/etc/xray/config.json",
        )
        wait_client("Xray path")
        curl_through("https://speed.cloudflare.com/__down?bytes=262144", attempts=2)
        current = wait_accounting(api, args.username, baseline, node["uuid"])
    finally:
        docker("rm", "-f", CLIENT_CONTAINER, check=False)
        XRAY_CLIENT_CONFIG.unlink(missing_ok=True)

    print(
        f"PASS production Xray path {args.tag}: handshake succeeded and "
        f"Remnawave attributed {current - baseline} bytes to {expected_name}"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
