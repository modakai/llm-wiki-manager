from pathlib import Path

import pytest

from app.services.parser_service import ParserError, parse_document


def test_parse_txt_file_reads_plain_text(tmp_path: Path) -> None:
    source = tmp_path / "note.txt"
    source.write_text("第一段知识\n第二段知识", encoding="utf-8")

    parsed = parse_document(source)

    assert parsed.text == "第一段知识\n第二段知识"
    assert parsed.source_type == "txt"


def test_parse_markdown_file_keeps_markdown_text(tmp_path: Path) -> None:
    source = tmp_path / "note.md"
    source.write_text("# 标题\n\n- 要点", encoding="utf-8")

    parsed = parse_document(source)

    assert "# 标题" in parsed.text
    assert parsed.source_type == "md"


def test_parse_pdf_file_extracts_text(tmp_path: Path) -> None:
    import fitz

    source = tmp_path / "paper.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "PDF knowledge text")
    document.save(source)
    document.close()

    parsed = parse_document(source)

    assert "PDF knowledge text" in parsed.text
    assert parsed.source_type == "pdf"


def test_parse_docx_file_extracts_paragraph_text(tmp_path: Path) -> None:
    from docx import Document

    source = tmp_path / "paper.docx"
    document = Document()
    document.add_paragraph("DOCX knowledge text")
    document.save(source)

    parsed = parse_document(source)

    assert "DOCX knowledge text" in parsed.text
    assert parsed.source_type == "docx"


def test_parse_doc_file_returns_clear_error(tmp_path: Path) -> None:
    source = tmp_path / "legacy.doc"
    source.write_bytes(b"legacy")

    with pytest.raises(ParserError, match="LibreOffice"):
        parse_document(source)


def test_parse_empty_text_file_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "empty.txt"
    source.write_text("   ", encoding="utf-8")

    with pytest.raises(ParserError, match="没有提取到有效文本"):
        parse_document(source)
