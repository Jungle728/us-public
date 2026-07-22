# AaITR edge 入口

该目录对应 AaITR 机器 `/root/code/us-public/s-ui-edge`。它用 Docker 运行 Nginx 和 Certbot，负责公网 80/443、TLS 证书、SNI 路由、面板反向代理和订阅兼容路径。

## 职责

- TCP 80：ACME HTTP-01 验证和 HTTP 到 HTTPS 跳转。
- TCP 443：按 SNI 分流 Reality、HTTPS 代理、面板和订阅。
- `panel.bigpandas.top`：反向代理到 s-ui 面板。
- `sub.bigpandas.top`：提供 `/sub/`、`/json/`、`/clash/` 兼容订阅路径。
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

证书续期每 12 小时检查一次。Nginx 容器每 5 分钟检查证书 mtime；如果证书变化，会先运行 `nginx -t`，成功后热重载。

s-ui 内置 sing-box core 同时 watch 证书文件，Hysteria2 和 AnyTLS 可随证书续期原地刷新。
