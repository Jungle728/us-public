#!/usr/bin/env python3
"""Keep every production client on the four public subscription inbounds."""

from __future__ import annotations

from sui_runtime import SUI, fail


PRODUCTION_TAGS = {
    "yuntu-reality",
    "yuntu-hysteria2",
    "yuntu-anytls",
    "yuntu-shadowsocks",
}


def reconcile_production_clients() -> int:
    sui = SUI()
    sui.login()
    inbounds = sui.get("inbounds") or []
    by_tag = {item.get("tag"): item for item in inbounds}
    missing = PRODUCTION_TAGS - set(by_tag)
    if missing:
        fail(f"production inbounds are missing: {sorted(missing)}")
    desired = sorted(int(by_tag[tag]["id"]) for tag in PRODUCTION_TAGS)

    changed = 0
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
        if current == desired:
            continue
        client["inbounds"] = desired
        sui.save("clients", client, action="edit")
        changed += 1

    print(f"production client inbound permissions repaired: {changed}")
    return changed


def main() -> None:
    reconcile_production_clients()


if __name__ == "__main__":
    main()
