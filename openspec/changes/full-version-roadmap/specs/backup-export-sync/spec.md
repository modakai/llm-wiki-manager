# Backup Export and Sync Specification

## Purpose

定义本地备份、恢复、导出、Obsidian 兼容导出和可选同步行为。

## Requirements

### Requirement: Manual Backup

系统 SHALL 支持手动备份整个工作空间。

#### Scenario: Create backup

- **GIVEN** 用户打开一个工作空间
- **WHEN** 用户触发备份
- **THEN** 系统 SHALL 生成包含原始资料、Wiki、笔记和元数据的备份

### Requirement: Restore Backup

系统 SHALL 支持从备份恢复工作空间。

#### Scenario: Restore valid backup

- **GIVEN** 用户选择有效备份文件
- **WHEN** 用户确认恢复
- **THEN** 系统 SHALL 恢复工作空间内容
- **AND** 系统 SHALL 避免静默覆盖当前工作空间

### Requirement: Markdown Export

系统 SHALL 支持导出 Markdown 笔记和 Wiki。

#### Scenario: Export wiki

- **GIVEN** 用户选择导出 Wiki
- **WHEN** 导出完成
- **THEN** 系统 SHALL 生成可阅读的 Markdown 文件夹

### Requirement: Optional Cloud Sync

系统 MAY 支持云盘或 Git 同步。

#### Scenario: Sync disabled

- **GIVEN** 用户未启用同步
- **WHEN** 用户使用本地知识库
- **THEN** 系统 SHALL 完全本地运行

#### Scenario: Sync conflict

- **GIVEN** 同步目标存在冲突版本
- **WHEN** 系统检测到冲突
- **THEN** 系统 SHALL 提示用户选择保留版本
- **AND** 系统 MUST NOT 静默覆盖任何版本
