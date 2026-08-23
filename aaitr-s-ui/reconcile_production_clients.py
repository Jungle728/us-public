#!/usr/bin/env python3
"""Keep production users on Reality and Hysteria2 only."""

from __future__ import annotations

from sui_runtime import SUI, fail


PRODUCTION_TAGS = {
    "yuntu-reality",
    "yuntu-hysteria2",
}
FORWARD_PROXY_TAG = "aaitr-socks5"
LEGACY_TAGS = {"yuntu-anytls", "yuntu-shadowsocks", "yuntu-http", "aaitr-https"}


def reconcile_production_clients() -> int:
    sui = SUI()
    sui.login()
    inbounds = sui.get("inbounds") or []
    by_tag = {item.get("tag"): item for item in inbounds}
    changed = 0
    if FORWARD_PROXY_TAG not in by_tag and "yuntu-socks5" in by_tag:
        legacy = sui.get("inbounds", {"id": int(by_tag["yuntu-socks5"]["id"])}) or []
        if len(legacy) != 1:
            fail("unable to load the existing SOCKS5 inbound")
        socks = legacy[0]
        socks.update(
            {
                "tag": FORWARD_PROXY_TAG,
                "listen": "0.0.0.0",
                "listen_port": 1080,
                "addrs": [
                    {
                        "server": "verizon.bigpandas.top",
                        "server_port": 1080,
                        "remark": "-socks5",
                    }
                ],
            }
        )
        sui.save("inbounds", socks, action="edit")
        changed += 1
        inbounds = sui.get("inbounds") or []
        by_tag = {item.get("tag"): item for item in inbounds}

    proxy_summary = by_tag.get(FORWARD_PROXY_TAG)
    if proxy_summary is not None:
        proxy_rows = sui.get("inbounds", {"id": int(proxy_summary["id"])}) or []
        if len(proxy_rows) != 1:
            fail("unable to load the AaITR SOCKS5 inbound")
        proxy_inbound = proxy_rows[0]
        desired_proxy_addrs = [
            {
                "server": "verizon.bigpandas.top",
                "server_port": 1080,
                "remark": "-socks5",
            }
        ]
        if (
            proxy_inbound.get("listen") != "0.0.0.0"
            or int(proxy_inbound.get("listen_port", 0)) != 1080
            or proxy_inbound.get("addrs") != desired_proxy_addrs
        ):
            proxy_inbound["listen"] = "0.0.0.0"
            proxy_inbound["listen_port"] = 1080
            proxy_inbound["addrs"] = desired_proxy_addrs
            sui.save("inbounds", proxy_inbound, action="edit")
            changed += 1
            inbounds = sui.get("inbounds") or []
            by_tag = {item.get("tag"): item for item in inbounds}

    missing = (PRODUCTION_TAGS | {FORWARD_PROXY_TAG}) - set(by_tag)
    if missing:
        fail(f"production inbounds are missing: {sorted(missing)}")
    desired = sorted(int(by_tag[tag]["id"]) for tag in PRODUCTION_TAGS)
    proxy_id = int(by_tag[FORWARD_PROXY_TAG]["id"])

    production = [
        item
        for item in (sui.get("clients") or [])
        if item.get("group") == "aaitr-production"
    ]
    if not production:
        fail("no aaitr-production clients found")
    for summary in production:
        rows = sui.get("clients", {"id": int(summary["id"])}) or []
        if len(rows) != 1:
            fail("unable to load a production client")
        client = rows[0]
        current = sorted(int(value) for value in (client.get("inbounds") or []))
        current_config = client.get("config") or {}
        next_config = dict(current_config)
        for key in ("http", "mixed", "shadowsocks", "shadowsocks16", "anytls"):
            next_config.pop(key, None)
        if current == desired and next_config == current_config:
            continue
        client["inbounds"] = desired
        client["config"] = next_config
        sui.save("clients", client, action="edit")
        changed += 1

    for summary in sui.get("clients") or []:
        if summary.get("group") != "forward-proxy":
            continue
        rows = sui.get("clients", {"id": int(summary["id"])}) or []
        if len(rows) != 1:
            fail("unable to load the forward proxy client")
        client = rows[0]
        config = client.get("config") or {}
        if "socks" not in config:
            fail("forward proxy client has no SOCKS5 credentials")
        next_config = {"socks": config["socks"]}
        if sorted(int(value) for value in (client.get("inbounds") or [])) != [proxy_id] or config != next_config:
            client["inbounds"] = [proxy_id]
            client["config"] = next_config
            sui.save("clients", client, action="edit")
            changed += 1

    for tag in LEGACY_TAGS:
        item = by_tag.get(tag)
        if item is not None:
            sui.save("inbounds", item["tag"], action="del")
            changed += 1

    print(f"production protocol reduction applied: {changed} changes")
    return changed


def main() -> None:
    reconcile_production_clients()


if __name__ == "__main__":
    main()
