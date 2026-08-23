# AaITR s-ui + sing-box 旧方案

这个仓库保存远程机器重装所需的公开模板和运维文档。目标方案是：

- `s-ui` 作为用户、入站和订阅管理面板；
- sing-box 提供 Reality、Hysteria2、TUIC、AnyTLS 数据面；
- 线路机只做 TCP/UDP 四层转发，不保存用户数据库。

Remnawave 相关目录属于本地历史归档，已从公开提交排除。仓库不包含数据库、面板
密码、用户 UUID、Reality 私钥、TUIC/HY2/AnyTLS 密码、证书私钥、订阅 token 或生成
后的运行配置。重装前请先阅读 [REINSTALL.md](REINSTALL.md)。

## 目录

```text
aaitr-s-ui/   s-ui Compose、订阅模板、验证/同步脚本和静态管理面板
yuntu-line/   线路机 HAProxy/GOST 编排（目录名为旧部署兼容标识）
decoy/        TLS 回落站
```

`aaitr-s-ui/README.md` 是面板机入口，`yuntu-line/README.md` 是线路机入口。模板中
的域名、IP 和端口只是当前部署的示例，换机后必须按实际环境修改。

## 恢复后的链路

```text
客户端 -> 线路机 -> AaITR s-ui/sing-box -> 目标网站
客户端 -> AaITR s-ui/sing-box -> 目标网站
```

每个出口可由 s-ui 生成四类协议节点：VLESS Reality（TCP）、Hysteria2（UDP）、
TUIC（UDP）和 AnyTLS（TCP/TLS）。线路机不解密协议，只转发到面板机对应端口。

## 配置校验

面板机：

```bash
cd /root/code/us-public/aaitr-s-ui
docker compose config -q
python3 ./verify_s_ui.py all
```

线路机：

```bash
cd /root/code/aaitr
docker compose config -q
docker compose run --rm --no-deps relay haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg
```

四类协议必须在恢复 s-ui 数据后做实际代理请求验证；不能仅凭 Compose 校验判断
密码、证书、Reality 参数或 UDP 转发正确。

## 公开仓库安全边界

禁止提交：`.env`、`.admin-password`、`db/`、`backups/`、`*.key`、`*.pem`、
`*.crt`、订阅链接、UUID、密码、Reality 私钥、证书目录和任何 `config.json`。
提交前检查：

```bash
git status --short
git diff --cached --name-only
```
