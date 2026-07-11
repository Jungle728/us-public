#!/usr/bin/env bash
set -euo pipefail

stack_dir="${STACK_DIR:-/opt/3x-ui}"
container="${XUI_CONTAINER:-3x-ui}"

cd "$stack_dir"
docker compose up -d x-ui

docker exec -i "$container" python3 - <<'PY'
import datetime
import os
import sqlite3

database_path = "/etc/x-ui/x-ui.db"
template_path = "/opt/templates/mihomo-template.yaml"
backup_dir = "/etc/x-ui/backups"

with open(template_path, "r", encoding="utf-8") as handle:
    template = handle.read()

os.makedirs(backup_dir, mode=0o700, exist_ok=True)
timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup_path = os.path.join(backup_dir, f"x-ui-before-mihomo-{timestamp}.db")

source = sqlite3.connect(database_path, timeout=10)
backup = sqlite3.connect(backup_path)
source.backup(backup)
backup.close()
os.chmod(backup_path, 0o600)

for key, value in (
    ("subClashEnableRouting", "true"),
    ("subClashRules", template),
):
    row = source.execute("SELECT id FROM settings WHERE key = ?", (key,)).fetchone()
    if row:
        source.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
    else:
        source.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))

source.commit()
source.close()
PY

docker compose restart x-ui

for _ in $(seq 1 60); do
  state=$(docker inspect "$container" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}')
  if [[ "$state" == "healthy" ]]; then
    exit 0
  fi
  sleep 1
done

echo "3X-UI 重启后未通过健康检查。" >&2
exit 1
