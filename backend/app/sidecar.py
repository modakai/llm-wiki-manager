import os

import uvicorn
from app.main import app


def main() -> None:
    """Tauri sidecar 入口：启动本地 FastAPI 服务。"""

    port = int(os.getenv("LLM_WIKI_BACKEND_PORT", "8765"))
    workspace = os.getenv("LLM_WIKI_WORKSPACE", "")
    print(f"[sidecar] workspace = {workspace}, port = {port}", flush=True)
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level=os.getenv("LLM_WIKI_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
