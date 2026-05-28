use tauri_plugin_shell::process::CommandEvent;
use tauri::Manager;
use tauri_plugin_shell::ShellExt;

const BACKEND_PORT: u16 = 8765;

#[tauri::command]
fn backend_url() -> String {
    format!("http://127.0.0.1:{BACKEND_PORT}")
}

fn main() {
    // Rust 负责桌面生命周期和后端 sidecar，业务逻辑仍由 Python FastAPI 承担。
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![backend_url])
        .setup(|app| {
            start_backend(app.handle())?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("failed to run LLM Wiki Manager desktop app");
}

fn start_backend(app: &tauri::AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let workspace_dir = app.path().app_data_dir()?.join("workspace");
    std::fs::create_dir_all(&workspace_dir)?;

    let command = if cfg!(debug_assertions) {
        let backend_dir = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..")
            .join("..")
            .join("backend");
        app.shell()
            .command("python")
            .args(["-m", "app.sidecar"])
            .env("LLM_WIKI_BACKEND_PORT", BACKEND_PORT.to_string())
            .env("LLM_WIKI_WORKSPACE", workspace_dir.to_string_lossy().to_string())
            .current_dir(backend_dir)
    } else {
        app.shell()
            .sidecar("llm-wiki-backend")?
            .env("LLM_WIKI_BACKEND_PORT", BACKEND_PORT.to_string())
            .env("LLM_WIKI_WORKSPACE", workspace_dir.to_string_lossy().to_string())
    };

    let (mut rx, child) = command.spawn()?;
    tauri::async_runtime::spawn(async move {
        let _child_guard = child;
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    println!("[backend] {}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Stderr(line) => {
                    eprintln!("[backend] {}", String::from_utf8_lossy(&line));
                }
                _ => {}
            }
        }
    });

    Ok(())
}
