#!/usr/bin/env python3
"""Provision and switch the Remnawave-managed CStoneCloud sing-box HY2 node."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "production"))

from manage_canary import (  # noqa: E402
    Api,
    DEFAULT_BASE_URL,
    DEFAULT_TOKEN_FILE,
    find_named,
    get_profiles,
    get_squads,
    inbound_ids,
    response,
    secure_write,
)


NODE_ENV = ROOT / "node.env"
STATE = ROOT / "state.json"
PROFILE_NAME = "CStoneCloud-HY2-SingBox"
INBOUND_TAG = "CSTONECLOUD-HY2-SINGBOX"
NODE_NAME = "CStoneCloud HY2 sing-box"
NODE_ADDRESS = "cstonecloud.bigpandas.top"
NODE_PORT = 2323
DATA_PORT = 34444
HOST_REMARK = "csc-hy2"
SQUAD_NAME = "Production-All"


def profile_config() -> dict[str, Any]:
    return {
        "log": {"level": "warn", "timestamp": True},
        "inbounds": [
            {
                "type": "hysteria2",
                "tag": INBOUND_TAG,
                "listen": "0.0.0.0",
                "listen_port": DATA_PORT,
                "up_mbps": 100,
                "down_mbps": 100,
                "users": [],
                "tls": {
                    "enabled": True,
                    "server_name": "cstonecloud.bigpandas.top",
                    "certificate_path": "/etc/remnawave/cert/fullchain.pem",
                    "key_path": "/etc/remnawave/cert/privkey.pem",
                },
            }
        ],
        "outbounds": [{"type": "direct", "tag": "direct"}],
        "route": {"final": "direct", "auto_detect_interface": True},
    }


def ensure_profile(api: Api) -> tuple[dict[str, Any], dict[str, Any]]:
    profile = find_named(get_profiles(api), PROFILE_NAME)
    if profile is None:
        profile = response(
            api.request(
                "POST",
                "/api/config-profiles",
                {"name": PROFILE_NAME, "coreType": "singbox", "config": profile_config()},
            )
        )
    if profile.get("coreType") != "singbox":
        raise RuntimeError(f"{PROFILE_NAME} exists but is not a sing-box profile")
    inbound = next(
        (item for item in profile.get("inbounds", []) if item.get("tag") == INBOUND_TAG),
        None,
    )
    if inbound is None or inbound.get("type") != "hysteria2" or inbound.get("port") != DATA_PORT:
        raise RuntimeError(f"{PROFILE_NAME} does not contain the expected HY2 inbound")
    return profile, inbound


def ensure_squad(api: Api, inbound_uuid: str) -> dict[str, Any]:
    squad = find_named(get_squads(api), SQUAD_NAME)
    if squad is None:
        raise RuntimeError(f"production squad {SQUAD_NAME} was not found")
    ids = inbound_ids(squad)
    if inbound_uuid not in ids:
        squad = response(
            api.request(
                "PATCH",
                "/api/internal-squads",
                {"uuid": squad["uuid"], "inbounds": [*ids, inbound_uuid]},
            )
        )
    return squad


def ensure_node(api: Api, profile_uuid: str, inbound_uuid: str) -> dict[str, Any]:
    node = find_named(response(api.request("GET", "/api/nodes")), NODE_NAME)
    if node is None:
        node = response(
            api.request(
                "POST",
                "/api/nodes",
                {
                    "name": NODE_NAME,
                    "address": NODE_ADDRESS,
                    "port": NODE_PORT,
                    "isTrafficTrackingActive": True,
                    "countryCode": "US",
                    "consumptionMultiplier": 1,
                    "nodeConsumptionMultiplier": 1,
                    "configProfile": {
                        "activeConfigProfileUuid": profile_uuid,
                        "activeInbounds": [inbound_uuid],
                    },
                    "tags": ["HY2_MANAGED", "CSC"],
                    "note": "Managed CStoneCloud sing-box Hysteria2 data plane",
                },
            )
        )
    if node.get("address") != NODE_ADDRESS or node.get("port") != NODE_PORT:
        node = response(
            api.request(
                "PATCH",
                "/api/nodes",
                {"uuid": node["uuid"], "address": NODE_ADDRESS, "port": NODE_PORT},
            )
        )
    current_profile = node.get("configProfile") or {}
    current_inbounds = {
        item.get("uuid") if isinstance(item, dict) else item
        for item in current_profile.get("activeInbounds", [])
    }
    if (
        current_profile.get("activeConfigProfileUuid") != profile_uuid
        or current_inbounds != {inbound_uuid}
    ):
        node = response(
            api.request(
                "PATCH",
                "/api/nodes",
                {
                    "uuid": node["uuid"],
                    "configProfile": {
                        "activeConfigProfileUuid": profile_uuid,
                        "activeInbounds": [inbound_uuid],
                    },
                },
            )
        )
    if node.get("isDisabled"):
        api.request("POST", f"/api/nodes/{node['uuid']}/actions/enable")
        node = response(api.request("GET", f"/api/nodes/{node['uuid']}"))
    return node


def ensure_node_env(api: Api) -> None:
    if NODE_ENV.exists():
        return
    secret_key = response(api.request("GET", "/api/keygen"))["secretKey"]
    secure_write(
        NODE_ENV,
        "".join(
            (
                f"NODE_PORT={NODE_PORT}\n",
                f"SECRET_KEY={secret_key}\n",
                "SINGBOX_STATS_STATE_PATH=/var/lib/remnawave/singbox-stats.json\n",
            )
        ),
    )


def get_host(api: Api) -> dict[str, Any]:
    host = next(
        (
            item
            for item in response(api.request("GET", "/api/hosts"))
            if item.get("remark") == HOST_REMARK
        ),
        None,
    )
    if host is None:
        raise RuntimeError(f"production host {HOST_REMARK} was not found")
    return host


def host_inbound(host: dict[str, Any]) -> dict[str, str]:
    inbound = host.get("inbound") or {}
    profile_uuid = inbound.get("configProfileUuid")
    inbound_uuid = inbound.get("configProfileInboundUuid")
    if not isinstance(profile_uuid, str) or not isinstance(inbound_uuid, str):
        raise RuntimeError(f"host {HOST_REMARK} has no managed inbound")
    return {
        "configProfileUuid": profile_uuid,
        "configProfileInboundUuid": inbound_uuid,
    }


def load_state() -> dict[str, Any]:
    return json.loads(STATE.read_text(encoding="utf-8"))


def provision(api: Api) -> None:
    profile, inbound = ensure_profile(api)
    squad = ensure_squad(api, inbound["uuid"])
    node = ensure_node(api, profile["uuid"], inbound["uuid"])
    ensure_node_env(api)
    if not STATE.exists():
        secure_write(
            STATE,
            json.dumps(
                {
                    "profileUuid": profile["uuid"],
                    "inboundUuid": inbound["uuid"],
                    "squadUuid": squad["uuid"],
                    "nodeUuid": node["uuid"],
                    "hostOriginalInbound": host_inbound(get_host(api)),
                },
                indent=2,
            ),
        )
    print("provisioned the CStoneCloud managed sing-box HY2 profile and node")


def require_connected(api: Api, state: dict[str, Any]) -> dict[str, Any]:
    node = response(api.request("GET", f"/api/nodes/{state['nodeUuid']}"))
    versions = node.get("versions") or {}
    if not node.get("isConnected"):
        raise RuntimeError(f"{NODE_NAME} is not connected")
    if versions.get("coreType") != "singbox" or not str(versions.get("singbox", "")).startswith(
        "1.13.15"
    ):
        raise RuntimeError(f"{NODE_NAME} has an unexpected Core version")
    return node


def activate(api: Api) -> None:
    state = load_state()
    require_connected(api, state)
    host = get_host(api)
    api.request(
        "PATCH",
        "/api/hosts",
        {
            "uuid": host["uuid"],
            "inbound": {
                "configProfileUuid": state["profileUuid"],
                "configProfileInboundUuid": state["inboundUuid"],
            },
            "isDisabled": False,
        },
    )
    print(f"switched {HOST_REMARK} to the managed CStoneCloud sing-box HY2 inbound")


def restore(api: Api) -> None:
    state = load_state()
    host = get_host(api)
    api.request(
        "PATCH",
        "/api/hosts",
        {"uuid": host["uuid"], "inbound": state["hostOriginalInbound"], "isDisabled": False},
    )
    squad = next(item for item in get_squads(api) if item.get("uuid") == state["squadUuid"])
    api.request(
        "PATCH",
        "/api/internal-squads",
        {
            "uuid": squad["uuid"],
            "inbounds": [value for value in inbound_ids(squad) if value != state["inboundUuid"]],
        },
    )
    print(f"restored {HOST_REMARK} and removed the CStoneCloud sing-box inbound from the squad")


def status(api: Api) -> None:
    state = load_state()
    node = response(api.request("GET", f"/api/nodes/{state['nodeUuid']}"))
    versions = node.get("versions") or {}
    managed = host_inbound(get_host(api))["configProfileInboundUuid"] == state["inboundUuid"]
    print(
        "node_connected={} core={} singbox={} csc_hy2_managed={}".format(
            bool(node.get("isConnected")),
            versions.get("coreType"),
            versions.get("singbox"),
            managed,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("provision", "activate", "restore", "status"))
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-token-file", type=Path, default=DEFAULT_TOKEN_FILE)
    args = parser.parse_args()
    token = args.api_token_file.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError("API token file is empty")
    api = Api(args.base_url, token)
    if args.command == "provision":
        provision(api)
    elif args.command == "activate":
        activate(api)
    elif args.command == "restore":
        restore(api)
    else:
        status(api)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
