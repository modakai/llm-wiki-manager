import type { ModelConfigPayload, ModelConfigView, UploadResult, WikiPage, WikiPageContent } from "../types";

type FetchLike = typeof fetch;

// 开发期默认连接本地 FastAPI；Tauri sidecar 接入后只需替换这个基址。
export const DEFAULT_API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export class ApiClient {
  private readonly fetcher: FetchLike;

  constructor(
    private readonly baseUrl: string = DEFAULT_API_BASE,
    fetcher?: FetchLike,
  ) {
    // 浏览器原生 fetch 需要绑定 globalThis，否则作为类字段调用会触发 Illegal invocation。
    this.fetcher = fetcher ?? globalThis.fetch.bind(globalThis);
  }

  async loadModelConfig(): Promise<ModelConfigView> {
    return this.request<ModelConfigView>("/api/settings/model");
  }

  async saveModelConfig(payload: ModelConfigPayload): Promise<ModelConfigView> {
    return this.request<ModelConfigView>("/api/settings/model", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  async uploadFile(file: File): Promise<UploadResult> {
    const body = new FormData();
    body.append("file", file);
    return this.request<UploadResult>("/api/uploads", { method: "POST", body });
  }

  async generateWiki(sourceId: string): Promise<WikiPage> {
    return this.request<WikiPage>("/api/wiki/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_id: sourceId }),
    });
  }

  async loadPages(): Promise<WikiPage[]> {
    return this.request<WikiPage[]>("/api/wiki/pages");
  }

  async loadPage(pageId: string): Promise<WikiPageContent> {
    return this.request<WikiPageContent>(`/api/wiki/pages/${encodeURIComponent(pageId)}`);
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await this.fetcher(`${this.baseUrl}${path}`, init);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(extractErrorMessage(data, response.status));
    }
    return data as T;
  }
}

// FastAPI 错误通常在 detail 字段；这里统一成适合界面展示的文本。
function extractErrorMessage(data: unknown, status: number): string {
  if (typeof data === "object" && data && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return `请求失败：HTTP ${status}`;
}
