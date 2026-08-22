#!/usr/bin/env python3
"""Export active Remnawave users to a standalone sing-box Hysteria2 server."""

import argparse
import fcntl
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


def api_request(base_url: str, token: str, path: str):
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Remnawave API returned HTTP {error.code}: {detail}"
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Remnawave API request failed: {error.reason}") from error


def load_token(token_file: Path) -> str:
    token = os.environ.get("REMNAWAVE_API_TOKEN", "").strip()
    if token:
        return token
    try:
        token = token_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError as error:
        raise RuntimeError(
            "Set REMNAWAVE_API_TOKEN or provide an existing --token-file."
        ) from error
    if not token:
        raise RuntimeError("The Remnawave API token is empty.")
    return token


def load_active_users(panel_url: str, token: str):
    payload = api_request(panel_url, token, "/api/users?start=0&size=1000")
    response = payload.get("response", payload)
    users = response.get("users", []) if isinstance(response, dict) else response
    if not isinstance(users, list):
        raise RuntimeError("Unexpected users response from Remnawave API.")

    exported = []
    for user in users:
        if user.get("status") != "ACTIVE":
            continue
        username = str(user.get("username", "")).strip()
        password = str(user.get("vlessUuid", "")).strip()
        if not username or not password:
            raise RuntimeError("An active Remnawave user lacks username or vlessUuid.")
        exported.append({"name": username, "password": password})

    exported.sort(key=lambda item: item["name"])
    if not exported:
        raise RuntimeError("Refusing to publish an empty Hysteria2 user list.")
    return exported


def build_config(args, users):
    return {
        "log": {"level": "warn", "timestamp": True},
        "inbounds": [
            {
                "type": "hysteria2",
                "tag": "remnawave-hy2-in",
                "listen": "0.0.0.0",
                "listen_port": args.listen_port,
                "up_mbps": args.up_mbps,
                "down_mbps": args.down_mbps,
                "users": users,
                "tls": {
                    "enabled": True,
                    "server_name": args.server_name,
                    "certificate_path": str(args.certificate),
                    "key_path": str(args.private_key),
                },
            }
        ],
    }


def encode_config(config) -> bytes:
    return (json.dumps(config, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def replace_if_changed(output: Path, content: bytes) -> bool:
    try:
        if output.read_bytes() == content:
            os.chmod(output, 0o600)
            return False
    except FileNotFoundError:
        pass

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as temp:
        temp_path = Path(temp.name)
        os.chmod(temp_path, 0o600)
        temp.write(content)
        temp.flush()
        os.fsync(temp.fileno())
    try:
        os.replace(temp_path, output)
        os.chmod(output, 0o600)
    finally:
        temp_path.unlink(missing_ok=True)
    return True


def recreate_if_running(compose_dir: Path):
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--project-directory",
            str(compose_dir),
            "ps",
            "--status",
            "running",
            "--services",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if "hy2" in result.stdout.split():
        subprocess.run(
            [
                "docker",
                "compose",
                "--project-directory",
                str(compose_dir),
                "up",
                "-d",
                "--force-recreate",
                "hy2",
            ],
            check=True,
        )


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel-url", default="https://panel-verizon.bigpandas.top")
    parser.add_argument(
        "--token-file", type=Path, default=script_dir.parent / "remnawave/.api-token"
    )
    parser.add_argument("--output", type=Path, default=script_dir / "config.json")
    parser.add_argument("--listen-port", type=int, default=34443)
    parser.add_argument("--up-mbps", type=int, default=100)
    parser.add_argument("--down-mbps", type=int, default=100)
    parser.add_argument("--server-name", default="verizon.bigpandas.top")
    parser.add_argument(
        "--certificate",
        type=Path,
        default=Path("/etc/letsencrypt/live/remnawave-domains/fullchain.pem"),
    )
    parser.add_argument(
        "--private-key",
        type=Path,
        default=Path("/etc/letsencrypt/live/remnawave-domains/privkey.pem"),
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--compose-dir", type=Path, default=script_dir)
    args = parser.parse_args()

    if not 1 <= args.listen_port <= 65535:
        raise RuntimeError("--listen-port must be between 1 and 65535.")
    if args.up_mbps <= 0 or args.down_mbps <= 0:
        raise RuntimeError("Bandwidth values must be positive.")
    if args.check and args.restart:
        raise RuntimeError("--check and --restart cannot be used together.")

    lock_path = args.output.parent / ".sync.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        token = load_token(args.token_file)
        users = load_active_users(args.panel_url, token)
        content = encode_config(build_config(args, users))

        if args.check:
            current = args.output.exists() and args.output.read_bytes() == content
            print(
                f"Hysteria2 user configuration is {'current' if current else 'different'} "
                f"({len(users)} active users)."
            )
            return 0 if current else 1

        changed = replace_if_changed(args.output, content)
        if changed and args.restart:
            recreate_if_running(args.compose_dir)
        state = "updated" if changed else "already current"
        print(f"Hysteria2 user configuration {state} ({len(users)} active users).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
