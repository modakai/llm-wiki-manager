from pathlib import Path

import pytest

from app.core.paths import WorkspacePaths
from app.services.storage_service import save_upload_bytes
from app.services.wiki_service import WikiGenerationResult, write_wiki_page


def test_save_upload_bytes_uses_source_id_and_preserves_extension(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)

    saved = save_upload_bytes(paths, "AI 资料.pdf", b"pdf-bytes")

    assert saved.path.exists()
    assert saved.path.suffix == ".pdf"
    assert saved.path.read_bytes() == b"pdf-bytes"
    assert saved.source_id in saved.path.name


def test_write_wiki_page_writes_page_and_updates_index(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)
    result = WikiGenerationResult(
        title="LLM Wiki 基础",
        markdown="# LLM Wiki 基础\n\n## 摘要\n内容\n\n## 来源文件\n- source.pdf",
    )

    page = write_wiki_page(paths, result, source_filename="source.pdf")

    assert page.page_id == "llm-wiki"
    assert page.path.read_text(encoding="utf-8").startswith("# LLM Wiki 基础")
    assert "- [[LLM Wiki 基础]]" in paths.index_file.read_text(encoding="utf-8")


def test_write_wiki_page_rejects_missing_source_section(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)
    result = WikiGenerationResult(title="坏页面", markdown="# 坏页面\n\n没有来源")

    with pytest.raises(ValueError, match="来源文件"):
        write_wiki_page(paths, result, source_filename="source.pdf")
