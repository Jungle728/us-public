# Remnawave Node（Verizon）

该目录是 Verizon 同机 Remnawave Node 的公开 Docker Compose 模板。Node 使用 host 网络承载 Xray 入站，面板、PostgreSQL 和 Valkey 则位于相邻的 `remnawave/` 目录。

## 部署

1. 在 Remnawave 面板中生成 Node `SECRET_KEY`。
2. 复制 `.env.example` 为 `.env`，填写密钥；`.env` 不得提交。
3. 启动并检查：

```bash
docker compose config
docker compose pull
docker compose up -d
docker compose ps
docker compose logs --tail=100
```

默认管理端口为 `2222`。协议入站端口由 Remnawave Config Profile 控制，
同一主机上的端口必须保持唯一。

迁移配置使用 `127.0.0.1:30443` 承载 VLESS + TLS Vision。Verizon 边缘 Nginx
按 `verizon.bigpandas.top` SNI 将公网 443 转到该端口；TLS Vision 的普通 HTTPS
fallback 指向 Nginx 明文端口 `127.0.0.1:18080`。高位 Reality 也以
`127.0.0.1:30443` 为目标和自有域名为 SNI，不依赖第三方站点。

Verizon Node 还在同一个 Xray 配置中提供 `1080/TCP` 认证 SOCKS5。该入站使用
Remnawave 允许的 `mixed` 兼容名称，但底层由 Xray 的 SOCKS 服务实现；它使用
由管理员 `lhl` 持有的静态认证账户，不会进入用户订阅或 Remnawave 内部分组，
也不与 Remnawave 中同名的普通订阅用户自动联动。用户名和密码只在面板的
`Verizon-Production` Config Profile、`VERIZON-SOCKS5` 入站中维护，不得写入
仓库或公共 Shadowrocket 配置。

证书只读挂载自 `/root/code/us-public/remnawave-edge/letsencrypt`，不依赖旧
s-ui 目录。

该 Compose 会本地构建 `Remnawave Node 3.3.2 + Xray 26.6.27`。Xray
`26.7.11` 及更新版本的 Reality 握手与当前 Mihomo/Clash 客户端不兼容，
会导致密钥、short ID 和 SNI 均正确时仍然认证失败。不要在未完成 Mihomo
真实握手验证前移除 Dockerfile 中的核心版本固定。

Compose 只读挂载 Remnawave Edge 的 Certbot 目录，供 Hysteria2 TLS 入站复用
`verizon.bigpandas.top` 的有效证书。证书续期后需重启 Node 或在面板中重启
Xray，使核心重新读取证书文件。

Xray 的旧 Hysteria2 入站继续监听 `33443/udp`，供迁移期客户端和快速回滚使用。
生产 `aaitr-hy2` 已由相邻 `remnawave-singbox-hy2/production` 中受 Remnawave
管理的 sing-box Node 承载 `34443/udp`；本 Compose 的 `hy2-compat-relay` 监听
公网 `32443/udp` 并转发到 `34443/udp`，因此正式订阅端口和节点名称保持不变。
