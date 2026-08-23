import "./styles.css";
import {
  Activity,
  ArrowDownToLine,
  ArrowUpFromLine,
  Check,
  ChevronRight,
  CircleGauge,
  Copy,
  Cpu,
  DatabaseBackup,
  Download,
  ExternalLink,
  Eye,
  EyeOff,
  FileJson,
  HardDrive,
  KeyRound,
  LogOut,
  MemoryStick,
  Moon,
  Network,
  Pencil,
  Plus,
  RefreshCw,
  RotateCw,
  Route,
  Search,
  Server,
  ShieldCheck,
  Sun,
  Terminal,
  Trash2,
  Users,
  Wifi,
  WifiOff,
  X,
  createIcons,
} from "lucide";
import { api, AuthenticationRequired } from "./api";
import type { Client, ClientConfig, Inbound, PanelData, ServerStatus, ViewName } from "./types";

const root = document.querySelector<HTMLDivElement>("#app") as HTMLDivElement;
if (!root) throw new Error("Application root not found");

const iconSet = {
  Activity, ArrowDownToLine, ArrowUpFromLine, Check, ChevronRight, CircleGauge,
  Copy, Cpu, DatabaseBackup, Download, ExternalLink, Eye, EyeOff, FileJson,
  HardDrive, KeyRound, LogOut, MemoryStick, Moon, Network, Pencil, Plus,
  RefreshCw, RotateCw, Route, Search, Server, ShieldCheck, Sun, Terminal,
  Trash2, Users, Wifi, WifiOff, X,
};

const viewMeta: Record<ViewName, { label: string; title: string; icon: string }> = {
  dashboard: { label: "总览", title: "运行总览", icon: "circle-gauge" },
  clients: { label: "用户", title: "用户与订阅", icon: "users" },
  inbounds: { label: "协议", title: "入口协议", icon: "network" },
  operations: { label: "运维", title: "系统运维", icon: "terminal" },
};

let panel: PanelData | null = null;
let serverStatus: ServerStatus = {};
let activeView: ViewName = getViewFromHash();
let authenticated = false;
let busy = true;
let refreshTimer: number | undefined;

function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderIcons(): void {
  createIcons({
    icons: iconSet,
    attrs: { "aria-hidden": "true", width: 18, height: 18, "stroke-width": 1.8 },
  });
}

function getViewFromHash(): ViewName {
  const candidate = window.location.hash.replace(/^#\/?/, "") as ViewName;
  return candidate in viewMeta ? candidate : "dashboard";
}

function setTheme(theme: "light" | "dark"): void {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("aaitr-theme", theme);
}

function initializeTheme(): void {
  const stored = localStorage.getItem("aaitr-theme");
  if (stored === "light" || stored === "dark") setTheme(stored);
  else setTheme(window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}

function formatBytes(value = 0, decimals = 1): string {
  if (!Number.isFinite(value) || value <= 0) return "0 B";
  const units = ["B", "KiB", "MiB", "GiB", "TiB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / 1024 ** index).toFixed(index === 0 ? 0 : decimals)} ${units[index]}`;
}

function formatDate(timestamp = 0, withTime = false): string {
  if (!timestamp) return "不限";
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric", month: "2-digit", day: "2-digit",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  }).format(new Date(timestamp * 1000));
}

function formatDuration(seconds = 0): string {
  if (seconds < 60) return `${Math.floor(seconds)} 秒`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时`;
  return `${Math.floor(seconds / 86400)} 天`;
}

function percent(current = 0, total = 0): number {
  if (!total) return 0;
  return Math.max(0, Math.min(100, (current / total) * 100));
}

function protocolName(type: string, tag = ""): string {
  if (type === "vless" && tag.includes("reality")) return "VLESS Reality";
  if (type === "hysteria2") return "Hysteria2";
  if (type === "anytls") return "AnyTLS";
  if (type === "shadowsocks") return "Shadowsocks 2022";
  if (type === "socks") return "SOCKS5";
  if (type === "http" && tag.includes("https")) return "HTTPS";
  return type.toUpperCase();
}

function routeName(tag: string): string {
  if (tag.includes("reality") || tag.includes("hysteria") || tag.includes("anytls") || tag.includes("shadowsocks")) return "加密节点";
  if (tag.includes("socks") || tag.includes("http") || tag.includes("https")) return "转发代理";
  return "其他入口";
}

function showToast(message: string, tone: "success" | "danger" = "success"): void {
  document.querySelector(".toast")?.remove();
  const element = document.createElement("div");
  element.className = `toast toast-${tone}`;
  element.innerHTML = `<i data-lucide="${tone === "success" ? "check" : "x"}"></i><span>${escapeHtml(message)}</span>`;
  document.body.appendChild(element);
  renderIcons();
  window.setTimeout(() => element.remove(), 3600);
}

function renderLoading(): void {
  root.innerHTML = `
    <main class="boot-screen">
      <div class="brand-mark"><span>AA</span></div>
      <div class="boot-copy"><strong>AaITR Console</strong><span>正在连接管理服务</span></div>
      <div class="boot-progress"><span></span></div>
    </main>`;
}

function renderLogin(error = ""): void {
  document.title = "登录 · AaITR Console";
  root.innerHTML = `
    <main class="login-layout">
      <section class="login-brand">
        <div class="brand-lockup"><div class="brand-mark"><span>AA</span></div><span>AaITR Console</span></div>
        <div class="login-status">
          <div class="status-orbit"><i data-lucide="route"></i></div>
          <p>线路管理</p>
          <strong>CStoneCloud <span>→</span> AaITR</strong>
          <div class="login-tags"><span>Reality</span><span>Hysteria2</span></div>
        </div>
        <small>Private operations surface</small>
      </section>
      <section class="login-panel">
        <form id="login-form" class="login-form" autocomplete="on">
          <div class="mobile-brand"><div class="brand-mark"><span>AA</span></div><span>AaITR Console</span></div>
          <div class="form-heading"><span>管理后台</span><h1>欢迎回来</h1></div>
          ${error ? `<div class="form-error">${escapeHtml(error)}</div>` : ""}
          <label class="field"><span>用户名</span><input name="user" autocomplete="username" required autofocus /></label>
          <label class="field password-field"><span>密码</span><input name="pass" type="password" autocomplete="current-password" required /><button type="button" class="icon-btn password-toggle" title="显示密码"><i data-lucide="eye"></i></button></label>
          <button class="primary-btn login-submit" type="submit"><span>登录</span><i data-lucide="chevron-right"></i></button>
        </form>
      </section>
    </main>`;
  renderIcons();

  const form = document.querySelector<HTMLFormElement>("#login-form");
  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector<HTMLButtonElement>("button[type=submit]");
    const data = new FormData(form);
    submit?.setAttribute("disabled", "true");
    if (submit) submit.innerHTML = `<span>正在登录</span><i class="spin" data-lucide="refresh-cw"></i>`;
    renderIcons();
    try {
      await api.login(String(data.get("user") || ""), String(data.get("pass") || ""));
      authenticated = true;
      await reloadAll();
      startRefresh();
    } catch (requestError) {
      renderLogin(requestError instanceof Error ? requestError.message : "登录失败");
    }
  });

  document.querySelector<HTMLButtonElement>(".password-toggle")?.addEventListener("click", (event) => {
    const button = event.currentTarget as HTMLButtonElement;
    const input = document.querySelector<HTMLInputElement>('input[name="pass"]');
    if (!input) return;
    const visible = input.type === "text";
    input.type = visible ? "password" : "text";
    button.innerHTML = `<i data-lucide="${visible ? "eye" : "eye-off"}"></i>`;
    button.title = visible ? "显示密码" : "隐藏密码";
    renderIcons();
  });
}

function navigationItem(view: ViewName): string {
  const meta = viewMeta[view];
  return `<a href="#/${view}" class="nav-item ${activeView === view ? "active" : ""}" data-route="${view}"><i data-lucide="${meta.icon}"></i><span>${meta.label}</span></a>`;
}

function renderShell(): void {
  if (!panel) return;
  const theme = document.documentElement.dataset.theme || "light";
  const coreRunning = Boolean(serverStatus.sbd?.running);
  document.title = `${viewMeta[activeView].title} · AaITR Console`;
  root.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar">
        <div class="brand-lockup"><div class="brand-mark"><span>AA</span></div><span>AaITR Console</span></div>
        <nav>${navigationItem("dashboard")}${navigationItem("clients")}${navigationItem("inbounds")}${navigationItem("operations")}</nav>
        <div class="sidebar-foot">
          <div class="core-chip"><span class="status-dot ${coreRunning ? "online" : "offline"}"></span><div><strong>${coreRunning ? "Core online" : "Core offline"}</strong><small>sing-box ${escapeHtml(serverStatus.sys?.appVersion || "")}</small></div></div>
          <a href="/app/" class="legacy-link"><i data-lucide="external-link"></i><span>高级配置</span></a>
        </div>
      </aside>
      <div class="workspace">
        <header class="topbar">
          <div><span class="eyebrow">AaITR / ${viewMeta[activeView].label}</span><h1>${viewMeta[activeView].title}</h1></div>
          <div class="topbar-actions">
            <button class="icon-btn" id="refresh-button" title="刷新"><i data-lucide="refresh-cw"></i></button>
            <button class="icon-btn" id="theme-button" title="切换外观"><i data-lucide="${theme === "dark" ? "sun" : "moon"}"></i></button>
            <button class="icon-btn" id="logout-button" title="退出登录"><i data-lucide="log-out"></i></button>
          </div>
        </header>
        <main class="content">${renderActiveView()}</main>
        <nav class="mobile-nav">${navigationItem("dashboard")}${navigationItem("clients")}${navigationItem("inbounds")}${navigationItem("operations")}</nav>
      </div>
    </div>`;
  renderIcons();
  attachShellEvents();
}

function renderActiveView(): string {
  switch (activeView) {
    case "clients": return renderClients();
    case "inbounds": return renderInbounds();
    case "operations": return renderOperations();
    default: return renderDashboard();
  }
}

function metricCard(icon: string, label: string, value: string, detail: string, usage?: number): string {
  return `<article class="metric-card"><div class="metric-head"><span class="metric-icon"><i data-lucide="${icon}"></i></span><span>${label}</span></div><strong>${value}</strong><small>${detail}</small>${usage === undefined ? "" : `<div class="meter"><span style="width:${usage.toFixed(1)}%"></span></div>`}</article>`;
}

function renderDashboard(): string {
  if (!panel) return "";
  const clients = panel.clients || [];
  const online = panel.onlines?.user?.length || 0;
  const traffic = clients.reduce((sum, client) => sum + client.up + client.down, 0);
  const enabled = clients.filter((client) => client.enable).length;
  const recent = [...clients].sort((a, b) => (b.onlineAt || 0) - (a.onlineAt || 0)).slice(0, 5);
  const uptime = serverStatus.sbd?.stats?.Uptime || 0;
  return `
    <section class="metrics-grid">
      ${metricCard("activity", "核心状态", serverStatus.sbd?.running ? "运行中" : "已停止", `连续运行 ${formatDuration(uptime)}`)}
      ${metricCard("users", "在线用户", `${online}`, `${enabled} 个启用账户`)}
      ${metricCard("memory-stick", "内存", `${percent(serverStatus.mem?.current, serverStatus.mem?.total).toFixed(0)}%`, `${formatBytes(serverStatus.mem?.current)} / ${formatBytes(serverStatus.mem?.total)}`, percent(serverStatus.mem?.current, serverStatus.mem?.total))}
      ${metricCard("arrow-down-to-line", "累计流量", formatBytes(traffic), `上传 ${formatBytes(clients.reduce((sum, client) => sum + client.up, 0))}`)}
    </section>
    <section class="dashboard-grid">
      <article class="panel route-panel">
        <div class="section-head"><div><span class="eyebrow">Traffic routes</span><h2>三种出口模式</h2></div><span class="quiet-badge">${panel.inbounds.filter((item) => ["vless", "hysteria2"].includes(item.type)).length} 个协议入口</span></div>
        <div class="route-list">
          ${routeRow("CS", "CStoneCloud → AaITR", "家宽出口", "默认", "route-blue")}
          ${routeRow("CSE", "CStoneCloud Exit", "机房出口", "备用", "route-amber")}
          ${routeRow("AA", "AaITR Exit", "家宽直连", "对照", "route-green")}
        </div>
      </article>
      <article class="panel system-panel">
        <div class="section-head"><div><span class="eyebrow">Server</span><h2>资源状态</h2></div><span class="status-pill ${serverStatus.sbd?.running ? "ok" : "error"}">${serverStatus.sbd?.running ? "健康" : "异常"}</span></div>
        ${resourceRow("CPU", serverStatus.cpu || 0, `${(serverStatus.cpu || 0).toFixed(1)}%`)}
        ${resourceRow("内存", percent(serverStatus.mem?.current, serverStatus.mem?.total), formatBytes(serverStatus.mem?.current))}
        ${resourceRow("磁盘", percent(serverStatus.dsk?.current, serverStatus.dsk?.total), formatBytes(serverStatus.dsk?.current))}
        <div class="system-meta"><span>${escapeHtml(serverStatus.sys?.cpuType || "Unknown CPU")}</span><span>${serverStatus.sys?.cpuCount || 0} vCPU</span></div>
      </article>
      <article class="panel recent-panel">
        <div class="section-head"><div><span class="eyebrow">Clients</span><h2>最近活动</h2></div><button class="text-btn" data-go="clients">查看全部<i data-lucide="chevron-right"></i></button></div>
        <div class="recent-list">${recent.map(renderRecentClient).join("") || `<div class="empty-state">暂无用户</div>`}</div>
      </article>
    </section>`;
}

function routeRow(code: string, name: string, exit: string, badge: string, color: string): string {
  return `<div class="route-row"><span class="route-code ${color}">${code}</span><div><strong>${name}</strong><small>${exit}</small></div><span class="quiet-badge">${badge}</span></div>`;
}

function resourceRow(label: string, value: number, display: string): string {
  return `<div class="resource-row"><div><span>${label}</span><strong>${display}</strong></div><div class="meter"><span style="width:${Math.min(100, value).toFixed(1)}%"></span></div></div>`;
}

function renderRecentClient(client: Client): string {
  const online = panel?.onlines?.user?.includes(client.name);
  return `<div class="recent-row"><span class="avatar">${escapeHtml(client.name.slice(0, 2).toUpperCase())}</span><div><strong>${escapeHtml(client.name)}</strong><small>${escapeHtml(client.group || "未分组")}</small></div><span class="last-seen"><span class="status-dot ${online ? "online" : ""}"></span>${online ? "在线" : formatDate(client.onlineAt, true)}</span></div>`;
}

function renderClients(): string {
  if (!panel) return "";
  const groups = [...new Set(panel.clients.map((client) => client.group).filter(Boolean))];
  return `
    <section class="toolbar panel-flat">
      <div class="search-box"><i data-lucide="search"></i><input id="client-search" placeholder="搜索名称、备注或分组" /></div>
      <select id="client-group-filter" aria-label="按分组筛选"><option value="">全部分组</option>${groups.map((group) => `<option value="${escapeHtml(group)}">${escapeHtml(group)}</option>`).join("")}</select>
      <select id="client-state-filter" aria-label="按状态筛选"><option value="">全部状态</option><option value="online">在线</option><option value="enabled">已启用</option><option value="disabled">已停用</option><option value="expired">已过期</option></select>
      <button class="primary-btn" id="add-client" aria-label="新建用户" title="新建用户"><i data-lucide="plus"></i><span>新建用户</span></button>
    </section>
    <section class="panel table-panel">
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>用户</th><th>状态</th><th>用量</th><th>到期</th><th>入口</th><th class="align-right">操作</th></tr></thead>
          <tbody id="client-rows">${panel.clients.map(renderClientRow).join("")}</tbody>
        </table>
      </div>
      <div id="client-empty" class="empty-state hidden">没有符合条件的用户</div>
      <footer class="table-footer"><span>共 ${panel.clients.length} 个用户</span><span>${panel.onlines?.user?.length || 0} 个在线</span></footer>
    </section>`;
}

function renderClientRow(client: Client): string {
  const online = Boolean(panel?.onlines?.user?.includes(client.name));
  const used = client.up + client.down;
  const usedPercent = percent(used, client.volume);
  const expired = Boolean(client.expiry && client.expiry < Date.now() / 1000);
  const search = `${client.name} ${client.desc} ${client.group}`.toLowerCase();
  return `<tr data-client-row data-search="${escapeHtml(search)}" data-group="${escapeHtml(client.group)}" data-enabled="${client.enable}" data-online="${online}" data-expired="${expired}">
    <td><div class="user-cell"><span class="avatar">${escapeHtml(client.name.slice(0, 2).toUpperCase())}</span><div><strong>${escapeHtml(client.name)}</strong><small>${escapeHtml(client.desc || client.group || "-")}</small></div></div></td>
    <td><button class="status-toggle ${client.enable ? "enabled" : ""}" data-toggle-client="${client.id}" title="${client.enable ? "停用用户" : "启用用户"}"><span></span></button><span class="state-label"><span class="status-dot ${online ? "online" : ""}"></span>${online ? "在线" : client.enable ? "离线" : "停用"}</span></td>
    <td><div class="usage-cell"><span>${formatBytes(used)} / ${client.volume ? formatBytes(client.volume) : "不限"}</span>${client.volume ? `<div class="meter small"><span style="width:${usedPercent.toFixed(1)}%"></span></div>` : ""}</div></td>
    <td><span class="${expired ? "danger-text" : ""}">${formatDate(client.expiry)}</span></td>
    <td><span class="count-badge">${client.inbounds?.length || 0}</span></td>
    <td><div class="row-actions"><button class="icon-btn" data-copy-sub="${client.id}" title="订阅链接"><i data-lucide="copy"></i></button><button class="icon-btn" data-edit-client="${client.id}" title="编辑用户"><i data-lucide="pencil"></i></button><button class="icon-btn danger" data-delete-client="${client.id}" title="删除用户"><i data-lucide="trash-2"></i></button></div></td>
  </tr>`;
}

function renderInbounds(): string {
  if (!panel) return "";
  const encrypted = panel.inbounds.filter((item) => ["vless", "hysteria2"].includes(item.type));
  const forwards = panel.inbounds.filter((item) => !["vless", "hysteria2"].includes(item.type));
  return `
    <section class="protocol-summary">
      ${metricCard("shield-check", "加密协议", `${encrypted.length}`, "Reality · Hysteria2")}
      ${metricCard("route", "转发入口", `${forwards.length}`, "直连 SOCKS5")}
      ${metricCard("users", "已分配", `${new Set(panel.inbounds.flatMap((item) => item.users || [])).size}`, "去重后的入口用户")}
    </section>
    <section class="panel protocol-panel">
      <div class="section-head"><div><span class="eyebrow">Inbound services</span><h2>监听状态</h2></div><a href="/app/inbounds" class="text-btn">高级编辑<i data-lucide="external-link"></i></a></div>
      <div class="protocol-list">${panel.inbounds.map(renderInboundRow).join("")}</div>
    </section>`;
}

function renderInboundRow(inbound: Inbound): string {
  const live = Boolean(panel?.onlines?.inbound?.includes(inbound.tag));
  return `<div class="protocol-row"><span class="protocol-glyph ${inbound.type}">${protocolName(inbound.type, inbound.tag).slice(0, 2).toUpperCase()}</span><div class="protocol-main"><strong>${escapeHtml(protocolName(inbound.type, inbound.tag))}</strong><small>${escapeHtml(inbound.tag)}</small></div><span class="protocol-kind">${routeName(inbound.tag)}</span><code>${escapeHtml(inbound.listen)}:${inbound.listen_port}</code><span class="protocol-users"><i data-lucide="users"></i>${inbound.users?.length || 0}</span><span class="status-pill ${live ? "ok" : "neutral"}">${live ? "有连接" : "监听中"}</span></div>`;
}

function renderOperations(): string {
  const sys = serverStatus.sys;
  return `
    <section class="operation-grid">
      <article class="panel operation-main">
        <div class="section-head"><div><span class="eyebrow">Runtime</span><h2>服务控制</h2></div><span class="status-pill ${serverStatus.sbd?.running ? "ok" : "error"}">${serverStatus.sbd?.running ? "Core online" : "Core offline"}</span></div>
        <div class="server-identity"><span class="metric-icon"><i data-lucide="server"></i></span><div><strong>${escapeHtml(sys?.hostName || "AaITR")}</strong><small>${escapeHtml(sys?.cpuType || "Unknown CPU")}</small></div></div>
        <dl class="detail-list"><div><dt>版本</dt><dd>s-ui ${escapeHtml(sys?.appVersion || "-")}</dd></div><div><dt>系统启动</dt><dd>${formatDate(sys?.bootTime, true)}</dd></div><div><dt>核心运行</dt><dd>${formatDuration(serverStatus.sbd?.stats?.Uptime)}</dd></div><div><dt>应用内存</dt><dd>${formatBytes(sys?.appMem)}</dd></div></dl>
        <div class="operation-actions"><button class="secondary-btn" id="restart-core"><i data-lucide="rotate-cw"></i>重启核心</button><a class="secondary-btn" href="/app/"><i data-lucide="external-link"></i>高级配置</a></div>
      </article>
      <article class="panel download-panel">
        <div class="section-head"><div><span class="eyebrow">Export</span><h2>备份与导出</h2></div></div>
        <a class="download-row" href="/app/api/getdb"><span><i data-lucide="database-backup"></i></span><div><strong>数据库备份</strong><small>SQLite 完整备份</small></div><i data-lucide="download"></i></a>
        <a class="download-row" href="/app/api/singbox-config"><span><i data-lucide="file-json"></i></span><div><strong>sing-box 配置</strong><small>当前运行配置</small></div><i data-lucide="download"></i></a>
      </article>
      <article class="panel logs-panel">
        <div class="section-head"><div><span class="eyebrow">Logs</span><h2>最近日志</h2></div><button class="icon-btn" id="reload-logs" title="刷新日志"><i data-lucide="refresh-cw"></i></button></div>
        <pre id="runtime-logs"><span class="log-placeholder">点击刷新读取日志</span></pre>
      </article>
    </section>`;
}

function attachShellEvents(): void {
  document.querySelectorAll<HTMLElement>("[data-route]").forEach((item) => item.addEventListener("click", () => {
    activeView = item.dataset.route as ViewName;
  }));
  document.querySelector<HTMLElement>("[data-go]")?.addEventListener("click", (event) => {
    const view = (event.currentTarget as HTMLElement).dataset.go as ViewName;
    window.location.hash = `/${view}`;
  });
  document.querySelector("#refresh-button")?.addEventListener("click", () => reloadAll(true));
  document.querySelector("#theme-button")?.addEventListener("click", () => {
    setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
    renderShell();
  });
  document.querySelector("#logout-button")?.addEventListener("click", async () => {
    try { await api.logout(); } catch { /* The local session is cleared below. */ }
    stopRefresh();
    authenticated = false;
    panel = null;
    renderLogin();
  });
  if (activeView === "clients") attachClientEvents();
  if (activeView === "operations") attachOperationEvents();
}

function attachClientEvents(): void {
  document.querySelector("#add-client")?.addEventListener("click", () => openClientModal());
  document.querySelectorAll<HTMLElement>("[data-edit-client]").forEach((button) => button.addEventListener("click", () => openClientModal(Number(button.dataset.editClient))));
  document.querySelectorAll<HTMLElement>("[data-toggle-client]").forEach((button) => button.addEventListener("click", () => toggleClient(Number(button.dataset.toggleClient))));
  document.querySelectorAll<HTMLElement>("[data-delete-client]").forEach((button) => button.addEventListener("click", () => confirmDeleteClient(Number(button.dataset.deleteClient))));
  document.querySelectorAll<HTMLElement>("[data-copy-sub]").forEach((button) => button.addEventListener("click", () => openSubscriptionModal(Number(button.dataset.copySub))));
  ["client-search", "client-group-filter", "client-state-filter"].forEach((id) => {
    document.querySelector(`#${id}`)?.addEventListener(id === "client-search" ? "input" : "change", filterClientRows);
  });
}

function filterClientRows(): void {
  const search = document.querySelector<HTMLInputElement>("#client-search")?.value.toLowerCase().trim() || "";
  const group = document.querySelector<HTMLSelectElement>("#client-group-filter")?.value || "";
  const state = document.querySelector<HTMLSelectElement>("#client-state-filter")?.value || "";
  let visible = 0;
  document.querySelectorAll<HTMLElement>("[data-client-row]").forEach((row) => {
    const stateMatches = !state || (state === "online" && row.dataset.online === "true") || (state === "enabled" && row.dataset.enabled === "true") || (state === "disabled" && row.dataset.enabled === "false") || (state === "expired" && row.dataset.expired === "true");
    const show = (!search || row.dataset.search?.includes(search)) && (!group || row.dataset.group === group) && stateMatches;
    row.classList.toggle("hidden", !show);
    if (show) visible += 1;
  });
  document.querySelector("#client-empty")?.classList.toggle("hidden", visible !== 0);
}

function attachOperationEvents(): void {
  document.querySelector("#restart-core")?.addEventListener("click", confirmRestartCore);
  document.querySelector("#reload-logs")?.addEventListener("click", loadLogs);
  loadLogs();
}

function randomSequence(length = 16): string {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789";
  const values = crypto.getRandomValues(new Uint8Array(length));
  return Array.from(values, (value) => chars[value % chars.length]).join("");
}

function randomConfigs(name: string): ClientConfig {
  const password = randomSequence();
  const uuid = crypto.randomUUID();
  return {
    vless: { name, uuid, flow: "xtls-rprx-vision" },
    hysteria2: { name, password },
  };
}

function syncConfigIdentity(config: ClientConfig, name: string): ClientConfig {
  Object.values(config).forEach((entry) => {
    if ("name" in entry) entry.name = name;
    if ("username" in entry) entry.username = name;
  });
  return config;
}

async function openClientModal(id?: number): Promise<void> {
  if (!panel) return;
  const subscriptionInboundTypes = new Set(["vless", "hysteria2"]);
  let client: Client = {
    enable: true, name: "", config: {}, inbounds: panel.inbounds.filter((item) => subscriptionInboundTypes.has(item.type)).map((item) => item.id), links: [], volume: 0,
    expiry: 0, up: 0, down: 0, desc: "", group: "aaitr-production", remark: "", delayStart: false,
    autoReset: false, resetDays: 0, nextReset: 0, totalUp: 0, totalDown: 0,
  };
  if (id) {
    try { client = await api.loadClient(id); }
    catch (error) { showToast(error instanceof Error ? error.message : "读取用户失败", "danger"); return; }
  }
  const expiryValue = client.expiry ? new Date((client.expiry - new Date().getTimezoneOffset() * 60) * 1000).toISOString().slice(0, 16) : "";
  openModal(`
    <form id="client-form" class="modal-card wide">
      <header class="modal-head"><div><span class="eyebrow">${id ? "Edit client" : "New client"}</span><h2>${id ? "编辑用户" : "新建用户"}</h2></div><button type="button" class="icon-btn" data-close-modal title="关闭"><i data-lucide="x"></i></button></header>
      <div class="modal-body">
        <div class="form-grid">
          <label class="field"><span>名称</span><input name="name" value="${escapeHtml(client.name)}" required pattern="[A-Za-z0-9._-]+" /></label>
          <label class="field"><span>分组</span><input name="group" value="${escapeHtml(client.group)}" list="client-groups" required /><datalist id="client-groups">${[...new Set(panel.clients.map((item) => item.group))].map((group) => `<option value="${escapeHtml(group)}"></option>`).join("")}</datalist></label>
          <label class="field"><span>说明</span><input name="desc" value="${escapeHtml(client.desc)}" /></label>
          <label class="field"><span>备注</span><input name="remark" value="${escapeHtml(client.remark || "")}" /></label>
          <label class="field"><span>流量上限 (GiB)</span><input name="volume" type="number" min="0" step="1" value="${client.volume ? Math.round(client.volume / 1024 ** 3) : 0}" /></label>
          <label class="field"><span>到期时间</span><input name="expiry" type="datetime-local" value="${expiryValue}" /></label>
        </div>
        <div class="toggle-row"><label class="check-line"><input name="enable" type="checkbox" ${client.enable ? "checked" : ""} /><span>启用用户</span></label><label class="check-line"><input name="autoReset" type="checkbox" ${client.autoReset ? "checked" : ""} /><span>周期重置</span></label><label class="field compact-field"><span>重置天数</span><input name="resetDays" type="number" min="1" value="${client.resetDays || 30}" /></label></div>
        <fieldset class="inbound-fieldset"><legend>可用入口</legend><div class="inbound-options">${panel.inbounds.map((inbound) => `<label class="inbound-option"><input type="checkbox" name="inbounds" value="${inbound.id}" ${client.inbounds.includes(inbound.id) ? "checked" : ""} /><span><strong>${escapeHtml(protocolName(inbound.type, inbound.tag))}</strong><small>${escapeHtml(inbound.tag)}</small></span></label>`).join("")}</div></fieldset>
        ${id ? `<div class="edit-note"><i data-lucide="key-round"></i><span>协议凭据保持不变。修改名称时会同步更新各协议身份。</span></div>` : ""}
      </div>
      <footer class="modal-actions"><button type="button" class="secondary-btn" data-close-modal>取消</button><button type="submit" class="primary-btn"><i data-lucide="check"></i>保存</button></footer>
    </form>`);

  const form = document.querySelector<HTMLFormElement>("#client-form");
  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const name = String(data.get("name") || "").trim();
    const duplicate = panel?.clients.some((item) => item.name === name && item.id !== client.id);
    if (duplicate) { showToast("用户名称已存在", "danger"); return; }
    const expiry = String(data.get("expiry") || "");
    const config = id ? syncConfigIdentity(client.config || {}, name) : randomConfigs(name);
    const next: Client = {
      ...client,
      enable: data.has("enable"), name, config,
      inbounds: data.getAll("inbounds").map(Number),
      volume: Math.max(0, Number(data.get("volume") || 0)) * 1024 ** 3,
      expiry: expiry ? Math.floor(new Date(expiry).getTime() / 1000) : 0,
      desc: String(data.get("desc") || "").trim(), group: String(data.get("group") || "").trim(),
      remark: String(data.get("remark") || "").trim(), autoReset: data.has("autoReset"),
      resetDays: data.has("autoReset") ? Math.max(1, Number(data.get("resetDays") || 30)) : 0,
      links: client.links || [],
    };
    const submit = form.querySelector<HTMLButtonElement>('button[type="submit"]');
    submit?.setAttribute("disabled", "true");
    try {
      await api.saveClient(id ? "edit" : "new", next);
      closeModal();
      await reloadAll();
      showToast(id ? "用户已更新" : "用户已创建");
    } catch (error) {
      submit?.removeAttribute("disabled");
      showToast(error instanceof Error ? error.message : "保存失败", "danger");
    }
  });
}

async function toggleClient(id: number): Promise<void> {
  try {
    const client = await api.loadClient(id);
    client.enable = !client.enable;
    await api.saveClient("edit", client);
    await reloadAll();
    showToast(client.enable ? "用户已启用" : "用户已停用");
  } catch (error) { showToast(error instanceof Error ? error.message : "操作失败", "danger"); }
}

function confirmDeleteClient(id: number): void {
  const client = panel?.clients.find((item) => item.id === id);
  if (!client) return;
  openModal(`<section class="modal-card confirm-card"><header class="modal-head"><div><span class="eyebrow">Delete client</span><h2>删除 ${escapeHtml(client.name)}？</h2></div><button class="icon-btn" data-close-modal><i data-lucide="x"></i></button></header><div class="modal-body"><p>用户凭据和订阅将立即失效，CStoneCloud 出口会在下一次同步中移除该用户。</p></div><footer class="modal-actions"><button class="secondary-btn" data-close-modal>取消</button><button class="danger-btn" id="delete-confirm"><i data-lucide="trash-2"></i>确认删除</button></footer></section>`);
  document.querySelector("#delete-confirm")?.addEventListener("click", async () => {
    try { await api.saveClient("del", id); closeModal(); await reloadAll(); showToast("用户已删除"); }
    catch (error) { showToast(error instanceof Error ? error.message : "删除失败", "danger"); }
  });
}

function subscriptionUrls(name: string): Array<{ label: string; value: string }> {
  const base = `${panel?.subURI || ""}${name}`;
  const replacePath = (segment: string) => base.includes("/sub/") ? base.replace("/sub/", `/${segment}/`) : `${base}?format=${segment === "clash" ? "clash" : "json"}`;
  return [{ label: "Clash / Mihomo", value: replacePath("clash") }, { label: "sing-box JSON", value: replacePath("json") }, { label: "通用订阅", value: base }];
}

async function openSubscriptionModal(id: number): Promise<void> {
  const client = panel?.clients.find((item) => item.id === id);
  if (!client) return;
  const urls = subscriptionUrls(client.name);
  openModal(`<section class="modal-card subscription-card"><header class="modal-head"><div><span class="eyebrow">Subscription</span><h2>${escapeHtml(client.name)}</h2></div><button class="icon-btn" data-close-modal><i data-lucide="x"></i></button></header><div class="modal-body subscription-layout"><div class="qr-shell"><canvas id="subscription-qr"></canvas><small>Clash / Mihomo</small></div><div class="subscription-list">${urls.map((item, index) => `<div class="subscription-row"><div><strong>${item.label}</strong><code>${escapeHtml(item.value)}</code></div><button class="icon-btn" data-copy-value="${index}" title="复制"><i data-lucide="copy"></i></button></div>`).join("")}</div></div></section>`);
  document.querySelectorAll<HTMLElement>("[data-copy-value]").forEach((button) => button.addEventListener("click", async () => {
    await navigator.clipboard.writeText(urls[Number(button.dataset.copyValue)].value);
    showToast("订阅链接已复制");
  }));
  try {
    const QRCode = await import("qrcode");
    const canvas = document.querySelector<HTMLCanvasElement>("#subscription-qr");
    if (canvas) await QRCode.toCanvas(canvas, urls[0].value, { width: 190, margin: 1, color: { dark: "#17221d", light: "#ffffff" } });
  } catch { /* Copy remains available if QR rendering fails. */ }
}

function openModal(content: string): void {
  closeModal();
  const overlay = document.createElement("div");
  overlay.id = "modal-overlay";
  overlay.className = "modal-overlay";
  overlay.innerHTML = content;
  document.body.appendChild(overlay);
  overlay.addEventListener("mousedown", (event) => { if (event.target === overlay) closeModal(); });
  overlay.querySelectorAll("[data-close-modal]").forEach((button) => button.addEventListener("click", closeModal));
  document.addEventListener("keydown", closeOnEscape);
  renderIcons();
}

function closeOnEscape(event: KeyboardEvent): void { if (event.key === "Escape") closeModal(); }

function closeModal(): void {
  document.querySelector("#modal-overlay")?.remove();
  document.removeEventListener("keydown", closeOnEscape);
}

async function confirmRestartCore(): Promise<void> {
  openModal(`<section class="modal-card confirm-card"><header class="modal-head"><div><span class="eyebrow">Restart core</span><h2>重启 sing-box？</h2></div><button class="icon-btn" data-close-modal><i data-lucide="x"></i></button></header><div class="modal-body"><p>现有连接会短暂中断，通常会在数秒内恢复。</p></div><footer class="modal-actions"><button class="secondary-btn" data-close-modal>取消</button><button class="primary-btn" id="restart-confirm"><i data-lucide="rotate-cw"></i>确认重启</button></footer></section>`);
  document.querySelector("#restart-confirm")?.addEventListener("click", async () => {
    try { await api.restartCore(); closeModal(); showToast("核心重启指令已发送"); window.setTimeout(() => reloadAll(), 3500); }
    catch (error) { showToast(error instanceof Error ? error.message : "重启失败", "danger"); }
  });
}

async function loadLogs(): Promise<void> {
  const target = document.querySelector<HTMLElement>("#runtime-logs");
  if (!target) return;
  target.textContent = "正在读取日志...";
  try { target.textContent = (await api.logs()).join("\n") || "暂无日志"; }
  catch (error) { target.textContent = error instanceof Error ? error.message : "读取日志失败"; }
}

async function reloadAll(showSuccess = false): Promise<void> {
  try {
    const [nextPanel, nextStatus] = await Promise.all([api.load(), api.status()]);
    panel = nextPanel;
    serverStatus = nextStatus;
    authenticated = true;
    busy = false;
    renderShell();
    if (showSuccess) showToast("数据已刷新");
  } catch (error) {
    busy = false;
    if (error instanceof AuthenticationRequired) {
      authenticated = false;
      stopRefresh();
      renderLogin();
      return;
    }
    if (!panel) renderLogin(error instanceof Error ? error.message : "无法连接管理服务");
    else showToast(error instanceof Error ? error.message : "刷新失败", "danger");
  }
}

function startRefresh(): void {
  stopRefresh();
  refreshTimer = window.setInterval(() => { if (authenticated && !document.hidden) reloadAll(); }, 15000);
}

function stopRefresh(): void {
  if (refreshTimer) window.clearInterval(refreshTimer);
  refreshTimer = undefined;
}

window.addEventListener("hashchange", () => {
  activeView = getViewFromHash();
  if (authenticated) renderShell();
});

initializeTheme();
if (busy) renderLoading();
reloadAll().then(() => { if (authenticated) startRefresh(); });
