#!/usr/bin/env python3
"""Migrate the existing VLESS users into an isolated s-ui canary.

The source database is opened read-only. No source values are printed.
Run without --apply for a structural dry run; use --apply only after the
summary is what is expected.
"""

from __future__ import annotations

import argparse
import base64
import json
import secrets
import sqlite3
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path


SOURCE_DB = "/opt/3x-ui/data/x-ui.db"
ADMIN_PASSWORD = Path(__file__).resolve().with_name(".admin-password")
SUI_BASE = "http://127.0.0.1:3095/app"
SUI_SUB = "http://127.0.0.1:3096"
PUBLIC_HOST = "cstonecloud.bigpandas.top"
TLS_SNI = "cstonecloud.bigpandas.top"
CERT_PATH = "/app/cert/live/s-ui-domains/fullchain.pem"
KEY_PATH = "/app/cert/live/s-ui-domains/privkey.pem"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_source() -> dict:
    db = sqlite3.connect(f"file:{SOURCE_DB}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        inbound_rows = db.execute(
            "SELECT * FROM inbounds WHERE protocol = 'vless' ORDER BY id"
        ).fetchall()
        candidates = []
        for row in inbound_rows:
            try:
                stream = json.loads(row["stream_settings"] or "{}")
            except json.JSONDecodeError:
                continue
            if stream.get("security") == "reality":
                candidates.append((row, stream))
        if len(candidates) != 1:
            fail(f"expected one VLESS REALITY inbound, found {len(candidates)}")

        inbound, stream = candidates[0]
        reality = stream.get("realitySettings") or {}
        private_key = reality.get("privateKey")
        short_ids = reality.get("shortIds") or []
        server_names = reality.get("serverNames") or []
        dest = reality.get("dest") or "www.cloudflare.com:443"
        if not private_key or not short_ids or not server_names:
            fail("existing REALITY profile is incomplete")
        target, _, target_port = dest.rpartition(":")
        if not target:
            target, target_port = dest, "443"

        host = db.execute(
            "SELECT * FROM hosts WHERE inbound_id = ? ORDER BY id LIMIT 1",
            (inbound["id"],),
        ).fetchone()
        fingerprint = (host["fingerprint"] if host else None) or "chrome"
        sni = (host["sni"] if host else None) or server_names[0]

        client_rows = db.execute(
            """
            SELECT c.* FROM clients c
            JOIN client_inbounds ci ON ci.client_id = c.id
            WHERE ci.inbound_id = ? ORDER BY c.id
            """,
            (inbound["id"],),
        ).fetchall()
        if not client_rows:
            fail("no clients are attached to the existing REALITY inbound")

        clients = []
        for row in client_rows:
            expiry = int(row["expiry_time"] or 0)
            if expiry > 10_000_000_000:
                expiry //= 1000
            total_gb = int(row["total_gb"] or 0)
            clients.append(
                {
                    "old_id": int(row["id"]),
                    "name": row["sub_id"],
                    "uuid": row["uuid"],
                    "flow": row["flow"] or "xtls-rprx-vision",
                    "enable": bool(row["enable"]),
                    "expiry": expiry,
                    # 3x-ui keeps this historical field in bytes despite its name.
                    "volume": total_gb,
                    "desc": row["email"] or row["comment"] or "",
                    "remark": row["comment"] or "",
                }
            )

        proxy_rows = db.execute(
            "SELECT settings FROM inbounds WHERE protocol = 'http' ORDER BY id"
        ).fetchall()
        proxy_accounts = []
        for row in proxy_rows:
            settings = json.loads(row["settings"] or "{}")
            proxy_accounts.extend(settings.get("accounts") or [])
        if len(proxy_accounts) != 1:
            fail(f"expected one existing HTTP proxy account, found {len(proxy_accounts)}")
        proxy_user = proxy_accounts[0].get("user")
        proxy_password = proxy_accounts[0].get("pass")
        if not proxy_user or not proxy_password:
            fail("existing HTTP proxy account is incomplete")

        return {
            "reality": {
                "private_key": private_key,
                "short_ids": short_ids,
                "server_name": sni,
                "target": target,
                "target_port": int(target_port or 443),
                "fingerprint": fingerprint,
            },
            "clients": clients,
            "proxy": {"name": proxy_user, "password": proxy_password},
            "source_inbound_id": int(inbound["id"]),
        }
    finally:
        db.close()


def derive_public_key(private_key: str) -> str:
    result = subprocess.run(
        [
            "docker",
            "exec",
            "3x-ui",
            "/app/bin/xray-linux-amd64",
            "x25519",
            "-i",
            private_key,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in result.stdout.splitlines():
        if line.startswith(("PublicKey:", "Password (PublicKey):")):
            return line.split(":", 1)[1].strip()
    fail("unable to derive REALITY public key")


def password() -> str:
    return secrets.token_hex(16)


class SUI:
    def __init__(self) -> None:
        self.jar = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    def request(self, method: str, url: str, data: dict | None = None) -> dict:
        body = None
        headers = {"Host": "sub-verizon.bigpandas.top"}
        if data is not None:
            body = urllib.parse.urlencode(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=15) as response:
                payload = json.loads(response.read().decode())
        except Exception as exc:  # noqa: BLE001
            fail(f"s-ui API request failed: {method} {url}: {type(exc).__name__}")
        if not payload.get("success", False):
            fail(f"s-ui API rejected {method} {url}: {payload.get('msg', 'unknown error')}")
        return payload

    def login(self) -> None:
        if not ADMIN_PASSWORD.exists():
            fail("admin password file is missing")
        self.request(
            "POST",
            f"{SUI_BASE}/api/login",
            {"user": "suiadmin", "pass": ADMIN_PASSWORD.read_text().strip()},
        )

    def get(self, object_name: str, query: dict | None = None):
        url = f"{SUI_BASE}/api/{object_name}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        obj = self.request("GET", url).get("obj")
        if isinstance(obj, dict) and object_name in obj:
            return obj[object_name]
        return obj

    def save(
        self,
        object_name: str,
        data: dict,
        init_users: str = "",
        action: str = "new",
    ):
        return self.save_raw(
            object_name,
            json.dumps(data, separators=(",", ":")),
            init_users=init_users,
            action=action,
        )

    def save_raw(
        self,
        object_name: str,
        data: str,
        init_users: str = "",
        action: str = "new",
    ):
        form = {
            "object": object_name,
            "action": action,
            "data": data,
        }
        if init_users:
            form["initUsers"] = init_users
        return self.request("POST", f"{SUI_BASE}/api/save", form).get("obj")

    @staticmethod
    def _object(payload: dict):
        obj = payload.get("obj")
        if isinstance(obj, str):
            try:
                return json.loads(obj)
            except json.JSONDecodeError:
                return obj
        return obj

    def link_convert(self, link: str) -> dict:
        obj = self._object(
            self.request("POST", f"{SUI_BASE}/api/linkConvert", {"link": link})
        )
        if isinstance(obj, list) and len(obj) == 1:
            obj = obj[0]
        if isinstance(obj, dict) and isinstance(obj.get("outbound"), dict):
            obj = obj["outbound"]
        if not isinstance(obj, dict) or not obj.get("type"):
            fail("s-ui link conversion returned no outbound")
        return obj

    def check_outbound(self, tag: str) -> dict:
        query = urllib.parse.urlencode(
            {"tag": tag, "link": "https://api.ipify.org"}
        )
        payload = self.request("GET", f"{SUI_BASE}/api/checkOutbound?{query}")
        obj = self._object(payload)
        if not isinstance(obj, dict):
            fail("s-ui outbound check returned no result")
        ok = obj.get("OK")
        if ok is None:
            ok = obj.get("ok")
        if ok is not True:
            fail("s-ui outbound check reported a failed connection")
        return obj

    def delete_outbound(self, tag: str) -> None:
        self.save_raw("outbounds", json.dumps(tag), action="del")


def tls_profiles(source: dict, public_key: str) -> tuple[dict, dict]:
    r = source["reality"]
    reality_server = {
        "enabled": True,
        "server_name": r["server_name"],
        "reality": {
            "enabled": True,
            "handshake": {
                "server": r["target"],
                "server_port": r["target_port"],
            },
            "private_key": r["private_key"],
            "short_id": r["short_ids"],
        },
    }
    reality_client = {
        "enabled": True,
        "server_name": r["server_name"],
        "utls": {"enabled": True, "fingerprint": r["fingerprint"]},
        "reality": {
            "enabled": True,
            "public_key": public_key,
            "short_id": r["short_ids"][0],
        },
    }
    cert_server = {
        "enabled": True,
        "certificate_path": CERT_PATH,
        "key_path": KEY_PATH,
    }
    cert_client = {"enabled": True, "server_name": TLS_SNI}
    return (
        {"id": 0, "name": "canary-reality", "server": reality_server, "client": reality_client},
        {"id": 0, "name": "canary-tls", "server": cert_server, "client": cert_client},
    )


def client_payload(item: dict) -> dict:
    user = item["name"]
    return {
        "id": 0,
        "enable": item["enable"],
        "name": user,
        "config": {
            "vless": {"name": user, "uuid": item["uuid"], "flow": item["flow"]},
            "hysteria2": {"name": user, "password": password()},
        },
        "inbounds": [],
        "links": [],
        "volume": item["volume"],
        "expiry": item["expiry"],
        "desc": item["desc"],
        "group": "aaitr-canary",
        "remark": item["remark"],
        "up": 0,
        "down": 0,
        "totalUp": 0,
        "totalDown": 0,
    }


def proxy_client_payload(item: dict) -> dict:
    return {
        "id": 0,
        "enable": True,
        "name": item["name"],
        "config": {
            "socks": {"username": item["name"], "password": item["password"]},
        },
        "inbounds": [],
        "links": [],
        "volume": 0,
        "expiry": 0,
        "desc": "forward proxy account",
        "group": "forward-proxy",
        "remark": "",
        "up": 0,
        "down": 0,
        "totalUp": 0,
        "totalDown": 0,
    }


def inbound_payloads(tls_ids: dict) -> list[dict]:
    return [
        {
            "id": 0,
            "type": "vless",
            "tag": "canary-reality",
            "listen": "0.0.0.0",
            "listen_port": 31443,
            "tls_id": tls_ids["canary-reality"],
            "transport": {},
            "addrs": [{"server": PUBLIC_HOST, "server_port": 31443, "remark": "yuntu-canary"}],
            "out_json": {},
        },
        {
            "id": 0,
            "type": "hysteria2",
            "tag": "canary-hysteria2",
            "listen": "0.0.0.0",
            "listen_port": 32443,
            "tls_id": tls_ids["canary-tls"],
            "up_mbps": 100,
            "down_mbps": 100,
            "addrs": [{"server": PUBLIC_HOST, "server_port": 32443, "remark": "yuntu-canary"}],
            "out_json": {},
        },
        {
            "id": 0,
            "type": "socks",
            "tag": "canary-socks5",
            "listen": "0.0.0.0",
            "listen_port": 1080,
            "tls_id": 0,
            "addrs": [{"server": "verizon.bigpandas.top", "server_port": 1080, "remark": "-socks5"}],
            "out_json": {},
        },
    ]


def fetch_subscription(client_name: str, format_name: str = "") -> str:
    path = f"{SUI_SUB}/sub/{urllib.parse.quote(client_name, safe='')}"
    if format_name:
        path += "?" + urllib.parse.urlencode({"format": format_name})
    request = urllib.request.Request(path, headers={"Host": "sub-verizon.bigpandas.top"})
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status != 200:
            fail(f"subscription returned HTTP {response.status}")
        return response.read().decode()


def subscription_links(client_name: str) -> dict[str, str]:
    raw = fetch_subscription(client_name)
    decoded = raw
    if "://" not in decoded:
        try:
            decoded = base64.b64decode(raw + "=" * (-len(raw) % 4)).decode()
        except Exception as exc:  # noqa: BLE001
            fail(f"unable to decode raw subscription: {type(exc).__name__}")
    links = {}
    for line in decoded.splitlines():
        line = line.strip()
        if "://" not in line:
            continue
        scheme = line.split("://", 1)[0].lower()
        links.setdefault(scheme, line)
    return links


def verify_subscriptions(source: dict) -> None:
    expected_links = {"vless", "hysteria2"}
    expected_json = {"vless", "hysteria2"}
    for item in source["clients"]:
        raw = fetch_subscription(item["name"])
        decoded = raw
        if "://" not in decoded:
            try:
                decoded = base64.b64decode(raw + "=" * (-len(raw) % 4)).decode()
            except Exception as exc:  # noqa: BLE001
                fail(f"unable to decode raw subscription: {type(exc).__name__}")
        schemes = {
            line.split("://", 1)[0]
            for line in decoded.splitlines()
            if "://" in line
        }
        if not expected_links.issubset(schemes):
            fail(f"raw subscription is missing protocols: {sorted(expected_links - schemes)}")

        json_sub = json.loads(fetch_subscription(item["name"], "json"))
        outbound_types = {
            outbound.get("type")
            for outbound in json_sub.get("outbounds", [])
            if isinstance(outbound, dict)
        }
        if not expected_json.issubset(outbound_types):
            fail(
                "JSON subscription is missing protocols: "
                + str(sorted(expected_json - outbound_types))
            )

        clash = fetch_subscription(item["name"], "clash")
        for protocol in ("vless", "hysteria2"):
            if f"type: {protocol}" not in clash:
                fail(f"Clash subscription is missing protocol: {protocol}")
    print(f"verified subscriptions: {len(source['clients'])}")
    print("raw/json/clash protocol coverage: complete")


def verify_protocols(source: dict) -> None:
    """Perform real outbound checks through every main subscription protocol."""
    sui = SUI()
    sui.login()
    protocol_aliases = {"vless": "vless", "hysteria2": "hysteria2", "hy2": "hysteria2"}
    checks = []
    for client in source["clients"]:
        links = subscription_links(client["name"])
        found = set()
        for scheme, protocol in protocol_aliases.items():
            if scheme in links and protocol not in found:
                checks.append((client["name"], protocol, links[scheme]))
                found.add(protocol)
        present = {protocol_aliases[s] for s in links if s in protocol_aliases}
        missing = {"vless", "hysteria2"} - present
        if missing:
            fail(f"subscription is missing protocol links: {sorted(missing)}")

    verified = 0
    for index, (client_name, protocol, link) in enumerate(checks):
        # Tags are local and intentionally do not contain a client name or URI.
        tag = f"verify-{protocol}-{index}-{secrets.token_hex(4)}"
        outbound = sui.link_convert(link)
        if outbound.get("type") != protocol:
            fail(f"s-ui converted {protocol} into an unexpected outbound type")
        outbound["tag"] = tag
        try:
            sui.save("outbounds", outbound)
            result = sui.check_outbound(tag)
            delay = result.get("Delay")
            if delay is None:
                delay = result.get("delay", "unknown")
            verified += 1
            print(f"verified {protocol} outbound for client {index + 1}: {delay} ms")
        finally:
            try:
                sui.delete_outbound(tag)
            except Exception as exc:  # noqa: BLE001
                fail(f"unable to remove temporary outbound: {type(exc).__name__}")
    expected = len(source["clients"]) * 2
    if verified != expected:
        fail(f"verified {verified} protocol outbounds, expected {expected}")
    print("VLESS Reality and Hysteria2 real outbound checks: complete")


def verify_forward_proxies(source: dict) -> None:
    credential = f"{source['proxy']['name']}:{source['proxy']['password']}"
    checks = {
        "socks5": [
            "curl", "-4fsS", "--max-time", "20",
            "--socks5-hostname", "127.0.0.1:1080",
            "--proxy-user", credential,
            "https://api.ipify.org",
        ],
    }
    for name, command in checks.items():
        result = subprocess.run(command, capture_output=True, text=True, timeout=25)
        if result.returncode != 0:
            fail(f"{name} proxy test failed with curl exit {result.returncode}")
        if result.stdout.strip() != "47.178.15.216":
            fail(f"{name} proxy egress did not match the AaITR IPv4 address")
    print("verified forward proxy: direct AaITR SOCKS5")
    print("forward proxy egress: AaITR IPv4")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--verify-protocols", action="store_true")
    parser.add_argument("--verify-proxies", action="store_true")
    args = parser.parse_args()

    source = load_source()
    print(f"source VLESS REALITY inbound: 1 (id hidden)")
    print(f"source clients: {len(source['clients'])}")
    print("protocols to create: VLESS/REALITY, Hysteria2, direct SOCKS5")
    if args.verify:
        verify_subscriptions(source)
        return 0
    if args.verify_protocols:
        verify_protocols(source)
        return 0
    if args.verify_proxies:
        verify_forward_proxies(source)
        return 0
    if not args.apply:
        print("dry run only; no s-ui data was changed")
        return 0

    public_key = derive_public_key(source["reality"]["private_key"])
    sui = SUI()
    sui.login()
    existing_tls = {x.get("name"): x for x in (sui.get("tls") or [])}
    tls_reality, tls_cert = tls_profiles(source, public_key)
    tls_ids = {}
    for profile in (tls_reality, tls_cert):
        old = existing_tls.get(profile["name"])
        if old:
            tls_ids[profile["name"]] = int(old["id"])
        else:
            saved = sui.save("tls", profile)
            if not saved:
                fail(f"s-ui did not return TLS profile {profile['name']}")
            current = {x.get("name"): x for x in (sui.get("tls") or [])}
            if profile["name"] not in current:
                fail(f"s-ui did not persist TLS profile {profile['name']}")
            tls_ids[profile["name"]] = int(current[profile["name"]]["id"])

    existing_clients = {x.get("name"): x for x in (sui.get("clients") or [])}
    client_ids = []
    for source_client in source["clients"]:
        if source_client["name"] in existing_clients:
            client_ids.append(int(existing_clients[source_client["name"]]["id"]))
            continue
        sui.save("clients", client_payload(source_client))
        current = {x.get("name"): x for x in (sui.get("clients") or [])}
        if source_client["name"] not in current:
            fail("s-ui did not persist a migrated client")
        client_ids.append(int(current[source_client["name"]]["id"]))

    proxy_name = source["proxy"]["name"]
    current_clients = {x.get("name"): x for x in (sui.get("clients") or [])}
    if proxy_name not in current_clients:
        sui.save("clients", proxy_client_payload(source["proxy"]))
        current_clients = {x.get("name"): x for x in (sui.get("clients") or [])}
    if proxy_name not in current_clients:
        fail("s-ui did not persist the forward proxy client")
    proxy_id = int(current_clients[proxy_name]["id"])

    existing_inbounds = {x.get("tag"): x for x in (sui.get("inbounds") or [])}
    for inbound in inbound_payloads(tls_ids):
        if inbound["tag"] in existing_inbounds:
            continue
        init_ids = client_ids if inbound["tag"] in {"canary-reality", "canary-hysteria2"} else [proxy_id]
        sui.save("inbounds", inbound, ",".join(str(x) for x in init_ids))

    current_inbounds = {x.get("tag"): x for x in (sui.get("inbounds") or [])}
    core_ids = [int(current_inbounds[tag]["id"]) for tag in ("canary-reality", "canary-hysteria2")]
    proxy_ids = [int(current_inbounds["canary-socks5"]["id"])]

    for source_client in source["clients"]:
        client_id = int(current_clients[source_client["name"]]["id"])
        full = (sui.get("clients", {"id": client_id}) or [None])[0]
        if not full:
            fail("unable to load a migrated client for reconciliation")
        full["inbounds"] = core_ids
        if isinstance(full.get("config"), dict):
            for key in ("socks", "http", "mixed", "shadowsocks", "shadowsocks16", "anytls"):
                full["config"].pop(key, None)
        sui.save("clients", full, action="edit")

    proxy_full = (sui.get("clients", {"id": proxy_id}) or [None])[0]
    if not proxy_full:
        fail("unable to load the forward proxy client for reconciliation")
    proxy_full["inbounds"] = proxy_ids
    proxy_full["config"] = proxy_client_payload(source["proxy"])["config"]
    sui.save("clients", proxy_full, action="edit")

    print("s-ui canary objects created successfully")
    print(f"migrated clients: {len(client_ids)}")
    print("forward proxy account: migrated separately")
    print("subscription path is /sub/<existing-sub-id> on port 3096")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"migration failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
