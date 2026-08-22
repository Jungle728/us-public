# Remnawave dual-core Hysteria2 adapter

该目录为 `Cd1s/remnawave-singbox` 双 Core 分支增加受 Remnawave 管理的
sing-box Hysteria2 入站。它不会直接替换当前生产 Remnawave/Xray 服务；首先应在
独立数据库、独立 Node 管理端口和独立 UDP 端口完成全栈验证。

## 身份和流量模型

- sing-box Hysteria2 的 `name` 使用 Remnawave 数字用户 ID，作为稳定统计键。
- `password` 继续使用用户的 `vlessUuid`，与现有 Remnawave HY2 订阅兼容。
- Node 通过 sing-box V2Ray Stats API 读取
  `user>>><id>>>traffic>>>{uplink,downlink}`，再沿原 Remnawave Node 统计接口上报。
- 动态增删用户会在重载前抓取并清零 Core 计数，由 Node 内存累计器保留，避免正常
  配置重载期间漏计或重复计数。
- 待上报累计值使用原子 JSON 快照写入 `SINGBOX_STATS_STATE_PATH`；部署时必须把其
  所在目录挂到持久卷，使 Node 进程或容器重启后仍能恢复待上报流量。

## 固定上游

| 组件 | 仓库 | 固定提交 |
|---|---|---|
| Backend | `Cd1s/remnawave-backend:singbox` | `257ba1c2bcc36fee1a117a148e1b6d0b09613ffb` |
| Node | `Cd1s/remnawave-node:singbox` | `079be99ab2f19744d0ca1336702b456d590fb786` |
| Frontend | `Cd1s/remnawave-frontend:singbox` | `4bdde8a18cd2bc93630ba70191232ef3e8ca2d34` |

Backend、Node 和 Frontend 补丁分别位于 `patches/`。Frontend 补丁为配置编辑器
增加 HY2 schema 和 TLS 校验；准备源码、运行编译检查并构建本地镜像：

```bash
python3 ./prepare_hy2_fork.py --workdir /root/build/remnawave-singbox-hy2 --build
```

默认构建：

- `local/remnawave-backend:3.3.2-singbox-hy2`
- `local/remnawave-node:3.3.2-singbox-hy2`
- sing-box `1.13.15`
- Xray `26.6.27`，保持当前 Mihomo Reality 兼容基线

脚本会拒绝在非空源码目录上覆盖文件，并在构建前运行补丁检查、Backend/Node
编译、类型检查和 HY2 回归验证。

## 隔离实验栈

`isolated/` 使用独立 PostgreSQL、Valkey、Panel、Node 管理端口、UDP 端口和两个
sing-box 客户端。运行时凭据与测试用户状态仅写入被忽略且权限为 `0600` 的文件。

```bash
cd isolated
python3 ./bootstrap_lab.py init
docker compose up -d hy2-db hy2-valkey hy2-panel
python3 ./bootstrap_lab.py wait
python3 ./bootstrap_lab.py provision
docker compose --profile node --profile client up -d hy2-node hy2-client-a hy2-client-b
python3 ./validate_accounting.py
python3 ./validate_container_restart.py
```

验证脚本会检查双用户独立计数、正常核心重载保留、动态禁用/启用和按 Remnawave
用量限额自动停用，以及带有待上报累计值时的 Node 容器重启恢复。容器重启脚本会在
快照落盘后短暂暂停隔离 Panel，消除 15 秒采集任务与故障注入之间的竞态。测试 Panel
只监听 `127.0.0.1:3300/3301`；Node 管理端口仅存在于实验 Docker 网络，对外只发布
`35443/UDP`。

## 隔离验证门槛

正式切换前必须在全新数据库中证明：

1. Xray 配置仍默认使用 Xray，双 Core 变更不会隐式迁移现有 Profile。
2. HY2 Profile 启动后，初始用户使用数字 ID 写入 sing-box 配置。
3. 新增、禁用和重新启用用户分别触发 `1 → 2 → 1 → 2` 的动态同步。
4. 两个测试用户分别传输已知大小数据，面板按正确用户累计非零且单调递增流量。
5. Node 重载和容器重启前后的累计值不减少、不重复；持久累计文件可恢复正常重载前
   已抓取的 Core 计数。突然断电时仍可能丢失“上次 15 秒采集以后、落盘以前”的
   sing-box 内存窗口，必须在压测中量化，不能用零流量测试代替。
6. 用户达到限额或被禁用后不能继续建立新的 HY2 会话。
7. SINGBOX、Mihomo 和分享链接中的地址、端口、SNI、密码一致，并完成真实出口验证。

验证通过后仍应新建 sing-box Profile 和 Canary Node；不要原地把现有
`Verizon-Production` Xray Profile 改成 sing-box。

## 生产 Canary

`production/` 提供独立 Docker network namespace 的 Node，管理端口为 `2323`，HY2 数据端口为
`34443/UDP`。它复用现有 `csc-aaitr-hy2-singbox-test` 的公网 `444/UDP` 路径，
不会占用正式 `443/UDP` 与 `32443/UDP`。生产 Panel 切换到本目录构建的同版本
Backend 镜像并完成数据库备份后，按以下顺序操作：

新 Node 使用独立的 Docker network namespace，并通过现有私有
`remnawave-network` 中的 `remnanode-singbox-hy2:2323` 供 Panel 连接。管理端口
不发布到宿主机或公网，只有 `34443/UDP` 数据端口映射到宿主机；这也避免与现有
host-network Xray Node 共享同一 namespace。

```bash
cd production
python3 ./manage_canary.py provision
docker compose config --quiet
docker compose up -d
python3 ./manage_canary.py status
python3 ./manage_canary.py activate
python3 ./validate_canary.py --username <验证用户名>
# promote 后再分别验证两个正式入口：
python3 ./validate_canary.py --username <验证用户名> --tag aaitr-hy2
python3 ./validate_canary.py --username <验证用户名> --tag csc-aaitr-hy2
python3 ./manage_canary.py retire-canary
```

`provision` 会新建 sing-box Profile 和 Node，并把新入站加入现有
`Production-All` squad；不会修改 Reality/TLS Profile。`activate` 只切换测试
Host；`promote` 才会把正式的 `aaitr-hy2` 与 `csc-aaitr-hy2` Host 改到新入站。
正式公网 UDP 转发必须在 `promote` 前单独从旧 `33443` 切到 `34443`。
`validate_canary.py` 不输出订阅、密码或节点 URI；临时客户端配置以 `0600` 写入
被忽略的 `production/runtime/`，测试结束后立即删除。验证同时要求用户用量增长和
`lastConnectedNodeUuid` 指向新 sing-box Node，不能只以握手成功作为上线依据。
两个正式入口验证通过后运行 `retire-canary`，只禁用测试 Host 的订阅输出；
`444/UDP` 转发与 Host 对象保留，便于以后临时启用诊断。

## 回滚

隔离阶段只需停止 Canary Node 和测试面板，不影响生产服务。正式上线时保留当前
Xray Profile、Node 镜像和数据库备份；出现统计、订阅或握手异常时，把端口转发切回
现有 Xray HY2，运行 `python3 ./manage_canary.py restore`，再停止 sing-box Canary；
不要删除原 Profile。

## 生产状态

生产共运行两个 Xray Node 和两个 sing-box Node。`aaitr-hy2` 与
`csc-aaitr-hy2` 使用 AaITR sing-box Node，公开端口 `32443/udp` 与 `443/udp`
转发至 AaITR `34443/udp`；`csc-hy2` 使用 `cstonecloud/` 部署的 CStoneCloud
sing-box Node，`2443/udp` 转发至本机 `34444/udp`。旧 Xray `33443/udp`、
`33444/udp` 及 CStoneCloud `33445/udp` 保留，standalone 同步 timer 停用。
Remnawave 当前每 15 秒采集一次统计，因此正常运行、重载和容器重启不会丢失已抓取
的累计值；突然断电仍存在最多一个采集周期的 sing-box 内存窗口。

生产验收使用 `production/validate_canary.py` 对三条 HY2 路径执行真实流量与 Node
归属检查，并使用 `production/validate_xray_paths.py` 对 Reality/TLS 的直连和
链式路径执行同样检查。
