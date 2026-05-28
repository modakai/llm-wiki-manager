from pathlib import Path

from fastapi.testclient import TestClient

from app.core.paths import WorkspacePaths
from app.main import create_app


def test_settings_api_masks_saved_key(tmp_path: Path) -> None:
    client = TestClient(create_app(WorkspacePaths(tmp_path)))

    response = client.post(
        "/api/settings/model",
        json={
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-test-secret",
            "model": "deepseek-chat",
            "temperature": 0.2,
            "timeout": 30,
        },
    )

    assert response.status_code == 200
    assert response.json()["api_key_masked"] == "sk-***cret"
    assert response.json()["api_key"] is None


def test_upload_api_saves_raw_and_parsed_text(tmp_path: Path) -> None:
    client = TestClient(create_app(WorkspacePaths(tmp_path)))

    response = client.post(
        "/api/uploads",
        files={"file": ("note.txt", b"LLM Wiki text", "text/plain")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "parsed"
    assert payload["text_chars"] == len("LLM Wiki text")


def test_generate_wiki_api_uses_mocked_llm(tmp_path: Path, monkeypatch) -> None:
    async def fake_chat_completion(self, system_prompt: str, user_prompt: str) -> str:
        return "# LLM Wiki 测试\n\n## 摘要\n测试\n\n## 来源文件\n- note.txt"

    monkeypatch.setattr(
        "app.services.llm_service.OpenAICompatibleClient.chat_completion",
        fake_chat_completion,
    )
    client = TestClient(create_app(WorkspacePaths(tmp_path)))
    client.post(
        "/api/settings/model",
        json={
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-test-secret",
            "model": "deepseek-chat",
            "temperature": 0.2,
            "timeout": 30,
        },
    )
    upload = client.post(
        "/api/uploads",
        files={"file": ("note.txt", b"LLM Wiki text", "text/plain")},
    ).json()

    response = client.post("/api/wiki/generate", json={"source_id": upload["source_id"]})

    assert response.status_code == 200
    assert response.json()["page_id"] == "llm-wiki"
    assert "LLM Wiki 测试" in client.get("/api/wiki/pages/llm-wiki").json()["markdown"]


def test_generate_wiki_api_rejects_invalid_source_id(tmp_path: Path) -> None:
    client = TestClient(create_app(WorkspacePaths(tmp_path)))

    response = client.post("/api/wiki/generate", json={"source_id": "../evil"})

    assert response.status_code == 422
