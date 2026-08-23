#!/usr/bin/env python3
"""Install and verify the production Clash policy through the native s-ui API."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from sui_runtime import SUI, fail, verify_clash_policy


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "clash-template.yaml"
DATABASE = ROOT / "db" / "s-ui.db"
BACKUPS = ROOT / "db" / "backups"
SETTING_KEYS = ("subClashExt", "subClashNoDefGrp", "subClashSprtAll")


def backup_database() -> Path:
    BACKUPS.mkdir(mode=0o700, exist_ok=True)
    BACKUPS.chmod(0o700)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = BACKUPS / f"s-ui-before-clash-policy-{stamp}.db"
    with sqlite3.connect(DATABASE) as source, sqlite3.connect(destination) as target:
        source.backup(target)
    destination.chmod(0o600)
    return destination


def production_clients(sui: SUI) -> list[str]:
    clients = [
        item["name"]
        for item in (sui.get("clients") or [])
        if item.get("group") == "aaitr-production"
    ]
    if not clients:
        fail("no production subscription clients found")
    return clients


def main() -> None:
    template = TEMPLATE.read_text()
    sui = SUI()
    sui.login()
    current = sui.get("settings") or {}
    previous = {key: str(current.get(key, "")) for key in SETTING_KEYS}
    clients = production_clients(sui)
    backup = backup_database()

    desired = {
        "subClashExt": template,
        "subClashNoDefGrp": "true",
        "subClashSprtAll": "false",
    }
    try:
        sui.save("settings", desired)
        for client_name in clients:
            verify_clash_policy(client_name)
    except Exception as exc:  # noqa: BLE001
        sui.save("settings", previous)
        fail(f"Clash policy verification failed and settings were rolled back: {exc}")

    print(f"installed Clash policy for {len(clients)} production clients")
    print(f"database backup: {backup}")
    print("Clash routing policy verification: complete")


if __name__ == "__main__":
    main()
