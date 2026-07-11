#!/usr/bin/env bash
set -euo pipefail

stack_dir="${STACK_DIR:-/opt/3x-ui}"
email="${LE_EMAIL:-}"

if [[ -z "$email" ]]; then
  echo "请通过 LE_EMAIL 提供 Let's Encrypt 联系邮箱。" >&2
  exit 1
fi

cd "$stack_dir"
install -d -m 700 letsencrypt certbot-lib certbot-logs
install -d -m 755 certbot-www

docker compose run --rm --no-deps --entrypoint certbot certbot \
  certonly \
  --standalone \
  --non-interactive \
  --agree-tos \
  --no-eff-email \
  --email "$email" \
  --cert-name 3x-ui-domains \
  -d panel.bigpandas.top \
  -d sub.bigpandas.top

docker compose up -d
