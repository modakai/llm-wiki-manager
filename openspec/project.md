# LLM Wiki Manager OpenSpec Project

## Purpose

本 OpenSpec 项目用于描述 AI 个人知识库桌面端 App 的行为契约。规格覆盖完整版目标，但不把所有功能压进单个文件；每个能力域独立维护，便于后续按模块实现、评审、验收和归档。

## Product Scope

LLM Wiki Manager 是本地优先的桌面端个人知识库应用。系统通过 OpenAI 兼容模型、AI Agent、文档解析、本地 Markdown Wiki、搜索、编辑、备份和后续扩展能力，帮助用户把个人资料整理成可维护、可追溯的 LLM Wiki。

## Architecture Principles

- 本地优先：原始资料、Wiki、配置和操作记录默认保存在本机。
- LLM Wiki 优先：LLM Wiki 不是 RAG，不要求 Embedding 或向量数据库。
- 可追溯：AI 生成内容必须能追踪来源文件或来源片段。
- 用户确认：AI 对知识库的写入、覆盖、删除、移动必须经过用户确认或可预览。
- 模块化演进：每个功能域独立 spec，后续实现应按 spec 拆分计划。

## Current MVP

当前已实现的 MVP 包含：

- Tauri + Vue 桌面端壳。
- Python FastAPI sidecar 后端。
- OpenAI 兼容模型配置。
- PDF、DOCX、TXT、MD 文本解析。
- 基于模型生成 Markdown Wiki 页面。
- Wiki 页面列表与 Markdown 查看。

## OpenSpec Layout

未来完整版能力以变更形式放在：

```text
openspec/changes/full-version-roadmap/specs/<capability>/spec.md
```

这些规格描述目标行为，不代表当前已经实现。
