# AI 个人知识库桌面端 App 技术栈方案（Python 后端版）

## 1. 技术栈定位

本项目是一个 Windows 和 macOS 桌面端 App，核心架构为：

```text
Tauri 桌面端
+ Vue 3 前端
+ Python 本地后端服务
+ AI Agent
+ LLM Wiki
+ 本地 Markdown 文件系统
+ SQLite 元数据存储
```

本项目不使用 RAG 架构，不使用向量数据库，不使用 Embedding 知识库。

系统核心流程：

```text
用户在聊天窗口上传文件
→ Python 后端解析内容
→ AI Agent 读取和理解资料
→ Agent 维护 LLM Wiki
→ 更新 index.md / log.md / Wiki 页面
→ 用户通过聊天窗口测试 LLM Wiki 效果
```

---

## 2. 总体架构

```text
前端界面层
├── Tauri
├── Vue 3
├── TypeScript
├── Ant Design Vue
├── CodeMirror 6
└── Markdown Preview

桌面能力层
├── Tauri Rust Commands
├── 文件系统访问
├── 窗口管理
├── 系统托盘
├── 自动更新
└── Python Sidecar 管理

Python 后端服务层
├── FastAPI
├── 文档解析服务
├── AI Agent 服务
├── LLM 调用服务
├── LLM Wiki 管理服务
├── Wiki 检索服务
├── 本地搜索服务
└── SQLite 数据服务

知识库层
├── raw 原始资料
├── wiki Markdown 页面
├── index.md
├── log.md
├── AGENTS.md
├── WIKI_SCHEMA.md
├── PROMPTS.md
├── STYLE_GUIDE.md
└── app.sqlite
```

---

## 3. 前端技术栈

| 类型 | 技术选型 |
|---|---|
| 桌面端框架 | Tauri 2 |
| 前端框架 | Vue 3 |
| 开发语言 | TypeScript |
| 构建工具 | Vite |
| UI 组件库 | Ant Design Vue |
| 状态管理 | Pinia |
| 路由管理 | Vue Router |
| 请求工具 | Axios |
| Markdown 编辑器 | CodeMirror 6 |
| Markdown 渲染 | markdown-it |
| PDF 预览 | PDF.js |
| 图谱可视化 | AntV G6 / ECharts |
| 图标库 | Iconify / Ant Design Icons |
| 样式方案 | SCSS / Less |
| 桌面端打包 | Tauri CLI |

---

## 4. Tauri 技术栈

| 类型 | 技术选型 |
|---|---|
| 桌面运行框架 | Tauri 2 |
| 本地能力语言 | Rust |
| 前后端通信 | Tauri Commands / invoke |
| 文件系统访问 | Tauri fs plugin / Rust std::fs |
| 系统托盘 | Tauri tray |
| 自动更新 | Tauri updater |
| Python 后端集成 | Tauri Sidecar |
| 安装包构建 | Tauri Bundler |
| 支持平台 | Windows / macOS |

---

## 5. Python 后端技术栈

| 类型 | 技术选型 |
|---|---|
| 后端语言 | Python 3.11+ |
| 本地服务框架 | FastAPI |
| ASGI 服务 | Uvicorn |
| 数据校验 | Pydantic |
| 配置管理 | pydantic-settings |
| 数据库 | SQLite |
| ORM | SQLAlchemy / SQLModel |
| 数据迁移 | Alembic |
| 日志管理 | loguru |
| 打包方式 | PyInstaller / Nuitka |
| 与 Tauri 集成 | Sidecar 本地进程 |

---

## 6. AI 技术栈

| 类型 | 技术选型 |
|---|---|
| 云端 LLM | OpenAI / Claude / Gemini / DeepSeek / 通义千问 / 智谱 |
| 本地 LLM | Ollama / LM Studio |
| LLM 调用封装 | OpenAI SDK / LiteLLM |
| Agent 编排 | LangGraph |
| Agent 工具调用 | 自定义 Tools |
| Prompt 管理 | Markdown Prompt 模板 |
| Wiki 生成 | Agent + LLM |
| Wiki 检索 | index.md + 全文搜索 + 标签 + 双链展开 |
| 来源引用 | Wiki 页面 + Source 页面 + 原始文件路径 |
| Wiki 健康检查 | Agent Lint 流程 |

---

## 7. 文档解析技术栈

| 文件类型 | Python 技术 |
|---|---|
| PDF | PyMuPDF / pypdf |
| DOCX | python-docx |
| DOC | LibreOffice Headless 转 DOCX 后解析 |
| Markdown | markdown / mistune |
| TXT | Python 原生文本读取 |
| HTML | BeautifulSoup / readability-lxml |
| 图片 OCR | PaddleOCR / Tesseract |
| 音频转文字 | Whisper / faster-whisper，后续扩展 |
| 视频处理 | ffmpeg + Whisper，后续扩展 |

---

## 8. LLM Wiki 技术栈

| 类型 | 技术选型 |
|---|---|
| Wiki 文件格式 | Markdown |
| Wiki 元数据 | YAML Frontmatter |
| 双链格式 | `[[页面名称]]` |
| 总索引 | `wiki/index.md` |
| 操作日志 | `wiki/log.md` |
| Agent 规则 | `AGENTS.md` |
| Wiki Schema | `WIKI_SCHEMA.md` |
| Prompt 模板 | `PROMPTS.md` |
| 写作规范 | `STYLE_GUIDE.md` |
| Wiki 预览 | markdown-it |
| Wiki 编辑 | CodeMirror 6 |
| 页面版本 | SQLite + 文件快照 |

---

## 9. 本地搜索技术栈

本项目不使用 RAG，不使用 Embedding，不使用向量数据库。

LLM Wiki 检索方式如下：

| 类型 | 技术选型 |
|---|---|
| index 检索 | 读取 `wiki/index.md` |
| 标题搜索 | 解析 Markdown H1 和 Frontmatter title |
| 标签搜索 | 解析 YAML tags 和 `#标签` |
| 全文搜索 | SQLite FTS5 |
| 文件搜索 | Python pathlib / os |
| 双链搜索 | 解析 `[[页面名称]]` |
| 最近更新搜索 | 读取 `wiki/log.md` 和文件修改时间 |
| Agent 判断 | LLM 根据 index 摘要选择相关页面 |

---

## 10. 数据存储技术栈

| 类型 | 技术选型 |
|---|---|
| 原始文件存储 | 本地文件系统 `raw/` |
| Wiki 页面存储 | 本地 Markdown 文件 `wiki/` |
| 用户笔记存储 | 本地 Markdown 文件 `notes/` |
| 附件存储 | 本地文件系统 `attachments/` |
| 元数据存储 | SQLite |
| 聊天记录 | SQLite |
| Agent 任务记录 | SQLite |
| 操作日志 | `log.md` + SQLite |
| 版本历史 | SQLite + 文件快照 |
| 配置文件 | JSON / TOML |
| 密钥存储 | 系统 Keychain / Credential Manager |

---

## 11. 数据库核心表

| 表名 | 说明 |
|---|---|
| workspace | 工作空间 |
| raw_source | 原始资料 |
| wiki_page | Wiki 页面 |
| wiki_relation | Wiki 页面关系 |
| wiki_tag | Wiki 标签 |
| chat_session | 聊天会话 |
| chat_message | 聊天消息 |
| agent_task | Agent 任务 |
| agent_action | Agent 操作 |
| version_history | 版本历史 |
| import_record | 导入记录 |
| app_setting | 应用配置 |

---

## 12. 明确不使用的技术

| 技术 | 原因 |
|---|---|
| RAG | 本项目采用 LLM Wiki，不走 RAG 路线 |
| Embedding 模型 | 不做向量检索 |
| 向量数据库 | 不做向量知识库 |
| 文档 Chunk 召回 | 不按 chunk 临时拼接答案 |
| Milvus / Chroma / FAISS | 不需要向量数据库 |
| reranker | 不做 RAG 检索重排 |

---

## 13. Tauri 与 Python 后端通信

推荐模式：

```text
Vue 前端
→ Tauri invoke
→ Rust Command
→ 启动或管理 Python Sidecar
→ Python FastAPI 本地服务
→ 返回结果给前端
```

开发阶段可以简化为：

```text
Vue 前端
→ localhost HTTP
→ Python FastAPI
```

---

## 14. 后端接口建议

| 接口 | 说明 |
|---|---|
| `POST /api/chat/send` | 发送聊天消息 |
| `POST /api/upload/file` | 上传文件 |
| `POST /api/agent/ingest` | 执行资料导入和 Wiki 整理 |
| `POST /api/agent/query` | 基于 LLM Wiki 问答 |
| `POST /api/agent/lint` | 执行 Wiki 健康检查 |
| `GET /api/wiki/page` | 读取 Wiki 页面 |
| `POST /api/wiki/update` | 更新 Wiki 页面 |
| `GET /api/wiki/search` | 搜索 Wiki 页面 |
| `GET /api/wiki/index` | 读取 Wiki index |
| `GET /api/settings/model` | 获取模型配置 |
| `POST /api/settings/model` | 保存模型配置 |

---

## 15. Python 后端目录结构

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── chat_api.py
│   │   ├── upload_api.py
│   │   ├── wiki_api.py
│   │   ├── agent_api.py
│   │   └── settings_api.py
│   ├── services/
│   │   ├── file_service.py
│   │   ├── parser_service.py
│   │   ├── wiki_service.py
│   │   ├── search_service.py
│   │   ├── agent_service.py
│   │   └── llm_service.py
│   ├── agents/
│   │   ├── ingest_agent.py
│   │   ├── query_agent.py
│   │   ├── update_agent.py
│   │   ├── lint_agent.py
│   │   └── citation_agent.py
│   ├── db/
│   │   ├── database.py
│   │   ├── models.py
│   │   └── migrations/
│   ├── schemas/
│   ├── prompts/
│   ├── core/
│   └── utils/
├── pyproject.toml
└── README.md
```

---

## 16. 前端目录结构

```text
src/
├── assets/
├── components/
│   ├── chat/
│   ├── editor/
│   ├── file-tree/
│   ├── wiki/
│   └── common/
├── layouts/
├── pages/
│   ├── startup/
│   ├── workspace/
│   ├── chat/
│   ├── wiki/
│   ├── editor/
│   ├── search/
│   ├── graph/
│   └── settings/
├── router/
├── stores/
├── services/
├── types/
└── utils/
```

---

## 17. 工作空间目录结构

```text
workspace-root/
├── raw/
│   ├── documents/
│   ├── images/
│   ├── web/
│   ├── audio/
│   └── video/
├── wiki/
│   ├── index.md
│   ├── log.md
│   ├── glossary.md
│   ├── todo.md
│   ├── topics/
│   ├── concepts/
│   ├── entities/
│   ├── sources/
│   ├── claims/
│   ├── questions/
│   └── comparisons/
├── notes/
├── attachments/
├── .app/
│   ├── app.sqlite
│   ├── logs/
│   ├── cache/
│   └── config.json
├── AGENTS.md
├── WIKI_SCHEMA.md
├── PROMPTS.md
├── STYLE_GUIDE.md
└── backups/
```

---

## 18. MVP 技术栈总结

```text
前端：
Tauri 2
+ Vue 3
+ TypeScript
+ Vite
+ Ant Design Vue
+ Pinia
+ CodeMirror 6
+ markdown-it
+ PDF.js

后端：
Python 3.11+
+ FastAPI
+ Uvicorn
+ Pydantic
+ SQLite
+ SQLAlchemy
+ PyMuPDF
+ python-docx
+ BeautifulSoup
+ LangGraph
+ LiteLLM / OpenAI SDK

AI：
OpenAI / DeepSeek / 通义千问 / Claude
+ Ollama 本地模型

知识库：
Markdown
+ YAML Frontmatter
+ index.md
+ log.md
+ AGENTS.md
+ WIKI_SCHEMA.md
+ STYLE_GUIDE.md

搜索：
SQLite FTS5
+ Wiki 文件全文搜索
+ 双链解析
+ 标签解析

不使用：
RAG
Embedding
向量数据库
文档 chunk 召回
```

---

## 19. 最终推荐

第一版推荐使用：

```text
Tauri + Vue 3 + TypeScript + Python FastAPI + SQLite + LangGraph + Markdown LLM Wiki
```

核心原则：

```text
用户上传资料
→ Agent 读取资料
→ Agent 更新 LLM Wiki
→ 用户基于 LLM Wiki 提问和测试
→ Agent 检索 index.md 和 Wiki 页面
→ 回答并引用来源
→ 有价值内容继续沉淀进 Wiki
```
