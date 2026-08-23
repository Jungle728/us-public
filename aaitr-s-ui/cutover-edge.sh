#!/bin/sh
set -eu

OLD=/opt/3x-ui
EDGE=/root/code/us-public/s-ui-edge
BACKUP=$EDGE/backups/$(date +%Y%m%d-%H%M%S)

mkdir -p "$BACKUP"
cp -a "$OLD/docker-compose.yml" "$BACKUP/docker-compose.yml"
cp -a "$OLD/nginx/nginx.conf" "$BACKUP/nginx.conf"

docker compose -f "$EDGE/docker-compose.yml" config -q
docker compose -f "$EDGE/docker-compose.yml" run --rm --no-deps nginx nginx -t

docker compose -f "$OLD/docker-compose.yml" down
if docker compose -f "$EDGE/docker-compose.yml" up -d; then
    sleep 3
    if docker compose -f "$EDGE/docker-compose.yml" ps --status running | grep -q s-ui-edge-nginx; then
        echo "s-ui edge cutover: complete"
        exit 0
    fi
fi

echo "s-ui edge cutover failed; restoring 3x-ui edge" >&2
docker compose -f "$EDGE/docker-compose.yml" down || true
docker compose -f "$OLD/docker-compose.yml" up -d
exit 1
