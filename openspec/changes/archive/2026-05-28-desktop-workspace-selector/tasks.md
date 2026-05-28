## 1. 后端 workspace API

- [x] 1.1 新增 `GET /api/workspace` 端点，返回当前 workspace 路径和子目录信息（`app/api/workspace.py`）
- [x] 1.2 扩展 `GET /api/health` 响应，加入 `workspace` 字段
- [x] 1.3 在 `app/main.py` 注册 workspace 路由

## 2. Tauri Rust 端 workspace 管理

- [x] 2.1 在 `main.rs` 中新增 `get_workspace_path` Tauri command —— 从 `app_data_dir/workspace_path.txt` 读取路径，若不存在或路径无效则返回空字符串
- [x] 2.2 在 `main.rs` 中新增 `select_workspace_dir` Tauri command —— 调用 Tauri dialog 插件打开系统目录选择器，将用户选择的路径写入 `workspace_path.txt`，并重启 sidecar
- [x] 2.3 修改 `start_backend` 函数签名，接受可选的 workspace 路径参数（未指定时回退到默认 `app_data_dir/workspace`）
- [x] 2.4 添加 `tauri-plugin-dialog` 依赖到 `Cargo.toml`，并在 `main.rs` 中注册插件
- [x] 2.5 将新增 Tauri commands 注册到 `invoke_handler`

## 3. Vue 前端 workspace 选择交互

- [x] 3.1 在 `App.vue` `onMounted` 中新增初始化逻辑：调用 `get_workspace_path`，若返回空则调用 `select_workspace_dir` 弹出目录选择器
- [x] 3.2 在设置面板顶部（section 01 之前）新增 "Workspace" 展示区：显示当前路径和"更换目录"按钮
- [x] 3.3 实现"更换目录"流程：调用 `select_workspace_dir` → 显示 loading 状态 → 等待 sidecar 重启（轮询 `/api/health`）→ 重新加载模型配置并刷新页面列表
- [x] 3.4 后端 sidecar 重启期间，前端禁用所有操作按钮并显示"正在切换存储目录..."
- [x] 3.5 在 `types.ts` 中新增 `WorkspaceInfo` 类型

## 4. 样式与体验完善

- [x] 4.1 在 `style.css` 中新增 workspace 展示区样式（路径截断文本、更换按钮）
- [x] 4.2 新增 sidecar 重启 loading 状态的视觉反馈
