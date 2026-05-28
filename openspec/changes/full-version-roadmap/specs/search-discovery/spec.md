# Search and Discovery Specification

## Purpose

定义全文搜索、标签搜索、文件搜索、Wiki 检索和可选语义搜索行为。

## Requirements

### Requirement: Full Text Search

系统 SHALL 支持对笔记、解析文本和 Wiki 页面进行全文搜索。

#### Scenario: Search keyword

- **GIVEN** 工作空间中已有索引内容
- **WHEN** 用户输入关键词
- **THEN** 系统 SHALL 返回匹配页面或文件
- **AND** 系统 SHOULD 展示命中摘要

### Requirement: Tag Search

系统 SHALL 支持按标签筛选知识内容。

#### Scenario: Filter by tag

- **GIVEN** 笔记或 Wiki 页面包含标签
- **WHEN** 用户选择某个标签
- **THEN** 系统 SHALL 展示关联内容列表

### Requirement: File Type Filtering

系统 SHALL 支持按文件类型过滤搜索结果。

#### Scenario: Filter PDF sources

- **GIVEN** 搜索结果包含多种来源类型
- **WHEN** 用户选择 PDF 类型
- **THEN** 系统 SHALL 只展示 PDF 来源相关结果

### Requirement: Optional Semantic Search

系统 MAY 提供语义搜索作为增强能力。

#### Scenario: Semantic search disabled

- **GIVEN** 用户未启用语义搜索
- **WHEN** 用户执行普通搜索
- **THEN** 系统 MUST NOT 要求向量数据库才能返回结果

#### Scenario: Semantic search enabled

- **GIVEN** 用户启用语义搜索
- **WHEN** 系统建立语义索引
- **THEN** 系统 SHALL 明确标注这是增强能力而非 LLM Wiki 核心依赖
