import json

from pydantic import BaseModel, Field

from app.core.paths import WorkspacePaths
from app.core.secrets import protect_secret, unprotect_secret


class ModelConfig(BaseModel):
    """OpenAI 兼容模型配置；MVP 阶段保存在本地配置文件。"""

    base_url: str = Field(default="https://api.openai.com/v1")
    api_key: str = Field(default="")
    model: str = Field(default="")
    temperature: float = Field(default=0.2, ge=0, le=2)
    timeout: int = Field(default=60, ge=1, le=600)


def mask_secret(secret: str) -> str:
    """对密钥做脱敏展示，避免前端和日志暴露完整 API Key。"""

    if not secret:
        return ""
    if len(secret) <= 8:
        return "***"
    return f"{secret[:3]}***{secret[-4:]}"


def save_model_config(paths: WorkspacePaths, config: ModelConfig) -> None:
    """保存模型配置；后续桌面端应替换为系统凭据管理。"""

    paths.ensure()
    data = config.model_dump()
    api_key = data.pop("api_key", "")
    data["api_key_protected"] = protect_secret(api_key)
    paths.config_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_model_config(paths: WorkspacePaths) -> ModelConfig:
    """读取模型配置；没有配置时返回空配置。"""

    paths.ensure()
    if not paths.config_file.exists():
        return ModelConfig()
    data = json.loads(paths.config_file.read_text(encoding="utf-8"))
    if "api_key_protected" in data:
        data["api_key"] = unprotect_secret(data.pop("api_key_protected"))
        return ModelConfig.model_validate(data)

    config = ModelConfig.model_validate(data)
    if config.api_key:
        # 兼容早期 MVP 明文配置，读取成功后立即迁移为受保护密文。
        save_model_config(paths, config)
    return config
