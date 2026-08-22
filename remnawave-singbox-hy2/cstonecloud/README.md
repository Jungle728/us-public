# CStoneCloud managed sing-box Hysteria2

该目录在 CStoneCloud 上部署第二个 Remnawave Node，专门运行 sing-box HY2。
现有 host-network Xray Node 继续承载 Reality/TLS；两个 Node 使用不同 network
namespace，不能把新 Node 改成 host network。

## 端口与安全边界

- `34444/UDP`：sing-box HY2 数据入站，只映射到宿主机 `127.0.0.1`，由现有
  GOST `2443/UDP` 转发。
- `2324/TCP`：Node API 的 Docker 回环映射，不对公网开放。
- `2323/TCP`：GOST host-network 管理转发，只允许 AaITR `47.178.15.216` 通过
  UFW 访问。
- TLS 证书只读复用 `/root/code/aaitr/remnawave-node/cert`。
- 统计待上报值持久化到 `runtime/node-state/singbox-stats.json`。

部署目录为 `/root/code/aaitr/remnawave-singbox-hy2-cstonecloud`。`node.env` 由
AaITR 上的 `manage_cstonecloud.py provision` 生成，权限必须是 `0600`，不得提交。

```bash
docker compose -f compose.yml config --quiet
docker compose -f compose.yml up -d
docker compose -f compose.yml ps
```

面板侧操作与验证：

```bash
cd /root/code/us-public/remnawave-singbox-hy2/cstonecloud
python3 ./manage_cstonecloud.py provision
python3 ./manage_cstonecloud.py status
python3 ./manage_cstonecloud.py activate

cd ../production
python3 ./validate_canary.py --username <验证用户名> --tag csc-hy2
```

## 回滚

1. 把 CStoneCloud `remnawave-relay` 的 `2443/UDP` 目标从 `127.0.0.1:34444`
   改回旧 Xray `127.0.0.1:33444` 并只重建 `hy2-compat-relay`。
2. 在 AaITR 运行 `manage_cstonecloud.py restore` 恢复 `csc-hy2` Host 映射。
3. 停止本目录两个容器。Profile、Node、状态卷和旧 Xray 入站均保留，不要删除。
