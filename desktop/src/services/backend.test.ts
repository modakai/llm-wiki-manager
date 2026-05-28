import { describe, expect, it, vi } from "vitest";
import { DEFAULT_API_BASE } from "./api";
import { resolveBackendUrl } from "./backend";

describe("resolveBackendUrl", () => {
  it("优先使用 Tauri 命令返回的 sidecar 地址", async () => {
    const invoke = vi.fn().mockResolvedValue("http://127.0.0.1:8765");

    await expect(resolveBackendUrl(invoke)).resolves.toBe("http://127.0.0.1:8765");
  });

  it("非 Tauri 浏览器环境回退到开发 API 地址", async () => {
    const invoke = vi.fn().mockRejectedValue(new Error("not in tauri"));

    await expect(resolveBackendUrl(invoke)).resolves.toBe(DEFAULT_API_BASE);
  });
});
