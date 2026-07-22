# AaITR + YunTu 代理基础设施

这个仓库整理了两台机器上的公开部署模板和运维说明：

- **AaITR 落地机**：运行 s-ui、订阅服务、HTTPS/SNI 边缘入口和 AaITR 家宽出口。
- **YunTu 线路机**：作为入口中转、UDP 转发、SOCKS/HTTP 转发入口，以及可选的 YunTu 机房出口。

仓库只保存可公开的编排、模板、脚本和中文说明；运行数据库、面板密码、证书私钥、订阅凭据、客户端配置和备份都被 `.gitignore` 排除。

## 当前拓扑

```text
客户端
  ├─ yuntu-aaitr-*  -> YunTu 线路机 -> AaITR 家宽落地 -> 目标网站
  ├─ yuntu-exit-*   -> YunTu 线路机 -> 目标网站
  └─ aaitr-exit-*   -> AaITR 家宽落地 -> 目标网站
```

桌面订阅里保留三组出口模式：

| 分组 | 链路 | 出口 IP 类型 | 推荐用途 |
|---|---|---|---|
| `YUNTU-AAITR-AUTO` | 客户端 -> YunTu -> AaITR -> 互联网 | AaITR 家宽 | 默认主力，适合 Google、Gmail、Gemini、Claude、ChatGPT、Telegram 等 |
| `YUNTU-EXIT-AUTO` | 客户端 -> YunTu -> 互联网 | YunTu 机房 | 备用、下载、对 IP 质量不敏感的流量 |
| `AAITR-EXIT-AUTO` | 客户端 -> AaITR -> 互联网 | AaITR 家宽 | 直连 AaITR 备用与对照测试 |

每个 AUTO 分组内部自动在 Reality、Hysteria2、AnyTLS 三种协议中选择延迟最低的节点。

## 目录结构

```text
3x-ui/          已停用的旧 3x-ui Docker 模板，仅作为迁移参考
s-ui/           AaITR s-ui 主服务、订阅模板、同步脚本和验证脚本
s-ui-edge/      AaITR Nginx/Certbot 边缘入口，负责 80/443、证书和订阅兼容路径
yuntu-line/     YunTu 线路机 Docker 编排和 HAProxy/GOST/sing-box 说明
workspace-activation/
                独立静态/接口工具，保留为既有仓库内容
```

## 分流策略

当前 Clash/Mihomo 订阅使用极简 CN 白名单策略：

```yaml
rules:
  - DOMAIN-SUFFIX,browserleaks.com,EXIT-MODE
  - GEOSITE,private,DIRECT
  - GEOIP,private,DIRECT,no-resolve
  - GEOSITE,cn,DIRECT
  - GEOIP,cn,DIRECT,no-resolve
  - MATCH,EXIT-MODE
```

含义：

- 局域网和国内域名/IP 走 `DIRECT`。
- 其他全部走 `EXIT-MODE`。
- `browserleaks.com` 被前置修正，因为当前 geosite 数据库会把它归到 `cn`。

如果以后发现某个域名误分类，优先在 `GEOSITE,cn,DIRECT` 前添加个人补丁规则。

## 自动同步

AaITR 是管理源。新增或修改生产用户后：

1. s-ui 生成订阅中的三种链路节点。
2. `yuntu-exit-sync.timer` 每分钟渲染 YunTu exit 配置。
3. 同步脚本通过 SSH 推送到 YunTu。
4. YunTu 先用 sing-box 校验配置；只有配置 hash 变化时才重启 `yuntu-exit`。

## 安全边界

禁止提交：

- s-ui SQLite 数据库与面板密码
- 订阅 token、用户密码、UUID、Reality 私钥/short id
- ACME 账号、证书私钥、`letsencrypt/`
- YunTu 生成的 `yuntu-exit/config.json`
- 运行备份、日志和本地测试产物

提交前建议运行：

```bash
git status --short
git diff --cached --name-only
```

并确认没有 `.admin-password`、`db/`、`letsencrypt/`、`yuntu-exit/config.json`、`backups/` 等内容进入暂存区。

## 常用验证

AaITR：

```bash
cd /root/code/us-public/s-ui
python3 ./verify_s_ui.py subscriptions
python3 ./verify_s_ui.py protocols
python3 ./verify_s_ui.py proxies
```

YunTu：

```bash
cd /root/code/aaitr
docker compose ps
docker compose run --rm --no-deps relay haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg
docker compose run --rm --no-deps yuntu-exit check -c /etc/sing-box/config.json
```

更多细节见各子目录 README。
