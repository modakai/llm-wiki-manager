from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import settings, uploads, wiki, workspace
from app.core.paths import WorkspacePaths, default_workspace


def create_app(paths: WorkspacePaths | None = None) -> FastAPI:
    """创建 FastAPI 应用，测试可注入临时 workspace。"""

    app = FastAPI(title="LLM Wiki Manager MVP")
    app.state.paths = paths or default_workspace()
    app.state.paths.ensure()

    # 桌面端开发期由 Vite/Tauri WebView 调本地 API，只放行本机来源。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:1420",
            "http://localhost:1420",
            "tauri://localhost",
            "http://tauri.localhost",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(settings.router)
    app.include_router(uploads.router)
    app.include_router(wiki.router)
    app.include_router(workspace.router)

    web_dir = __import__("pathlib").Path(__file__).resolve().parent / "web"
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=web_dir), name="static")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        """健康检查接口。"""

        return {"status": "ok", "workspace": str(app.state.paths.root.resolve())}

    @app.get("/")
    def index():
        """返回最小 Web UI。"""

        if not web_dir.exists():
            return {"status": "ok", "message": "LLM Wiki backend sidecar is running"}
        return FileResponse(web_dir / "index.html")

    return app


app = create_app()
