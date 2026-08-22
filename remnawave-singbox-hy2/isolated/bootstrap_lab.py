#!/usr/bin/env python3
"""Create and provision the isolated Remnawave + sing-box HY2 accounting lab."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import string
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
PANEL_ENV = ROOT / "panel.env"
ADMIN_ENV = ROOT / "admin.env"
NODE_ENV = ROOT / "node.env"
STATE = ROOT / "lab-state.json"
RUNTIME = ROOT / "runtime"
DEFAULT_BASE_URL = "http://127.0.0.1:3300"
PROXY_HEADERS = {
    "X-Forwarded-For": "127.0.0.1",
    "X-Forwarded-Proto": "https",
    "X-Remnawave-Client-Type": "browser",
}


def secure_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.chmod(path, 0o600)


def random_alnum(length: int) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def init_runtime(force: bool) -> None:
    existing = [path for path in (PANEL_ENV, ADMIN_ENV) if path.exists()]
    if existing and not force:
        raise SystemExit("runtime environment already exists; use --force only for a fresh lab")

    postgres_password = random_alnum(40)
    app_secret = secrets.token_hex(48)
    metrics_password = random_alnum(32)
    admin_password = f"A{random_alnum(30)}z9"

    panel = f"""APP_PORT=3000
METRICS_PORT=3001
API_INSTANCES=1
DATABASE_URL=postgresql://remnawave_hy2_lab:{postgres_password}@hy2-db:5432/remnawave_hy2_lab
POSTGRES_USER=remnawave_hy2_lab
POSTGRES_PASSWORD={postgres_password}
POSTGRES_DB=remnawave_hy2_lab
REDIS_HOST=hy2-valkey
REDIS_PORT=6379
REDIS_DB=1
APP_SECRET={app_secret}
FRONT_END_DOMAIN=http://127.0.0.1:3300
PANEL_DOMAIN=http://127.0.0.1:3300
SUB_PUBLIC_DOMAIN=127.0.0.1:3300
METRICS_USER=hy2_lab
METRICS_PASS={metrics_password}
IS_TELEGRAM_NOTIFICATIONS_ENABLED=false
WEBHOOK_ENABLED=false
EXPORT_TO_STREAM_ENABLED=false
SERVICE_DISABLE_USER_USAGE_RECORDS=false
USER_USAGE_IGNORE_BELOW_BYTES=0
"""
    admin = f"ADMIN_USERNAME=hy2_lab_admin\nADMIN_PASSWORD={admin_password}\n"
    secure_write(PANEL_ENV, panel)
    secure_write(ADMIN_ENV, admin)
    print("created isolated runtime environment (credentials were not printed)")


def read_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        result[key] = value
    return result


class Api:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None

    def request(self, method: str, path: str, data: Any | None = None) -> Any:
        body = None if data is None else json.dumps(data).encode("utf-8")
        headers = {"Accept": "application/json", **PROXY_HEADERS}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=body, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
                return json.loads(payload) if payload else None
        except urllib.error.HTTPError as error:
            payload = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method} {path} failed with HTTP {error.code}: {payload}") from error

    def authenticate(self, username: str, password: str) -> None:
        try:
            result = self.request(
                "POST", "/api/auth/register", {"username": username, "password": password}
            )
        except RuntimeError:
            result = self.request(
                "POST", "/api/auth/login", {"username": username, "password": password}
            )
        self.token = result["response"]["accessToken"]


def first_uuid(value: dict[str, Any], key: str = "uuid") -> str:
    result = value.get(key)
    if not isinstance(result, str):
        raise RuntimeError(f"response is missing {key}")
    return result


def client_config(port: int, password: str) -> dict[str, Any]:
    return {
        "log": {"level": "warn", "timestamp": True},
        "inbounds": [
            {
                "type": "mixed",
                "tag": "mixed-in",
                "listen": "0.0.0.0",
                "listen_port": port,
            }
        ],
        "outbounds": [
            {
                "type": "hysteria2",
                "tag": "hy2-out",
                "server": "hy2-node",
                "server_port": 35443,
                "password": password,
                "tls": {"enabled": True, "server_name": "verizon.bigpandas.top"},
            }
        ],
        "route": {"final": "hy2-out", "auto_detect_interface": True},
    }


def provision(base_url: str) -> None:
    if STATE.exists():
        raise SystemExit("lab-state.json already exists; refusing to create duplicate test objects")
    admin = read_env(ADMIN_ENV)
    api = Api(base_url)
    api.authenticate(admin["ADMIN_USERNAME"], admin["ADMIN_PASSWORD"])

    profile_config = {
        "log": {"level": "warn", "timestamp": True},
        "inbounds": [
            {
                "type": "hysteria2",
                "tag": "hy2-accounting-lab",
                "listen": "0.0.0.0",
                "listen_port": 35443,
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
    profile = api.request(
        "POST",
        "/api/config-profiles",
        {"name": "HY2 Accounting Lab", "coreType": "singbox", "config": profile_config},
    )["response"]
    profile_uuid = first_uuid(profile)
    inbound_uuid = first_uuid(profile["inbounds"][0])

    squad = api.request(
        "POST", "/api/internal-squads", {"name": "HY2 Accounting Lab", "inbounds": [inbound_uuid]}
    )["response"]
    squad_uuid = first_uuid(squad)

    node = api.request(
        "POST",
        "/api/nodes",
        {
            "name": "HY2 Accounting Lab",
            "address": "hy2-node",
            "port": 2322,
            "isTrafficTrackingActive": True,
            "countryCode": "US",
            "consumptionMultiplier": 1,
            "nodeConsumptionMultiplier": 1,
            "configProfile": {
                "activeConfigProfileUuid": profile_uuid,
                "activeInbounds": [inbound_uuid],
            },
            "tags": ["HY2_LAB"],
        },
    )["response"]
    node_uuid = first_uuid(node)

    host = api.request(
        "POST",
        "/api/hosts",
        {
            "inbound": {
                "configProfileUuid": profile_uuid,
                "configProfileInboundUuid": inbound_uuid,
            },
            "remark": "hy2-accounting-lab",
            "address": "127.0.0.1",
            "port": 35443,
            "sni": "verizon.bigpandas.top",
            "securityLayer": "TLS",
            "nodes": [node_uuid],
            "tags": ["HY2_LAB"],
        },
    )["response"]
    host_uuid = first_uuid(host)

    expire_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    users: list[dict[str, Any]] = []
    for suffix in ("a", "b"):
        user = api.request(
            "POST",
            "/api/users",
            {
                "username": f"hy2_meter_{suffix}",
                "status": "ACTIVE",
                "trafficLimitBytes": (50 if suffix == "a" else 1) * 1024 * 1024,
                "trafficLimitStrategy": "NO_RESET",
                "expireAt": expire_at,
                "activeInternalSquads": [squad_uuid],
                "description": "isolated HY2 accounting validation",
            },
        )["response"]
        users.append(
            {
                "id": user["id"],
                "shortUuid": user["shortUuid"],
                "username": user["username"],
                "vlessUuid": user["vlessUuid"],
            }
        )

    secret_key = api.request("GET", "/api/keygen")["response"]["secretKey"]
    secure_write(
        NODE_ENV,
        "".join(
            (
                "NODE_PORT=2322\n",
                f"SECRET_KEY={secret_key}\n",
                "SINGBOX_STATS_STATE_PATH=/var/lib/remnawave/singbox-stats.json\n",
            )
        ),
    )

    secure_write(RUNTIME / "client-a.json", json.dumps(client_config(20880, users[0]["vlessUuid"]), indent=2))
    secure_write(RUNTIME / "client-b.json", json.dumps(client_config(20881, users[1]["vlessUuid"]), indent=2))
    secure_write(
        STATE,
        json.dumps(
            {
                "baseUrl": base_url,
                "profileUuid": profile_uuid,
                "inboundUuid": inbound_uuid,
                "squadUuid": squad_uuid,
                "nodeUuid": node_uuid,
                "hostUuid": host_uuid,
                "users": users,
            },
            indent=2,
        ),
    )
    print(
        "provisioned profile, node, host, squad and two metered users "
        "(credentials were not printed)"
    )


def wait_panel(base_url: str, timeout: int) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request(
                f"{base_url.rstrip('/')}/api/auth/status", headers=PROXY_HEADERS
            )
            with urllib.request.urlopen(request, timeout=3):
                print("isolated panel API is ready")
                return
        except Exception:
            time.sleep(2)
    raise SystemExit("timed out waiting for isolated panel API")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--force", action="store_true")
    wait_parser = subparsers.add_parser("wait")
    wait_parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    wait_parser.add_argument("--timeout", type=int, default=180)
    provision_parser = subparsers.add_parser("provision")
    provision_parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    if args.command == "init":
        init_runtime(args.force)
    elif args.command == "wait":
        wait_panel(args.base_url, args.timeout)
    elif args.command == "provision":
        provision(args.base_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
