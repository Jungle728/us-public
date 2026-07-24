# AaITR s-ui 主服务

该目录对应 AaITR 机器 `/root/code/us-public/s-ui`。它是当前唯一的代理用户管理源，旧 `3x-ui` 仅作为离线迁移备份保留，不再运行。

## 职责

- 管理生产订阅用户和转发代理用户。
- 生成 raw / sing-box JSON / Clash 订阅。
- 提供 Reality、Hysteria2、AnyTLS、SOCKS5、HTTP、HTTPS 入站。
- 渲染 YunTu 直接出口配置，并通过 systemd timer 同步到 YunTu。
- 提供验证脚本，检查订阅、协议链路和 forward proxy 出口。

## 监听端口

| 地址/端口 | 用途 |
|---|---|
| `127.0.0.1:3095` | s-ui 面板 |
| `127.0.0.1:3096` | 订阅服务 |
| `127.0.0.1:31443` | VLESS Reality，由 edge SNI 路由选择 |
| `32443/udp` | Hysteria2，可经 YunTu UDP 443 中转或 AaITR 直连 |
| `33443/tcp` | AnyTLS，可经 YunTu TCP 8443 中转或 AaITR 直连 |
| `31080/tcp` | SOCKS5 后端，仅供 YunTu 入口转发 |
| `31081/tcp` | HTTP 后端，仅供 YunTu 入口转发 |
| `127.0.0.1:31444` | HTTPS 代理后端，由 edge SNI 路由选择 |

s-ui 容器使用 host network，因此公网暴露由 UFW 和 `s-ui-edge` 控制。SOCKS5/HTTP/HTTPS 代理不做来源白名单，但仍要求 s-ui 用户名/密码认证。

## Clash 分流策略

`clash-template.yaml` 是生产 Clash/Mihomo 模板。当前使用 CN 白名单模式：

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

说明：

- 私有地址和中国域名/IP 走 `DIRECT`。
- 其他全部走 `EXIT-MODE`。
- 海外 AI 域名优先走 `EXIT-MODE`，并通过海外 DoH 解析，避免与 `geosite:cn` 重叠时误走直连。
- `browserleaks.com` 被显式放入 `EXIT-MODE`，用于修正上游 geosite 数据库误分类。
- 最后的 `MATCH,REJECT` 是 fail-closed 保护：只有所选出口不支持当前流量、导致前一个 `MATCH,EXIT-MODE` 被 Mihomo 跳过时才会命中，防止内核隐式回落到 `DIRECT`。
- Clash 订阅入口会为 Reality / Hysteria2 / AnyTLS 明确写入 UDP 能力；Reality 同时使用 `xudp` 封装，保证浏览器 QUIC 也服从 `EXIT-MODE`。

`EXIT-MODE` 下有三个手动模式组：

| 分组 | 链路 |
|---|---|
| `YUNTU-AAITR` | 客户端 -> YunTu -> AaITR -> 目标网站 |
| `YUNTU-EXIT` | 客户端 -> YunTu -> 目标网站 |
| `AAITR-EXIT` | 客户端 -> AaITR -> 目标网站 |

每个手动模式组默认选择对应的 `*-AUTO` URLTest，也允许固定 Reality、Hysteria2 或 AnyTLS。AUTO 仍会在同一条出口链路的三个协议中选择延迟最低的节点，不会跨模式改变出口。

应用模板：

```bash
cd /root/code/us-public/s-ui
python3 ./apply_clash_template.py
```

脚本会先备份 SQLite，写入模板后验证生产订阅；验证失败会自动回滚。

## 节点地址布局

当前桌面订阅节点命名按链路优先：

```text
yuntu-aaitr-reality / yuntu-aaitr-hy2 / yuntu-aaitr-anytls
yuntu-exit-reality  / yuntu-exit-hy2  / yuntu-exit-anytls
aaitr-exit-reality  / aaitr-exit-hy2  / aaitr-exit-anytls
```

刷新入站地址布局：

```bash
cd /root/code/us-public/s-ui
python3 ./apply_desktop_direct_nodes.py
```

## YunTu exit 自动同步

AaITR 负责生成 YunTu 直接出口 sing-box 配置：

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

s-ui 会立即为新用户生成订阅；timer 负责在约一分钟内把 `aaitr-production` 用户的 Reality、Hysteria2 和 AnyTLS 认证同步到 YunTu exit。`yuntu-exit-sync-*` 是单次同步使用的临时工作目录，正常结束会自动删除，不是用户数据目录。

同步流程：

1. 从 s-ui 读取 `aaitr-production` 组用户。
2. 渲染 YunTu Reality / Hysteria2 / AnyTLS 直接出口配置。
3. SSH 推送到 YunTu 临时文件。
4. 在 YunTu 上用 sing-box 校验。
5. 只有配置 hash 变化时才替换配置并重启 `yuntu-exit`。

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
