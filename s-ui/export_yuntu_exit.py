#!/usr/bin/env python3
"""Render the YunTu pure-exit sing-box config from the production s-ui DB."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from sui_runtime import fail


ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "db" / "s-ui.db"
DEFAULT_OUTPUT = ROOT / "yuntu-exit" / "config.json"
CERTIFICATE_PATH = "/etc/sing-box/cert/fullchain.pem"
KEY_PATH = "/etc/sing-box/cert/privkey.pem"


def decode_json(value: Any, fallback: Any = None) -> Any:
    if value is None:
        return fallback
    if isinstance(value, bytes):
        value = value.decode()
    if isinstance(value, str):
        return json.loads(value)
    return value


def load_rows(connection: sqlite3.Connection) -> tuple[list[dict], dict, dict]:
    connection.row_factory = sqlite3.Row
    clients = []
    for row in connection.execute(
        """
        select name, config
        from clients
        where enable = 1 and `group` = 'aaitr-production'
        order by id
        """
    ):
        config = decode_json(row["config"], {})
        vless = config.get("vless") or {}
        hy2 = config.get("hysteria2") or {}
        if not vless.get("uuid") or not hy2.get("password"):
            fail(f"production client {row['name']} is missing protocol credentials")
        clients.append(
            {
                "name": row["name"],
                "vless_uuid": vless["uuid"],
                "vless_flow": vless.get("flow", "xtls-rprx-vision"),
                "hy2_password": hy2["password"],
            }
        )
    if not clients:
        fail("no enabled aaitr-production clients found")

    tls_rows = {
        row["id"]: row
        for row in connection.execute("select id, server, client from tls order by id")
    }
    if 1 not in tls_rows or 2 not in tls_rows:
        fail("expected TLS rows 1 (Reality) and 2 (certificate TLS)")
    reality_server = decode_json(tls_rows[1]["server"], {})
    certificate_server = decode_json(tls_rows[2]["server"], {})
    return clients, reality_server, certificate_server


def build_config(
    clients: list[dict],
    reality_server: dict,
    certificate_server: dict,
) -> dict:
    reality = reality_server.get("reality") or {}
    handshake = reality.get("handshake") or {}
    short_id = reality.get("short_id") or []
    if isinstance(short_id, str):
        short_id = [short_id]
    if not reality.get("private_key") or not short_id:
        fail("Reality server key or short_id is missing")
    if not handshake.get("server") or not handshake.get("server_port"):
        fail("Reality handshake target is missing")

    server_name = certificate_server.get("server_name") or "yuntu.bigpandas.top"

    return {
        "log": {"level": "warn", "timestamp": True},
        "inbounds": [
            {
                "type": "vless",
                "tag": "yuntu-exit-reality",
                "listen": "0.0.0.0",
                "listen_port": 1443,
                "users": [
                    {
                        "name": client["name"],
                        "uuid": client["vless_uuid"],
                        "flow": client["vless_flow"],
                    }
                    for client in clients
                ],
                "tls": {
                    "enabled": True,
                    "server_name": reality_server.get("server_name", handshake["server"]),
                    "reality": {
                        "enabled": True,
                        "handshake": {
                            "server": handshake["server"],
                            "server_port": int(handshake["server_port"]),
                        },
                        "private_key": reality["private_key"],
                        "short_id": short_id,
                    },
                },
            },
            {
                "type": "hysteria2",
                "tag": "yuntu-exit-hy2",
                "listen": "0.0.0.0",
                "listen_port": 2443,
                "up_mbps": 100,
                "down_mbps": 100,
                "users": [
                    {"name": client["name"], "password": client["hy2_password"]}
                    for client in clients
                ],
                "tls": {
                    "enabled": True,
                    "server_name": server_name,
                    "certificate_path": CERTIFICATE_PATH,
                    "key_path": KEY_PATH,
                },
            },
        ],
        "outbounds": [{"type": "direct", "tag": "direct"}],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not DATABASE.exists():
        fail("s-ui database is missing")
    with sqlite3.connect(DATABASE) as connection:
        clients, reality_server, certificate_server = load_rows(connection)
    config = build_config(clients, reality_server, certificate_server)
    args.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    args.output.write_text(json.dumps(config, indent=2, sort_keys=False) + "\n")
    args.output.chmod(0o600)
    print(f"rendered YunTu exit config: {len(clients)} production clients, 2 inbounds")


if __name__ == "__main__":
    main()
