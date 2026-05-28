# OpenSpec Authoring Rules

始终使用中文维护本项目 OpenSpec 文档。

规格必须遵守：

- 每个能力域一个目录，不要把所有功能写进一个 spec。
- `spec.md` 描述可验证行为，不写具体实现步骤。
- 使用 `### Requirement:` 表达需求。
- 每个 requirement 至少包含一个 `#### Scenario:`。
- 场景使用 `GIVEN`、`WHEN`、`THEN`、`AND` 结构。
- 使用 SHALL/MUST 表达强约束，SHOULD 表达推荐行为，MAY 表达可选能力。
- RAG、Embedding、向量数据库只能作为增强能力出现，不得替代 LLM Wiki 核心定位。
- 涉及 AI 写入、删除、移动、覆盖的行为必须包含预览、确认或可回滚约束。
