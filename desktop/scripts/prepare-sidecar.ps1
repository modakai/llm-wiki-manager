param(
    [string]$BackendDir = (Resolve-Path "$PSScriptRoot\..\..\backend").Path,
    [string]$TauriDir = (Resolve-Path "$PSScriptRoot\..\src-tauri").Path
)

# 生成 Tauri externalBin 需要的 Python 后端 sidecar 可执行文件。
$ErrorActionPreference = "Stop"

$cargoBin = Join-Path $env:USERPROFILE ".cargo\bin"
if (Test-Path $cargoBin) {
    $env:PATH = "$cargoBin;$env:PATH"
}

$targetTriple = (& rustc --print host-tuple).Trim()
if (-not $targetTriple) {
    throw "无法获取 Rust target triple。"
}

Push-Location $BackendDir
try {
    python -m pip install -e ".[dev]"
    python -m PyInstaller --name llm-wiki-backend --onefile --noconsole app\sidecar.py
}
finally {
    Pop-Location
}

$binaryDir = Join-Path $TauriDir "binaries"
New-Item -ItemType Directory -Force -Path $binaryDir | Out-Null
Copy-Item `
    (Join-Path $BackendDir "dist\llm-wiki-backend.exe") `
    (Join-Path $binaryDir "llm-wiki-backend-$targetTriple.exe") `
    -Force
