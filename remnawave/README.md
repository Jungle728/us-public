# Remnawave Panel

该目录保存 Verizon 上 Remnawave Panel、PostgreSQL 与 Valkey 的公开 Docker Compose 模板。生产环境路径为 `/root/code/us-public/remnawave`，管理入口由独立的 `remnawave-edge` Nginx 反向代理提供 HTTPS。

运行时 `.env`、管理员密码和数据库卷不会进入仓库。当前部署固定使用与 Remnawave
`3.3.2` 数据库兼容的 `local/remnawave-backend:3.3.2-singbox-hy2`，在保持 Xray
Profile 不变的同时允许独立 sing-box Node 管理 HY2；数据库仅绑定到 `127.0.0.1`。
`remnawave-network` 由 Panel、Subscription Page 等多个 Compose 项目共享，因此
在本 Compose 中声明为 external，避免只重建 Panel 时误删仍有活动端点的网络。

正式管理入口为 `https://panel-verizon.bigpandas.top/`，正式订阅域名为
`https://sub-verizon.bigpandas.top/`。`rw-panel.bigpandas.top` 与
`rw-sub.bigpandas.top` 保留为别名。旧 s-ui 面板、订阅路由和默认 SNI 回落均
不再接入生产入口。

当前主力机为 `47.178.15.216`。面板的直接管理路径为
`https://panel-verizon.bigpandas.top/dashboard`；唯一管理员用户名为 `lhl`，
密码不进入版本控制。

正式用户入口由官方 Subscription Page 的 `/<short-uuid>` 提供；旧
`/api/sub/<short-uuid>` 继续兼容。版本控制中的 `mihomo-template.yaml` 是生产
默认 Mihomo 模板，使用 `apply_subscription_template.py` 应用或检查。
响应规则中的通用 Clash 客户端（包括 Clash Mi、ClashMetaForAndroid 等）统一返回
该 Mihomo 模板；使用 `apply_subscription_response_rules.py` 应用或检查，避免手机端
命中旧的空代理 Clash 模板。

用户可见节点固定使用 `csc-aaitr-{reality,hy2,tls}`、
`csc-{reality,hy2,tls}` 和 `aaitr-{reality,hy2,tls}`；对应分组为
`CSC-AAITR`、`CSC`、`AAITR`，不使用提供商名加 `-exit` 的表达。

Hysteria2 的订阅公网端口保持旧布局：`csc-aaitr-hy2` 使用 `443/udp`、
`csc-hy2` 使用 `2443/udp`、`aaitr-hy2` 使用 `32443/udp`。Remnawave Xray
入站仍保留迁移期高位端口用于回滚；正式 HY2 流量由受 Remnawave 管理的
sing-box Node 终止，并按用户上报流量。链式 HY2 只做四层转发，不重复记账。

Remnawave 3.3.2 只允许一个面板管理员，当前管理员用户名为 `lhl`。普通代理
用户没有密码和面板登录能力；管理员创建用户后，应将用户的私有 Subscription
Page 地址交给本人。该地址就是访问凭据，泄露时在面板撤销并重新生成。

`verizon.bigpandas.top:1080` 是 Xray `VERIZON-SOCKS5` 静态入站，用户名为
`lhl`，仅启用 TCP。它不进入订阅，也不与同名 Remnawave 普通用户自动联动；
密码只在生产 Config Profile 中维护。

常用检查：

```bash
docker compose config
docker compose ps
docker compose logs --tail=100 remnawave
curl -fsS http://127.0.0.1:3001/health
```
