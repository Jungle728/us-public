export interface ApiMessage<T> {
  success: boolean;
  msg: string;
  obj: T | null;
}

export interface ClientConfig {
  [protocol: string]: Record<string, unknown>;
}

export interface ClientLink {
  type: "local" | "external" | "sub";
  remark?: string;
  uri: string;
}

export interface Client {
  id?: number;
  enable: boolean;
  name: string;
  config?: ClientConfig;
  inbounds: number[];
  links?: ClientLink[];
  volume: number;
  expiry: number;
  up: number;
  down: number;
  desc: string;
  group: string;
  remark?: string;
  delayStart?: boolean;
  autoReset?: boolean;
  resetDays?: number;
  nextReset?: number;
  totalUp?: number;
  totalDown?: number;
  createdAt?: number;
  onlineAt?: number;
}

export interface Inbound {
  id: number;
  type: string;
  tag: string;
  listen: string;
  listen_port: number;
  tls_id: number;
  users: string[];
}

export interface OnlineState {
  inbound: string[];
  outbound: string[];
  user: string[];
}

export interface PanelData {
  clients: Client[];
  inbounds: Inbound[];
  outbounds: Array<Record<string, unknown>>;
  endpoints: Array<Record<string, unknown>>;
  services: Array<Record<string, unknown>>;
  onlines: OnlineState;
  subURI: string;
  enableTraffic: boolean;
  os: string;
  config?: Record<string, unknown>;
  lastLog?: string;
}

export interface ResourceUsage {
  current: number;
  total: number;
}

export interface ServerStatus {
  cpu?: number;
  mem?: ResourceUsage;
  dsk?: ResourceUsage;
  net?: { sent: number; recv: number; psent: number; precv: number };
  sys?: {
    appMem: number;
    appThreads: number;
    appVersion: string;
    bootTime: number;
    cpuCount: number;
    cpuType: string;
    hostName: string;
    ipv4: string[];
    ipv6: string[];
  };
  sbd?: {
    running: boolean;
    stats: { Alloc: number; NumGoroutine: number; Uptime: number };
  };
  db?: {
    clients: number;
    inbounds: number;
    outbounds: number;
    endpoints: number;
    services: number;
    clientUp: number;
    clientDown: number;
  };
}

export type ViewName = "dashboard" | "clients" | "inbounds" | "operations";
