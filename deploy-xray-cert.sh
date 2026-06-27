#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:-proxy.bigpandas.top}"
SOURCE_DIR="/etc/letsencrypt/live/${DOMAIN}"
TARGET_DIR="/usr/local/etc/xray/certs"
SING_BOX_TARGET_DIR="/etc/sing-box/certs"

install -d -m 700 -o nobody -g nogroup "${TARGET_DIR}"
install -m 600 -o nobody -g nogroup "${SOURCE_DIR}/fullchain.pem" "${TARGET_DIR}/fullchain.pem"
install -m 600 -o nobody -g nogroup "${SOURCE_DIR}/privkey.pem" "${TARGET_DIR}/privkey.pem"

if id sing-box >/dev/null 2>&1; then
  install -d -m 700 -o sing-box -g sing-box "${SING_BOX_TARGET_DIR}"
  install -m 600 -o sing-box -g sing-box "${SOURCE_DIR}/fullchain.pem" "${SING_BOX_TARGET_DIR}/fullchain.pem"
  install -m 600 -o sing-box -g sing-box "${SOURCE_DIR}/privkey.pem" "${SING_BOX_TARGET_DIR}/privkey.pem"
fi

systemctl restart xray
if systemctl list-unit-files sing-box.service >/dev/null 2>&1; then
  systemctl restart sing-box
fi
