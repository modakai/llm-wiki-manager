# Authoring and Obsidian Specification

## Purpose

定义 Markdown 笔记编辑、目录管理、标签、双链和 Obsidian Vault 兼容行为。

## Requirements

### Requirement: Markdown Note Editing

系统 SHALL 支持创建、编辑、保存和删除 Markdown 笔记。

#### Scenario: Create note

- **GIVEN** 用户位于笔记目录
- **WHEN** 用户创建新笔记并输入内容
- **THEN** 系统 SHALL 保存 Markdown 文件
- **AND** 系统 SHALL 更新元数据索引

### Requirement: Live Preview

系统 SHALL 提供 Markdown 编辑与预览能力。

#### Scenario: Edit and preview

- **GIVEN** 用户打开 Markdown 笔记
- **WHEN** 用户修改内容
- **THEN** 系统 SHOULD 展示实时或手动刷新预览

### Requirement: Tags and Backlinks

系统 SHALL 识别标签和双链语法。

#### Scenario: Parse wiki link

- **GIVEN** 笔记内容包含 `[[主题名称]]`
- **WHEN** 系统保存或重新索引笔记
- **THEN** 系统 SHALL 建立双链关系

#### Scenario: Parse tags

- **GIVEN** 笔记内容包含 `#标签`
- **WHEN** 系统保存或重新索引笔记
- **THEN** 系统 SHALL 将标签加入标签索引

### Requirement: Vault Import

系统 SHALL 支持导入 Obsidian Vault。

#### Scenario: Import vault

- **GIVEN** 用户选择 Obsidian Vault 目录
- **WHEN** 系统扫描 Markdown 和附件
- **THEN** 系统 SHALL 保留目录结构
- **AND** 系统 SHALL 识别双链、标签和附件引用
