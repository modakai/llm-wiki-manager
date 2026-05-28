# Chat Knowledge Operations Specification

## Purpose

定义通过聊天窗口管理知识库、整理资料、生成笔记和触发 Agent 操作的行为。

## Requirements

### Requirement: Workspace Chat

系统 SHALL 提供面向当前工作空间的聊天入口。

#### Scenario: Ask to organize recent files

- **GIVEN** 用户打开聊天窗口
- **WHEN** 用户输入“帮我整理最近导入的资料”
- **THEN** 系统 SHALL 找到最近导入记录
- **AND** 系统 SHALL 返回整理计划或需要确认的问题

### Requirement: Current Document Chat

系统 SHALL 支持围绕当前打开文档进行聊天操作。

#### Scenario: Summarize current document

- **GIVEN** 用户正在查看某个文档或 Wiki 页面
- **WHEN** 用户请求总结当前内容
- **THEN** 系统 SHALL 基于当前内容生成摘要
- **AND** 系统 SHALL 标注内容来源

### Requirement: Chat-Initiated Writes

系统 SHALL 对聊天触发的写入操作执行确认流程。

#### Scenario: Save answer as note

- **GIVEN** 聊天回答可保存为笔记
- **WHEN** 用户请求保存
- **THEN** 系统 SHALL 展示目标路径和内容预览
- **AND** 用户确认后系统 SHALL 创建笔记

### Requirement: Chat History

系统 SHALL 保存用户允许保留的聊天会话。

#### Scenario: Reopen chat session

- **GIVEN** 用户之前保存过聊天会话
- **WHEN** 用户重新打开该会话
- **THEN** 系统 SHALL 展示历史消息
- **AND** 系统 SHALL 保留与相关资料的关联
