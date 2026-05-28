# Document Ingestion Specification

## Purpose

定义文档上传、解析、清洗、导入记录和失败隔离行为。

## Requirements

### Requirement: Supported Document Parsing

系统 SHALL 解析 PDF、DOCX、TXT、MD 文件中的文本内容。

#### Scenario: Parse supported file

- **GIVEN** 用户上传支持的文件
- **WHEN** 文件可读取且包含文本
- **THEN** 系统 SHALL 保存原始文件
- **AND** 系统 SHALL 保存解析后的文本
- **AND** 系统 SHALL 创建导入记录

#### Scenario: Scanned PDF without OCR

- **GIVEN** 用户上传扫描版 PDF
- **WHEN** 系统无法提取文本
- **THEN** 系统 SHALL 标记解析失败
- **AND** 系统 SHALL 说明需要 OCR 能力

### Requirement: Legacy DOC Handling

系统 SHALL 明确处理老式 `.doc` 文件的转换边界。

#### Scenario: DOC conversion available

- **GIVEN** 系统配置了可用的文档转换工具
- **WHEN** 用户上传 `.doc` 文件
- **THEN** 系统 SHALL 转换为可解析格式后提取文本

#### Scenario: DOC conversion unavailable

- **GIVEN** 系统未配置文档转换工具
- **WHEN** 用户上传 `.doc` 文件
- **THEN** 系统 SHALL 返回明确错误
- **AND** 系统 MUST NOT 宣称已成功导入

### Requirement: Import Failure Isolation

系统 SHALL 隔离单个文件的导入失败。

#### Scenario: Batch import mixed results

- **GIVEN** 用户批量导入多个文件
- **WHEN** 其中部分文件损坏或不支持
- **THEN** 系统 SHALL 导入可处理文件
- **AND** 系统 SHALL 为失败文件记录失败阶段和原因
