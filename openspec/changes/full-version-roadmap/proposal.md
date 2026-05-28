# Full Version Roadmap Proposal

## Why

当前 MVP 已验证“模型配置 -> 文档解析 -> Wiki 生成 -> 桌面查看”的核心闭环，但完整版产品还缺少工作空间管理、手动笔记、Agent 操作确认、聊天式管理、搜索、备份、同步、多媒体处理、图谱等能力。为了避免后续实现失控，需要先按功能域建立 OpenSpec 行为契约。

## What

本变更新增完整版功能规格，按以下能力域拆分：

- `workspace-management`
- `document-ingestion`
- `llm-wiki-governance`
- `agent-operations`
- `chat-knowledge-ops`
- `authoring-obsidian`
- `search-discovery`
- `model-security`
- `backup-export-sync`
- `automation-tasks`
- `graph-relations`
- `multimedia-processing`

## Impact

这些规格不直接修改运行时代码。它们为后续实现计划、验收测试和功能拆分提供规范。后续每个功能域应单独创建 implementation plan，不应一次性实现全部完整版能力。
