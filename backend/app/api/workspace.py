from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


@router.get("")
def get_workspace(request: Request) -> dict:
    """返回当前 workspace 路径和子目录信息。"""

    paths = request.app.state.paths
    return {
        "path": str(paths.root.resolve()),
        "directories": {
            "raw": str(paths.raw_dir.resolve()),
            "parsed": str(paths.parsed_dir.resolve()),
            "wiki": str(paths.wiki_dir.resolve()),
        },
    }
