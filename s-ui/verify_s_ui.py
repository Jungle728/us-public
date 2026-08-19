#!/usr/bin/env python3
"""Verify the production s-ui deployment without reading legacy 3x-ui data."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from verify_shadowrocket import validate as verify_shadowrocket


MODULE_PATH = Path(__file__).with_name("sui_runtime.py")
SPEC = importlib.util.spec_from_file_location("sui_support", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load s-ui support module")
SUPPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUPPORT)


def production_state() -> dict:
    sui = SUPPORT.SUI()
    sui.login()
    summaries = sui.get("clients") or []
    clients = [
        {"name": item["name"]}
        for item in summaries
        if item.get("group") == "aaitr-production"
    ]
    if not clients:
        raise RuntimeError("no production subscription clients found")

    proxy_summary = next(
        (item for item in summaries if item.get("group") == "forward-proxy"),
        None,
    )
    if proxy_summary is None:
        raise RuntimeError("forward proxy client not found")
    rows = sui.get("clients", {"id": int(proxy_summary["id"])}) or []
    if len(rows) != 1:
        raise RuntimeError("unable to load the forward proxy client")
    config = rows[0].get("config") or {}
    socks = config.get("socks") or {}
    if not socks.get("username") or not socks.get("password"):
        raise RuntimeError("forward proxy SOCKS5 credentials are incomplete")
    return {
        "clients": clients,
        "proxy": {"name": socks["username"], "password": socks["password"]},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "check",
        choices=("all", "subscriptions", "protocols", "proxies", "shadowrocket"),
        default="all",
        nargs="?",
    )
    args = parser.parse_args()
    if args.check in {"all", "shadowrocket"}:
        verify_shadowrocket()
    if args.check == "shadowrocket":
        return
    state = production_state()
    print(f"production subscription clients: {len(state['clients'])}")
    if args.check in {"all", "subscriptions"}:
        SUPPORT.verify_subscriptions(state)
    if args.check in {"all", "protocols"}:
        SUPPORT.verify_protocols(state)
    if args.check in {"all", "proxies"}:
        SUPPORT.verify_forward_proxies(state)
    print("production s-ui verification: complete")


if __name__ == "__main__":
    main()
