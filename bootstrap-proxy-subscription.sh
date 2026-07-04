#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:-proxy.bigpandas.top}"
SECRETS_FILE="${SECRETS_FILE:-/root/proxy-subscription-secrets.env}"
STAMP="$(date +%Y%m%d%H%M%S)"
WEB_ROOT="/var/www/html"
SUB_ROOT="${WEB_ROOT}/sub"
XRAY_CONFIG="/usr/local/etc/xray/config.json"
SING_BOX_CONFIG="/etc/sing-box/config.json"
XRAY_CERT_DIR="/usr/local/etc/xray/certs"
SING_BOX_CERT_DIR="/etc/sing-box/certs"

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

rand_hex() {
  openssl rand -hex "$1"
}

new_uuid() {
  if command -v uuidgen >/dev/null 2>&1; then
    uuidgen
  else
    cat /proc/sys/kernel/random/uuid
  fi
}

backup_file() {
  local path="$1"
  if [ -e "$path" ] || [ -L "$path" ]; then
    cp -a "$path" "${path}.bak.${STAMP}"
  fi
}

install_base_packages() {
  log "Installing base packages"
  apt_wait update
  DEBIAN_FRONTEND=noninteractive apt_wait install -y \
    ca-certificates \
    certbot \
    curl \
    nginx \
    openssl \
    uuid-runtime
}

install_xray_if_missing() {
  if command -v xray >/dev/null 2>&1; then
    return
  fi

  log "Installing Xray"
  bash -c "$(curl -fsSL https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
}

install_sing_box_if_missing() {
  if command -v sing-box >/dev/null 2>&1; then
    return
  fi

  log "Installing sing-box"
  install -d -m 0755 /etc/apt/keyrings
  curl -fsSL https://sing-box.app/gpg.key -o /etc/apt/keyrings/sagernet.asc
  chmod a+r /etc/apt/keyrings/sagernet.asc
  cat >/etc/apt/sources.list.d/sagernet.sources <<'SOURCES'
Types: deb
URIs: https://deb.sagernet.org/
Suites: *
Components: *
Enabled: yes
Signed-By: /etc/apt/keyrings/sagernet.asc
SOURCES
  apt_wait update
  DEBIAN_FRONTEND=noninteractive apt_wait install -y sing-box
}

load_or_create_secrets() {
  if [ -r "$SECRETS_FILE" ]; then
    log "Loading existing secrets from ${SECRETS_FILE}"
    # shellcheck source=/dev/null
    . "$SECRETS_FILE"
    return
  fi

  log "Creating new proxy credentials"
  SUB_TOKEN="${SUB_TOKEN:-$(rand_hex 16)}"
  XRAY_UUID="${XRAY_UUID:-$(new_uuid)}"
  TROJAN_PASSWORD="${TROJAN_PASSWORD:-$(rand_hex 16)}"
  HY2_PASSWORD="${HY2_PASSWORD:-$(rand_hex 16)}"
  ANYTLS_PASSWORD="${ANYTLS_PASSWORD:-$(rand_hex 16)}"

  umask 077
  cat >"$SECRETS_FILE" <<EOF
SUB_TOKEN='${SUB_TOKEN}'
XRAY_UUID='${XRAY_UUID}'
TROJAN_PASSWORD='${TROJAN_PASSWORD}'
HY2_PASSWORD='${HY2_PASSWORD}'
ANYTLS_PASSWORD='${ANYTLS_PASSWORD}'
EOF
  chmod 600 "$SECRETS_FILE"
}

configure_nginx() {
  log "Writing Nginx site"
  install -d -m 0755 "$WEB_ROOT/.well-known/acme-challenge"
  cat >"${WEB_ROOT}/index.html" <<EOF
ok
EOF

  backup_file /etc/nginx/sites-available/vpn
  cat >/etc/nginx/sites-available/vpn <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    root ${WEB_ROOT};
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

    root ${WEB_ROOT};
    index index.html;

    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF

  ln -sfn /etc/nginx/sites-available/vpn /etc/nginx/sites-enabled/vpn
  nginx -t
  systemctl enable --now nginx
  systemctl reload nginx
}

issue_certificate() {
  log "Issuing or reusing Let's Encrypt certificate for ${DOMAIN}"
  certbot certonly \
    --webroot \
    -w "$WEB_ROOT" \
    -d "$DOMAIN" \
    --agree-tos \
    --register-unsafely-without-email \
    --non-interactive \
    --keep-until-expiring
}

install_cert_hook() {
  log "Installing certificate deploy hook"
  install -d -m 0755 /etc/letsencrypt/renewal-hooks/deploy
  cat >/etc/letsencrypt/renewal-hooks/deploy/xray-cert <<EOF
#!/usr/bin/env bash
set -euo pipefail

DOMAIN="\${DOMAIN:-${DOMAIN}}"
SOURCE_DIR="/etc/letsencrypt/live/\${DOMAIN}"
TARGET_DIR="${XRAY_CERT_DIR}"
SING_BOX_TARGET_DIR="${SING_BOX_CERT_DIR}"

install -d -m 700 -o nobody -g nogroup "\${TARGET_DIR}"
install -m 600 -o nobody -g nogroup "\${SOURCE_DIR}/fullchain.pem" "\${TARGET_DIR}/fullchain.pem"
install -m 600 -o nobody -g nogroup "\${SOURCE_DIR}/privkey.pem" "\${TARGET_DIR}/privkey.pem"

if id sing-box >/dev/null 2>&1; then
  install -d -m 700 -o sing-box -g sing-box "\${SING_BOX_TARGET_DIR}"
  install -m 600 -o sing-box -g sing-box "\${SOURCE_DIR}/fullchain.pem" "\${SING_BOX_TARGET_DIR}/fullchain.pem"
  install -m 600 -o sing-box -g sing-box "\${SOURCE_DIR}/privkey.pem" "\${SING_BOX_TARGET_DIR}/privkey.pem"
else
  install -d -m 700 "\${SING_BOX_TARGET_DIR}"
  install -m 600 "\${SOURCE_DIR}/fullchain.pem" "\${SING_BOX_TARGET_DIR}/fullchain.pem"
  install -m 600 "\${SOURCE_DIR}/privkey.pem" "\${SING_BOX_TARGET_DIR}/privkey.pem"
fi

systemctl try-restart xray || true
systemctl try-restart sing-box || true
EOF
  chmod 755 /etc/letsencrypt/renewal-hooks/deploy/xray-cert
  DOMAIN="$DOMAIN" /etc/letsencrypt/renewal-hooks/deploy/xray-cert
}

write_xray_config() {
  log "Writing Xray config"
  install -d -m 0755 "$(dirname "$XRAY_CONFIG")"
  backup_file "$XRAY_CONFIG"
  cat >"$XRAY_CONFIG" <<EOF
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
              "certificateFile": "${XRAY_CERT_DIR}/fullchain.pem",
              "keyFile": "${XRAY_CERT_DIR}/privkey.pem"
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
              "certificateFile": "${XRAY_CERT_DIR}/fullchain.pem",
              "keyFile": "${XRAY_CERT_DIR}/privkey.pem"
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
  chown root:nogroup "$XRAY_CONFIG"
  chmod 640 "$XRAY_CONFIG"
}

write_sing_box_config() {
  log "Writing sing-box config"
  install -d -m 0755 "$(dirname "$SING_BOX_CONFIG")"
  backup_file "$SING_BOX_CONFIG"
  cat >"$SING_BOX_CONFIG" <<EOF
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
        "certificate_path": "${SING_BOX_CERT_DIR}/fullchain.pem",
        "key_path": "${SING_BOX_CERT_DIR}/privkey.pem"
      },
      "masquerade": "http://127.0.0.1:8080"
    },
    {
      "type": "hysteria2",
      "tag": "hy2-udp-8443",
      "listen": "::",
      "listen_port": 8443,
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
        "certificate_path": "${SING_BOX_CERT_DIR}/fullchain.pem",
        "key_path": "${SING_BOX_CERT_DIR}/privkey.pem"
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
        "certificate_path": "${SING_BOX_CERT_DIR}/fullchain.pem",
        "key_path": "${SING_BOX_CERT_DIR}/privkey.pem"
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
}

write_subscriptions() {
  log "Writing subscription files"
  local sub_dir="${SUB_ROOT}/${SUB_TOKEN}"
  install -d -m 0755 "$sub_dir"

  cat >"${sub_dir}/config.yaml" <<EOF
mixed-port: 7890
allow-lan: true
bind-address: '*'
mode: rule
log-level: info
external-controller: 127.0.0.1:9090
unified-delay: true
tcp-concurrent: true
ipv6: false

tun:
  enable: true
  stack: mixed
  dns-hijack:
    - any:53
    - tcp://any:53
  auto-route: true
  auto-detect-interface: true
  strict-route: true

geox-url:
  geoip: https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/geoip.dat
  geosite: https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/geosite.dat
  mmdb: https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/country.mmdb

dns:
  enable: true
  listen: 0.0.0.0:1053
  ipv6: false
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  use-hosts: true
  respect-rules: true
  default-nameserver:
    - https://1.1.1.1/dns-query
    - https://1.0.0.1/dns-query
  proxy-server-nameserver:
    - https://1.1.1.1/dns-query
    - https://1.0.0.1/dns-query
  nameserver:
    - https://1.1.1.1/dns-query#DNS-US
    - https://1.0.0.1/dns-query#DNS-US
  fake-ip-filter:
    - '*.lan'
    - '*.localdomain'
    - '*.example'
    - '*.invalid'
    - '*.localhost'
    - '*.test'
    - '*.local'
    - '*.home.arpa'
    - 'time.*.com'
    - 'time.*.gov'
    - 'time.*.edu.cn'
    - 'time.*.apple.com'
    - 'time1.*.com'
    - 'time2.*.com'
    - 'time3.*.com'
    - 'time4.*.com'
    - 'time5.*.com'
    - 'time6.*.com'
    - 'time7.*.com'
    - 'ntp.*.com'
    - 'ntp1.*.com'
    - 'ntp2.*.com'
    - 'ntp3.*.com'
    - 'ntp4.*.com'
    - 'ntp5.*.com'
    - 'ntp6.*.com'
    - 'ntp7.*.com'
    - '*.time.edu.cn'
    - '*.ntp.org.cn'
    - '+.pool.ntp.org'
    - 'time1.cloud.tencent.com'
    - 'stun.*.*'
    - 'stun.*.*.*'
    - 'swscan.apple.com'
    - 'mesu.apple.com'
    - '*.msftconnecttest.com'
    - '*.msftncsi.com'

proxies:
  - name: US-VPS-VLESS
    type: vless
    server: ${DOMAIN}
    port: 443
    uuid: ${XRAY_UUID}
    network: tcp
    tls: true
    udp: true
    flow: xtls-rprx-vision
    servername: ${DOMAIN}
    client-fingerprint: chrome

  - name: US-VPS-Trojan
    type: trojan
    server: ${DOMAIN}
    port: 8443
    password: ${TROJAN_PASSWORD}
    udp: true
    sni: ${DOMAIN}
    skip-cert-verify: false

  - name: US-VPS-Hysteria2
    type: hysteria2
    server: ${DOMAIN}
    port: 443
    password: ${HY2_PASSWORD}
    sni: ${DOMAIN}
    alpn:
      - h3
    skip-cert-verify: false

  - name: US-VPS-Hysteria2-8443
    type: hysteria2
    server: ${DOMAIN}
    port: 8443
    password: ${HY2_PASSWORD}
    sni: ${DOMAIN}
    alpn:
      - h3
    skip-cert-verify: false

  - name: US-VPS-AnyTLS
    type: anytls
    server: ${DOMAIN}
    port: 9443
    password: ${ANYTLS_PASSWORD}
    sni: ${DOMAIN}
    skip-cert-verify: false

proxy-groups:
  - name: US-VPS
    type: select
    proxies:
      - AUTO
      - HY2
      - FALLBACK
      - US-VPS-VLESS
      - US-VPS-Trojan
      - US-VPS-Hysteria2
      - US-VPS-Hysteria2-8443
      - US-VPS-AnyTLS
      - DIRECT
  - name: HY2
    type: url-test
    proxies:
      - US-VPS-Hysteria2
      - US-VPS-Hysteria2-8443
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 50
  - name: AUTO
    type: url-test
    proxies:
      - US-VPS-VLESS
      - US-VPS-Trojan
      - US-VPS-Hysteria2
      - US-VPS-Hysteria2-8443
      - US-VPS-AnyTLS
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 0
  - name: FALLBACK
    type: fallback
    proxies:
      - US-VPS-VLESS
      - US-VPS-Trojan
      - US-VPS-Hysteria2
      - US-VPS-Hysteria2-8443
      - US-VPS-AnyTLS
    url: http://www.gstatic.com/generate_204
    interval: 300
  - name: DNS-US
    type: select
    proxies:
      - US-VPS-VLESS
      - US-VPS-Trojan
      - US-VPS-Hysteria2
      - US-VPS-Hysteria2-8443
      - US-VPS-AnyTLS

rule-anchor:
  ip:
    type: http
    interval: 86400
    behavior: ipcidr
    format: mrs
  domain:
    type: http
    interval: 86400
    behavior: domain
    format: mrs

rule-providers:
  private_domain:
    type: http
    interval: 86400
    behavior: domain
    format: mrs
    url: https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/private.mrs
  cn_domain:
    type: http
    interval: 86400
    behavior: domain
    format: mrs
    url: https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/cn.mrs
  geolocation-!cn:
    type: http
    interval: 86400
    behavior: domain
    format: mrs
    url: https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/geolocation-!cn.mrs
  cn_ip:
    type: http
    interval: 86400
    behavior: ipcidr
    format: mrs
    url: https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geoip/cn.mrs

rules:
  - AND,((DST-PORT,53),(NETWORK,UDP)),REJECT
  - AND,((DST-PORT,53),(NETWORK,TCP)),REJECT
  - DST-PORT,853,REJECT
  - DOMAIN,api.ip.sb,REJECT
  - DOMAIN,ipapi.co,REJECT
  - DOMAIN,api.ipapi.is,REJECT
  - DOMAIN,ipwho.is,REJECT
  - DOMAIN,injections.adguard.org,DIRECT
  - DOMAIN,local.adguard.org,DIRECT
  - IP-CIDR,0.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,10.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,100.64.0.0/10,DIRECT,no-resolve
  - IP-CIDR,127.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,169.254.0.0/16,DIRECT,no-resolve
  - IP-CIDR,172.16.0.0/12,DIRECT,no-resolve
  - IP-CIDR,192.0.0.0/24,DIRECT,no-resolve
  - IP-CIDR,192.0.2.0/24,DIRECT,no-resolve
  - IP-CIDR,192.88.99.0/24,DIRECT,no-resolve
  - IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
  - IP-CIDR,198.18.0.0/15,DIRECT,no-resolve
  - IP-CIDR,198.51.100.0/24,DIRECT,no-resolve
  - IP-CIDR,203.0.113.0/24,DIRECT,no-resolve
  - IP-CIDR,224.0.0.0/3,DIRECT,no-resolve
  - IP-CIDR,::/127,DIRECT,no-resolve
  - IP-CIDR,fc00::/7,DIRECT,no-resolve
  - IP-CIDR,fe80::/10,DIRECT,no-resolve
  - IP-CIDR,ff00::/8,DIRECT,no-resolve
  - RULE-SET,private_domain,DIRECT,no-resolve
  - IP-CIDR,5.28.195.0/24,REJECT,no-resolve
  - DOMAIN,safebrowsing.urlsec.qq.com,DIRECT
  - DOMAIN,safebrowsing.googleapis.com,DIRECT
  - DOMAIN,developer.apple.com,US-VPS
  - DOMAIN-SUFFIX,digicert.com,US-VPS
  - DOMAIN,ocsp.apple.com,US-VPS
  - DOMAIN,ocsp.comodoca.com,US-VPS
  - DOMAIN,ocsp.usertrust.com,US-VPS
  - DOMAIN,ocsp.sectigo.com,US-VPS
  - DOMAIN,ocsp.verisign.net,US-VPS
  - DOMAIN-SUFFIX,apple-dns.net,US-VPS
  - DOMAIN,testflight.apple.com,US-VPS
  - DOMAIN,sandbox.itunes.apple.com,US-VPS
  - DOMAIN,itunes.apple.com,US-VPS
  - DOMAIN-SUFFIX,apps.apple.com,US-VPS
  - DOMAIN-SUFFIX,blobstore.apple.com,US-VPS
  - DOMAIN,cvws.icloud-content.com,US-VPS
  - DOMAIN-SUFFIX,mzstatic.com,DIRECT
  - DOMAIN-SUFFIX,itunes.apple.com,DIRECT
  - DOMAIN-SUFFIX,icloud.com,DIRECT
  - DOMAIN-SUFFIX,icloud-content.com,DIRECT
  - DOMAIN-SUFFIX,me.com,DIRECT
  - DOMAIN-SUFFIX,aaplimg.com,DIRECT
  - DOMAIN-SUFFIX,cdn20.com,DIRECT
  - DOMAIN-SUFFIX,cdn-apple.com,DIRECT
  - DOMAIN-SUFFIX,akadns.net,DIRECT
  - DOMAIN-SUFFIX,akamaiedge.net,DIRECT
  - DOMAIN-SUFFIX,edgekey.net,DIRECT
  - DOMAIN-SUFFIX,mwcloudcdn.com,DIRECT
  - DOMAIN-SUFFIX,mwcname.com,DIRECT
  - DOMAIN-SUFFIX,apple.com,DIRECT
  - DOMAIN-SUFFIX,apple-cloudkit.com,DIRECT
  - DOMAIN-SUFFIX,apple-mapkit.com,DIRECT
  - AND,((DST-PORT,443),(NETWORK,UDP)),REJECT
  - DOMAIN-SUFFIX,services.googleapis.cn,US-VPS
  - DOMAIN-SUFFIX,xn--ngstr-lra8j.com,US-VPS
  - RULE-SET,geolocation-!cn,US-VPS,no-resolve
  - RULE-SET,cn_domain,DIRECT,no-resolve
  - IP-CIDR,221.228.32.13/32,US-VPS
  - RULE-SET,cn_ip,DIRECT
  - MATCH,US-VPS
EOF

  cat >"${sub_dir}/client-links.txt" <<EOF
vless://${XRAY_UUID}@${DOMAIN}:443?encryption=none&security=tls&sni=${DOMAIN}&type=tcp&flow=xtls-rprx-vision#proxy-vless-vision
trojan://${TROJAN_PASSWORD}@${DOMAIN}:8443?security=tls&sni=${DOMAIN}&type=tcp#proxy-trojan
hysteria2://${HY2_PASSWORD}@${DOMAIN}:443?sni=${DOMAIN}&alpn=h3&insecure=0#proxy-hysteria2
hysteria2://${HY2_PASSWORD}@${DOMAIN}:8443?sni=${DOMAIN}&alpn=h3&insecure=0#proxy-hysteria2-8443
anytls://${ANYTLS_PASSWORD}@${DOMAIN}:9443?security=tls&sni=${DOMAIN}&insecure=0#proxy-anytls
EOF

  cp "${sub_dir}/client-links.txt" "${sub_dir}/shadowrocket-links.txt"

  cat >"${sub_dir}/sing-box-client.json" <<EOF
{
  "outbounds": [
    {
      "type": "vless",
      "tag": "proxy-vless-vision",
      "server": "${DOMAIN}",
      "server_port": 443,
      "uuid": "${XRAY_UUID}",
      "flow": "xtls-rprx-vision",
      "tls": {
        "enabled": true,
        "server_name": "${DOMAIN}",
        "utls": {
          "enabled": true,
          "fingerprint": "chrome"
        }
      }
    },
    {
      "type": "trojan",
      "tag": "proxy-trojan",
      "server": "${DOMAIN}",
      "server_port": 8443,
      "password": "${TROJAN_PASSWORD}",
      "tls": {
        "enabled": true,
        "server_name": "${DOMAIN}"
      }
    },
    {
      "type": "hysteria2",
      "tag": "proxy-hysteria2",
      "server": "${DOMAIN}",
      "server_port": 443,
      "password": "${HY2_PASSWORD}",
      "tls": {
        "enabled": true,
        "server_name": "${DOMAIN}",
        "alpn": [
          "h3"
        ]
      }
    },
    {
      "type": "hysteria2",
      "tag": "proxy-hysteria2-8443",
      "server": "${DOMAIN}",
      "server_port": 8443,
      "password": "${HY2_PASSWORD}",
      "tls": {
        "enabled": true,
        "server_name": "${DOMAIN}",
        "alpn": [
          "h3"
        ]
      }
    },
    {
      "type": "anytls",
      "tag": "proxy-anytls",
      "server": "${DOMAIN}",
      "server_port": 9443,
      "password": "${ANYTLS_PASSWORD}",
      "tls": {
        "enabled": true,
        "server_name": "${DOMAIN}"
      }
    }
  ]
}
EOF

  chmod -R go+rX "$sub_dir"
}

open_firewall_if_active() {
  if ! command -v ufw >/dev/null 2>&1; then
    return
  fi

  if ufw status | grep -q "Status: active"; then
    log "Opening UFW ports"
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8443/tcp
    ufw allow 9443/tcp
    ufw allow 443/udp
  fi
}

validate_and_restart() {
  log "Validating configs"
  xray run -test -config "$XRAY_CONFIG"
  sing-box check -c "$SING_BOX_CONFIG"
  nginx -t

  log "Restarting services"
  systemctl enable --now xray
  systemctl restart xray
  systemctl enable --now sing-box
  systemctl restart sing-box
  systemctl reload nginx
}

print_result() {
  cat <<EOF

Done.

Mihomo/Clash subscription:
  https://${DOMAIN}/sub/${SUB_TOKEN}/config.yaml

Shadowrocket/manual links:
  https://${DOMAIN}/sub/${SUB_TOKEN}/shadowrocket-links.txt

sing-box client sample:
  https://${DOMAIN}/sub/${SUB_TOKEN}/sing-box-client.json

Secrets file:
  ${SECRETS_FILE}

Required provider firewall ports:
  TCP 80, 443, 8443, 9443
  UDP 443
EOF
}

main() {
  install_base_packages
  install_xray_if_missing
  install_sing_box_if_missing
  load_or_create_secrets
  configure_nginx
  issue_certificate
  install_cert_hook
  write_xray_config
  write_sing_box_config
  write_subscriptions
  open_firewall_if_active
  validate_and_restart
  print_result
}

main "$@"
