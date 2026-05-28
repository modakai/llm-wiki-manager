import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.core.paths import WorkspacePaths


@dataclass(frozen=True)
class SavedUpload:
    """上传文件落盘后的标识。"""

    source_id: str
    filename: str
    path: Path


def save_upload_bytes(paths: WorkspacePaths, filename: str, content: bytes) -> SavedUpload:
    """保存上传文件，用 source_id 防止同名文件互相覆盖。"""

    paths.ensure()
    safe_name = _safe_filename(filename)
    suffix = Path(safe_name).suffix.lower()
    source_id = uuid.uuid4().hex[:12]
    stored_name = f"{source_id}_{Path(safe_name).stem}{suffix}"
    target = paths.raw_dir / stored_name
    target.write_bytes(content)
    return SavedUpload(source_id=source_id, filename=safe_name, path=target)


def save_parsed_text(paths: WorkspacePaths, source_id: str, text: str) -> Path:
    """保存解析文本，方便后续重新生成 Wiki。"""

    paths.ensure()
    target = paths.parsed_dir / f"{source_id}.txt"
    target.write_text(text, encoding="utf-8")
    return target


def _safe_filename(filename: str) -> str:
    """清理文件名中的路径分隔符和控制字符。"""

    name = Path(filename).name.strip() or "upload"
    return re.sub(r"[^\w\u4e00-\u9fff.\- ]+", "_", name)
