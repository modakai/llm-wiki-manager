# LLM Wiki Manager Desktop

这是 Tauri 2 + Vue 3 桌面端工程。Tauri 会在启动时拉起 FastAPI 后端 sidecar。

## 开发期启动

开发期 `npm run tauri:dev` 会通过 Rust 启动 `python -m app.sidecar`，端口为 `8765`。

## 启动 Vue 开发界面

```powershell
cd D:\ProgramData\python\project\llm-wiki-manager\desktop
npm install
npm run dev:web
```

## 启动 Tauri

如果当前 PowerShell 找不到 Rust，把 Cargo 路径加入本次会话：

```powershell
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
npm run tauri:dev
```

## 构建 sidecar

打包前需要把 Python 后端冻结为 Tauri external binary。已提供脚本：

```powershell
cd D:\ProgramData\python\project\llm-wiki-manager\desktop
npm run prepare:sidecar
npm run tauri:build
```
