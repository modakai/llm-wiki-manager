# Graph Relations Specification

## Purpose

定义笔记、Wiki 页面、标签、主题之间的关系识别和图谱展示行为。

## Requirements

### Requirement: Relation Extraction

系统 SHALL 从双链、标签和来源关系中提取知识关系。

#### Scenario: Extract backlink relation

- **GIVEN** 笔记包含 `[[目标页面]]`
- **WHEN** 系统索引该笔记
- **THEN** 系统 SHALL 建立当前笔记到目标页面的关系

### Requirement: Graph View

系统 SHOULD 提供知识关系图视图。

#### Scenario: Open graph

- **GIVEN** 工作空间中已有关系数据
- **WHEN** 用户打开图谱视图
- **THEN** 系统 SHALL 展示节点和边
- **AND** 用户 SHALL 能点击节点打开对应内容

### Requirement: AI Relation Suggestions

系统 MAY 使用 AI 推荐潜在关系。

#### Scenario: Suggest related pages

- **GIVEN** 多个页面主题相近
- **WHEN** 用户请求关联分析
- **THEN** 系统 SHALL 展示建议关系
- **AND** 用户确认前系统 MUST NOT 写入关系

### Requirement: Graph Filtering

系统 SHALL 支持按类型过滤图谱。

#### Scenario: Filter by tag nodes

- **GIVEN** 图谱包含页面、文件和标签节点
- **WHEN** 用户选择只查看标签关系
- **THEN** 系统 SHALL 隐藏非标签关系或降低其权重
