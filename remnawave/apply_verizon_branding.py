#!/usr/bin/env python3
"""Apply AaITR/CSC subscription names to an existing Remnawave deployment."""

import argparse
import sys
from pathlib import Path

from apply_subscription_template import api_request, load_token


HOSTS = {
    "aaitr-reality": {
        "previous": ("verizon-exit-reality", "aaitr-exit-reality"),
        "description": "AaITR Reality",
        "tags": ["PRODUCTION", "AAITR"],
        "profile": "Verizon-Production",
        "inbound": "VERIZON-REALITY",
    },
    "aaitr-hy2": {
        "previous": ("verizon-exit-hy2", "aaitr-exit-hy2"),
        "description": "AaITR Hysteria2",
        "tags": ["PRODUCTION", "AAITR"],
        "profile": "Verizon-Production",
        "inbound": "VERIZON-HY2",
        "port": 32443,
    },
    "aaitr-tls": {
        "previous": ("verizon-exit-tls", "aaitr-exit-tls"),
        "description": "AaITR TLS Vision",
        "tags": ["PRODUCTION", "AAITR", "TLS"],
        "profile": "Verizon-Production",
        "inbound": "VERIZON-TLS-VISION",
    },
    "csc-reality": {
        "previous": "cstonecloud-exit-reality",
        "description": "CSC Reality",
        "tags": ["PRODUCTION", "CSC"],
        "profile": "CStoneCloud-Production",
        "inbound": "CSTONECLOUD-REALITY",
    },
    "csc-hy2": {
        "previous": "cstonecloud-exit-hy2",
        "description": "CSC Hysteria2",
        "tags": ["PRODUCTION", "CSC"],
        "profile": "CStoneCloud-Production",
        "inbound": "CSTONECLOUD-HY2",
        "port": 2443,
    },
    "csc-tls": {
        "previous": "cstonecloud-exit-tls",
        "description": "CSC TLS Vision",
        "tags": ["PRODUCTION", "CSC", "TLS"],
        "profile": "CStoneCloud-Production",
        "inbound": "CSTONECLOUD-TLS-VISION",
    },
    "csc-aaitr-reality": {
        "previous": ("cstonecloud-verizon-reality", "cstonecloud-aaitr-reality"),
        "description": "CSC to AaITR Reality",
        "tags": ["PRODUCTION", "CSC", "AAITR"],
        "profile": "Verizon-Production",
        "inbound": "VERIZON-REALITY",
    },
    "csc-aaitr-hy2": {
        "previous": ("cstonecloud-verizon-hy2", "cstonecloud-aaitr-hy2"),
        "description": "CSC to AaITR Hysteria2",
        "tags": ["PRODUCTION", "CSC", "AAITR"],
        "profile": "Verizon-Production",
        "inbound": "VERIZON-HY2",
        "port": 443,
    },
    "csc-aaitr-tls": {
        "previous": ("cstonecloud-verizon-tls", "cstonecloud-aaitr-tls"),
        "description": "CSC to AaITR TLS Vision",
        "tags": ["PRODUCTION", "CSC", "AAITR", "TLS"],
        "profile": "Verizon-Production",
        "inbound": "VERIZON-TLS-VISION",
    },
}

NODES = {
    "Verizon": "AaITR-Verizon",
    "CStoneCloud": "CStoneCloud-Line",
}

PROFILES = {
    "Verizon-Production": "AaITR-Production",
    "CStoneCloud-Production": "CStoneCloud-Production",
}

INBOUND_TAGS = {
    "Verizon-Production": {
        "AAITR-REALITY-TEST": "VERIZON-REALITY",
        "AAITR-HY2-TEST": "VERIZON-HY2",
        "AAITR-TLS-VISION": "VERIZON-TLS-VISION",
        "AAITR-SOCKS5": "VERIZON-SOCKS5",
    },
    "CStoneCloud-Production": {
        "CSTONE-REALITY-TEST": "CSTONECLOUD-REALITY",
        "CSTONE-HY2-TEST": "CSTONECLOUD-HY2",
        "CSTONE-TLS-VISION": "CSTONECLOUD-TLS-VISION",
    },
}


def find_by_names(items, field, desired, previous=None):
    accepted = {desired}
    if isinstance(previous, str):
        accepted.add(previous)
    elif previous:
        accepted.update(previous)
    return next((item for item in items if item[field] in accepted), None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel-url", default="https://panel-verizon.bigpandas.top")
    parser.add_argument("--token-file", type=Path, default=Path(".api-token"))
    args = parser.parse_args()
    token = load_token(args.token_file)

    nodes = api_request(args.panel_url, token, "GET", "/api/nodes")["response"]
    for desired, previous in NODES.items():
        node = find_by_names(nodes, "name", desired, previous)
        if node is None:
            raise RuntimeError(f"Node not found for {desired}.")
        api_request(
            args.panel_url,
            token,
            "PATCH",
            "/api/nodes",
            {"uuid": node["uuid"], "name": desired},
        )

    profile_response = api_request(
        args.panel_url, token, "GET", "/api/config-profiles"
    )["response"]
    profiles = profile_response["configProfiles"]
    for desired, previous in PROFILES.items():
        profile = find_by_names(profiles, "name", desired, previous)
        if profile is None:
            raise RuntimeError(f"Config profile not found for {desired}.")
        if profile["name"] != desired:
            api_request(
                args.panel_url,
                token,
                "PATCH",
                "/api/config-profiles",
                {"uuid": profile["uuid"], "name": desired},
            )

    profiles = api_request(
        args.panel_url, token, "GET", "/api/config-profiles"
    )["response"]["configProfiles"]
    for desired, tag_map in INBOUND_TAGS.items():
        profile = find_by_names(profiles, "name", desired)
        if profile is None:
            raise RuntimeError(f"Config profile not found for {desired}.")
        detail = api_request(
            args.panel_url,
            token,
            "GET",
            f"/api/config-profiles/{profile['uuid']}",
        )["response"]
        changed = False
        for inbound in detail["config"].get("inbounds", []):
            renamed = tag_map.get(inbound.get("tag"))
            if renamed:
                inbound["tag"] = renamed
                changed = True
        if changed:
            api_request(
                args.panel_url,
                token,
                "PATCH",
                "/api/config-profiles",
                {"uuid": profile["uuid"], "name": desired, "config": detail["config"]},
            )

    profiles = api_request(
        args.panel_url, token, "GET", "/api/config-profiles"
    )["response"]["configProfiles"]
    profile_details = {}
    for profile in profiles:
        if profile["name"] in PROFILES:
            profile_details[profile["name"]] = api_request(
                args.panel_url,
                token,
                "GET",
                f"/api/config-profiles/{profile['uuid']}",
            )["response"]

    squads_response = api_request(
        args.panel_url, token, "GET", "/api/internal-squads"
    )["response"]
    production_squad = find_by_names(
        squads_response["internalSquads"], "name", "Production-All"
    )
    if production_squad is None:
        raise RuntimeError("Internal squad Production-All was not found.")
    api_request(
        args.panel_url,
        token,
        "PATCH",
        "/api/internal-squads",
        {
            "uuid": production_squad["uuid"],
            "inbounds": [
                inbound["uuid"]
                for profile in profile_details.values()
                for inbound in profile["inbounds"]
            ],
        },
    )

    nodes = api_request(args.panel_url, token, "GET", "/api/nodes")["response"]
    node_profile = {
        "Verizon": "Verizon-Production",
        "CStoneCloud": "CStoneCloud-Production",
    }
    for node_name, profile_name in node_profile.items():
        node = find_by_names(nodes, "name", node_name)
        profile = profile_details[profile_name]
        if node is None:
            raise RuntimeError(f"Node not found for {node_name}.")
        api_request(
            args.panel_url,
            token,
            "PATCH",
            "/api/nodes",
            {
                "uuid": node["uuid"],
                "configProfile": {
                    "activeConfigProfileUuid": profile["uuid"],
                    "activeInbounds": [item["uuid"] for item in profile["inbounds"]],
                },
            },
        )
        api_request(
            args.panel_url,
            token,
            "POST",
            f"/api/nodes/{node['uuid']}/actions/enable",
        )

    hosts = api_request(args.panel_url, token, "GET", "/api/hosts")["response"]
    for desired, settings in HOSTS.items():
        host = find_by_names(hosts, "remark", desired, settings.get("previous"))
        if host is None:
            raise RuntimeError(f"Host not found for {desired}.")
        profile = profile_details[settings["profile"]]
        inbound = next(
            (item for item in profile["inbounds"] if item["tag"] == settings["inbound"]),
            None,
        )
        if inbound is None:
            raise RuntimeError(f"Inbound not found for {desired}.")
        api_request(
            args.panel_url,
            token,
            "PATCH",
            "/api/hosts",
            {
                "uuid": host["uuid"],
                "remark": desired,
                "serverDescription": settings["description"],
                "tags": settings["tags"],
                **({"port": settings["port"]} if "port" in settings else {}),
                "inbound": {
                    "configProfileUuid": profile["uuid"],
                    "configProfileInboundUuid": inbound["uuid"],
                },
            },
        )

    print("AaITR/CSC subscription names and production tags applied.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
