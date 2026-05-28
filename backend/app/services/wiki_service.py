import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.core.paths import WorkspacePaths


@dataclass(frozen=True)
class WikiGenerationResult:
    """LLM 生成的 Wiki 内容。"""

    title: str
    markdown: str


@dataclass(frozen=True)
class WikiPage:
    """写入后的 Wiki 页面信息。"""

    page_id: str
    title: str
    path: Path


def write_wiki_page(
    paths: WorkspacePaths,
    result: WikiGenerationResult,
    source_filename: str,
) -> WikiPage:
    """校验并写入 Wiki 页面，同时维护 index.md。"""

    paths.ensure()
    _validate_markdown(result.markdown, source_filename)
    page_id = _slugify(result.title)
    page_path = paths.wiki_dir / f"{page_id}.md"
    _atomic_write(page_path, result.markdown)
    _update_index(paths, result.title, page_id, source_filename)
    return WikiPage(page_id=page_id, title=result.title, path=page_path)


def list_wiki_pages(paths: WorkspacePaths) -> list[WikiPage]:
    """列出 Wiki 页面，跳过首页索引。"""

    paths.ensure()
    pages: list[WikiPage] = []
    for path in sorted(paths.wiki_dir.glob("*.md")):
        if path.name == "index.md":
            continue
        title = _extract_title(path.read_text(encoding="utf-8")) or path.stem
        pages.append(WikiPage(page_id=path.stem, title=title, path=path))
    return pages


def build_wiki_prompt(source_filename: str, text: str, max_chars: int = 45000) -> tuple[str, str]:
    """组装 LLM Wiki 生成提示词，并对超长文档做明确截断。"""

    clipped = text[:max_chars]
    truncation_note = "\n\n注意：原文过长，以下内容已截断。" if len(text) > max_chars else ""
    system = (
        "你是严谨的 LLM Wiki 知识整理 Agent。"
        "只根据用户提供的原文生成 Markdown，不要编造没有来源的事实。"
    )
    user = f"""
请把下面资料整理为一页 LLM Wiki Markdown。

硬性结构：
# 页面标题
## 摘要
## 核心概念
## 知识卡片
## 待确认问题
## 来源文件
- {source_filename}

来源文件章节必须存在，且必须包含文件名：{source_filename}。
{truncation_note}

资料原文：
{clipped}
""".strip()
    return system, user


def parse_llm_markdown(markdown: str, fallback_title: str) -> WikiGenerationResult:
    """从 LLM Markdown 中提取标题，缺失时使用文件名兜底。"""

    title = _extract_title(markdown) or Path(fallback_title).stem
    return WikiGenerationResult(title=title.strip(), markdown=markdown.strip())


def _validate_markdown(markdown: str, source_filename: str) -> None:
    """确保模型输出具备 MVP 所需的来源追踪结构。"""

    if not markdown.strip().startswith("# "):
        raise ValueError("Wiki 页面必须以一级标题开头。")
    if "## 来源文件" not in markdown or source_filename not in markdown:
        raise ValueError("Wiki 页面必须包含来源文件章节和原始文件名。")


def _slugify(title: str) -> str:
    """生成适合文件名和 URL 使用的页面 ID。"""

    tokens = re.findall(r"[a-zA-Z0-9]+", title.lower())
    if not tokens:
        tokens = ["wiki", datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")]
    return "-".join(tokens[:6])


def _extract_title(markdown: str) -> str | None:
    """提取 Markdown 一级标题。"""

    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _atomic_write(path: Path, content: str) -> None:
    """使用临时文件替换，避免生成失败留下半成品。"""

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as tmp:
        tmp.write(content)
        temp_path = Path(tmp.name)
    temp_path.replace(path)


def _update_index(paths: WorkspacePaths, title: str, page_id: str, source_filename: str) -> None:
    """维护简单 Wiki 首页，确保页面和来源可追踪。"""

    lines = [
        "# LLM Wiki 首页",
        "",
        "## 页面列表",
        "",
    ]
    existing = {
        page.page_id: page
        for page in list_wiki_pages(paths)
    }
    existing[page_id] = WikiPage(page_id=page_id, title=title, path=paths.wiki_dir / f"{page_id}.md")
    for page in sorted(existing.values(), key=lambda item: item.title):
        lines.append(f"- [[{page.title}]] (`{page.page_id}`) - 来源：{source_filename if page.page_id == page_id else '见页面'}")
    lines.append("")
    lines.append(f"最近更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    _atomic_write(paths.index_file, "\n".join(lines) + "\n")
