import type { Client, PanelData, ServerStatus } from "./types";

const now = Math.floor(Date.now() / 1000);

export const demoData: PanelData = {
  clients: [
    { id: 1, enable: true, name: "lhl", inbounds: [1, 2, 3, 4, 5, 6, 7], volume: 500 * 1024 ** 3, expiry: 0, down: 18.4 * 1024 ** 3, up: 8.7 * 1024 ** 3, desc: "Main account", group: "aaitr-production", remark: "lhl", createdAt: now - 86400 * 16, onlineAt: now - 42 },
    { id: 2, enable: true, name: "wzd", inbounds: [1, 2, 3, 7], volume: 200 * 1024 ** 3, expiry: now + 86400 * 92, down: 62.1 * 1024 ** 3, up: 4.2 * 1024 ** 3, desc: "Production", group: "aaitr-production", remark: "wzd", createdAt: now - 86400 * 9, onlineAt: now - 440 },
    { id: 3, enable: true, name: "gpf", inbounds: [1, 2, 3, 7], volume: 100 * 1024 ** 3, expiry: now + 86400 * 31, down: 12.8 * 1024 ** 3, up: 1.4 * 1024 ** 3, desc: "Classmate", group: "aaitr-production", remark: "gpf", createdAt: now - 86400 * 5, onlineAt: now - 86400 },
    { id: 4, enable: false, name: "archive", inbounds: [1, 2, 3, 7], volume: 50 * 1024 ** 3, expiry: now - 86400, down: 50 * 1024 ** 3, up: 2.2 * 1024 ** 3, desc: "Expired", group: "archive", remark: "archive", createdAt: now - 86400 * 60, onlineAt: now - 86400 * 8 },
  ],
  inbounds: [
    { id: 1, type: "vless", tag: "yuntu-reality", listen: "127.0.0.1", listen_port: 31443, tls_id: 1, users: ["lhl", "wzd", "gpf"] },
    { id: 2, type: "hysteria2", tag: "yuntu-hysteria2", listen: "0.0.0.0", listen_port: 32443, tls_id: 2, users: ["lhl", "wzd", "gpf"] },
    { id: 3, type: "anytls", tag: "yuntu-anytls", listen: "0.0.0.0", listen_port: 33443, tls_id: 2, users: ["lhl", "wzd", "gpf"] },
    { id: 4, type: "socks", tag: "yuntu-socks5", listen: "0.0.0.0", listen_port: 31080, tls_id: 0, users: ["lhl"] },
    { id: 5, type: "http", tag: "yuntu-http", listen: "0.0.0.0", listen_port: 31081, tls_id: 0, users: ["lhl"] },
    { id: 6, type: "http", tag: "aaitr-https", listen: "127.0.0.1", listen_port: 31444, tls_id: 2, users: ["lhl"] },
    { id: 7, type: "shadowsocks", tag: "yuntu-shadowsocks", listen: "0.0.0.0", listen_port: 34443, tls_id: 0, users: ["lhl", "wzd", "gpf"] },
  ],
  outbounds: [], endpoints: [], services: [],
  onlines: { inbound: ["yuntu-reality", "yuntu-anytls", "yuntu-http"], outbound: [], user: ["lhl", "wzd"] },
  subURI: "https://sub.bigpandas.top/sub/",
  enableTraffic: true,
  os: "linux",
};

export const demoStatus: ServerStatus = {
  cpu: 13.6,
  mem: { current: 492 * 1024 ** 2, total: 2 * 1024 ** 3 },
  dsk: { current: 7.2 * 1024 ** 3, total: 20 * 1024 ** 3 },
  net: { sent: 384 * 1024 ** 3, recv: 821 * 1024 ** 3, psent: 0, precv: 0 },
  sys: { appMem: 78 * 1024 ** 2, appThreads: 28, appVersion: "1.5.4", bootTime: now - 86400 * 5, cpuCount: 1, cpuType: "Intel Xeon Gold 6133", hostName: "aaitr", ipv4: ["203.0.113.10/24"], ipv6: [] },
  sbd: { running: true, stats: { Alloc: 54 * 1024 ** 2, NumGoroutine: 28, Uptime: 86400 * 5 } },
  db: { clients: 4, inbounds: 7, outbounds: 3, endpoints: 0, services: 0, clientUp: 16.5 * 1024 ** 3, clientDown: 143.3 * 1024 ** 3 },
};

export const demoLogs = [
  "2026/08/06 08:31:22 INFO sing-box core is running",
  "2026/08/06 08:30:01 INFO configuration reloaded",
  "2026/08/06 08:29:44 INFO client synchronization complete",
];

let nextClientId = 5;

export function demoSaveClient(action: "new" | "edit" | "del", value: Client | number): void {
  if (action === "del") {
    demoData.clients = demoData.clients.filter((client) => client.id !== value);
    return;
  }
  const client = value as Client;
  if (action === "new") {
    client.id = nextClientId++;
    client.createdAt = now;
    client.onlineAt = 0;
    demoData.clients.unshift(client);
    return;
  }
  const index = demoData.clients.findIndex((item) => item.id === client.id);
  if (index >= 0) demoData.clients[index] = client;
}
