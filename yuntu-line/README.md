# YunTu 线路机

该目录对应 YunTu 机器 `/root/code/aaitr` 的公开部署模板。YunTu 不是用户管理源，它只承担入口线路、中转和可选机房出口。

## 职责

```text
客户端 -> YunTu -> AaITR -> 目标网站
客户端 -> YunTu -> 目标网站
```

公开监听：

| 端口 | 协议 | 用途 |
|---|---|---|
| TCP 443 | HAProxy TCP | Reality 中转到 AaITR，同时承载 HTTPS 代理 SNI 路由 |
| UDP 443 | GOST UDP | Hysteria2 中转到 AaITR |
| TCP 8443 | HAProxy TCP | AnyTLS 中转到 AaITR |
| TCP 1080 | HAProxy TCP | SOCKS5 代理入口，后端仍由 AaITR 认证 |
| TCP 8080 | HAProxy TCP | HTTP 代理入口，后端仍由 AaITR 认证 |
| TCP 1443 | sing-box | YunTu Reality 直接出口 |
| UDP 2443 | sing-box | YunTu Hysteria2 直接出口 |
| TCP 9443 | sing-box | YunTu AnyTLS 直接出口 |

## 文件

```text
docker-compose.yml  Docker 服务编排：relay、udp-relay、yuntu-exit
haproxy.cfg         TCP 中转到 AaITR 的 HAProxy 配置
```

运行时生成且不提交：

```text
yuntu-exit/config.json    由 AaITR 根据生产用户渲染
yuntu-exit/cert/          从 AaITR 同步的证书和私钥
yuntu-exit/backups/       自动同步前的远端备份
backups/                  手工备份
```

## 运维

```bash
cd /root/code/aaitr
docker compose ps
docker compose logs --tail=100
docker compose up -d
```

校验配置：

```bash
docker compose run --rm --no-deps relay haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg
docker compose run --rm --no-deps yuntu-exit check -c /etc/sing-box/config.json
```

## 与 AaITR 的关系

- AaITR s-ui 是唯一用户管理源。
- YunTu exit 配置由 AaITR 的 `sync_yuntu_exit.py` 生成并同步。
- YunTu 上不保存面板密码和用户管理数据库。
- 生产新增用户后通常不需要手动改 YunTu；等待 1 分钟同步即可。
