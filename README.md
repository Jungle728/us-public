# us.bigpandas.top VPN Setup

This repository documents the VPN/proxy setup deployed on the VPS for
`us.bigpandas.top`.

The server currently supports multiple client protocols, uses TLS certificates
from Let's Encrypt, and applies server-side egress routing so AI services can use
stable exits.

## Overview

Domain:

```text
us.bigpandas.top
```

Server IP:

```text
154.44.3.210
```

Runtime components:

```text
Nginx     HTTP challenge, fallback web service, subscription hosting
Xray      VLESS Vision and Trojan
sing-box  Hysteria2 and AnyTLS
Certbot   Let's Encrypt certificate issuance and renewal
WARP      Cloudflare WARP WireGuard endpoint for selected Google traffic
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

## Egress Policy

The current routing goal is account-safety oriented:

```text
ChatGPT / OpenAI / Claude / Anthropic -> VPS native IP
Gemini / Google / YouTube             -> Cloudflare WARP
Everything else                       -> VPS native IP
```

This keeps OpenAI and Anthropic on a stable, fixed server exit while using WARP
only for Google/Gemini, where the native VPS IP previously showed region or risk
issues.

## Important Paths

System paths:

```text
/usr/local/etc/xray/config.json
/etc/sing-box/config.json
/etc/nginx/sites-available/vpn
/etc/letsencrypt/renewal-hooks/deploy/xray-cert
/usr/local/etc/xray/certs/
/etc/sing-box/certs/
/var/www/html/sub/<token>/config.yaml
```

Workspace files:

```text
xray-config.json              Xray service config, contains credentials
sing-box-config.json          sing-box service config, contains credentials
nginx-vpn.conf                Nginx site config
deploy-xray-cert.sh           Certbot deploy hook
mihomo-subscription.yaml      Clash/Mihomo subscription, contains node secrets
shadowrocket-links.txt        Shadowrocket/manual links, contains node secrets
client-links.txt              Raw client links, contains node secrets
wgcf-account.toml             WARP account credentials
wgcf-profile.conf             WARP WireGuard credentials
config.before-warp.json       Backup before WARP routing was added
test-*.json                   Local protocol test configs, contain credentials
```

## Subscription

The live Mihomo/Clash subscription is served by Nginx from:

```text
https://us.bigpandas.top/sub/<token>/config.yaml
```

The Shadowrocket/manual link file is served from:

```text
https://us.bigpandas.top/sub/<token>/shadowrocket-links.txt
```

Do not commit the real token or published subscription contents to a public
repository unless all node credentials have been rotated.

## Certificate Renewal

Certbot issued a Let's Encrypt certificate for `us.bigpandas.top`.

The deploy hook:

```text
/etc/letsencrypt/renewal-hooks/deploy/xray-cert
```

copies renewed certificates to both Xray and sing-box certificate directories,
then restarts both services.

Manual certificate deploy:

```bash
sudo /etc/letsencrypt/renewal-hooks/deploy/xray-cert
```

Check renewal timer:

```bash
systemctl list-timers certbot.timer --no-pager
```

## Service Commands

Check status:

```bash
systemctl status xray --no-pager
systemctl status sing-box --no-pager
systemctl status nginx --no-pager
```

Restart services:

```bash
systemctl restart xray
systemctl restart sing-box
systemctl restart nginx
```

Validate configs:

```bash
xray run -test -config /usr/local/etc/xray/config.json
sing-box check -c /etc/sing-box/config.json
nginx -t
```

Check listening ports:

```bash
ss -tulpn
```

## Verification Performed

The following checks were performed during setup:

```text
DNS A record: us.bigpandas.top -> 154.44.3.210
TLS handshake: TCP 443 and TCP 8443 verified
Xray config: Configuration OK
sing-box config: check passed
Hysteria2: local client test passed
AnyTLS: local client test passed
WARP trace: warp=on, loc=US for Google/WARP-routed traffic
```

## Security Notes

This workspace contains real production secrets:

```text
VPN UUIDs and passwords
WARP private key and account data
Published subscription token
TLS-dependent client links
```

Before pushing to GitHub:

1. Keep the current `.gitignore`.
2. Do not force-add ignored config or credential files.
3. If secrets were already committed, rotate all node passwords, UUIDs, WARP
   credentials, and subscription URL token.
4. Prefer publishing sanitized template files such as `*.example.json` for
   reusable documentation.

## References

- Xray: <https://github.com/XTLS/Xray-core>
- Xray install script: <https://github.com/XTLS/Xray-install>
- sing-box Hysteria2 inbound: <https://sing-box.sagernet.org/configuration/inbound/hysteria2/>
- sing-box AnyTLS inbound: <https://sing-box.sagernet.org/configuration/inbound/anytls/>
- sing-box WireGuard endpoint: <https://sing-box.sagernet.org/configuration/endpoint/wireguard/>
- Certbot: <https://certbot.eff.org/>
