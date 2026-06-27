# proxy.bigpandas.top VPN Setup

This repository documents the VPN/proxy setup deployed on the VPS for
`proxy.bigpandas.top`.

The server supports multiple client protocols, uses TLS certificates from Let's
Encrypt, and serves a Mihomo subscription with rule-based routing.

## Overview

Domain:

```text
proxy.bigpandas.top
```

Server IP:

```text
Set by the current VPS provider.
```

Runtime components:

```text
Docker Compose  Runtime supervisor
Nginx container HTTP challenge, fallback web service, subscription hosting
Xray container  VLESS Vision and Trojan
sing-box        Hysteria2 and AnyTLS
Certbot         Let's Encrypt certificate issuance and renewal
```

## Protocols

```text
VLESS Vision    TCP 443     Xray
Trojan          TCP 8443    Xray
Hysteria2       UDP 443     sing-box
AnyTLS          TCP 9443    sing-box
```

The host firewall `ufw` is currently inactive. If the VPS provider has a cloud
firewall or security group, these ports must be allowed:

```text
TCP 80
TCP 443
TCP 8443
TCP 9443
UDP 443
```

## Client Routing And DNS

The generated Mihomo subscription follows this policy:

```text
Private and China domains/IPs -> DIRECT
Non-China domains             -> US-VPS
Fallback traffic              -> US-VPS
```

DNS is configured to avoid local ISP/system DNS:

```text
Regular DNS queries          -> encrypted DoH through DNS-US proxy group
Proxy server bootstrap DNS   -> encrypted Cloudflare/Google/Quad9 DoH
System/local DNS             -> not used by the generated subscription
```

## Important Paths

Docker deployment paths:

```text
/opt/proxy-subscription/docker-compose.yml
/opt/proxy-subscription/xray/config.json
/opt/proxy-subscription/sing-box/config.json
/opt/proxy-subscription/nginx/default.conf
/opt/proxy-subscription/certs/
/opt/proxy-subscription/www/sub/<token>/config.yaml
/root/proxy-subscription-secrets.env
/etc/letsencrypt/renewal-hooks/deploy/proxy-subscription-docker
```

Workspace files:

```text
nginx-vpn.conf                Nginx site config
deploy-xray-cert.sh           Legacy bare-metal Certbot deploy hook
bootstrap-proxy-subscription.sh
bootstrap-docker-proxy-subscription.sh
```

## Docker Deployment

Run as root on the VPS:

```bash
sudo /root/code/us-public/bootstrap-docker-proxy-subscription.sh
```

The Docker migration script reuses credentials from
`/root/proxy-subscription-secrets.env`, builds local Xray and sing-box images
from the installed static binaries, writes the Compose stack under
`/opt/proxy-subscription`, disables the host `xray`, `sing-box`, and `nginx`
services, starts containers, and verifies the subscription URL.

The older `bootstrap-proxy-subscription.sh` script is kept as a legacy
bare-metal bootstrap and should not be needed for normal operation.

## Subscription

The live Mihomo/Clash subscription is served by Nginx from:

```text
https://proxy.bigpandas.top/sub/<token>/config.yaml
```

The Shadowrocket/manual link file is served from:

```text
https://proxy.bigpandas.top/sub/<token>/shadowrocket-links.txt
```

Do not commit the real token or published subscription contents to a public
repository unless all node credentials have been rotated.

## Certificate Renewal

Certbot issues a Let's Encrypt certificate for `proxy.bigpandas.top`.

The Docker deploy hook:

```text
/etc/letsencrypt/renewal-hooks/deploy/proxy-subscription-docker
```

copies renewed certificates to `/opt/proxy-subscription/certs`, then restarts
the Xray and sing-box containers.

Manual certificate deploy:

```bash
sudo /etc/letsencrypt/renewal-hooks/deploy/proxy-subscription-docker
```

Check renewal timer:

```bash
systemctl list-timers certbot.timer --no-pager
```

## Service Commands

Check status:

```bash
docker compose -f /opt/proxy-subscription/docker-compose.yml ps
```

Restart services:

```bash
docker compose -f /opt/proxy-subscription/docker-compose.yml restart
```

Validate configs:

```bash
docker run --rm \
  -v /opt/proxy-subscription/xray/config.json:/etc/xray/config.json:ro \
  -v /opt/proxy-subscription/certs:/opt/proxy-subscription/certs:ro \
  proxy-subscription-xray:local run -test -config /etc/xray/config.json

docker run --rm \
  -v /opt/proxy-subscription/sing-box/config.json:/etc/sing-box/config.json:ro \
  -v /opt/proxy-subscription/certs:/opt/proxy-subscription/certs:ro \
  proxy-subscription-sing-box:local check -c /etc/sing-box/config.json
```

Check listening ports:

```bash
ss -tulpn
```

## Verification Checklist

Run these checks after setup:

```text
DNS A record: proxy.bigpandas.top -> current VPS IP
TLS handshake: TCP 443 and TCP 8443 verified
Docker containers: proxy-xray, proxy-sing-box, proxy-nginx are Up
Host services: xray, sing-box, nginx are disabled and inactive
Hysteria2: client test passes
AnyTLS: client test passes
DNS leak test: resolver IPs are not local ISP resolvers
```

## Security Notes

Runtime files on the VPS contain real production secrets:

```text
VPN UUIDs and passwords
Published subscription token
TLS-dependent client links
Generated Docker configs under /opt/proxy-subscription
```

Before pushing to GitHub:

1. Keep the current `.gitignore`.
2. Do not force-add ignored config or credential files.
3. If secrets were already committed, rotate all node passwords, UUIDs, and
   subscription URL token.
4. Prefer publishing sanitized template files such as `*.example.json` for
   reusable documentation.

## References

- Xray: <https://github.com/XTLS/Xray-core>
- Xray install script: <https://github.com/XTLS/Xray-install>
- sing-box Hysteria2 inbound: <https://sing-box.sagernet.org/configuration/inbound/hysteria2/>
- sing-box AnyTLS inbound: <https://sing-box.sagernet.org/configuration/inbound/anytls/>
- sing-box WireGuard endpoint: <https://sing-box.sagernet.org/configuration/endpoint/wireguard/>
- Certbot: <https://certbot.eff.org/>
