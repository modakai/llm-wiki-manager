from pydantic import BaseModel, Field


class ModelConfigRequest(BaseModel):
    """保存 OpenAI 兼容模型配置的请求体。"""

    base_url: str
    api_key: str
    model: str
    temperature: float = Field(default=0.2, ge=0, le=2)
    timeout: int = Field(default=60, ge=1, le=600)


class ModelConfigResponse(BaseModel):
    """返回脱敏配置，避免 API Key 原文流回前端。"""

    base_url: str
    api_key: None = None
    api_key_masked: str
    model: str
    temperature: float
    timeout: int
    configured: bool
