# LLM Wiki Governance Specification

## Purpose

定义 LLM Wiki 页面生成、更新、结构约束、来源追踪、确认和版本治理行为。

## Requirements

### Requirement: Wiki Page Structure

系统 SHALL 生成符合固定结构的 Markdown Wiki 页面。

#### Scenario: Generate topic page

- **GIVEN** 系统已有解析文本
- **WHEN** 用户触发 Wiki 生成
- **THEN** 页面 SHALL 包含标题、摘要、核心概念、知识卡片、来源文件和更新时间
- **AND** 页面 SHALL 保存为 Markdown

### Requirement: Source Traceability

系统 SHALL 让 AI 生成内容可追溯到来源资料。

#### Scenario: View generated page

- **GIVEN** 用户打开 AI 生成的 Wiki 页面
- **WHEN** 页面包含事实性陈述
- **THEN** 系统 SHALL 展示来源文件
- **AND** 系统 SHOULD 展示段落、页码或来源片段

### Requirement: Preview Before Write

系统 SHALL 在写入或覆盖 Wiki 前展示预览。

#### Scenario: Confirm generated changes

- **GIVEN** AI 已生成 Wiki 草稿
- **WHEN** 草稿将新增或覆盖页面
- **THEN** 系统 SHALL 展示变更预览
- **AND** 用户确认前系统 MUST NOT 写入最终 Wiki 文件

### Requirement: Version History

系统 SHALL 保留 Wiki 页面关键修改历史。

#### Scenario: Roll back page

- **GIVEN** Wiki 页面已有历史版本
- **WHEN** 用户选择回滚到历史版本
- **THEN** 系统 SHALL 恢复页面内容
- **AND** 系统 SHALL 记录回滚操作
