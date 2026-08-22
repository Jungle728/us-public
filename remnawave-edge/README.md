# Remnawave Edge

该目录是 Verizon 上独立于旧 s-ui 的公网入口，生产路径为
`/root/code/us-public/remnawave-edge`。它只服务 Remnawave、Remnawave Node、
ACME 续期、TLS Vision 普通 HTTPS 回落和公共 Shadowrocket 规则。

## 端口与路由

- `80/TCP`：ACME HTTP-01 和 HTTPS 跳转。
- `443/TCP`：面板/订阅域名进入本机 `11443`，节点域名进入 Xray
  `30443` TLS Vision。
- `127.0.0.1:11443`：终止面板与订阅 HTTPS；面板反代 Remnawave `3000`，订阅根路径按短 UUID 反代 Mihomo YAML。
- `127.0.0.1:18080`：TLS Vision 解密后的普通 HTTPS 回落站。
- 未识别 SNI 直接拒绝，不再回落旧 s-ui Reality。

旧 `/app/`、`/modern/`、`/sub/`、`/json/` 和 `/clash/` 路径返回 `410`。
唯一的用户订阅入口是
`https://sub-verizon.bigpandas.top/<short-uuid>`。该地址直接代理
`/api/sub/<short-uuid>/mihomo`，响应体就是原始 YAML，不经过 Subscription Page，
也不需要追加 `/clash` 或 `.yaml` 后缀。

短 UUID 仍是用户订阅凭据；面板中修改节点、协议权限或模板后，客户端刷新这一
地址即可获得最新配置。

## 运行数据

以下目录仅存在于服务器并由 `.gitignore` 排除：

```text
letsencrypt/  certbot-www/  certbot-lib/  certbot-logs/
```

证书 lineage 固定为 `remnawave-domains`。Remnawave Node 只读挂载同一份
`letsencrypt/`，Hysteria2 和入口 Nginx 共用自动续期证书。

`sync_cstonecloud_cert.py` 每 6 小时由 systemd timer 检查一次证书。只有证书
内容变化且证书、私钥匹配时，才更新 CStoneCloud 的独立证书目录并重启其
Remnawave Node；该流程不读取旧 s-ui 数据库。

## 验证

```bash
cd /root/code/us-public/remnawave-edge
docker compose config -q
docker compose run --rm --no-deps nginx nginx -t
docker compose ps
docker compose logs --tail=100 nginx certbot
```
