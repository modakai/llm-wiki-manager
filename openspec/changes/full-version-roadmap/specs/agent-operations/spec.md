# Agent Operations Specification

## Purpose

定义 AI Agent 自动整理、分类、标签、关联、执行预览、确认和审计行为。

## Requirements

### Requirement: Agent Task Lifecycle

系统 SHALL 为每次 Agent 操作创建可追踪任务。

#### Scenario: Start ingest agent task

- **GIVEN** 用户选择资料并触发 AI 整理
- **WHEN** Agent 开始执行
- **THEN** 系统 SHALL 创建任务记录
- **AND** 任务状态 SHALL 在 pending、running、succeeded、failed、cancelled 中流转

### Requirement: User Confirmation

系统 SHALL 要求用户确认会修改知识库的 Agent 操作。

#### Scenario: Agent proposes file changes

- **GIVEN** Agent 计划创建、修改、移动或删除知识内容
- **WHEN** 执行前生成操作计划
- **THEN** 系统 SHALL 展示操作清单
- **AND** 用户确认前系统 MUST NOT 应用变更

### Requirement: Agent Audit Log

系统 SHALL 记录 Agent 的输入、输出摘要和实际操作。

#### Scenario: Review task log

- **GIVEN** 用户打开 Agent 任务历史
- **WHEN** 选择某个任务
- **THEN** 系统 SHALL 展示任务状态、来源文件、生成页面和错误摘要

### Requirement: Safe Agent Boundaries

系统 SHALL 限制 Agent 的文件系统操作范围。

#### Scenario: Agent requests unsafe path

- **GIVEN** Agent 生成的操作包含工作空间外路径
- **WHEN** 系统校验操作计划
- **THEN** 系统 MUST 拒绝该操作
- **AND** 系统 SHALL 标记为安全校验失败
