#!/usr/bin/env python3
"""Verify the three Shadowsocks routes without printing credentials or URIs."""

from __future__ import annotations

import json
import secrets
import socket
import subprocess
import tempfile
import time
from pathlib import Path

from sui_runtime import (
    AAITR_IPV4,
    SUI,
    fail,
    link_route_marker,
    subscription_link_lines,
)


YUNTU_IPV4 = "154.23.242.22"
CLIENT_IMAGE = "proxy-subscription-sing-box:local"


def available_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def wait_for_listener(port: int, process: subprocess.Popen) -> None:
    for _ in range(50):
        if process.poll() is not None:
            fail("temporary Shadowsocks client stopped before becoming ready")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    fail("temporary Shadowsocks client did not become ready")


def check_route(sui: SUI, marker: str, link: str) -> None:
    outbound = sui.link_convert(link)
    if outbound.get("type") != "shadowsocks":
        fail(f"{marker} did not convert to a Shadowsocks outbound")
    outbound["tag"] = "ss-egress"
    port = available_port()
    config = {
        "log": {"level": "warn", "timestamp": True},
        "inbounds": [
            {
                "type": "mixed",
                "tag": "local-test",
                "listen": "127.0.0.1",
                "listen_port": port,
            }
        ],
        "outbounds": [outbound],
        "route": {"final": "ss-egress"},
    }
    expected = YUNTU_IPV4 if marker == "yuntu-exit" else AAITR_IPV4
    container = f"verify-ss-egress-{secrets.token_hex(4)}"
    with tempfile.TemporaryDirectory(prefix="verify-ss-egress-") as directory:
        path = Path(directory) / "config.json"
        path.write_text(json.dumps(config, separators=(",", ":")))
        path.chmod(0o600)
        process = subprocess.Popen(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "host",
                "--name",
                container,
                "-v",
                f"{path}:/etc/sing-box/config.json:ro",
                CLIENT_IMAGE,
                "run",
                "-c",
                "/etc/sing-box/config.json",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            wait_for_listener(port, process)
            result = subprocess.run(
                [
                    "curl",
                    "-4fsS",
                    "--max-time",
                    "20",
                    "--socks5-hostname",
                    f"127.0.0.1:{port}",
                    "https://api.ipify.org",
                ],
                capture_output=True,
                text=True,
                timeout=25,
                check=False,
            )
            if result.returncode != 0:
                fail(f"{marker} Shadowsocks exit query failed")
            actual = result.stdout.strip()
            if actual != expected:
                fail(f"{marker} Shadowsocks exit IP is unexpected")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            subprocess.run(
                ["docker", "rm", "-f", container],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
    print(f"verified {marker} Shadowsocks egress: {expected}")


def main() -> None:
    sui = SUI()
    sui.login()
    production = [
        item
        for item in (sui.get("clients") or [])
        if item.get("group") == "aaitr-production"
    ]
    if not production:
        fail("no production client found")
    links = {
        link_route_marker(link): link
        for link in subscription_link_lines(production[0]["name"])
        if link.lower().startswith("ss://")
    }
    expected_markers = {"yuntu-aaitr", "aaitr-exit", "yuntu-exit"}
    if set(links) != expected_markers:
        fail("the production subscription is missing a Shadowsocks route")
    for marker in ("yuntu-aaitr", "aaitr-exit", "yuntu-exit"):
        check_route(sui, marker, links[marker])
    print("Shadowsocks route egress verification: complete")


if __name__ == "__main__":
    main()
