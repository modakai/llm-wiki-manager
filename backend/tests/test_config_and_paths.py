from pathlib import Path

from app.core.config import ModelConfig, load_model_config, mask_secret, save_model_config
from app.core.paths import WorkspacePaths


def test_workspace_paths_create_expected_directories(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)

    paths.ensure()

    assert paths.raw_dir.is_dir()
    assert paths.parsed_dir.is_dir()
    assert paths.wiki_dir.is_dir()
    assert paths.app_dir.is_dir()


def test_model_config_is_saved_and_loaded_with_secret_masking(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)
    config = ModelConfig(
        base_url="https://api.deepseek.com/v1",
        api_key="sk-test-secret",
        model="deepseek-chat",
        temperature=0.2,
        timeout=30,
    )

    save_model_config(paths, config)
    loaded = load_model_config(paths)

    assert loaded == config
    assert mask_secret(loaded.api_key) == "sk-***cret"
    assert "sk-test-secret" not in paths.config_file.read_text(encoding="utf-8")


def test_legacy_plaintext_config_is_migrated_to_protected_secret(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)
    paths.ensure()
    paths.config_file.write_text(
        """
        {
          "base_url": "https://api.deepseek.com/v1",
          "api_key": "sk-legacy-secret",
          "model": "deepseek-chat",
          "temperature": 0.2,
          "timeout": 30
        }
        """,
        encoding="utf-8",
    )

    loaded = load_model_config(paths)

    assert loaded.api_key == "sk-legacy-secret"
    assert "sk-legacy-secret" not in paths.config_file.read_text(encoding="utf-8")
