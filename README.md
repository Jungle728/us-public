# proxy.bigpandas.top 代理服务运维手册

这个仓库用于记录 `proxy.bigpandas.top` 上代理服务的公开运维说明和部署脚本。

真实 VPS 上会生成配置文件、证书、订阅 token、节点 UUID 和密码等敏感信息。这些运行时密钥不应该提交到这个公开仓库。

## 当前架构

生产环境使用 Docker 部署，主目录是：

```text
/opt/proxy-subscription
```

运行组件：

```text
Nginx 容器      ACME HTTP 验证、默认 HTTP 响应、订阅文件托管
Xray 容器       VLESS Vision TCP 443、Trojan TCP 8443
sing-box 容器   Hysteria2 UDP 443、AnyTLS TCP 9443
Certbot         Let's Encrypt 证书签发和续期
Docker Compose  代理服务编排和进程托管
```

VPS 云防火墙或安全组需要放行：

```text
TCP 80
TCP 443
TCP 8443
TCP 9443
UDP 443
```

当前预期主机上的 `ufw` 是关闭状态。如果之后启用主机防火墙，也需要同步放行上面的端口。

## 协议

```text
VLESS Vision    TCP 443     Xray
Trojan          TCP 8443    Xray
Hysteria2       UDP 443     sing-box
AnyTLS          TCP 9443    sing-box
```

不同客户端和内核版本对新协议的支持不完全一致。Mihomo/Clash Verge 使用 Clash 订阅；Shadowrocket 或手动导入使用单独生成的链接文件。

## 订阅

常规 Mihomo/Clash 订阅地址格式：

```text
https://proxy.bigpandas.top/sub/<token>/config.yaml
```

手动链接文件地址格式：

```text
https://proxy.bigpandas.top/sub/<token>/shadowrocket-links.txt
```

可选的链式代理订阅会发布在独立 token 路径下：

```text
https://proxy.bigpandas.top/sub/<chain-token>/config.yaml
```

链式订阅保留原有 VPS 节点，并新增机场 provider 和中转分组。链路方向是：

```text
客户端 -> 机场节点 -> 美国 VPS -> 目标网站
```

链式代理相关分组：

```text
US-VPS
AIRPORT -> US-VPS
CHAIN-AUTO
AIRPORT
AIRPORT-AUTO
```

使用链式代理时，在客户端里选择：

```text
US-VPS = AIRPORT -> US-VPS
```

如果自动选择的机场节点效果不好，再到 `AIRPORT` 分组里手动切换香港、日本、新加坡、美国等节点测试。

不要把真实订阅 token 提交到仓库。如果订阅 token、机场链接或节点凭据已经暴露，需要先轮换凭据，再继续使用。

## 客户端 DNS 和路由

生成的 Mihomo 配置面向 Windows 和 macOS 上的 Clash Verge，其他 Mihomo 兼容客户端也可以使用。

路由策略：

```text
私有网络和中国大陆域名/IP -> DIRECT
非中国大陆域名            -> US-VPS
兜底流量                  -> US-VPS
```

DNS 策略：

```text
DNS 覆写       开启
增强模式       fake-ip
IPv6           关闭
本地/系统 DNS  尽量不参与代理路由解析
```

Windows 上尤其需要开启 DNS 覆写。否则系统 DNS 可能先返回被污染、不可达或优先 IPv6 的解析结果，导致订阅可以导入，但节点测速和访问全部 timeout。

生成的客户端配置默认关闭 IPv6。很多网络环境里 IPv6 是“看起来可用，实际不稳”：Windows 可能优先使用 AAAA 记录，但本地网络、TUN、所选节点或目标路由并没有完整可用的 IPv6 链路。

## 重要路径

VPS 运行时路径：

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

仓库文件：

```text
bootstrap-docker-proxy-subscription.sh  当前 Docker 部署脚本
bootstrap-proxy-subscription.sh         旧版裸机部署脚本
deploy-xray-cert.sh                     旧版裸机 Certbot hook
nginx-vpn.conf                          旧版 Nginx 站点配置
README.md                               公开运维手册
```

## 部署

在 VPS 上以 root 身份运行 Docker 部署脚本：

```bash
sudo /root/code/us-public/bootstrap-docker-proxy-subscription.sh
```

脚本会执行：

```text
复用 /root/proxy-subscription-secrets.env 中的已有凭据
基于主机上的静态 xray 和 sing-box 二进制文件构建本地镜像
在 /opt/proxy-subscription 下写入 Docker Compose 栈
在 /opt/proxy-subscription/www 下发布订阅文件
安装 Docker 版证书续期 deploy hook
禁用主机上的 xray、sing-box、nginx 服务
启动并验证容器化代理栈
```

`bootstrap-proxy-subscription.sh` 是旧版裸机部署脚本，正常 Docker 部署不需要使用它。

## 证书续期

Certbot 为 `proxy.bigpandas.top` 签发和续期 Let's Encrypt 证书。

Docker 部署使用的续期 hook：

```text
/etc/letsencrypt/renewal-hooks/deploy/proxy-subscription-docker
```

hook 会把续期后的证书复制到 `/opt/proxy-subscription/certs`，然后重启 Xray 和 sing-box 容器。

手动执行 hook：

```bash
sudo /etc/letsencrypt/renewal-hooks/deploy/proxy-subscription-docker
```

查看续期定时器：

```bash
systemctl list-timers certbot.timer --no-pager
```

## 日常运维

查看容器状态：

```bash
docker compose -f /opt/proxy-subscription/docker-compose.yml ps
```

查看日志：

```bash
docker compose -f /opt/proxy-subscription/docker-compose.yml logs -f
```

重启代理栈：

```bash
docker compose -f /opt/proxy-subscription/docker-compose.yml restart
```

验证 Xray 配置：

```bash
docker run --rm \
  -v /opt/proxy-subscription/xray/config.json:/etc/xray/config.json:ro \
  -v /opt/proxy-subscription/certs:/opt/proxy-subscription/certs:ro \
  proxy-subscription-xray:local run -test -config /etc/xray/config.json
```

验证 sing-box 配置：

```bash
docker run --rm \
  -v /opt/proxy-subscription/sing-box/config.json:/etc/sing-box/config.json:ro \
  -v /opt/proxy-subscription/certs:/opt/proxy-subscription/certs:ro \
  proxy-subscription-sing-box:local check -c /etc/sing-box/config.json
```

查看监听端口：

```bash
ss -tulpn
```

## 验证清单

部署或大改配置后，检查：

```text
DNS A 记录指向当前 VPS IP
TCP 443 和 TCP 8443 的 TLS 握手正常
proxy-xray、proxy-sing-box、proxy-nginx 容器处于 Up
主机上的 xray、sing-box、nginx 服务已禁用或停止
常规订阅可以在 Clash Verge 中导入
Clash Verge 已开启 DNS 覆写
客户端配置中 IPv6 已关闭
VLESS Vision 和 Trojan 连通性测试通过
Hysteria2 和 AnyTLS 只在兼容客户端中测试
DNS 泄漏测试不显示本地运营商解析器
```

Windows Clash Verge 排查优先检查：

```text
DNS 覆写是否开启
需要全局设备路由时 TUN 是否开启
IPv6 是否关闭
先测试 VLESS 或 Trojan，再测试较新的协议
订阅链接是否能在客户端内刷新
```

## 安全说明

VPS 运行时文件包含生产凭据：

```text
节点 UUID 和密码
机场 provider 订阅链接
公开订阅 token
依赖 TLS 的客户端链接
/opt/proxy-subscription 下生成的配置
```

推送到 GitHub 前确认：

```text
不要强制提交被 .gitignore 忽略的生成文件
不要提交真实 config.yaml 订阅文件
不要提交 /root/proxy-subscription-secrets.env
不要提交机场订阅 token
如果凭据出现在聊天、日志、提交或截图中，需要轮换
```

## 参考

- Xray: <https://github.com/XTLS/Xray-core>
- Xray 安装脚本: <https://github.com/XTLS/Xray-install>
- sing-box Hysteria2 inbound: <https://sing-box.sagernet.org/configuration/inbound/hysteria2/>
- sing-box AnyTLS inbound: <https://sing-box.sagernet.org/configuration/inbound/anytls/>
- Certbot: <https://certbot.eff.org/>
