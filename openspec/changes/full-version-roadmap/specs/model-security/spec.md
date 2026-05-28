# Model and Security Specification

## Purpose

定义 OpenAI 兼容模型配置、本地模型配置、密钥保护、隐私提示和外部调用边界行为。

## Requirements

### Requirement: OpenAI-Compatible Configuration

系统 SHALL 支持 OpenAI 兼容模型配置。

#### Scenario: Configure cloud model

- **GIVEN** 用户输入 base URL、API key 和模型名
- **WHEN** 用户保存配置
- **THEN** 系统 SHALL 保存配置
- **AND** 系统 MUST NOT 在界面或日志中显示 API key 原文

### Requirement: Local Model Configuration

系统 SHOULD 支持本地模型服务配置。

#### Scenario: Configure Ollama or LM Studio

- **GIVEN** 用户输入本地模型服务地址
- **WHEN** 用户保存配置并测试连接
- **THEN** 系统 SHALL 返回连接状态
- **AND** 系统 SHALL 允许用户将其设为默认模型

### Requirement: Secret Storage

系统 SHALL 使用平台安全机制保护密钥。

#### Scenario: Store API key on Windows

- **GIVEN** 用户保存 API key
- **WHEN** 系统运行在 Windows
- **THEN** 系统 SHALL 使用当前用户可解密的安全存储或等效保护机制

#### Scenario: Return model settings

- **GIVEN** 前端请求模型配置
- **WHEN** 后端返回配置
- **THEN** 响应 SHALL 只包含脱敏密钥状态

### Requirement: External Model Privacy Notice

系统 SHALL 在发送资料到外部模型前提示隐私边界。

#### Scenario: First cloud model call

- **GIVEN** 用户使用云端模型处理文档
- **WHEN** 系统准备发送文档内容
- **THEN** 系统 SHALL 提示内容将发送到第三方模型服务
- **AND** 用户确认前系统 MUST NOT 发送原文
