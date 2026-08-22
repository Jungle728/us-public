#!/usr/bin/env python3
"""Prepare, validate, and optionally build the Remnawave sing-box HY2 fork."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


BACKEND_REPO = "https://github.com/Cd1s/remnawave-backend.git"
BACKEND_COMMIT = "257ba1c2bcc36fee1a117a148e1b6d0b09613ffb"
NODE_REPO = "https://github.com/Cd1s/remnawave-node.git"
NODE_COMMIT = "079be99ab2f19744d0ca1336702b456d590fb786"
FRONTEND_REPO = "https://github.com/Cd1s/remnawave-frontend.git"
FRONTEND_COMMIT = "4bdde8a18cd2bc93630ba70191232ef3e8ca2d34"


def run(command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None):
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, env=env, check=True)


def require_empty(path: Path):
    if path.exists() and any(path.iterdir()):
        raise RuntimeError(f"Refusing to overwrite non-empty directory: {path}")
    path.mkdir(parents=True, exist_ok=True)


def clone_at(repo: str, commit: str, destination: Path):
    run(["git", "clone", "--filter=blob:none", "--no-checkout", repo, str(destination)])
    run(["git", "fetch", "--depth", "1", "origin", commit], cwd=destination)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=destination)
    actual = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=destination,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual != commit:
        raise RuntimeError(f"Expected {commit}, checked out {actual} in {destination}")


def apply_patch(source: Path, patch: Path):
    run(["git", "apply", "--check", str(patch)], cwd=source)
    run(["git", "apply", str(patch)], cwd=source)
    run(["git", "diff", "--check"], cwd=source)


def validate_on_host(backend: Path, node: Path, frontend: Path):
    run(["npm", "ci", "--no-audit", "--no-fund"], cwd=backend)
    run(["npm", "run", "validate:hysteria2"], cwd=backend)
    run(["npm", "run", "check"], cwd=backend)
    run(["npm", "run", "build"], cwd=backend)
    run(["npm", "run", "build:seed"], cwd=backend)

    run(["npm", "ci", "--no-audit", "--no-fund"], cwd=node)
    run(["npm", "run", "validate:dual-core", "--", "--skip-binary"], cwd=node)
    run(["npm", "run", "check"], cwd=node)
    run(["npm", "run", "build"], cwd=node)
    run(["npm", "run", "typecheck"], cwd=node)

    run(["npm", "ci", "--no-audit", "--no-fund"], cwd=frontend)
    run(["npm", "run", "check"], cwd=frontend)
    run(["npm", "run", "typecheck"], cwd=frontend)


def validate_in_container(backend: Path, node: Path, frontend: Path):
    backend_command = " && ".join(
        [
            "npm ci --no-audit --no-fund",
            "npm run validate:hysteria2",
            "npm run check",
            "npm run build",
            "npm run build:seed",
        ]
    )
    node_command = " && ".join(
        [
            "npm ci --no-audit --no-fund",
            "npm run validate:dual-core -- --skip-binary",
            "npm run check",
            "npm run build",
            "npm run typecheck",
        ]
    )
    frontend_command = " && ".join(
        [
            "npm ci --no-audit --no-fund",
            "npm run check",
            "npm run typecheck",
        ]
    )
    for source, command in (
        (backend, backend_command),
        (node, node_command),
        (frontend, frontend_command),
    ):
        run(
            [
                "docker",
                "run",
                "--rm",
                "--volume",
                f"{source}:/work",
                "--workdir",
                "/work",
                "node:24.19-trixie-slim",
                "sh",
                "-lc",
                command,
            ]
        )


def validate(backend: Path, node: Path, frontend: Path):
    if shutil.which("npm") and shutil.which("node"):
        version = subprocess.run(
            ["node", "--version"], check=True, capture_output=True, text=True
        ).stdout.strip()
        try:
            major = int(version.removeprefix("v").split(".", 1)[0])
        except ValueError:
            major = 0
        if major >= 24:
            validate_on_host(backend, node, frontend)
            return
    validate_in_container(backend, node, frontend)


def build(backend: Path, node: Path, backend_image: str, node_image: str):
    run(
        [
            "docker",
            "build",
            "--file",
            "Dockerfile",
            "--build-arg",
            f"FRONTEND_REF={FRONTEND_COMMIT}",
            "--build-arg",
            f"__RW_METADATA_GIT_BACKEND_COMMIT={BACKEND_COMMIT}",
            "--build-arg",
            f"__RW_METADATA_GIT_FRONTEND_COMMIT={FRONTEND_COMMIT}",
            "--build-arg",
            "__RW_METADATA_VERSION=3.3.2",
            "--build-arg",
            "__RW_METADATA_GIT_BRANCH=singbox-hy2",
            "--tag",
            backend_image,
            ".",
        ],
        cwd=backend,
    )
    run(
        [
            "docker",
            "build",
            "--file",
            "docker/Dockerfile",
            "--build-arg",
            "RWNODE_VERSION=3.3.2-singbox-hy2",
            "--build-arg",
            "XRAY_CORE_VERSION=v26.6.27",
            "--build-arg",
            "SINGBOX_CORE_VERSION=v1.13.15",
            "--build-arg",
            "SINGBOX_CORE_VERSION_NAME=1.13.15",
            "--tag",
            node_image,
            ".",
        ],
        cwd=node,
    )


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--build", action="store_true")
    parser.add_argument(
        "--backend-image", default="local/remnawave-backend:3.3.2-singbox-hy2"
    )
    parser.add_argument(
        "--node-image", default="local/remnawave-node:3.3.2-singbox-hy2"
    )
    args = parser.parse_args()

    require_empty(args.workdir)
    backend = args.workdir / "backend"
    node = args.workdir / "node"
    frontend = args.workdir / "frontend"
    clone_at(BACKEND_REPO, BACKEND_COMMIT, backend)
    clone_at(NODE_REPO, NODE_COMMIT, node)
    clone_at(FRONTEND_REPO, FRONTEND_COMMIT, frontend)
    apply_patch(backend, script_dir / "patches/backend-hysteria2.patch")
    apply_patch(node, script_dir / "patches/node-hysteria2.patch")
    apply_patch(frontend, script_dir / "patches/frontend-hysteria2.patch")
    shutil.copyfile(
        script_dir / "patches/frontend-hysteria2.patch",
        backend / "frontend-hysteria2.patch",
    )
    validate(backend, node, frontend)
    if args.build:
        build(backend, node, args.backend_image, args.node_image)
    print(f"Prepared patched sources in {args.workdir}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
