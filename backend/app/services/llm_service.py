from typing import Any

import httpx

from app.core.config import ModelConfig, mask_secret


class LLMError(RuntimeError):
    """模型调用失败，错误信息必须经过脱敏。"""


class OpenAICompatibleClient:
    """最小 OpenAI 兼容 Chat Completions 客户端。"""

    def __init__(
        self,
        config: ModelConfig,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.config = config
        self.transport = transport

    async def chat_completion(self, system_prompt: str, user_prompt: str) -> str:
        """调用 `/chat/completions` 并返回 assistant 文本。"""

        if not self.config.api_key or not self.config.model:
            raise LLMError("模型配置不完整，请先填写 API Key 和模型名。")

        base_url = self.config.base_url.rstrip("/")
        payload: dict[str, Any] = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {self.config.api_key}"}

        try:
            async with httpx.AsyncClient(
                base_url=base_url,
                timeout=self.config.timeout,
                transport=self.transport,
            ) as client:
                response = await client.post("/chat/completions", json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise LLMError(_sanitize(f"模型网络请求失败：{exc}", self.config.api_key)) from exc

        if response.status_code >= 400:
            raise LLMError(_sanitize(f"模型服务返回错误：HTTP {response.status_code} {response.text}", self.config.api_key))

        try:
            data = response.json()
        except ValueError as exc:
            raise LLMError("模型返回格式异常，响应不是 JSON。") from exc
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("模型返回格式异常，未找到 choices[0].message.content。") from exc
        if not str(content).strip():
            raise LLMError("模型返回空内容。")
        return str(content)


def _sanitize(message: str, api_key: str) -> str:
    """过滤错误消息里的密钥原文。"""

    if api_key:
        message = message.replace(api_key, mask_secret(api_key))
    return message
