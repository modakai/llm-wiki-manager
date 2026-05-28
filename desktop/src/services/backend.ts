import { invoke } from "@tauri-apps/api/core";
import { DEFAULT_API_BASE } from "./api";

type InvokeLike = <T>(command: string) => Promise<T>;

// Tauri 环境优先从 Rust 获取 sidecar 地址；普通浏览器开发环境回退到手动启动的后端。
export async function resolveBackendUrl(invoker: InvokeLike = invoke): Promise<string> {
  try {
    return await invoker<string>("backend_url");
  } catch {
    return DEFAULT_API_BASE;
  }
}
