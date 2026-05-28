from pydantic import BaseModel, Field


class WikiGenerateRequest(BaseModel):
    """根据已上传 source_id 生成 Wiki。"""

    source_id: str = Field(pattern=r"^[0-9a-f]{12}$")


class WikiPageResponse(BaseModel):
    """Wiki 页面列表项和生成结果。"""

    page_id: str
    title: str
    path: str


class WikiPageContentResponse(BaseModel):
    """Wiki Markdown 页面内容。"""

    page_id: str
    title: str
    markdown: str
