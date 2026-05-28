# LLM Wiki Manager Backend MVP

这是一个本地 FastAPI + 静态 Web UI 技术验证版，用来验证：

1. 配置 OpenAI 兼容模型，例如 DeepSeek。
2. 上传 `pdf`、`docx`、`txt`、`md` 文件并提取文本。
3. 调用模型生成 Markdown LLM Wiki 页面。
4. 在浏览器查看生成的 Wiki。

本版本不包含 RAG、Embedding、向量数据库、Supabase、聊天、知识图谱、Tauri 打包。

## 启动

```powershell
cd D:\ProgramData\python\project\llm-wiki-manager\backend
python -m pip install -e .[dev]
python -m uvicorn app.main:app --reload --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

## 模型配置

在页面中填写：

```text
Base URL: https://api.deepseek.com/v1
API Key: 你的 key
Model: deepseek-chat
```

配置保存位置：

```text
workspace/.app/config.json
```

注意：Windows MVP 会使用当前用户的 DPAPI 加密 API Key 后再写入 JSON。它比明文配置安全，但仍不是最终跨平台方案。当前密钥保护实现只覆盖 Windows；正式桌面端应迁移到 Windows Credential Manager 或 macOS Keychain。

## 文件支持边界

支持：

- `.pdf`：仅文本型 PDF，不支持扫描件 OCR。
- `.docx`：提取段落文本，不处理图片。
- `.txt`
- `.md`

暂不支持：

- `.doc`：需要 LibreOffice headless 转换链路，本 MVP 直接返回明确错误。

## 测试

```powershell
cd D:\ProgramData\python\project\llm-wiki-manager\backend
python -m pytest tests -v
```
