#!/usr/bin/env python3
"""Sync the Remnawave TLS certificate to the CStoneCloud node."""

from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path


DEFAULT_SOURCE = Path(
    "/root/code/us-public/remnawave-edge/letsencrypt/live/remnawave-domains"
)
DEFAULT_IDENTITY = Path("/root/.ssh/remnawave_cert_sync_ed25519")
DEFAULT_REMOTE = "root@70.39.179.159"
DEFAULT_REMOTE_DIR = "/root/code/aaitr/remnawave-node/cert"


def run(command: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=90,
    )


def ssh_base(identity_file: Path, remote: str) -> list[str]:
    return [
        "ssh",
        "-i",
        str(identity_file),
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        remote,
    ]


def scp_base(identity_file: Path) -> list[str]:
    return [
        "scp",
        "-q",
        "-i",
        str(identity_file),
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--identity-file", type=Path, default=DEFAULT_IDENTITY)
    parser.add_argument("--remote", default=DEFAULT_REMOTE)
    parser.add_argument("--remote-dir", default=DEFAULT_REMOTE_DIR)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="verify SSH access and the local certificate without copying files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fullchain = args.source_dir / "fullchain.pem"
    privkey = args.source_dir / "privkey.pem"

    for path in (fullchain, privkey, args.identity_file):
        if not path.is_file():
            raise SystemExit(f"required file is missing: {path}")

    run(["openssl", "x509", "-checkend", "604800", "-noout", "-in", str(fullchain)])
    ssh = ssh_base(args.identity_file, args.remote)
    run(ssh + ["true"])

    if args.check_only:
        print("Remnawave certificate and CStoneCloud SSH access are valid")
        return 0

    remote_dir = args.remote_dir
    quoted_remote_dir = shlex.quote(remote_dir)
    run(ssh + [f"install -d -m 0700 {quoted_remote_dir}"])
    scp = scp_base(args.identity_file)
    run(scp + [str(fullchain), f"{args.remote}:{remote_dir}/.fullchain.pem.next"])
    run(scp + [str(privkey), f"{args.remote}:{remote_dir}/.privkey.pem.next"])

    remote_script = f"""
set -eu
remote_dir={quoted_remote_dir}
next_full="$remote_dir/.fullchain.pem.next"
next_key="$remote_dir/.privkey.pem.next"
full="$remote_dir/fullchain.pem"
key="$remote_dir/privkey.pem"

openssl x509 -checkend 604800 -noout -in "$next_full" >/dev/null
cert_pub=$(openssl x509 -pubkey -noout -in "$next_full" | sha256sum | awk '{{print $1}}')
key_pub=$(openssl pkey -pubout -in "$next_key" | sha256sum | awk '{{print $1}}')
test "$cert_pub" = "$key_pub"

if cmp -s "$next_full" "$full" && cmp -s "$next_key" "$key"; then
    echo unchanged
    exit 0
fi

install -m 0644 "$next_full" "$full"
install -m 0600 "$next_key" "$key"
cd /root/code/aaitr/remnawave-node
docker compose restart remnanode >/dev/null
echo updated
""".strip()

    result = run(ssh + ["sh", "-s"], input_text=remote_script)
    status = result.stdout.strip() or "updated"
    print(f"CStoneCloud Remnawave certificate: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
