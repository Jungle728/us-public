# Repository Guidelines

## 项目结构与模块组织

本仓库保存 AaITR 与 CStoneCloud 代理基础设施的公开模板、配置和运维脚本，不应包含生产数据库、证书私钥或订阅凭据。根目录的 `docker-compose.yml`、`haproxy.cfg` 是线路机组合模板；`aaitr-s-ui/` 是 AaITR s-ui 管理源，包含 Python 运维脚本、Clash 模板、systemd 定时同步单元和 `edge/` Nginx 入口配置；`yuntu-line/` 是为兼容既有部署而保留目录名的 CStoneCloud 线路机模板。说明文档放在根目录及各子目录 `README.md`。

## 构建、测试与本地开发命令

- `docker compose ps`：查看当前目录 Compose 服务状态。
- `docker compose up -d`：按当前目录的 `docker-compose.yml` 启动或更新服务。
- `docker compose logs --tail=100`：查看最近日志。
- `docker compose run --rm --no-deps relay haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg`：校验 HAProxy 配置。
- `docker compose run --rm --no-deps yuntu-exit check -c /etc/sing-box/config.json`：校验 sing-box 配置。
- `cd aaitr-s-ui && python3 ./verify_s_ui.py all`：运行 s-ui 生产订阅、协议和代理验证。

在真实服务器路径中操作时，参考 README 中的 `/root/code/us-public/s-ui` 与 `/root/code/aaitr` 示例。

## 架构概览

AaITR 是用户、订阅和出口认证的管理源；CStoneCloud 只负责入口中转、UDP 转发和可选机房出口。常见链路为 `client -> CStoneCloud -> AaITR -> internet`、`client -> CStoneCloud -> internet` 和 `client -> AaITR -> internet`。新增协议、端口或节点命名时，同时检查 `README.md`、`aaitr-s-ui/clash-template.yaml`、`aaitr-s-ui/export_yuntu_exit.py` 和相关 Compose 文件，避免文档、订阅和部署模板脱节。`yuntu-*` 脚本、服务和内部 tag 是兼容标识，不是当前提供商名称。

## 编码风格与命名约定

Python 脚本使用 Python 3、4 空格缩进、`argparse` CLI、`Path` 处理路径，并保持函数职责清晰。脚本名使用小写加下划线，例如 `sync_yuntu_exit.py`、`apply_clash_template.py`。YAML 配置使用 2 空格缩进；服务名、容器名和分组名应延续现有命名，如 `yuntu-exit`、`YUNTU-AAITR-AUTO`。修改配置时优先保持端口、链路和注释与 README 同步。

## 测试与验证指南

本仓库没有独立单元测试框架，验证以配置检查和线上只读脚本为主。提交前至少运行受影响目录的 Compose 配置校验；改动 `aaitr-s-ui/` 订阅、节点或同步逻辑时运行 `python3 ./verify_s_ui.py all`。验证脚本不得输出完整订阅链接、UUID、密码或节点 URI。

## 提交与 Pull Request 规范

当前工作副本没有可读取的 Git 历史，因此提交信息使用清晰的祈使句或简短中文摘要，例如 `Update YunTu HAProxy routing` 或 `修正 Clash 模板分流规则`。PR 应说明变更目的、影响的机器或目录、已运行的验证命令，并在涉及网络暴露、证书、端口或订阅格式时标注风险与回滚方式。

## 安全与配置注意事项

不要提交 `.env`、`*.key`、`*.pem`、`.admin-password`、`db/`、`letsencrypt/`、`yuntu-exit/config.json`、`backups/` 或日志文件。提交前运行 `git status --short` 和 `git diff --cached --name-only`，确认 `.gitignore` 覆盖了所有运行时数据。

## Agent 专用说明

自动化代理修改文件前先阅读相邻 README 和现有脚本入口，不要重写生产配置生成逻辑。涉及真实服务的命令应优先使用 `check`、`ps`、`logs --tail=100` 等只读或校验操作；需要重启服务时，在 PR 或交付说明中写明影响范围。
