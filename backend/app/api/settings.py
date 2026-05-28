from fastapi import APIRouter, Request

from app.core.config import ModelConfig, load_model_config, mask_secret, save_model_config
from app.schemas.settings import ModelConfigRequest, ModelConfigResponse

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/model", response_model=ModelConfigResponse)
def get_model_config(request: Request) -> ModelConfigResponse:
    """读取脱敏后的模型配置。"""

    config = load_model_config(request.app.state.paths)
    return _to_response(config)


@router.post("/model", response_model=ModelConfigResponse)
def update_model_config(payload: ModelConfigRequest, request: Request) -> ModelConfigResponse:
    """保存模型配置；MVP 只保存本地文件，不接 Supabase。"""

    config = ModelConfig(**payload.model_dump())
    save_model_config(request.app.state.paths, config)
    return _to_response(config)


def _to_response(config: ModelConfig) -> ModelConfigResponse:
    """统一配置响应，确保不返回 API Key 原文。"""

    return ModelConfigResponse(
        base_url=config.base_url,
        api_key_masked=mask_secret(config.api_key),
        model=config.model,
        temperature=config.temperature,
        timeout=config.timeout,
        configured=bool(config.api_key and config.model),
    )
