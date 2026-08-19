# AaITR edge 入口

该目录对应 AaITR 机器 `/root/code/us-public/s-ui-edge`。它用 Docker 运行 Nginx 和 Certbot，负责公网 80/443、TLS 证书、SNI 路由、面板反向代理和订阅兼容路径。

## 职责

- TCP 80：ACME HTTP-01 验证和 HTTP 到 HTTPS 跳转。
- TCP 443：按 SNI 分流 Reality、面板和订阅。
- `panel.bigpandas.top`：反向代理到 s-ui 面板。
- `panel.bigpandas.top/modern/`：由 Nginx 直接提供轻量现代控制台，根路径默认跳转至此。
- `panel.bigpandas.top/app/`：保留原 s-ui 面板，用于协议、TLS 和底层配置。
- `sub.bigpandas.top`：提供 `/sub/`、`/json/`、`/clash/` 兼容订阅路径。
- `sub.bigpandas.top/shadowrocket/config.conf`：提供不含用户凭据的 Shadowrocket 公共配置。
- `sub.bigpandas.top/shadowrocket/ai.list`：提供优先于 CN 白名单的关键 AI 域名规则。
- 对 `/json/` 和 `/clash/` 响应做显示名称规范化，不修改协议凭据。
- 隐藏 s-ui 默认订阅更新间隔，统一发布 `Profile-Update-Interval: 1`。

## 文件

```text
docker-compose.yml  Nginx 与 Certbot 编排
nginx.conf          入口、SNI、订阅和静态路由
```

运行时生成且不提交：

```text
letsencrypt/        ACME 账号、证书和私钥
certbot-www/        HTTP-01 challenge 文件
certbot-lib/        Certbot 状态
certbot-logs/       Certbot 日志
backups/            配置备份
```

## 运维

```bash
cd /root/code/us-public/s-ui-edge
docker compose config -q
docker compose ps
docker compose logs --tail=100 nginx certbot
docker compose exec -T nginx nginx -t
docker compose exec -T nginx nginx -s reload
```

现代控制台构建产物默认从 `/root/code/us-public/s-ui/modern-ui/dist` 只读挂载。Shadowrocket 公共配置默认从 `/root/code/us-public/s-ui/shadowrocket` 只读挂载；可以分别通过 `MODERN_UI_DIST` 和 `SHADOWROCKET_DIR` 覆盖路径。生产切换使用 `docker compose up -d nginx` 重新创建 Nginx 容器以加载新增挂载。

证书续期每 12 小时检查一次。Nginx 容器每 5 分钟检查证书 mtime；如果证书变化，会先运行 `nginx -t`，成功后热重载。

s-ui 内置 sing-box core 同时 watch 证书文件，Hysteria2 可随证书续期原地刷新。
