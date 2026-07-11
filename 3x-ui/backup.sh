#!/usr/bin/env bash
set -euo pipefail

stack_dir="${STACK_DIR:-/opt/3x-ui}"
backup_dir="${BACKUP_DIR:-/root/3x-ui-backups}"
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
archive="$backup_dir/3x-ui-$timestamp.tar.gz"

install -d -m 700 "$backup_dir"
cd "$stack_dir"

restart_stack() {
  docker compose up -d >/dev/null
}

docker compose stop
trap restart_stack EXIT

tar \
  --acls \
  --xattrs \
  --numeric-owner \
  --exclude='3x-ui/logs/*' \
  --exclude='3x-ui/certbot-logs/*' \
  -C "$(dirname "$stack_dir")" \
  -czf "$archive" \
  "$(basename "$stack_dir")"

chmod 600 "$archive"
sha256sum "$archive" >"$archive.sha256"
chmod 600 "$archive.sha256"

trap - EXIT
restart_stack

printf '%s\n' "$archive"
