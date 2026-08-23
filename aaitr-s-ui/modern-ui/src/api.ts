import type { ApiMessage, Client, PanelData, ServerStatus } from "./types";
import { demoData, demoLogs, demoSaveClient, demoStatus } from "./demo";

const API_ROOT = "/app/api";
const demoMode = import.meta.env.DEV && new URLSearchParams(window.location.search).has("demo");

export class AuthenticationRequired extends Error {}

async function decodeResponse<T>(response: Response): Promise<ApiMessage<T>> {
  const contentType = response.headers.get("content-type") || "";
  if (response.redirected || !contentType.includes("application/json")) {
    throw new AuthenticationRequired("Session expired");
  }
  const message = (await response.json()) as ApiMessage<T>;
  if (!message.success && message.msg === "Invalid login") {
    throw new AuthenticationRequired(message.msg);
  }
  return message;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}/${path}`, {
    credentials: "same-origin",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      ...(init?.headers || {}),
    },
    ...init,
  });
  const message = await decodeResponse<T>(response);
  if (!message.success) throw new Error(message.msg || "Request failed");
  return message.obj as T;
}

function formBody(values: Record<string, string | undefined>): URLSearchParams {
  const body = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined) body.set(key, value);
  });
  return body;
}

export const api = {
  async login(user: string, pass: string): Promise<void> {
    if (demoMode) return;
    await request<null>("login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8" },
      body: formBody({ user, pass }),
    });
  },

  async logout(): Promise<void> {
    if (demoMode) return;
    await request<null>("logout");
  },

  async load(): Promise<PanelData> {
    if (demoMode) return structuredClone(demoData);
    return request<PanelData>("load");
  },

  async loadClient(id: number): Promise<Client> {
    if (demoMode) {
      const client = demoData.clients.find((item) => item.id === id);
      if (!client) throw new Error("Client not found");
      return structuredClone(client);
    }
    const result = await request<{ clients: Client[] }>(`clients?id=${id}`);
    if (!result.clients?.[0]) throw new Error("Client not found");
    return result.clients[0];
  },

  async status(): Promise<ServerStatus> {
    if (demoMode) return structuredClone(demoStatus);
    return request<ServerStatus>("status?r=cpu,mem,dsk,net,sys,sbd,db");
  },

  async logs(count = 80, level = "info"): Promise<string[]> {
    if (demoMode) return demoLogs.slice(0, count);
    return request<string[]>(`logs?c=${count}&l=${encodeURIComponent(level)}`);
  },

  async saveClient(action: "new" | "edit" | "del", data: Client | number): Promise<void> {
    if (demoMode) {
      demoSaveClient(action, structuredClone(data));
      return;
    }
    await request<Record<string, unknown>>("save", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8" },
      body: formBody({
        object: "clients",
        action,
        data: JSON.stringify(data, null, 2),
      }),
    });
  },

  async restartCore(): Promise<void> {
    if (demoMode) return;
    await request<null>("restartSb", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8" },
      body: new URLSearchParams(),
    });
  },
};
