#!/usr/bin/env python3
"""Promote the validated s-ui canary inbounds to production endpoints."""

from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("sui_runtime.py")
SPEC = importlib.util.spec_from_file_location("sui_runtime", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load the migration module")
RUNTIME = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNTIME)


PROFILES = {
    "canary-reality": {
        "tag": "yuntu-reality",
        "listen": "127.0.0.1",
        "listen_port": 31443,
        "addrs": [{"server": "cstonecloud.bigpandas.top", "server_port": 443, "remark": "-reality"}],
    },
    "canary-hysteria2": {
        "tag": "yuntu-hysteria2",
        "listen": "0.0.0.0",
        "listen_port": 32443,
        "addrs": [{"server": "cstonecloud.bigpandas.top", "server_port": 443, "remark": "-hy2"}],
    },
    "canary-socks5": {
        "tag": "aaitr-socks5",
        "listen": "0.0.0.0",
        "listen_port": 1080,
        "addrs": [{"server": "verizon.bigpandas.top", "server_port": 1080, "remark": "-socks5"}],
    },
}


def main() -> None:
    sui = RUNTIME.SUI()
    sui.login()
    summaries = sui.get("inbounds") or []
    by_tag = {item.get("tag"): item for item in summaries}

    tls_rows = sui.get("tls") or []
    production_tls = next(
        (item for item in tls_rows if item.get("name") in {"canary-tls", "yuntu-tls"}),
        None,
    )
    if production_tls is None:
        raise RuntimeError("missing certificate TLS profile")
    tls_full = next(
        (item for item in tls_rows if int(item.get("id", 0)) == int(production_tls["id"])),
        None,
    )
    if tls_full is None:
        raise RuntimeError("unable to load certificate TLS profile")
    tls_full["name"] = "yuntu-tls"
    tls_full.setdefault("server", {})["certificate_path"] = (
        "/app/cert/live/s-ui-domains/fullchain.pem"
    )
    tls_full.setdefault("server", {})["key_path"] = (
        "/app/cert/live/s-ui-domains/privkey.pem"
    )
    tls_full.setdefault("server", {})["server_name"] = "cstonecloud.bigpandas.top"
    tls_full.setdefault("client", {})["server_name"] = "cstonecloud.bigpandas.top"
    sui.save("tls", tls_full, action="edit")
    print("promoted TLS SNI: cstonecloud.bigpandas.top")

    for old_tag, desired in PROFILES.items():
        current = by_tag.get(old_tag) or by_tag.get(desired["tag"])
        if current is None:
            raise RuntimeError(f"missing inbound for {desired['tag']}")
        rows = sui.get("inbounds", {"id": int(current["id"])}) or []
        if len(rows) != 1:
            raise RuntimeError(f"unable to load inbound for {desired['tag']}")
        inbound = rows[0]
        inbound.update(desired)
        sui.save("inbounds", inbound, action="edit")
        print(
            f"promoted {desired['tag']}: "
            f"{desired['listen']}:{desired['listen_port']} -> "
            f"{desired['addrs'][0]['server']}:{desired['addrs'][0]['server_port']}"
        )

    for summary in sui.get("clients") or []:
        if summary.get("group") != "aaitr-canary":
            continue
        rows = sui.get("clients", {"id": int(summary["id"])}) or []
        if len(rows) != 1:
            raise RuntimeError("unable to load a production client")
        client = rows[0]
        client["group"] = "aaitr-production"
        sui.save("clients", client, action="edit")
    print("promoted client group: aaitr-production")

    final = {item.get("tag") for item in (sui.get("inbounds") or [])}
    missing = {item["tag"] for item in PROFILES.values()} - final
    if missing:
        raise RuntimeError(f"production inbounds are missing: {sorted(missing)}")
    print("s-ui production endpoint promotion: complete")


if __name__ == "__main__":
    main()
