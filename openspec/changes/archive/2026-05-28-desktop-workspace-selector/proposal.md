## Why

当前桌面端 workspace 目录固定在系统应用数据目录（`app_data_dir/workspace`），用户无法选择 wiki 文档的存储位置。对于知识管理工具而言，用户需要将自己的资料和生成的 wiki 存放在指定的磁盘位置（如项目目录、移动硬盘、同步文件夹等），强制默认位置严重影响可用性。

## What Changes

- **新增** workspace 目录选择功能：桌面端启动时允许用户选择（或创建）wiki 存储目录
- **新增** 后端 API 支持动态切换 workspace 路径，并持久化用户选择
- **新增** Tauri 端原生目录选择对话框，调用系统文件选择器
- **修改** 桌面端启动流程：检测是否已有 workspace 路径，有则直接启动，无则弹出目录选择器
- **修改** 前端 UI 在设置面板中展示当前 workspace 路径，并提供"更换目录"入口
- **修改** Rust sidecar 启动逻辑，从持久化的路径配置中读取 workspace 而非硬编码 `app_data_dir`

## Capabilities

### New Capabilities

- `workspace-selection`: 用户可通过系统原生目录选择器选择或创建 wiki 存储目录，路径信息持久化保存，支持后续更换
- `workspace-api`: 后端提供 workspace 路径读写 API，支持启动时恢复上次路径，运行时切换路径

### Modified Capabilities

<!-- 无已有 spec 需要修改 -->

## Impact

- **Tauri Rust 端**: `main.rs` — sidecar 启动逻辑改为读取持久化路径
- **Vue 前端**: `App.vue` — 新增目录选择 UI 和 workspace 状态展示
- **后端 FastAPI**: 新增 workspace 管理 API，修改 `WorkspacePaths` 支持动态路径
- **配置文件**: 新增 workspace 路径持久化存储（`.app/workspace.json` 或系统级配置）
