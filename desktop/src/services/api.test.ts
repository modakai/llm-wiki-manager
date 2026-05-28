import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiClient } from "./api";

describe("ApiClient", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("保存模型配置时调用后端 settings API", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ configured: true }));
    const client = new ApiClient("http://127.0.0.1:8000", fetchMock);

    await client.saveModelConfig({
      base_url: "https://api.deepseek.com/v1",
      api_key: "sk-test",
      model: "deepseek-chat",
      temperature: 0.2,
      timeout: 60,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/settings/model",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("上传文件时返回 source_id", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ source_id: "abc123def456", status: "parsed" }));
    const client = new ApiClient("http://127.0.0.1:8000", fetchMock);

    const result = await client.uploadFile(new File(["text"], "note.txt"));

    expect(result.source_id).toBe("abc123def456");
  });

  it("生成 Wiki 时调用 source_id 接口", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ page_id: "wiki", title: "Wiki" }));
    const client = new ApiClient("http://127.0.0.1:8000", fetchMock);

    const result = await client.generateWiki("abc123def456");

    expect(result.title).toBe("Wiki");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/wiki/generate",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("后端错误会转换成可显示消息", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ detail: "模型配置不完整" }, false, 400));
    const client = new ApiClient("http://127.0.0.1:8000", fetchMock);

    await expect(client.loadPages()).rejects.toThrow("模型配置不完整");
  });
});

function jsonResponse(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: async () => body,
  } as Response;
}
