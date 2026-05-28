use std::net::TcpStream;
use std::sync::Mutex;
use std::time::Duration;
use tauri::Manager;
use tauri_plugin_dialog::DialogExt;
use tauri_plugin_shell::process::CommandEvent;
use tauri_plugin_shell::ShellExt;

const BACKEND_PORT: u16 = 8765;

struct BackendState {
    child: Mutex<Option<tauri_plugin_shell::process::CommandChild>>,
}

fn is_port_open(port: u16) -> bool {
    TcpStream::connect_timeout(
        &format!("127.0.0.1:{port}").parse().unwrap(),
        Duration::from_millis(300),
    )
    .is_ok()
}

fn wait_port_closed(port: u16, timeout_secs: u64) -> Result<(), String> {
    let start = std::time::Instant::now();
    while start.elapsed().as_secs() < timeout_secs {
        if !is_port_open(port) {
            return Ok(());
        }
        std::thread::sleep(Duration::from_millis(300));
    }
    Err(format!("端口 {} 在 {} 秒内未释放，旧后端可能仍在运行", port, timeout_secs))
}

fn wait_port_open(port: u16, timeout_secs: u64) -> Result<(), String> {
    let start = std::time::Instant::now();
    while start.elapsed().as_secs() < timeout_secs {
        if is_port_open(port) {
            return Ok(());
        }
        std::thread::sleep(Duration::from_millis(400));
    }
    Err(format!("后端在 {} 秒内未能在端口 {} 启动", timeout_secs, port))
}

#[tauri::command]
fn backend_url() -> String {
    format!("http://127.0.0.1:{BACKEND_PORT}")
}

#[tauri::command]
fn get_workspace_path(app: tauri::AppHandle) -> String {
    let config_path = app
        .path()
        .app_data_dir()
        .unwrap_or_default()
        .join("workspace_path.txt");
    if let Ok(content) = std::fs::read_to_string(&config_path) {
        let path = content.trim().to_string();
        if !path.is_empty() && std::path::Path::new(&path).exists() {
            return path;
        }
    }
    String::new()
}

#[tauri::command]
fn select_workspace_dir(app: tauri::AppHandle) -> Result<String, String> {
    let (tx, rx) = std::sync::mpsc::channel();

    app.dialog()
        .file()
        .pick_folder(move |dir_path| {
            let _ = tx.send(dir_path);
        });

    let dir_path = rx.recv().map_err(|e| e.to_string())?;

    let chosen = match dir_path {
        Some(p) => p.to_string(),
        None => {
            app.path()
                .app_data_dir()
                .map_err(|e| e.to_string())?
                .join("workspace")
                .to_string_lossy()
                .to_string()
        }
    };

    let config_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    std::fs::create_dir_all(&config_dir).map_err(|e| e.to_string())?;
    let config_path = config_dir.join("workspace_path.txt");
    std::fs::write(&config_path, &chosen).map_err(|e| e.to_string())?;

    let state = app.state::<BackendState>();
    if let Some(child) = state.child.lock().unwrap().take() {
        child.kill().map_err(|e| format!("无法停止旧后端进程: {e}"))?;
        wait_port_closed(BACKEND_PORT, 10)?;
    }

    start_backend(&app, Some(chosen.clone())).map_err(|e| e.to_string())?;
    wait_port_open(BACKEND_PORT, 15)?;
    Ok(chosen)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(BackendState {
            child: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            backend_url,
            get_workspace_path,
            select_workspace_dir
        ])
        .setup(|app| {
            let workspace_path = get_workspace_path(app.handle().clone());
            let path = if workspace_path.is_empty() {
                None
            } else {
                Some(workspace_path)
            };
            start_backend(app.handle(), path)?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("failed to run LLM Wiki Manager desktop app");
}

fn start_backend(
    app: &tauri::AppHandle,
    workspace_path: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    let workspace_dir = match workspace_path {
        Some(p) => std::path::PathBuf::from(p),
        None => app.path().app_data_dir()?.join("workspace"),
    };
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
            .env(
                "LLM_WIKI_WORKSPACE",
                workspace_dir.to_string_lossy().to_string(),
            )
            .current_dir(backend_dir)
    } else {
        app.shell()
            .sidecar("llm-wiki-backend")?
            .env("LLM_WIKI_BACKEND_PORT", BACKEND_PORT.to_string())
            .env(
                "LLM_WIKI_WORKSPACE",
                workspace_dir.to_string_lossy().to_string(),
            )
    };

    let (mut rx, child) = command.spawn()?;
    app.state::<BackendState>()
        .child
        .lock()
        .unwrap()
        .replace(child);

    tauri::async_runtime::spawn(async move {
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
