from pydantic import BaseModel


class UploadResponse(BaseModel):
    """文件上传并解析后的响应。"""

    source_id: str
    filename: str
    status: str
    text_chars: int
