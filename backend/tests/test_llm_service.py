import httpx
import pytest

from app.core.config import ModelConfig
from app.services.llm_service import LLMError, OpenAICompatibleClient


@pytest.mark.asyncio
async def test_chat_completion_returns_content_from_openai_compatible_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer sk-test"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "# Wiki\n\n## 来源文件\n- a.pdf"}}]},
        )

    client = OpenAICompatibleClient(
        ModelConfig(base_url="https://api.example.com/v1", api_key="sk-test", model="x"),
        transport=httpx.MockTransport(handler),
    )

    content = await client.chat_completion("system", "user")

    assert content.startswith("# Wiki")


@pytest.mark.asyncio
async def test_chat_completion_raises_sanitized_error_on_auth_failure() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "bad key sk-test"}})

    client = OpenAICompatibleClient(
        ModelConfig(base_url="https://api.example.com/v1", api_key="sk-test", model="x"),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(LLMError) as exc_info:
        await client.chat_completion("system", "user")

    assert "sk-test" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_chat_completion_raises_llm_error_on_non_json_response() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>bad gateway</html>")

    client = OpenAICompatibleClient(
        ModelConfig(base_url="https://api.example.com/v1", api_key="sk-test", model="x"),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(LLMError, match="模型返回格式异常"):
        await client.chat_completion("system", "user")
