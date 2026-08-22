#!/usr/bin/env python3
"""Apply or verify the version-controlled default Mihomo template."""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def api_request(base_url: str, token: str, method: str, path: str, body=None):
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Remnawave API returned HTTP {error.code}: {detail}") from error


def load_token(token_file: Path) -> str:
    token = os.environ.get("REMNAWAVE_API_TOKEN", "").strip()
    if token:
        return token
    try:
        return token_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError as error:
        raise RuntimeError(
            "Set REMNAWAVE_API_TOKEN or provide an existing --token-file."
        ) from error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel-url", default="https://panel-verizon.bigpandas.top")
    parser.add_argument("--token-file", type=Path, default=Path(".api-token"))
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).with_name("mihomo-template.yaml"),
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    token = load_token(args.token_file)
    local_yaml = args.template.read_bytes()
    templates_response = api_request(
        args.panel_url, token, "GET", "/api/subscription-templates"
    )["response"]
    templates = (
        templates_response["templates"]
        if isinstance(templates_response, dict)
        else templates_response
    )
    default = next(
        (
            item
            for item in templates
            if item["name"] == "Default" and item["templateType"] == "MIHOMO"
        ),
        None,
    )
    if default is None:
        raise RuntimeError("Default MIHOMO subscription template was not found.")

    current = api_request(
        args.panel_url,
        token,
        "GET",
        f"/api/subscription-templates/{default['uuid']}",
    )["response"]
    remote_yaml = base64.b64decode(current["encodedTemplateYaml"])
    matches = remote_yaml == local_yaml

    if args.check:
        print("Mihomo template is current." if matches else "Mihomo template differs.")
        return 0 if matches else 1

    if matches:
        print("Mihomo template is already current.")
        return 0

    api_request(
        args.panel_url,
        token,
        "PATCH",
        "/api/subscription-templates",
        {
            "uuid": default["uuid"],
            "encodedTemplateYaml": base64.b64encode(local_yaml).decode("ascii"),
        },
    )
    print("Mihomo template updated.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
