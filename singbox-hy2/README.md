# Standalone sing-box Hysteria2

> 该实现已停用，仅保留作回滚参考。生产 `34443/udp` 现由
> `remnawave-singbox-hy2/production` 的 Remnawave 管理 Node 承载；同步 timer
> 应保持 disabled，避免重启本目录容器并争抢端口。

该目录在 AaITR 上提供独立于 Remnawave Xray 的 sing-box Hysteria2 数据面。
Remnawave 仍是唯一用户管理源：`export_remnawave_hy2.py` 只导出状态为
`ACTIVE` 的用户，并使用与现有 Remnawave Hysteria2 订阅一致的 `vlessUuid`
作为认证密码。生成的 `config.json` 含凭据，只存在生产服务器且被 Git 忽略。

测试阶段仅监听 AaITR `34443/udp`，由 CStoneCloud `444/udp` 转发；现有 Xray
Hysteria2 和正式订阅端口不受影响。服务固定使用 sing-box `1.13.15`，上下行
参数均为 `100 Mbps`，以复现旧 s-ui/sing-box 的配置。

Mihomo 订阅中的测试节点名为 `csc-aaitr-hy2-singbox-test`，只加入
`CSC-AAITR` 手动选择组，并由 AUTO 的精确过滤规则排除。确认客户端 A/B 结果前
不要将其提升为正式 `csc-aaitr-hy2`。

部署和检查：

```bash
python3 ./export_remnawave_hy2.py
chmod 600 ./config.json
docker compose config
docker compose run --rm --no-deps hy2 check -c /etc/sing-box/config.json
docker compose up -d
docker compose ps
```

将同步单元安装到 `/etc/systemd/system/` 后启用定时同步：

```bash
systemctl daemon-reload
systemctl enable --now remnawave-hy2-sync.timer
systemctl list-timers remnawave-hy2-sync.timer
```

导出采用临时文件与原子替换；API 失败、空用户列表或字段异常时不会覆盖当前
可用配置。只有用户配置实际变化且容器已经运行时，`--restart` 才会重建该测试
容器，使原子替换后的只读配置挂载立即生效。
