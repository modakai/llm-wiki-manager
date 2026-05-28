from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class WorkspacePaths:
    """集中管理本地知识库目录，避免业务代码到处手写路径。"""

    root: Path

    @property
    def raw_dir(self) -> Path:
        return self.root / "raw"

    @property
    def parsed_dir(self) -> Path:
        return self.root / "parsed"

    @property
    def wiki_dir(self) -> Path:
        return self.root / "wiki"

    @property
    def app_dir(self) -> Path:
        return self.root / ".app"

    @property
    def config_file(self) -> Path:
        return self.app_dir / "config.json"

    @property
    def index_file(self) -> Path:
        return self.wiki_dir / "index.md"

    def ensure(self) -> None:
        """创建 MVP 所需的固定目录，并初始化 Wiki 首页。"""

        for directory in (self.raw_dir, self.parsed_dir, self.wiki_dir, self.app_dir):
            directory.mkdir(parents=True, exist_ok=True)
        if not self.index_file.exists():
            self.index_file.write_text("# LLM Wiki 首页\n\n暂无页面。\n", encoding="utf-8")


def default_workspace() -> WorkspacePaths:
    """返回仓库内默认 workspace，便于本地开发直接启动。"""

    if workspace_root := os.getenv("LLM_WIKI_WORKSPACE"):
        return WorkspacePaths(Path(workspace_root))
    backend_dir = Path(__file__).resolve().parents[3]
    return WorkspacePaths(backend_dir.parent / "workspace")
