#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:-proxy.bigpandas.top}"
APP_DIR="${APP_DIR:-/opt/proxy-subscription}"
SECRETS_FILE="${SECRETS_FILE:-/root/proxy-subscription-secrets.env}"
NGINX_IMAGE="${NGINX_IMAGE:-nginx:1.27-alpine}"
XRAY_IMAGE="${XRAY_IMAGE:-proxy-subscription-xray:local}"
SING_BOX_IMAGE="${SING_BOX_IMAGE:-proxy-subscription-sing-box:local}"
STAMP="$(date +%Y%m%d%H%M%S)"
MIGRATION_STARTED=0
MIGRATION_DONE=0

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo bash $0"
  exit 1
fi

log() {
  printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"
}

apt_wait() {
  apt-get -o DPkg::Lock::Timeout=600 "$@"
}

compose() {
  docker compose -f "${APP_DIR}/docker-compose.yml" "$@"
}

rollback() {
  if [ "$MIGRATION_STARTED" -eq 1 ] && [ "$MIGRATION_DONE" -eq 0 ]; then
    log "Migration failed, rolling back to host services"
    compose down >/dev/null 2>&1 || true
    systemctl enable --now nginx >/dev/null 2>&1 || true
    systemctl enable --now xray >/dev/null 2>&1 || true
    systemctl enable --now sing-box >/dev/null 2>&1 || true
  fi
}

trap rollback ERR

require_existing_runtime() {
  if [ ! -r "$SECRETS_FILE" ]; then
    echo "Missing ${SECRETS_FILE}. Run the bare-metal bootstrap once or provide existing secrets."
    exit 1
  fi

  if [ ! -r "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ] || [ ! -r "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" ]; then
    echo "Missing Let's Encrypt certificate for ${DOMAIN}."
    exit 1
  fi

  if [ ! -x /usr/local/bin/xray ] || [ ! -x /usr/bin/sing-box ]; then
    echo "Missing host xray or sing-box binaries used to build local container images."
    exit 1
  fi

  # shellcheck source=/dev/null
  . "$SECRETS_FILE"
  : "${SUB_TOKEN:?missing SUB_TOKEN}"
  : "${XRAY_UUID:?missing XRAY_UUID}"
  : "${TROJAN_PASSWORD:?missing TROJAN_PASSWORD}"
  : "${HY2_PASSWORD:?missing HY2_PASSWORD}"
  : "${ANYTLS_PASSWORD:?missing ANYTLS_PASSWORD}"
}

install_docker() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    return
  fi

  log "Installing Docker and Compose"
  apt_wait update
  DEBIAN_FRONTEND=noninteractive apt_wait install -y docker.io docker-compose-v2
  systemctl enable --now docker
}

prepare_layout() {
  log "Preparing ${APP_DIR}"
  install -d -m 0755 \
    "$APP_DIR" \
    "$APP_DIR/images/xray" \
    "$APP_DIR/images/sing-box" \
    "$APP_DIR/nginx" \
    "$APP_DIR/xray" \
    "$APP_DIR/sing-box" \
    "$APP_DIR/www/sub/${SUB_TOKEN}"
  install -d -m 0700 "$APP_DIR/certs"

  cp -a /var/www/html/. "$APP_DIR/www/"
  printf 'ok\n' >"$APP_DIR/www/index.html"

  install -m 0755 /usr/local/bin/xray "$APP_DIR/images/xray/xray"
  install -m 0755 /usr/bin/sing-box "$APP_DIR/images/sing-box/sing-box"

  cat >"$APP_DIR/images/xray/Dockerfile" <<'EOF'
FROM scratch
COPY xray /usr/local/bin/xray
ENTRYPOINT ["/usr/local/bin/xray"]
EOF

  cat >"$APP_DIR/images/sing-box/Dockerfile" <<'EOF'
FROM scratch
COPY sing-box /usr/local/bin/sing-box
ENTRYPOINT ["/usr/local/bin/sing-box"]
EOF
}

sync_certs() {
  log "Syncing TLS certificates"
  install -d -m 0700 "$APP_DIR/certs"
  install -m 0600 "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" "$APP_DIR/certs/fullchain.pem"
  install -m 0600 "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" "$APP_DIR/certs/privkey.pem"
}

write_nginx_config() {
  cat >"$APP_DIR/nginx/default.conf" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    root /var/www/html;
    index index.html;

    location /.well-known/acme-challenge/ {
        try_files \$uri =404;
    }

    location / {
        return 200 "ok\n";
        add_header Content-Type text/plain;
    }
}

server {
    listen 127.0.0.1:8080;
    server_name ${DOMAIN};

    root /var/www/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF
}

write_xray_config() {
  cat >"$APP_DIR/xray/config.json" <<EOF
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "tag": "vless-vision-443",
      "listen": "0.0.0.0",
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "${XRAY_UUID}",
            "flow": "xtls-rprx-vision"
          }
        ],
        "decryption": "none",
        "fallbacks": [
          {
            "dest": 8080
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {
          "alpn": [
            "http/1.1"
          ],
          "certificates": [
            {
              "certificateFile": "${APP_DIR}/certs/fullchain.pem",
              "keyFile": "${APP_DIR}/certs/privkey.pem"
            }
          ]
        }
      },
      "sniffing": {
        "enabled": true,
        "destOverride": [
          "http",
          "tls",
          "quic"
        ]
      }
    },
    {
      "tag": "trojan-8443",
      "listen": "0.0.0.0",
      "port": 8443,
      "protocol": "trojan",
      "settings": {
        "clients": [
          {
            "password": "${TROJAN_PASSWORD}"
          }
        ],
        "fallbacks": [
          {
            "dest": 8080
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {
          "alpn": [
            "http/1.1"
          ],
          "certificates": [
            {
              "certificateFile": "${APP_DIR}/certs/fullchain.pem",
              "keyFile": "${APP_DIR}/certs/privkey.pem"
            }
          ]
        }
      },
      "sniffing": {
        "enabled": true,
        "destOverride": [
          "http",
          "tls",
          "quic"
        ]
      }
    }
  ],
  "outbounds": [
    {
      "tag": "direct",
      "protocol": "freedom"
    },
    {
      "tag": "block",
      "protocol": "blackhole"
    }
  ],
  "routing": {
    "domainStrategy": "AsIs",
    "rules": []
  }
}
EOF
  chmod 0600 "$APP_DIR/xray/config.json"
}

write_sing_box_config() {
  cat >"$APP_DIR/sing-box/config.json" <<EOF
{
  "log": {
    "level": "warn",
    "timestamp": true
  },
  "inbounds": [
    {
      "type": "hysteria2",
      "tag": "hy2-udp-443",
      "listen": "::",
      "listen_port": 443,
      "users": [
        {
          "name": "proxy",
          "password": "${HY2_PASSWORD}"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "${DOMAIN}",
        "alpn": [
          "h3"
        ],
        "certificate_path": "${APP_DIR}/certs/fullchain.pem",
        "key_path": "${APP_DIR}/certs/privkey.pem"
      },
      "masquerade": "http://127.0.0.1:8080"
    },
    {
      "type": "anytls",
      "tag": "anytls-9443",
      "listen": "::",
      "listen_port": 9443,
      "users": [
        {
          "name": "proxy",
          "password": "${ANYTLS_PASSWORD}"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "${DOMAIN}",
        "certificate_path": "${APP_DIR}/certs/fullchain.pem",
        "key_path": "${APP_DIR}/certs/privkey.pem"
      }
    }
  ],
  "outbounds": [
    {
      "type": "direct",
      "tag": "direct"
    },
    {
      "type": "block",
      "tag": "block"
    }
  ],
  "route": {
    "final": "direct"
  }
}
EOF
  chmod 0600 "$APP_DIR/sing-box/config.json"
}

write_compose() {
  cat >"$APP_DIR/docker-compose.yml" <<EOF
services:
  xray:
    image: ${XRAY_IMAGE}
    build:
      context: ${APP_DIR}/images/xray
    container_name: proxy-xray
    command: ["run", "-config", "/etc/xray/config.json"]
    network_mode: host
    restart: unless-stopped
    volumes:
      - ${APP_DIR}/xray/config.json:/etc/xray/config.json:ro
      - ${APP_DIR}/certs:${APP_DIR}/certs:ro

  sing-box:
    image: ${SING_BOX_IMAGE}
    build:
      context: ${APP_DIR}/images/sing-box
    container_name: proxy-sing-box
    command: ["run", "-c", "/etc/sing-box/config.json"]
    network_mode: host
    restart: unless-stopped
    volumes:
      - ${APP_DIR}/sing-box/config.json:/etc/sing-box/config.json:ro
      - ${APP_DIR}/certs:${APP_DIR}/certs:ro

  nginx:
    image: ${NGINX_IMAGE}
    container_name: proxy-nginx
    network_mode: host
    restart: unless-stopped
    volumes:
      - ${APP_DIR}/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - ${APP_DIR}/www:/var/www/html:ro
EOF
}

install_certbot_hook() {
  log "Installing Docker certificate deploy hook"
  install -d -m 0755 /etc/letsencrypt/renewal-hooks/deploy
  cat >/etc/letsencrypt/renewal-hooks/deploy/proxy-subscription-docker <<EOF
#!/usr/bin/env bash
set -euo pipefail

DOMAIN="\${DOMAIN:-${DOMAIN}}"
APP_DIR="\${APP_DIR:-${APP_DIR}}"
SOURCE_DIR="/etc/letsencrypt/live/\${DOMAIN}"

install -d -m 0700 "\${APP_DIR}/certs"
install -m 0600 "\${SOURCE_DIR}/fullchain.pem" "\${APP_DIR}/certs/fullchain.pem"
install -m 0600 "\${SOURCE_DIR}/privkey.pem" "\${APP_DIR}/certs/privkey.pem"

if command -v docker >/dev/null 2>&1 && [ -f "\${APP_DIR}/docker-compose.yml" ]; then
  docker compose -f "\${APP_DIR}/docker-compose.yml" restart xray sing-box
fi
EOF
  chmod 0755 /etc/letsencrypt/renewal-hooks/deploy/proxy-subscription-docker
}

update_certbot_webroot() {
  local renewal="/etc/letsencrypt/renewal/${DOMAIN}.conf"
  if [ ! -f "$renewal" ]; then
    return
  fi

  log "Updating Certbot webroot to ${APP_DIR}/www"
  cp -a "$renewal" "${renewal}.bak.${STAMP}"
  sed -i \
    -e "s#^webroot_path = .*#webroot_path = ${APP_DIR}/www,#" \
    -e "s#^${DOMAIN} = .*#${DOMAIN} = ${APP_DIR}/www#" \
    "$renewal"
}

build_and_validate() {
  log "Building local Xray and sing-box images"
  compose build xray sing-box

  log "Pulling Nginx image"
  compose pull nginx

  log "Validating container configs"
  docker run --rm \
    -v "$APP_DIR/xray/config.json:/etc/xray/config.json:ro" \
    -v "$APP_DIR/certs:$APP_DIR/certs:ro" \
    "$XRAY_IMAGE" run -test -config /etc/xray/config.json

  docker run --rm \
    -v "$APP_DIR/sing-box/config.json:/etc/sing-box/config.json:ro" \
    -v "$APP_DIR/certs:$APP_DIR/certs:ro" \
    "$SING_BOX_IMAGE" check -c /etc/sing-box/config.json

  docker run --rm \
    -v "$APP_DIR/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro" \
    -v "$APP_DIR/www:/var/www/html:ro" \
    "$NGINX_IMAGE" nginx -t
}

migrate_services() {
  log "Stopping host services"
  MIGRATION_STARTED=1
  systemctl disable --now xray >/dev/null 2>&1 || true
  systemctl disable --now sing-box >/dev/null 2>&1 || true
  systemctl disable --now nginx >/dev/null 2>&1 || true

  log "Starting Docker Compose stack"
  compose up -d
  sleep 2

  log "Verifying subscription URL"
  curl -fsSI "https://${DOMAIN}/sub/${SUB_TOKEN}/config.yaml" >/dev/null
  MIGRATION_DONE=1
}

print_result() {
  cat <<EOF

Dockerized deployment complete.

Compose file:
  ${APP_DIR}/docker-compose.yml

Subscription:
  https://${DOMAIN}/sub/${SUB_TOKEN}/config.yaml

Manage services:
  docker compose -f ${APP_DIR}/docker-compose.yml ps
  docker compose -f ${APP_DIR}/docker-compose.yml logs -f
  docker compose -f ${APP_DIR}/docker-compose.yml restart

Host services disabled:
  xray, sing-box, nginx

Certbot renewal remains on the host, with a Docker deploy hook:
  /etc/letsencrypt/renewal-hooks/deploy/proxy-subscription-docker
EOF
}

main() {
  require_existing_runtime
  install_docker
  prepare_layout
  sync_certs
  write_nginx_config
  write_xray_config
  write_sing_box_config
  write_compose
  install_certbot_hook
  update_certbot_webroot
  build_and_validate
  migrate_services
  print_result
}

main "$@"
