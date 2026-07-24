# 3X-UI Docker 栈

该目录是生产环境 `/opt/3x-ui` 的无凭据模板。应用组件全部使用 Docker：

```text
3x-ui           面板、SQLite、Xray 和订阅
3x-ui-nginx     80/443 入口与 SNI 分流
3x-ui-certbot   Let's Encrypt 自动续期
```

## 文件

```text
docker-compose.yml          容器编排
nginx/nginx.conf            443 SNI、面板和订阅反向代理
mihomo-template.yaml        Clash Verge/Mihomo 的 TUN、防泄漏 DNS 和国内外分流模板
apply-mihomo-template.sh    将模板写入 3X-UI SQLite
init-certificates.sh        使用 Certbot 容器首次签发证书
backup.sh                   停止容器后创建可迁移归档
www/                        可选静态文件目录
```

运行时生成且禁止提交：

```text
data/              SQLite、面板凭据、订阅 ID 和 Reality 密钥
letsencrypt/       证书私钥和 ACME 账号
logs/              3X-UI 日志
certbot-*/         Certbot 状态与日志
```

## 启动

```bash
cd /opt/3x-ui
docker compose up -d
docker compose ps
```

面板、订阅和 Reality 后端必须在 SQLite 中配置为仅监听：

```text
127.0.0.1:2053   面板
127.0.0.1:2096   订阅
127.0.0.1:10443  Reality 入站
```

公网只由 `3x-ui-nginx` 监听 TCP 80/443。

## 更新规则

编辑 `mihomo-template.yaml` 后执行：

```bash
./apply-mihomo-template.sh
```

脚本会重新绑定最新模板文件、备份 SQLite、开启 3X-UI 的 Clash 自定义路由、写入完整 Mihomo 模板并等待容器恢复健康。

## 证书

首次签发：

```bash
LE_EMAIL='<your-email>' ./init-certificates.sh
```

运行后由 `3x-ui-certbot` 每 12 小时检查续期。Nginx 每 5 分钟检查证书时间戳，证书变化后自动测试配置并热重载，不需要宿主机 Certbot 或 Docker Socket。

## 迁移

```bash
./backup.sh
```

将生成的 `3x-ui-<UTC 时间>.tar.gz` 及校验文件传到目标 VPS，恢复为 `/opt/3x-ui` 后运行 `docker compose up -d`。归档含全部私钥和订阅凭据，只能以 `600` 权限保存。
