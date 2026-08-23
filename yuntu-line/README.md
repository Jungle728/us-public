# YunTu 线路机

该目录保留旧目录名兼容既有部署。线路机只承担 Reality/TUIC/AnyTLS 的 TCP 转发和
Hysteria2/TUIC 的 UDP 转发；用户、订阅和协议配置由 AaITR 上的 s-ui 管理。

当前 YunTu 主机为 `154.23.242.22`（`yuntu.bigpandas.top`），中转目标 Verizon
为 `47.178.15.216`（`verizon.bigpandas.top`）。

## 职责

```text
客户端 -> YunTu -> Verizon -> 目标网站
客户端 -> YunTu -> 目标网站
```

公开监听：

| 端口 | 协议 | 用途 |
|---|---|---|
| TCP 443 | HAProxy TCP/SNI | `csc-tls` 本机 TLS Vision，`csc-aaitr-tls` 中转到 Verizon |
| TCP 24445 | HAProxy TCP | `csc-aaitr-reality` 中转到 Verizon `24443` |
| TCP 24444 | s-ui/sing-box Reality | `csc-reality` 本机出口 |
| UDP 443 | GOST UDP | `csc-aaitr-hy2` 中转到 Verizon `34443` |
| UDP 2443 | GOST UDP | `csc-hy2` 临时转到本机 Xray HY2 `33444`；限速解除后迁移到受管 sing-box `34444` |
| UDP 444 | GOST UDP | 诊断入口，默认不进入订阅 |

## 文件

```text
docker-compose.yml  兼容目录中的 HAProxy 服务编排
haproxy.cfg         TCP 中转到 Verizon 的 HAProxy 配置
```

运行时生成且不提交：

```text
backups/                  手工备份
```

## 运维

```bash
cd /root/code/aaitr
docker compose config -q
docker compose ps
docker compose logs --tail=100
```

校验配置：

```bash
docker compose run --rm --no-deps relay haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg
```

## 与 Verizon 的关系

- s-ui 是唯一用户管理源。
- 线路机不保存用户数据库和协议密码。
- YunTu 上不保存面板密码和用户管理数据库。
- 生产新增用户后由 s-ui 生成订阅；线路机只转发到面板机。
