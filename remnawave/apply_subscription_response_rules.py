#!/usr/bin/env python3
"""Keep mobile Clash-family clients on the maintained Mihomo response."""

import argparse
import sys
from pathlib import Path

from apply_subscription_template import api_request, load_token


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel-url", default="https://panel-verizon.bigpandas.top")
    parser.add_argument("--token-file", type=Path, default=Path(".api-token"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    token = load_token(args.token_file)
    settings = api_request(args.panel_url, token, "GET", "/api/subscription-settings")[
        "response"
    ]
    rules_config = settings.get("responseRules")
    if not isinstance(rules_config, dict):
        raise RuntimeError("response rules are not configured")

    rules = rules_config.get("rules")
    if not isinstance(rules, list):
        raise RuntimeError("response rules list is missing")

    target = next((rule for rule in rules if rule.get("name") == "Clash Core Clients"), None)
    if target is None:
        raise RuntimeError("Clash Core Clients response rule was not found")

    changed = target.get("responseType") != "MIHOMO"
    if changed:
        target["responseType"] = "MIHOMO"

    if args.check:
        message = "Clash clients use the Mihomo response." if not changed else "Clash clients need the Mihomo response."
        print(message)
        return 0 if not changed else 1

    if changed:
        api_request(
            args.panel_url,
            token,
            "PATCH",
            "/api/subscription-settings",
            {"uuid": settings["uuid"], "responseRules": rules_config},
        )
        print("Clash client response rule updated to MIHOMO.")
    else:
        print("Clash client response rule is already MIHOMO.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
