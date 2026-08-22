#!/usr/bin/env python3
"""Copy the maintained Mihomo YAML into the explicit /clash template."""

import argparse
import base64
import sys
from pathlib import Path

from apply_subscription_template import api_request, load_token


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel-url", default="https://panel-verizon.bigpandas.top")
    parser.add_argument("--token-file", type=Path, default=Path(".api-token"))
    parser.add_argument("--template", type=Path, default=Path(__file__).with_name("mihomo-template.yaml"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    token = load_token(args.token_file)
    local_yaml = args.template.read_bytes()
    templates = api_request(args.panel_url, token, "GET", "/api/subscription-templates")["response"]["templates"]
    target = next((item for item in templates if item["name"] == "Default" and item["templateType"] == "CLASH"), None)
    if target is None:
        raise RuntimeError("Default CLASH subscription template was not found.")
    current = api_request(args.panel_url, token, "GET", f"/api/subscription-templates/{target['uuid']}")["response"]
    matches = base64.b64decode(current["encodedTemplateYaml"]) == local_yaml
    if args.check:
        print("CLASH template is current." if matches else "CLASH template differs.")
        return 0 if matches else 1
    if not matches:
        api_request(args.panel_url, token, "PATCH", "/api/subscription-templates", {
            "uuid": target["uuid"],
            "encodedTemplateYaml": base64.b64encode(local_yaml).decode("ascii"),
        })
        print("CLASH template updated from Mihomo template.")
    else:
        print("CLASH template is already current.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
