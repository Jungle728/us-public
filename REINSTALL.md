# 远程机器重装清单

本文件只描述公开模板的恢复顺序，不保存任何生产凭据。重装前必须在机器之外保留
加密备份，并确认备份可以解密读取。

## 需要从远程机器单独保留的内容

- s-ui SQLite 数据库、管理员密码文件和备份目录；
- Reality 私钥、公钥、short ID，以及四类协议的用户 UUID/密码；
- ACME 证书和私钥、DNS 记录、订阅域名与订阅 token；
- 线路机的 SSH 密钥、转发目标、监听端口和防火墙规则；
- 当前 s-ui 入站标签、用户分组和订阅模板。

以上内容不能放进公开 GitHub 仓库。建议使用 `age` 或密码管理器加密，权限保持为
`0600`/`0700`。

## 恢复顺序

1. 安装 Docker、Docker Compose、sing-box 检查工具和基础防火墙规则。
2. 从 GitHub 克隆本仓库到面板机和线路机。
3. 在面板机恢复证书和 s-ui 运行数据，先限制为本机监听。
4. 启动 `aaitr-s-ui`，确认 Reality、Hysteria2、TUIC、AnyTLS 四类入站均存在。
5. 运行 `python3 ./verify_s_ui.py all`，确认四类订阅均可生成且不打印凭据。
6. 在线路机修改 `yuntu-line/haproxy.cfg` 与 Compose 中的目标地址，运行 Compose
   和 HAProxy 校验，再启动 TCP/UDP 转发。
7. 逐协议做实际代理请求，确认出口 IP、UDP、TLS 和流量统计后再切换 DNS。

## 已知限制

公开仓库只提供模板和脚本，不含 TUIC/AnyTLS 用户数据。若加密备份不可用，必须在
重装后的 s-ui 中重新创建用户和协议凭据；不要把运行中生成的 `config.json` 直接
上传到 GitHub。
