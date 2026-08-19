# 迁移汇总

当前 AaITR 机器是管理源和迁移汇总点。GitHub 仓库只保存公开模板、脚本、前端构建产物和部署说明；生产数据库、面板密码、订阅凭据、证书私钥和生成的 YunTu 配置只保存在 AaITR 的受限迁移目录中。

## AaITR 上的目录

| 目录 | 内容 | 是否进入 GitHub |
|---|---|---|
| `/root/code/us-public/s-ui` | s-ui 管理源、四种桌面协议、订阅与同步脚本 | 代码与模板进入，运行数据排除 |
| `/root/code/us-public/s-ui-edge` | Nginx/Certbot 边缘入口 | 配置模板进入，证书目录排除 |
| `/root/code/us-public/yuntu-line` | YunTu 线路机公开编排模板 | 进入 |
| `/root/code/us-public/migration/` | 当前 AaITR、YunTu 的受限迁移归档 | 不进入 |

## 当前链路

```text
client -> YunTu -> AaITR -> internet
client -> YunTu -> internet
client -> AaITR -> internet
```

每条链路提供 VLESS Reality、Hysteria2、AnyTLS 和 Shadowsocks 2022。SOCKS5、HTTP、HTTPS 是独立的服务器转发代理，不进入桌面节点订阅。

## 更换机器时

1. 保存 AaITR 和 YunTu 的迁移归档，不要把归档提交到 GitHub。
2. 在新机器安装 Docker、Docker Compose、systemd 和 SSH 密钥。
3. 从 GitHub 部署公开模板，再恢复对应机器的运行归档。
4. 更新模板中的线路机和落地机地址、DNS、证书和防火墙端口。
5. 先运行配置检查，再启动服务；最后运行 `python3 ./verify_s_ui.py all` 和 YunTu 的 Compose 校验。
6. DNS 切换完成并确认订阅、四种协议和三个出口均正常后，再释放旧机器。

## 运行归档保护

迁移归档包含 s-ui SQLite 数据库、`.admin-password`、ACME 证书、Reality 私钥、用户认证信息和 YunTu 生成配置。目录权限应保持为 `0700`，归档文件保持为 `0600`；如果需要异地保存，应先加密后传输。
