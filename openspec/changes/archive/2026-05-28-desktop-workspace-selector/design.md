## Context

当前 LLM Wiki Manager 桌面端基于 Tauri 2 + Vue 3，后端为 Python FastAPI sidecar。workspace 路径由 Rust 层在启动时通过 `LLM_WIKI_WORKSPACE` 环境变量硬编码传入（指向 `app_data_dir/workspace`），用户无法更改。knowledge 管理工具的核心需求之一是用户能将文档存放在自己指定的位置——项目目录、外部硬盘、网盘同步文件夹等。

### 当前数据流

```
Tauri (Rust) → env LLM_WIKI_WORKSPACE → Python sidecar → WorkspacePaths
```

用户没有介入点。改变路径的唯一方式是手动修改环境变量，这在桌面端中无法做到。

### 约束

- Tauri 2 提供 `dialog` 插件可调用系统原生目录选择器
- Python sidecar 不能直接调用系统对话框（无 GUI 上下文）
- 路径必须在 Python 进程启动前确定（当前架构），或后端支持运行时切换
- workspace 路径需要跨会话持久化

## Goals / Non-Goals

**Goals:**
- 用户启动桌面端时，若未选择过 workspace 目录，弹出系统原生目录选择器
- 用户可在设置面板查看当前 workspace 路径，并点击"更换目录"重新选择
- 更换目录后，后端重新初始化新 workspace（创建目录结构），前端刷新页面列表
- 路径选择持久化到本地配置文件，下次启动自动恢复

**Non-Goals:**
- 不实现多 workspace 同时管理
- 不实现远程/网络存储路径（NAS、云存储等——用户可以选择挂载后的盘符）
- 不迁移已有 workspace 数据（更换目录后从空白开始，旧目录文件保留在原处）
- 不改变 MVP 文件存储结构（`raw/`、`parsed/`、`wiki/`、`.app/` 目录布局不变）

## Decisions

### 1. 路径持久化位置：Tauri app 配置目录

**选择**: 在 `app_data_dir` 下存储 `workspace_path.txt`（纯文本，一行一个绝对路径），不放在 workspace 内部。

**理由**: workspace 目录是用户选择的，可能随时更换，把配置放在 app 数据目录保证配置不会因更换 workspace 而丢失。使用纯文本而非 JSON 减少依赖，路径本身不需要结构化。

**备选方案**: 
- 存入系统注册表 → Windows 特化，跨平台迁移成本高
- 存入 workspace 内部的 `.app/` → 更换目录后丢失配置

### 2. 目录选择器触发时机：Vue 前端通过 Tauri invoke 调用

**选择**: 前端 `onMounted` 时调用 Tauri command `get_workspace_path`，若返回空则触发目录选择对话框（Tauri command `select_workspace_dir`），选择后重启 sidecar。

**理由**: 
- Tauri dialog 插件需要在 Rust 端调用系统 API，前端通过 `invoke` 触发
- 把选择逻辑放在前端初始化阶段，用户体验连贯
- 更换目录时同样调用 `select_workspace_dir` → 重启 sidecar

**备选方案**:
- 在 Rust `setup` 阶段弹出对话框 → 过早阻塞，窗口尚未渲染，用户体验差
- 用前端 `<input type="file" webkitdirectory>` → 非标准，兼容性差，且不是"选择目录"语义

### 3. 更换 workspace 时重启 sidecar

**选择**: 用户更换目录后，前端调用 Tauri command 更新配置，然后 Rust 端 kill 旧 sidecar 进程并用新路径重新启动。

**理由**: Python FastAPI 的 `WorkspacePaths` 在启动时注入，运行时切换需要改 app state 并重新初始化目录结构，同时前端状态（页面列表、选中页面）需全部重置。直接重启 sidecar 最简洁，避免状态不一致。

**备选方案**:
- 后端新增 `PUT /api/workspace` 运行时切换 → 增加后端复杂度，前端仍需重置所有状态，收益不大

### 4. 前端 UI 布局

**选择**: 在设置面板顶部（section 01 模型配置之前）新增 "Workspace" 区域，展示当前路径（只读文本 + 路径截断），并提供"更换目录"按钮。启动时若无 workspace 则弹出对话框引导选择。

## Risks / Trade-offs

- **[R] 更换目录时 sidecar 重启约 1-2 秒** → 前端显示加载状态，阻塞操作直到健康检查通过
- **[R] 用户选择系统根目录（如 C:\）** → 后端仍会创建子目录结构（`C:\raw\`, `C:\wiki\` 等），不会污染根目录自身，但建议前端提示"建议选择空目录或专用目录"
- **[R] 权限不足的目录（如 Program Files）** → 后端 `ensure()` 创建目录失败时抛出明确错误，前端展示错误信息
