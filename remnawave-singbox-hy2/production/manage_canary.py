#!/usr/bin/env python3
"""Provision and switch the production Remnawave-managed sing-box HY2 canary."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
NODE_ENV = ROOT / "node.env"
STATE = ROOT / "canary-state.json"
DEFAULT_BASE_URL = "http://127.0.0.1:3000"
DEFAULT_TOKEN_FILE = Path("/root/code/us-public/remnawave/.api-token")
PROFILE_NAME = "Verizon-HY2-SingBox"
INBOUND_TAG = "VERIZON-HY2-SINGBOX"
NODE_NAME = "Verizon HY2 sing-box"
NODE_ADDRESS = "remnanode-singbox-hy2"
SQUAD_NAME = "Production-All"
CANARY_HOST = "csc-aaitr-hy2-singbox-test"
FORMAL_HOSTS = ("aaitr-hy2", "csc-aaitr-hy2")


def secure_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.chmod(path, 0o600)


class Api:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request(self, method: str, path: str, data: Any | None = None) -> Any:
        body = None if data is None else json.dumps(data).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
            "X-Forwarded-For": "127.0.0.1",
            "X-Forwarded-Proto": "https",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=body, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = response.read()
                return json.loads(payload) if payload else None
        except urllib.error.HTTPError as error:
            payload = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"{method} {path} failed with HTTP {error.code}: {payload}"
            ) from error


def response(value: Any) -> Any:
    return value["response"]


def inbound_ids(squad: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for inbound in squad.get("inbounds", []):
        value = inbound.get("uuid") if isinstance(inbound, dict) else inbound
        if isinstance(value, str):
            result.append(value)
    return result


def get_profiles(api: Api) -> list[dict[str, Any]]:
    value = response(api.request("GET", "/api/config-profiles"))
    return value["configProfiles"]


def get_squads(api: Api) -> list[dict[str, Any]]:
    value = response(api.request("GET", "/api/internal-squads"))
    return value["internalSquads"]


def find_named(values: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    return next((item for item in values if item.get("name") == name), None)


def profile_config() -> dict[str, Any]:
    return {
        "log": {"level": "warn", "timestamp": True},
        "inbounds": [
            {
                "type": "hysteria2",
                "tag": INBOUND_TAG,
                "listen": "0.0.0.0",
                "listen_port": 34443,
                "up_mbps": 100,
                "down_mbps": 100,
                "users": [],
                "tls": {
                    "enabled": True,
                    "server_name": "verizon.bigpandas.top",
                    "certificate_path": "/etc/letsencrypt/live/remnawave-domains/fullchain.pem",
                    "key_path": "/etc/letsencrypt/live/remnawave-domains/privkey.pem",
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
        (item for item in profile.get("inbounds", []) if item.get("tag") == INBOUND_TAG), None
    )
    if inbound is None or inbound.get("type") != "hysteria2" or inbound.get("port") != 34443:
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
                    "port": 2323,
                    "isTrafficTrackingActive": True,
                    "countryCode": "US",
                    "consumptionMultiplier": 1,
                    "nodeConsumptionMultiplier": 1,
                    "configProfile": {
                        "activeConfigProfileUuid": profile_uuid,
                        "activeInbounds": [inbound_uuid],
                    },
                    "tags": ["HY2_MANAGED"],
                    "note": "Managed sing-box Hysteria2 data plane",
                },
            )
        )
    if node.get("address") != NODE_ADDRESS or node.get("port") != 2323:
        node = response(
            api.request(
                "PATCH",
                "/api/nodes",
                {"uuid": node["uuid"], "address": NODE_ADDRESS, "port": 2323},
            )
        )
    return node


def ensure_node_env(api: Api) -> None:
    if NODE_ENV.exists():
        return
    secret_key = response(api.request("GET", "/api/keygen"))["secretKey"]
    secure_write(
        NODE_ENV,
        "".join(
            (
                "NODE_PORT=2323\n",
                f"SECRET_KEY={secret_key}\n",
                "SINGBOX_STATS_STATE_PATH=/var/lib/remnawave/singbox-stats.json\n",
            )
        ),
    )


def get_hosts_by_remark(api: Api) -> dict[str, dict[str, Any]]:
    wanted = {CANARY_HOST, *FORMAL_HOSTS}
    hosts = {
        item["remark"]: item
        for item in response(api.request("GET", "/api/hosts"))
        if item.get("remark") in wanted
    }
    missing = wanted.difference(hosts)
    if missing:
        raise RuntimeError(f"missing production HY2 hosts: {', '.join(sorted(missing))}")
    return hosts


def host_inbound(host: dict[str, Any]) -> dict[str, str]:
    inbound = host.get("inbound") or {}
    profile_uuid = inbound.get("configProfileUuid")
    inbound_uuid = inbound.get("configProfileInboundUuid")
    if not isinstance(profile_uuid, str) or not isinstance(inbound_uuid, str):
        raise RuntimeError(f"host {host.get('remark')} has no managed inbound")
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
    hosts = get_hosts_by_remark(api)
    if not STATE.exists():
        secure_write(
            STATE,
            json.dumps(
                {
                    "profileUuid": profile["uuid"],
                    "inboundUuid": inbound["uuid"],
                    "squadUuid": squad["uuid"],
                    "nodeUuid": node["uuid"],
                    "hostOriginalInbounds": {
                        remark: host_inbound(host) for remark, host in hosts.items()
                    },
                },
                indent=2,
            ),
        )
    print("provisioned the managed HY2 profile, node, squad mapping and node environment")


def require_connected_node(api: Api, state: dict[str, Any]) -> dict[str, Any]:
    node = response(api.request("GET", f"/api/nodes/{state['nodeUuid']}"))
    versions = node.get("versions") or {}
    if not node.get("isConnected"):
        raise RuntimeError(f"{NODE_NAME} is not connected")
    if versions.get("coreType") != "singbox" or not str(versions.get("singbox", "")).startswith(
        "1.13.15"
    ):
        raise RuntimeError(f"{NODE_NAME} is connected with an unexpected core version")
    return node


def switch_hosts(api: Api, remarks: tuple[str, ...]) -> None:
    state = load_state()
    require_connected_node(api, state)
    hosts = get_hosts_by_remark(api)
    inbound = {
        "configProfileUuid": state["profileUuid"],
        "configProfileInboundUuid": state["inboundUuid"],
    }
    for remark in remarks:
        api.request(
            "PATCH",
            "/api/hosts",
            {"uuid": hosts[remark]["uuid"], "inbound": inbound, "isDisabled": False},
        )
    print(f"switched {', '.join(remarks)} to the managed sing-box HY2 inbound")


def restore(api: Api) -> None:
    state = load_state()
    hosts = get_hosts_by_remark(api)
    for remark, inbound in state["hostOriginalInbounds"].items():
        api.request(
            "PATCH",
            "/api/hosts",
            {"uuid": hosts[remark]["uuid"], "inbound": inbound, "isDisabled": False},
        )
    squad = next(
        item for item in get_squads(api) if item.get("uuid") == state["squadUuid"]
    )
    ids = [value for value in inbound_ids(squad) if value != state["inboundUuid"]]
    api.request(
        "PATCH",
        "/api/internal-squads",
        {"uuid": squad["uuid"], "inbounds": ids},
    )
    print("restored all HY2 hosts and removed the managed inbound from the production squad")


def retire_canary(api: Api) -> None:
    host = get_hosts_by_remark(api)[CANARY_HOST]
    api.request(
        "PATCH",
        "/api/hosts",
        {"uuid": host["uuid"], "isDisabled": True},
    )
    print(f"disabled the subscription-only canary host {CANARY_HOST}")


def status(api: Api) -> None:
    state = load_state()
    node = response(api.request("GET", f"/api/nodes/{state['nodeUuid']}"))
    hosts = get_hosts_by_remark(api)
    managed = [
        remark
        for remark, host in hosts.items()
        if host_inbound(host)["configProfileInboundUuid"] == state["inboundUuid"]
        and not host.get("isDisabled")
    ]
    disabled = [
        remark
        for remark, host in hosts.items()
        if host_inbound(host)["configProfileInboundUuid"] == state["inboundUuid"]
        and host.get("isDisabled")
    ]
    versions = node.get("versions") or {}
    print(
        "node_connected={} core={} singbox={} managed_hosts={} disabled_hosts={}".format(
            bool(node.get("isConnected")),
            versions.get("coreType"),
            versions.get("singbox"),
            ",".join(sorted(managed)) or "none",
            ",".join(sorted(disabled)) or "none",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("provision", "activate", "promote", "retire-canary", "restore", "status"),
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-token-file", type=Path, default=DEFAULT_TOKEN_FILE)
    args = parser.parse_args()
    token = args.api_token_file.read_text(encoding="utf-8").strip()
    if not token:
        raise SystemExit("API token file is empty")
    api = Api(args.base_url, token)

    if args.command == "provision":
        provision(api)
    elif args.command == "activate":
        switch_hosts(api, (CANARY_HOST,))
    elif args.command == "promote":
        switch_hosts(api, (CANARY_HOST, *FORMAL_HOSTS))
    elif args.command == "retire-canary":
        retire_canary(api)
    elif args.command == "restore":
        restore(api)
    elif args.command == "status":
        status(api)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
