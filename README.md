# Verizon + CStoneCloud 代理基础设施

这个仓库整理了两台机器上的公开部署模板和运维说明：

- **Verizon 落地机**：运行 Remnawave 管理源、订阅服务、独立 HTTPS/SNI 边缘入口和 Verizon 家宽出口。
- **CStoneCloud 线路机**：作为 Reality/Hysteria2 的入口中转，以及可选的 CStoneCloud 机房出口；自有域名的 443/TCP 由 HAProxy 分流到 TLS Vision 和本机 Nginx 回落站。

当前生产主机（2026-08-22 核对）：

| 角色 | 主机 | 节点域名 | 定位 |
|---|---|---|---|
| Verizon | `47.178.15.216` | `verizon.bigpandas.top` | 当前主力机；运行管理面、订阅、AaITR 出口及 Xray/sing-box Node |
| CStoneCloud | `70.39.179.159` | `cstonecloud.bigpandas.top` | 线路中转与备用机房出口 |

仓库只保存可公开的编排、模板、脚本和中文说明；运行数据库、面板密码、证书私钥、订阅凭据、客户端配置和备份都被 `.gitignore` 排除。

## 当前拓扑

```text
客户端
  ├─ csc-aaitr-*  -> CStoneCloud 线路机 -> AaITR 家宽落地 -> 目标网站
  ├─ csc-*        -> CStoneCloud 线路机 -> 目标网站
  └─ aaitr-*      -> AaITR 家宽落地 -> 目标网站
```

桌面订阅里保留三组出口模式：

| 分组 | 链路 | 出口 IP 类型 | 推荐用途 |
|---|---|---|---|
| `CSC-AAITR` | 客户端 -> CStoneCloud -> AaITR -> 互联网 | AaITR 家宽 | 默认主力，适合 Google、Gmail、Gemini、Claude、ChatGPT、Telegram 等 |
| `CSC` | 客户端 -> CStoneCloud -> 互联网 | CStoneCloud 机房 | 备用、下载、对 IP 质量不敏感的流量 |
| `AAITR` | 客户端 -> AaITR -> 互联网 | AaITR 家宽 | 直连 AaITR 备用与对照测试 |

每个模式组默认使用对应的 `*-AUTO`，自动在 Reality、Hysteria2 和 TLS Vision
三种协议中选择延迟最低的节点；需要排障或保持固定传输时，也可以在模式组内
手动指定协议。

Hysteria2 订阅使用经过既有线路验证的公网 UDP 端口：`csc-aaitr-hy2` 为
`443`、`csc-hy2` 为 `2443`、`aaitr-hy2` 为 `32443`。迁移期的
`33445`、`33444`、`33443` 仍作为兼容入口保留，不会使已下载的新配置失效。

两台机器都运行受 Remnawave 管理的 Xray 与 sing-box：Reality/TLS 固定由 Xray
`26.6.27` 承载，HY2 固定由 sing-box `1.13.15` 承载。`aaitr-hy2` 的
`32443/udp` 与 `csc-aaitr-hy2` 的 `443/udp` 转发到 AaITR `34443/udp`；
`csc-hy2` 的 `2443/udp` 转发到 CStoneCloud 本机 `34444/udp`。sing-box Node
使用 Remnawave 用户 ID 作为统计键并上报用户流量。旧 Xray `33443/udp`、
`33444/udp` 与 CStoneCloud `33445/udp` 保留用于兼容和快速回滚。

链式节点是四层透明中转：Reality/TLS 由 HAProxy 转发到 AaITR Xray，HY2 由
GOST 转发到 AaITR sing-box。CStoneCloud 不对同一用户流量做第二次协议解密，
因此不会重复统计；最终终止协议的 Remnawave Node 负责归账。

macOS 和 iOS 的 Shadowrocket 使用一份与节点订阅解耦的公共配置。用户添加自建或机场订阅后，再启用 `https://sub-verizon.bigpandas.top/shadowrocket/config.conf`，将全局路由设为“配置”，规则中的 `PROXY` 就会使用首页当前选中的任意节点；未知域名同样默认代理。Clash/Mihomo 仍保留三种链路分组和自动选路，不受 Shadowrocket 配置影响。

## 目录结构

```text
3x-ui/          已停用的旧 3x-ui Docker 模板，仅作为迁移参考
aaitr-s-ui/     已停用的旧 s-ui 实现，仅作为迁移归档与回滚参考
remnawave-edge/ Verizon 独立 Nginx/Certbot 入口、回落站和公共静态规则
remnawave/      Verizon Remnawave Panel、PostgreSQL 与 Valkey 编排
remnawave-node/ Verizon Remnawave Node 编排
remnawave-subscription/
                Remnawave 官方用户订阅页
remnawave-singbox-hy2/
                Remnawave 双 Core HY2 补丁、隔离验证与双机生产 Node
singbox-hy2/    已停用的 standalone sing-box HY2 回滚参考
decoy/          CStoneCloud TLS Vision 的本机 Nginx HTTP 回落站
yuntu-line/     CStoneCloud 线路机 Docker 编排（目录名为兼容旧部署而保留）
workspace-activation/
                独立静态/接口工具，保留为既有仓库内容
```

## 分流策略

当前 Clash/Mihomo 订阅使用极简 CN 白名单策略：

```yaml
rules:
  - GEOSITE,category-ai-!cn,EXIT-MODE
  - DOMAIN-SUFFIX,browserleaks.com,EXIT-MODE
  - GEOSITE,private,DIRECT
  - GEOIP,private,DIRECT,no-resolve
  - GEOSITE,cn,DIRECT
  - GEOIP,cn,DIRECT,no-resolve
  - MATCH,EXIT-MODE
  - MATCH,REJECT
```

含义：

- 局域网和国内域名/IP 走 `DIRECT`。
- 其他全部走 `EXIT-MODE`。
- 海外 AI 域名优先走 `EXIT-MODE`，即使与 `geosite:cn` 重叠也不会直连；其 DNS 同样经海外 DoH 和当前出口组解析。
- `browserleaks.com` 被前置修正，因为当前 geosite 数据库会把它归到 `cn`。
- 最后的 `MATCH,REJECT` 只在 `EXIT-MODE` 无法承载当前连接、被 Mihomo 跳过时生效，保证未知流量失败关闭而不是隐式直连。
- 公开 Clash 订阅包含 Reality、Hysteria2 和 TLS Vision，并明确启用 UDP；Reality 使用 `xudp`，避免浏览器 QUIC 绕过所选出口。

如果以后发现某个域名误分类，优先在 `GEOSITE,cn,DIRECT` 前添加个人补丁规则。

## 管理与转发服务

Remnawave 是唯一的用户、订阅、节点和出口管理源。生产共有四个 Node 实例：
Verizon Xray、Verizon sing-box、CStoneCloud Xray 和 CStoneCloud sing-box。
不再运行 s-ui 用户同步或旧 `yuntu-exit` 订阅同步。

正式管理入口为 `https://panel-verizon.bigpandas.top/dashboard`，当前唯一管理员
用户名为 `lhl`。面板密码属于运行凭据，不写入本仓库。

Remnawave 只允许一个面板管理员。管理员创建用户后，把面板生成的
`https://sub-verizon.bigpandas.top/<short-uuid>` 交给用户；浏览器打开是官方
订阅页，客户端添加同一个地址则获得对应格式。普通用户没有面板密码，私有地址
本身是访问凭据，泄露时应在面板撤销并重新生成。

Verizon 的 `1080/TCP` 认证 SOCKS5 由 Remnawave Node 内的 Xray 静态入站提供，
仅供服务器和 API 使用，不进入桌面订阅。该静态账户由管理员 `lhl` 持有，
但不与 Remnawave 中同名的普通订阅用户自动联动；凭据在
`Verizon-Production` Config Profile 的 `VERIZON-SOCKS5` 入站中管理，与旧
s-ui 数据库无运行时依赖。连接地址为 `verizon.bigpandas.top:1080`，用户名为
`lhl`，仅启用 TCP；密码只保存在生产配置中，不写入仓库。

## 自有域名 TLS 回落

Remnawave 使用两层互不回环的入口：公网 `443/TCP` 按自有 SNI 分流到本机
VLESS + TLS Vision，非 VLESS 的普通 HTTPS 请求在 TLS 解密后回落到
`127.0.0.1:18080` 的 Nginx 静态站；高位 Reality 则把本机 TLS Vision
`127.0.0.1:30443` 作为目标，并使用各自的
`verizon.bigpandas.top` 或 `cstonecloud.bigpandas.top` SNI。这样 Reality 不依赖
第三方域名，也不会把流量重新送回自己的 Reality 入站。

未识别 SNI 的 Verizon 443 流量直接拒绝，不再进入旧 s-ui。CStoneCloud 的
HAProxy 按自有域名分流本机 TLS Vision 与 Verizon 线路。

## 安全边界

禁止提交：

- s-ui SQLite 数据库与面板密码
- 订阅 token、用户密码、UUID、Reality 私钥/short id
- ACME 账号、证书私钥、`letsencrypt/`
- 旧 CStoneCloud `yuntu-exit/config.json` 归档
- 运行备份、日志和本地测试产物

提交前建议运行：

```bash
git status --short
git diff --cached --name-only
```

并确认没有 `.admin-password`、`db/`、`letsencrypt/`、`yuntu-exit/config.json`、`backups/` 等内容进入暂存区。

## 常用验证

Verizon：

```bash
cd /root/code/us-public/remnawave
docker compose ps
curl -fsS http://127.0.0.1:3001/health
cd /root/code/us-public/remnawave-edge
docker compose exec -T nginx nginx -t
```

CStoneCloud：

```bash
cd /root/code/aaitr
docker compose ps
docker compose run --rm --no-deps relay haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg
cd /root/code/aaitr/remnawave-relay
docker compose ps
```

更多细节见各子目录 README。

机器更换和运行数据迁移说明见 [MIGRATION.md](MIGRATION.md)。
