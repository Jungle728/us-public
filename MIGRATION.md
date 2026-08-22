# 迁移汇总

当前 AaITR 机器是 Remnawave 管理源和迁移汇总点。GitHub 仓库只保存公开模板、脚本、前端构建产物和部署说明；生产数据库、面板密码、订阅凭据和证书私钥只保存在 AaITR 的受限迁移目录中。旧 s-ui 已退出生产链路，仅保留受限归档用于回滚审计。

## AaITR 上的目录

| 目录 | 内容 | 是否进入 GitHub |
|---|---|---|
| `/root/code/us-public/s-ui` | 已停用 s-ui 归档 | 代码与模板保留，运行数据排除 |
| `/root/code/us-public/remnawave-edge` | 独立 Nginx/Certbot 入口、回落站与公共规则 | 配置模板进入，证书目录排除 |
| `/root/code/us-public/remnawave` | Remnawave Panel、PostgreSQL 与 Valkey | Compose 模板进入，`.env`、响应文件和数据库卷排除 |
| `/root/code/us-public/remnawave-node` | AaITR Remnawave Node | Dockerfile 与 Compose 模板进入，Node 密钥排除 |
| `/root/code/us-public/yuntu-line` | CStoneCloud 线路机公开编排模板（兼容目录名） | 进入 |
| `/root/code/us-public/migration/` | 当前 AaITR、CStoneCloud 的受限迁移归档 | 不进入 |

## 当前链路

```text
client -> CStoneCloud -> AaITR -> internet
client -> CStoneCloud -> internet
client -> AaITR -> internet
```

当前生产目标为：

- AaITR：`47.178.15.216`，节点域名 `verizon.bigpandas.top`
- CStoneCloud：`70.39.179.159`，节点域名 `cstonecloud.bigpandas.top`
- 面板：`panel-verizon.bigpandas.top`
- 订阅：`sub-verizon.bigpandas.top`
- AaITR 目录：`/root/code/us-public`
- CStoneCloud 目录：`/root/code/aaitr`

Remnawave 订阅为每条链路提供 VLESS Reality、Hysteria2 和 VLESS TLS Vision。Reality 与 TLS Vision 只使用自有域名；普通 HTTPS 回落到各机器本地 Nginx。SOCKS5 是 AaITR Remnawave Node 内 Xray 提供的独立服务器转发代理，不进入桌面节点订阅。

## 更换机器时

1. 保存 AaITR 和 CStoneCloud 的迁移归档，不要把归档提交到 GitHub。
2. 在新机器安装 Docker、Docker Compose、systemd 和 SSH 密钥。
3. 从 GitHub 部署公开模板，再恢复对应机器的运行归档。
4. 更新模板中的线路机和落地机地址、DNS、证书和防火墙端口。
5. 先运行配置检查，再启动服务；最后运行 Remnawave 订阅的九节点 Mihomo 出口检查、Xray SOCKS5 检查和 CStoneCloud 的 Compose 校验。
6. DNS 切换完成并确认新订阅三种协议和三个出口均正常后，再释放旧机器。

## 运行归档保护

迁移归档包含 s-ui SQLite 数据库、`.admin-password`、ACME 证书、Reality 私钥、用户认证信息和 CStoneCloud 生成配置。目录权限应保持为 `0700`，归档文件保持为 `0600`；如果需要异地保存，应先加密后传输。
