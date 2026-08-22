# Remnawave Edge

该目录是 Verizon 上独立于旧 s-ui 的公网入口，生产路径为
`/root/code/us-public/remnawave-edge`。它只服务 Remnawave、Remnawave Node、
ACME 续期、TLS Vision 普通 HTTPS 回落和公共 Shadowrocket 规则。

## 端口与路由

- `80/TCP`：ACME HTTP-01 和 HTTPS 跳转。
- `443/TCP`：面板/订阅域名进入本机 `11443`，节点域名进入 Xray
  `30443` TLS Vision。
- `127.0.0.1:11443`：终止面板与订阅 HTTPS；面板反代 Remnawave `3000`，订阅反代官方页面 `3010`。
- `127.0.0.1:18080`：TLS Vision 解密后的普通 HTTPS 回落站。
- 未识别 SNI 直接拒绝，不再回落旧 s-ui Reality。

旧 `/app/`、`/modern/`、`/sub/`、`/json/` 和 `/clash/` 路径返回 `410`。
正式用户入口由 Remnawave 官方 Subscription Page 的 `/<short-uuid>` 提供。
旧 `/api/sub/<short-uuid>` 仍代理到 Remnawave 后端，避免已添加的客户端失效。
用户订阅链接若被手机客户端自动追加 `/clash`，入口会将其改写到 `/mihomo`，
因为当前 Remnawave 的显式 CLASH 渲染器无法展开受管节点，而 Mihomo 渲染器可以。
同时提供 s-ui 风格兼容地址 `https://sub-verizon.bigpandas.top/clash/<short-uuid>`，
该地址也会返回 Mihomo YAML。为兼容要求文件扩展名的移动客户端，还提供
`https://sub-verizon.bigpandas.top/clash/<short-uuid>.yaml` 和 `.yml` 两种形式；
它们仍按短 UUID 动态生成对应用户配置，不是共享静态凭据文件。

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
