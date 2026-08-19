# AaITR modern console

这是 s-ui 的轻量静态管理前端。它不运行 Node 服务、不创建数据库，也不替换 s-ui API；生产构建后的 `dist/` 由现有 Docker edge Nginx 以 `/modern/` 提供。

日常功能：

- s-ui 原生会话登录、资源与核心状态总览。
- 用户搜索、筛选、新建、编辑、启停、删除与订阅复制。
- Reality、Hysteria2、AnyTLS、Shadowsocks 2022、SOCKS5、HTTP、HTTPS 入口状态。
- 日志查看、核心重启、数据库备份和 sing-box 配置导出。
- 高风险入站、TLS、路由和数据库操作继续使用 `/app/` 原面板。

生产运行时没有新增容器或 Node 进程。静态文件只读挂载到现有 `s-ui-edge-nginx`，因此额外常驻内存可以忽略。

## 构建

```bash
npm ci
npm run build
```

本地视觉调试使用内置的非生产演示数据：

```bash
npm run dev -- --host 127.0.0.1
# 打开 http://127.0.0.1:5173/modern/?demo=1
```

`demo` 仅在 Vite 开发模式生效，生产构建始终调用同源 `/app/api/*`。

## 部署

AaITR 目录布局：

```text
/root/code/us-public/s-ui/modern-ui/dist
/root/code/us-public/s-ui-edge
```

edge Compose 把前者只读挂载到 Nginx。更新构建产物后运行：

```bash
cd /root/code/us-public/s-ui-edge
docker compose config -q
docker compose up -d nginx
docker compose exec -T nginx nginx -t
```

访问路径：

- 新面板：`https://panel.bigpandas.top/` 或 `/modern/`
- 原面板高级配置：`https://panel.bigpandas.top/app/`

登录请求使用同源的 `/app/api/login`，数据读取复用 s-ui 的 `/app/api/{object}` 接口。当前首版把高风险的协议、TLS 和数据库写操作保留在原 s-ui 页面，点击“高级编辑”即可回到 `/app/`。
