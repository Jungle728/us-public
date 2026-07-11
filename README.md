# 个人代理节点运维手册

本仓库记录 `bigpandas.top` 个人代理节点的可迁移部署方案。生产环境以 Docker Compose 运行，节点由 3X-UI 管理，只保留 `VLESS + REALITY + Vision`。

仓库只保存模板和运维说明。真实账号、订阅 ID、UUID、Reality 密钥、证书私钥及 SQLite 数据库只能保留在 VPS 的 `/opt/3x-ui`，不得提交到 GitHub。

## 当前架构

```text
Clash Verge Rev / Mihomo
           |
           | TCP 443
           v
      Nginx stream
       |         |
       |         +-- 默认 SNI --> 3X-UI Xray --> VLESS REALITY Vision
       |
       +-- panel.bigpandas.top --> Nginx HTTPS --> 127.0.0.1:2053
       +-- sub.bigpandas.top   --> Nginx HTTPS --> 127.0.0.1:2096
```

Docker 容器：

| 容器 | 用途 |
| --- | --- |
| `3x-ui` | 面板、SQLite、Xray 与订阅生成 |
| `3x-ui-nginx` | HTTP、HTTPS 与 443 SNI 分流 |
| `3x-ui-certbot` | Let's Encrypt 自动续期 |

代理栈在宿主机层只依赖 Docker；SSH、UFW 和 SSH Fail2Ban 作为系统安全基线保留。Certbot、Nginx、Xray、sing-box 均不直接安装在宿主机。

## 域名与端口

| 域名 | 用途 |
| --- | --- |
| `proxy.bigpandas.top` | Reality 节点连接地址 |
| `panel.bigpandas.top` | 3X-UI 管理面板 |
| `sub.bigpandas.top` | 原始、JSON 和 Mihomo 订阅 |

公网只允许：

```text
TCP 22   SSH，仅公钥登录，由 UFW 限速和 Fail2Ban 防护
TCP 80   ACME HTTP-01 与 HTTPS 跳转
TCP 443  Reality、面板和订阅共用入口
```

面板、订阅和 Reality 后端分别只监听 `127.0.0.1:2053`、`127.0.0.1:2096`、`127.0.0.1:10443`，不能从公网绕过 Nginx 访问。

旧 Trojan、Hysteria2、AnyTLS、独立 Xray/sing-box 容器及 `8443/9443/UDP 443` 已停用。旧订阅不再发布，也不要在新机器上恢复。

## 订阅

真实订阅 ID 位于：

```text
/opt/3x-ui/data/reality-client.env
```

订阅格式：

```text
Clash Verge / Mihomo  https://sub.bigpandas.top/clash/<sub-id>
通用分享订阅          https://sub.bigpandas.top/sub/<sub-id>
JSON                  https://sub.bigpandas.top/json/<sub-id>
```

面板账号和随机面板路径位于：

```text
/opt/3x-ui/data/access.env
```

这两个文件权限必须为 `600`。README 和 Git 提交中只能使用 `<sub-id>` 等占位符。

## Mihomo 规则

3X-UI 的 `/clash/` 输出已应用 [mihomo-template.yaml](3x-ui/mihomo-template.yaml)，不是默认的简单 `MATCH,PROXY` 配置。

代理组：

```text
PROXY   主出口，只允许选择 AUTO 或 MANUAL，不提供 DIRECT
AUTO    对全部 3X-UI 节点执行 url-test，自动选择可用且延迟较低的节点
MANUAL  手动选择具体节点
```

路由顺序：

```text
常用 IP/DNS 检测站点       -> PROXY
私有域名和私有 IP          -> DIRECT
非中国大陆域名             -> PROXY
中国大陆域名               -> DIRECT
中国大陆 IP                -> DIRECT
其余流量                   -> PROXY
```

规则使用 Mihomo 内置 `GEOSITE/GEOIP`，不依赖多组远程 Rule Provider。Geo 数据通过 jsDelivr 下载，减少首次启动和切换节点时的等待。

## DNS 与 TUN

订阅内置：

```text
TUN                    开启
strict-route           开启
DNS hijack             any:53
增强模式               fake-ip
IPv6                   关闭
国外 DNS               Cloudflare/Google DoH，经 PROXY
国内直连 DNS           AliDNS/DNSPod DoH，经 DIRECT
代理节点域名 DNS       AliDNS/DNSPod DoH，用于启动链路
Fake-IP 持久化         关闭
```

Clash Verge Rev 中保持“DNS 覆写”关闭，避免客户端再次覆盖订阅内置 DNS。TUN 需要 Clash Verge Service 正常安装并运行。

规则模式允许国内站点走 `DIRECT`，因此访问国内应用时看到 VPS 与国内出口并存属于设计结果。`browserleaks.com`、`ipleak.net` 等检测站点已显式走 `PROXY`，不应再因中国规则集误判而暴露本地出口。

## 运行目录

完整生产状态位于一个目录：

```text
/opt/3x-ui/docker-compose.yml
/opt/3x-ui/data/x-ui.db
/opt/3x-ui/data/access.env
/opt/3x-ui/data/reality-client.env
/opt/3x-ui/letsencrypt/
/opt/3x-ui/nginx/nginx.conf
/opt/3x-ui/mihomo-template.yaml
/opt/3x-ui/www/
```

日常状态与日志：

```bash
cd /opt/3x-ui
docker compose ps
docker compose logs -f --tail=100
```

修改 Mihomo 模板后重新写入 3X-UI：

```bash
cd /opt/3x-ui
./apply-mihomo-template.sh
```

脚本会先用 SQLite 在线备份 API 保存数据库，再更新模板并重启 3X-UI。

## 迁移与备份

创建一致性归档：

```bash
cd /opt/3x-ui
./backup.sh
```

归档包含 SQLite、订阅凭据、Reality 密钥和 ACME 状态，权限为 `600`，必须按私钥处理。目标 VPS 安装 Docker 后，将归档恢复为 `/opt/3x-ui`，更新三个 A 记录，再运行：

```bash
cd /opt/3x-ui
docker compose up -d
```

域名不变时可以直接复用迁移过来的证书与 ACME 账号。全新部署且没有证书时，确认 TCP 80 空闲并执行：

```bash
cd /opt/3x-ui
LE_EMAIL='<your-email>' ./init-certificates.sh
```

全新数据库还需要在 3X-UI 中创建仅监听 `127.0.0.1:10443` 的 `VLESS + REALITY + Vision` 入站，并将公开地址设置为 `proxy.bigpandas.top:443`。随后执行 `apply-mihomo-template.sh`。

## 安全基线

```text
UFW 默认拒绝入站，只允许 TCP 22/80/443
SSH 禁用密码、键盘交互和 X11，只允许 root 公钥登录
Fail2Ban 仅保护 SSH，并通过 UFW 封禁
3X-UI、订阅和 Reality 后端只监听 127.0.0.1
3X-UI 容器不授予 NET_ADMIN，不运行容器内 Fail2Ban
Nginx 和 Certbot 使用固定版本镜像与摘要
```

发布前检查：

```bash
git status --short
git diff --cached
rg -n '(token=|uuid:|password:|private-key:|sub-id|VLESS_UUID)' --hidden .
```

不要提交 `/opt/3x-ui` 的任何运行时文件或备份归档。凭据一旦出现在公开提交、截图或聊天中，应立即轮换。

## 验证清单

```text
三个容器均为 Up，3x-ui 与 3x-ui-nginx 为 healthy
公网监听只有 TCP 22、80、443
panel.bigpandas.top 返回有效 HTTPS 证书
sub.bigpandas.top/clash/<sub-id> 能通过 Mihomo 配置测试
Reality 实际握手成功，出口为 VPS 公网 IP
PROXY 默认选择 AUTO，AUTO 选择实际节点
Clash Verge DNS 覆写关闭，TUN 与 strict-route 生效
浏览器 DNS 测试不出现本地运营商解析器
```

## 参考

- [3X-UI](https://github.com/MHSanaei/3x-ui)
- [Mihomo](https://github.com/MetaCubeX/mihomo)
- [Mihomo 配置文档](https://wiki.metacubex.one/)
- [Certbot](https://certbot.eff.org/)
