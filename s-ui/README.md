# AaITR s-ui 主服务

该目录对应 AaITR 机器 `/root/code/us-public/s-ui`。它是当前唯一的代理用户管理源，旧 `3x-ui` 仅作为离线迁移备份保留，不再运行。

## 职责

- 管理生产订阅用户和转发代理用户。
- 生成 raw / sing-box JSON / Clash 订阅。
- 提供 Reality、Hysteria2 桌面入站，以及一个直连 AaITR 的认证 SOCKS5 转发入口。
- 渲染 CStoneCloud 直接出口配置，并通过 systemd timer 同步到 CStoneCloud。
- 提供验证脚本，检查订阅、协议链路和 forward proxy 出口。

## 管理面板

- 日常管理：`https://panel-verizon.bigpandas.top/`，默认进入轻量现代控制台 `/modern/`。
- 高级配置：`https://panel-verizon.bigpandas.top/app/`，保留原 s-ui 页面处理入站、TLS、路由和底层数据库操作。

现代控制台位于 `modern-ui/`，复用 s-ui 原生登录和 `/app/api/*`，生产环境只由 edge Nginx 提供约 100 KiB 的静态构建产物，不增加常驻容器或 Node 进程。构建和部署方式见 `modern-ui/README.md`。

## 监听端口

| 地址/端口 | 用途 |
|---|---|
| `127.0.0.1:3095` | s-ui 面板 |
| `127.0.0.1:3096` | 订阅服务 |
| `127.0.0.1:31443` | VLESS Reality，由 edge SNI 路由选择 |
| `32443/udp` | Hysteria2，可经 CStoneCloud UDP 443 中转或 AaITR 直连 |
| `1080/tcp` | 认证 SOCKS5，直连 AaITR 出口，供服务器/API 使用 |

s-ui 容器使用 host network，因此公网暴露由 UFW 和 `s-ui-edge` 控制。SOCKS5 不做来源白名单，但仍要求 s-ui 用户名/密码认证。

## Clash 分流策略

`clash-template.yaml` 是生产 Clash/Mihomo 模板。当前使用 CN 白名单模式：

```yaml
rules:
  - DOMAIN-SUFFIX,bigpandas.top,DIRECT
  - DOMAIN-SUFFIX,shu26.cfd,DIRECT
  - DOMAIN,ucloud-frp.sometimesnaive.top,DIRECT
  - GEOSITE,category-ai-!cn,EXIT-MODE
  - DOMAIN-SUFFIX,browserleaks.com,EXIT-MODE
  - GEOSITE,private,DIRECT
  - GEOIP,private,DIRECT,no-resolve
  - GEOSITE,cn,DIRECT
  - GEOIP,cn,DIRECT,no-resolve
  - MATCH,EXIT-MODE
  - MATCH,REJECT
```

说明：

- 私有地址和中国域名/IP 走 `DIRECT`。
- `bigpandas.top` 的所有子域名和 `shu26.cfd` 显式走 `DIRECT`，DNS 同样通过国内 DoH 直连解析。
- H100 SSH 主机 `ucloud-frp.sometimesnaive.top` 精确走 `DIRECT`，不放开整个 `sometimesnaive.top`。
- 其他全部走 `EXIT-MODE`。
- 海外 AI 域名优先走 `EXIT-MODE`，并通过海外 DoH 解析，避免与 `geosite:cn` 重叠时误走直连。
- `browserleaks.com` 被显式放入 `EXIT-MODE`，用于修正上游 geosite 数据库误分类。
- 最后的 `MATCH,REJECT` 是 fail-closed 保护：只有所选出口不支持当前流量、导致前一个 `MATCH,EXIT-MODE` 被 Mihomo 跳过时才会命中，防止内核隐式回落到 `DIRECT`。
- Clash 订阅入口只为 Reality / Hysteria2 明确写入 UDP 能力；Reality 同时使用 `xudp` 封装，保证浏览器 QUIC 也服从 `EXIT-MODE`。

`EXIT-MODE` 下有三个手动模式组：

| 分组 | 链路 |
|---|---|
| `CSTONECLOUD-AAITR` | 客户端 -> CStoneCloud -> AaITR -> 目标网站 |
| `CSTONECLOUD-EXIT` | 客户端 -> CStoneCloud -> 目标网站 |
| `AAITR-EXIT` | 客户端 -> AaITR -> 目标网站 |

每个手动模式组默认选择对应的 `*-AUTO` URLTest，也允许固定 Reality 或 Hysteria2。AUTO 仍只会在同一条出口链路的两种协议中选择延迟最低的节点，不会跨模式改变出口。

## Shadowrocket（macOS / iOS）

Shadowrocket 使用两项相互独立的远程资源：

- 用户私有节点订阅：`https://sub-verizon.bigpandas.top/sub/<subscription-id>`
- 公共分流配置：`https://sub-verizon.bigpandas.top/shadowrocket/config.conf`

必须先添加节点订阅，再下载并启用公共配置。公共配置不含订阅 ID、UUID、密码或节点链接，也不绑定任何订阅名或节点名。自建订阅、机场订阅和手工节点可以同时存在；需要代理的流量统一使用 Shadowrocket 首页当前选中的节点。

Shadowrocket 策略刻意比 Clash 更保守：

- `bigpandas.top`、`shu26.cfd` 和 H100 SSH 域名始终直连，并返回真实 IP。
- AI、Google、Gmail、Gemini、Grok/X、Telegram、Claude 和 OpenAI 等关键域名优先走内置 `PROXY`。
- `.cn`、维护的国内域名集合、私网地址和已经明确是中国 IP 的连接走 `DIRECT`。
- `GEOIP,CN` 使用 `no-resolve`，不会为了判断未知域名而把海外域名先交给国内 DNS。
- 无法确认归属的域名最终走内置 `PROXY`；不支持 UDP 时拒绝连接，不回落到直连。
- 节点域名和 SSH 域名使用真实 IP，不会出现 Mihomo Fake-IP 的 `198.18.0.0/16` 地址。

使用时将全局路由设为“配置”，并在首页直接选择想用的节点。全局路由设为“代理”会让国内流量也走节点，设为“直连”则会绕过所有代理规则。配置包含 `update-url`，Shadowrocket 可更新配置和远程规则。节点订阅的自动更新间隔需在 Shadowrocket 的“设置 > 服务器订阅”中设为 1 小时；iOS 还应允许“后台 App 刷新”。

本地静态验证：

```bash
cd /root/code/us-public/s-ui
python3 ./verify_shadowrocket.py
```

应用模板：

```bash
cd /root/code/us-public/s-ui
python3 ./apply_clash_template.py
```

脚本会先备份 SQLite，写入模板后验证生产订阅；验证失败会自动回滚。

## 节点地址布局

当前桌面订阅节点命名按链路优先：

```text
cstonecloud-aaitr-reality / cstonecloud-aaitr-hy2
cstonecloud-exit-reality  / cstonecloud-exit-hy2
aaitr-exit-reality  / aaitr-exit-hy2
```

其中 CStoneCloud 节点地址和 TLS SNI 使用 `cstonecloud.bigpandas.top`，AaITR
直连节点及 SOCKS5 地址使用 `verizon.bigpandas.top`。

刷新入站地址布局：

```bash
cd /root/code/us-public/s-ui
python3 ./apply_desktop_direct_nodes.py
```

## CStoneCloud exit 自动同步

AaITR 负责生成 CStoneCloud 直接出口 sing-box 配置。为兼容既有生产部署，脚本文件、systemd 单元、容器和运行目录仍保留内部标识 `yuntu-exit`：

```bash
cd /root/code/us-public/s-ui
python3 ./export_yuntu_exit.py --output ./yuntu-exit/config.json
```

线上由 systemd timer 自动执行：

```bash
cd /root/code/us-public/s-ui
python3 ./install_yuntu_exit_sync.py
python3 ./install_yuntu_exit_sync.py --check
systemctl status yuntu-exit-sync.timer --no-pager
journalctl -u yuntu-exit-sync.service -n 50 --no-pager
```

s-ui 会立即为新用户生成订阅；timer 负责在约一分钟内规范化三条链路的节点名称，并把 `aaitr-production` 用户的 Reality、Hysteria2 认证同步到 CStoneCloud exit。`yuntu-exit-sync-*` 是单次同步使用的临时工作目录，正常结束会自动删除，不是用户数据目录。

同步流程：

1. 通过 s-ui 原生接口统一 `aaitr-production` 用户的两种协议权限，使运行中的核心立即热更新。
2. 将新用户的 6 个 raw 节点名称规范为三条链路的固定命名。
3. 渲染 CStoneCloud Reality / Hysteria2 直接出口配置。
4. SSH 推送配置和当前 TLS 证书到 CStoneCloud 临时目录。
5. 在 CStoneCloud 上用 sing-box 校验。
6. 只有配置或证书 hash 变化时才替换运行文件并重启 `yuntu-exit`。

手动立即同步：

```bash
cd /root/code/us-public/s-ui
python3 ./sync_yuntu_exit.py
```

## 验证

运行完整生产检查：

```bash
cd /root/code/us-public/s-ui
python3 ./verify_s_ui.py all
```

单项检查：

```bash
python3 ./verify_s_ui.py subscriptions
python3 ./verify_s_ui.py protocols
python3 ./verify_s_ui.py proxies
python3 ./verify_s_ui.py shadowrocket
```

验证脚本不会打印完整订阅链接、UUID、密码或节点 URI。

## 禁止提交

以下内容属于运行时敏感数据，必须由 `.gitignore` 排除：

```text
.admin-password
db/
s-ui.db
backups/
yuntu-exit/config.json
yuntu-exit/cert/
*.before-*
```
