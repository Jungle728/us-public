#!/usr/bin/env python3
"""Enable the production Shadowsocks 2022 inbound and reconcile its users."""

from __future__ import annotations

import base64
import secrets

from sui_runtime import SUI, fail


TAG = "yuntu-shadowsocks"
METHOD = "2022-blake3-aes-128-gcm"
LISTEN_PORT = 34443
ADDRS = [
    {
        "server": "yuntu.bigpandas.top",
        "server_port": 10443,
        "remark": "-yuntu-aaitr",
    },
    {
        "server": "proxy.bigpandas.top",
        "server_port": LISTEN_PORT,
        "remark": "-aaitr-exit",
    },
    {
        "server": "yuntu.bigpandas.top",
        "server_port": 10444,
        "remark": "-yuntu-exit",
    },
]


def random_key() -> str:
    return base64.b64encode(secrets.token_bytes(16)).decode()


def validate_client(client: dict) -> None:
    password = ((client.get("config") or {}).get("shadowsocks16") or {}).get(
        "password", ""
    )
    try:
        decoded = base64.b64decode(password, validate=True)
    except Exception as exc:  # noqa: BLE001
        fail(
            f"production client {client.get('name', 'unknown')} has an invalid "
            f"Shadowsocks 2022 key: {type(exc).__name__}"
        )
    if len(decoded) != 16:
        fail(
            f"production client {client.get('name', 'unknown')} has an invalid "
            "Shadowsocks 2022 key length"
        )


def inbound_payload(password: str, inbound_id: int = 0) -> dict:
    return {
        "id": inbound_id,
        "type": "shadowsocks",
        "tag": TAG,
        "listen": "0.0.0.0",
        "listen_port": LISTEN_PORT,
        "method": METHOD,
        "password": password,
        "managed": False,
        "multiplex": {},
        "tls_id": 0,
        "addrs": ADDRS,
        "out_json": {},
    }


def main() -> None:
    sui = SUI()
    sui.login()

    summaries = sui.get("clients") or []
    production = [
        summary
        for summary in summaries
        if summary.get("group") == "aaitr-production"
    ]
    if not production:
        fail("no aaitr-production clients found")

    clients = []
    for summary in production:
        rows = sui.get("clients", {"id": int(summary["id"])}) or []
        if len(rows) != 1:
            fail("unable to load a production client")
        validate_client(rows[0])
        clients.append(rows[0])

    by_tag = {
        item.get("tag"): item
        for item in (sui.get("inbounds") or [])
    }
    current = by_tag.get(TAG)
    if current is None:
        init_users = ",".join(str(int(client["id"])) for client in clients)
        sui.save("inbounds", inbound_payload(random_key()), init_users=init_users)
        print(f"created {TAG} for {len(clients)} production clients")
    else:
        rows = sui.get("inbounds", {"id": int(current["id"])}) or []
        if len(rows) != 1:
            fail(f"unable to load {TAG}")
        inbound = rows[0]
        password = inbound.get("password", "")
        try:
            decoded = base64.b64decode(password, validate=True)
        except Exception as exc:  # noqa: BLE001
            fail(f"existing Shadowsocks master key is invalid: {type(exc).__name__}")
        if len(decoded) != 16:
            fail("existing Shadowsocks master key has an invalid length")
        sui.save(
            "inbounds",
            inbound_payload(password, int(inbound["id"])),
            action="edit",
        )
        print(f"updated {TAG} without rotating its master key")

    refreshed = {
        item.get("tag"): item
        for item in (sui.get("inbounds") or [])
    }
    if TAG not in refreshed:
        fail(f"s-ui did not persist {TAG}")
    inbound_id = int(refreshed[TAG]["id"])

    reconciled = 0
    for client in clients:
        inbound_ids = [int(value) for value in (client.get("inbounds") or [])]
        if inbound_id in inbound_ids:
            continue
        client["inbounds"] = inbound_ids + [inbound_id]
        sui.save("clients", client, action="edit")
        reconciled += 1

    print(f"Shadowsocks production users checked: {len(clients)}")
    print(f"Shadowsocks client assignments repaired: {reconciled}")
    print("Shadowsocks master key: retained and hidden")


if __name__ == "__main__":
    main()
