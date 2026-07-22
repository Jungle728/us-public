#!/usr/bin/env python3
"""Publish desktop nodes for YunTu relay, YunTu exit, and AaITR exit paths."""

from __future__ import annotations

import json
import sqlite3
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from sui_runtime import fail


ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "db" / "s-ui.db"
BACKUPS = ROOT / "db" / "backups"

DESKTOP_ADDRS = {
    "yuntu-reality": [
        {
            "name": "yuntu-aaitr-reality",
            "remark": "-yuntu-aaitr",
            "server": "yuntu.bigpandas.top",
            "server_port": 443,
        },
        {
            "name": "aaitr-exit-reality",
            "remark": "-aaitr-exit",
            "server": "proxy.bigpandas.top",
            "server_port": 443,
        },
        {
            "name": "yuntu-exit-reality",
            "remark": "-yuntu-exit",
            "server": "yuntu.bigpandas.top",
            "server_port": 1443,
        },
    ],
    "yuntu-hysteria2": [
        {
            "name": "yuntu-aaitr-hy2",
            "remark": "-yuntu-aaitr",
            "server": "yuntu.bigpandas.top",
            "server_port": 443,
        },
        {
            "name": "aaitr-exit-hy2",
            "remark": "-aaitr-exit",
            "server": "proxy.bigpandas.top",
            "server_port": 32443,
        },
        {
            "name": "yuntu-exit-hy2",
            "remark": "-yuntu-exit",
            "server": "yuntu.bigpandas.top",
            "server_port": 2443,
        },
    ],
    "yuntu-anytls": [
        {
            "name": "yuntu-aaitr-anytls",
            "remark": "-yuntu-aaitr",
            "server": "yuntu.bigpandas.top",
            "server_port": 8443,
        },
        {
            "name": "aaitr-exit-anytls",
            "remark": "-aaitr-exit",
            "server": "proxy.bigpandas.top",
            "server_port": 33443,
        },
        {
            "name": "yuntu-exit-anytls",
            "remark": "-yuntu-exit",
            "server": "yuntu.bigpandas.top",
            "server_port": 9443,
        },
    ],
}

FORWARD_PROXY_TAGS = {"yuntu-socks5", "yuntu-http", "aaitr-https"}

SCHEME_TAGS = {
    "vless": "yuntu-reality",
    "hysteria2": "yuntu-hysteria2",
    "anytls": "yuntu-anytls",
}


def retarget_uri(uri: str, server: str, port: int, name: str) -> str:
    parts = urllib.parse.urlsplit(uri)
    if "@" not in parts.netloc:
        fail("subscription URI is missing credentials")
    credential = parts.netloc.rsplit("@", 1)[0]
    if parts.scheme not in SCHEME_TAGS:
        fail(f"unexpected desktop URI scheme: {parts.scheme}")
    return urllib.parse.urlunsplit(
        (
            parts.scheme,
            f"{credential}@{server}:{port}",
            parts.path,
            parts.query,
            name,
        )
    )


def desktop_links(existing_links: list[dict]) -> list[dict]:
    by_scheme = {}
    for link in existing_links:
        uri = str(link.get("uri", ""))
        if "://" not in uri:
            continue
        scheme = uri.split("://", 1)[0]
        if scheme in SCHEME_TAGS:
            by_scheme[scheme] = uri
    missing = set(SCHEME_TAGS) - set(by_scheme)
    if missing:
        fail(f"client links are missing desktop schemes: {sorted(missing)}")

    desired = []
    for scheme, tag in SCHEME_TAGS.items():
        base = by_scheme[scheme]
        for addr in DESKTOP_ADDRS[tag]:
            name = str(addr["name"])
            desired.append(
                {
                    "remark": name,
                    "type": "local",
                    "uri": retarget_uri(
                        base,
                        str(addr["server"]),
                        int(addr["server_port"]),
                        name,
                    ),
                }
            )
    return desired


def backup_database() -> Path:
    BACKUPS.mkdir(mode=0o700, exist_ok=True)
    BACKUPS.chmod(0o700)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = BACKUPS / f"s-ui-before-desktop-direct-{stamp}.db"
    with sqlite3.connect(DATABASE) as source, sqlite3.connect(destination) as target:
        source.backup(target)
    destination.chmod(0o600)
    return destination


def main() -> None:
    if not DATABASE.exists():
        fail("s-ui database is missing")
    backup = backup_database()
    with sqlite3.connect(DATABASE) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "select id, type, tag, addrs from inbounds order by id"
        ).fetchall()
        by_tag = {row["tag"]: row for row in rows}
        missing = set(DESKTOP_ADDRS) - set(by_tag)
        if missing:
            fail(f"missing desktop inbounds: {sorted(missing)}")

        for tag, addrs in DESKTOP_ADDRS.items():
            connection.execute(
                "update inbounds set addrs = ? where tag = ?",
                (sqlite3.Binary(json.dumps(addrs, separators=(",", ":")).encode()), tag),
            )
            print(f"updated {tag}: {len(addrs)} subscription addresses")

        proxy_tags = {
            row["tag"]
            for row in rows
            if row["tag"] in FORWARD_PROXY_TAGS and row["addrs"]
        }
        if proxy_tags != FORWARD_PROXY_TAGS:
            fail("forward proxy inbounds are incomplete")

        clients = connection.execute(
            "select name, `group`, inbounds, links from clients order by id"
        ).fetchall()
        production_count = 0
        proxy_count = 0
        for client in clients:
            inbound_ids = json.loads(client["inbounds"] or "[]")
            if client["group"] == "aaitr-production":
                production_count += 1
                if inbound_ids != [1, 2, 3]:
                    fail(f"unexpected desktop inbounds for {client['name']}")
                current_links = json.loads(client["links"] or "[]")
                links = desktop_links(current_links)
                connection.execute(
                    "update clients set links = ? where name = ?",
                    (
                        sqlite3.Binary(
                            json.dumps(links, separators=(",", ":")).encode()
                        ),
                        client["name"],
                    ),
                )
            if client["group"] == "forward-proxy":
                proxy_count += 1
                if inbound_ids != [4, 5, 6]:
                    fail(f"unexpected forward-proxy inbounds for {client['name']}")
        if production_count == 0:
            fail("no aaitr-production clients found")
        if proxy_count != 1:
            fail(f"expected one forward-proxy client, found {proxy_count}")

        connection.commit()

    print(f"production desktop clients checked: {production_count}")
    print("forward proxy client left unchanged")
    print(f"database backup: {backup}")


if __name__ == "__main__":
    main()
