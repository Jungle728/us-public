# proxy.bigpandas.top Proxy Runbook

This repository is the public runbook and bootstrap script collection for the
proxy stack deployed at `proxy.bigpandas.top`.

The live VPS contains generated configs, certificates, subscription tokens, and
node credentials. Those runtime secrets are intentionally not committed here.

## Current Architecture

The production deployment is Docker based and runs from:

```text
/opt/proxy-subscription
```

Runtime components:

```text
Nginx container     ACME challenge handling, fallback HTTP response, subscription files
Xray container      VLESS Vision on TCP 443, Trojan on TCP 8443
sing-box container  Hysteria2 on UDP 443, AnyTLS on TCP 9443
Certbot             Let's Encrypt issuance and renewal
Docker Compose      Process supervision for the proxy stack
```

Public ports that must be open in the VPS provider firewall or security group:

```text
TCP 80
TCP 443
TCP 8443
TCP 9443
UDP 443
```

The host `ufw` firewall is currently expected to be inactive. If a firewall is
enabled later, mirror the same allowlist above.

## Protocols

```text
VLESS Vision    TCP 443     Xray
Trojan          TCP 8443    Xray
Hysteria2       UDP 443     sing-box
AnyTLS          TCP 9443    sing-box
```

Client compatibility varies by app and core version. Mihomo/Clash Verge handles
the Clash subscription. Shadowrocket/manual links are generated separately.

## Subscriptions

The normal Mihomo/Clash subscription is served from:

```text
https://proxy.bigpandas.top/sub/<token>/config.yaml
```

The manual link file is served from:

```text
https://proxy.bigpandas.top/sub/<token>/shadowrocket-links.txt
```

Optional chained subscriptions can be published under a separate tokenized path:

```text
https://proxy.bigpandas.top/sub/<chain-token>/config.yaml
```

The chained subscription keeps the original VPS nodes and adds provider-backed
groups for an airport relay path:

```text
Client -> airport node -> US VPS -> destination
```

Expected chain-related groups:

```text
US-VPS
AIRPORT -> US-VPS
CHAIN-AUTO
AIRPORT
AIRPORT-AUTO
```

Select `US-VPS = AIRPORT -> US-VPS` to use the chained path. Then tune the
`AIRPORT` group manually if the automatic airport choice is not the best route.

Do not publish real subscription tokens in this repository. If a token or node
credential is exposed, rotate it before trusting the deployment again.

## Client DNS And Routing

The generated Mihomo config is designed for Windows and macOS clients using
Clash Verge or another Mihomo-compatible app.

Routing policy:

```text
Private networks and China domains/IPs -> DIRECT
Non-China domains                      -> US-VPS
Fallback traffic                       -> US-VPS
```

DNS policy:

```text
DNS override       Enabled on the client profile
Enhanced mode      fake-ip
IPv6               Disabled
Local/system DNS   Avoided for proxy routing
```

DNS override is important on Windows. Without it, the system resolver may return
polluted, unreachable, or IPv6-preferred answers before Mihomo can apply rules.
That can make every node appear to time out even when the subscription imports
correctly.

IPv6 is disabled in the generated client profile because partial IPv6 support is
often worse than no IPv6 support: Windows may prefer AAAA records, while the
local network, TUN stack, selected node, or destination route may not be usable
over IPv6.

## Important Paths

VPS runtime paths:

```text
/opt/proxy-subscription/docker-compose.yml
/opt/proxy-subscription/nginx/default.conf
/opt/proxy-subscription/xray/config.json
/opt/proxy-subscription/sing-box/config.json
/opt/proxy-subscription/certs/
/opt/proxy-subscription/www/sub/<token>/config.yaml
/root/proxy-subscription-secrets.env
/etc/letsencrypt/renewal-hooks/deploy/proxy-subscription-docker
```

Repository files:

```text
bootstrap-docker-proxy-subscription.sh  Current Docker deployment script
bootstrap-proxy-subscription.sh         Legacy bare-metal deployment script
deploy-xray-cert.sh                     Legacy bare-metal Certbot hook
nginx-vpn.conf                          Legacy Nginx site config
README.md                               Public runbook
```

## Deployment

Run the Docker bootstrap on the VPS as root:

```bash
sudo /root/code/us-public/bootstrap-docker-proxy-subscription.sh
```

The script:

```text
Reuses credentials from /root/proxy-subscription-secrets.env
Builds local Xray and sing-box images from installed static binaries
Writes the Compose stack under /opt/proxy-subscription
Publishes subscription files under /opt/proxy-subscription/www
Installs the Docker certificate deploy hook
Disables host xray, sing-box, and nginx services
Starts and verifies the containerized stack
```

The older `bootstrap-proxy-subscription.sh` script is kept for legacy
bare-metal installs and should not be used for the normal Docker deployment.

## Certificate Renewal

Certbot renews the Let's Encrypt certificate for `proxy.bigpandas.top`.

Docker renewal hook:

```text
/etc/letsencrypt/renewal-hooks/deploy/proxy-subscription-docker
```

The hook copies renewed certificates into `/opt/proxy-subscription/certs`, then
restarts the Xray and sing-box containers.

Manual hook run:

```bash
sudo /etc/letsencrypt/renewal-hooks/deploy/proxy-subscription-docker
```

Check the renewal timer:

```bash
systemctl list-timers certbot.timer --no-pager
```

## Operations

Check container status:

```bash
docker compose -f /opt/proxy-subscription/docker-compose.yml ps
```

Follow logs:

```bash
docker compose -f /opt/proxy-subscription/docker-compose.yml logs -f
```

Restart the stack:

```bash
docker compose -f /opt/proxy-subscription/docker-compose.yml restart
```

Validate Xray:

```bash
docker run --rm \
  -v /opt/proxy-subscription/xray/config.json:/etc/xray/config.json:ro \
  -v /opt/proxy-subscription/certs:/opt/proxy-subscription/certs:ro \
  proxy-subscription-xray:local run -test -config /etc/xray/config.json
```

Validate sing-box:

```bash
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

After deployment or a major config change, verify:

```text
DNS A record points proxy.bigpandas.top to the current VPS IP
TLS handshakes pass on TCP 443 and TCP 8443
proxy-xray, proxy-sing-box, and proxy-nginx containers are Up
Host xray, sing-box, and nginx services are disabled/inactive
The normal subscription URL imports in Clash Verge
DNS override is enabled in Clash Verge
IPv6 is disabled in the client profile
VLESS Vision and Trojan pass connectivity tests
Hysteria2 and AnyTLS are tested only with compatible clients
DNS leak tests do not show local ISP resolvers
```

For Windows Clash Verge troubleshooting, first check:

```text
DNS override is enabled
TUN mode is enabled when full-device routing is needed
IPv6 is disabled
The selected node is VLESS or Trojan before testing newer protocols
The subscription URL can be refreshed inside the app
```

## Security Notes

Runtime files on the VPS contain production secrets:

```text
Node UUIDs and passwords
Airport provider subscription URLs
Published subscription tokens
TLS-dependent client links
Generated configs under /opt/proxy-subscription
```

Before pushing to GitHub:

```text
Do not force-add ignored generated files
Do not commit live config.yaml subscription files
Do not commit /root/proxy-subscription-secrets.env
Do not commit airport subscription tokens
Rotate any credential that was exposed in chat, logs, commits, or screenshots
```

## References

- Xray: <https://github.com/XTLS/Xray-core>
- Xray install script: <https://github.com/XTLS/Xray-install>
- sing-box Hysteria2 inbound: <https://sing-box.sagernet.org/configuration/inbound/hysteria2/>
- sing-box AnyTLS inbound: <https://sing-box.sagernet.org/configuration/inbound/anytls/>
- Certbot: <https://certbot.eff.org/>
