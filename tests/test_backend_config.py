"""Covers shared/backend_config.py: the config file drives which storage
backend AccountManager()/ClassManager() get by default."""

from services.api_client import ApiClient
from services.local_storage_client import LocalStorageClient
from shared.backend_config import create_client, load_backend_config, save_backend_config


def test_defaults_to_the_server_backend_when_unconfigured(monkeypatch, tmp_path):
    monkeypatch.setattr("shared.backend_config.BACKEND_CONFIG_PATH", tmp_path / "missing.json")

    config = load_backend_config()

    assert config["backend"] == "server"
    assert isinstance(create_client(), ApiClient)


def test_configuring_local_backend_returns_a_local_storage_client(monkeypatch, tmp_path):
    config_path = tmp_path / ".backend_config.json"
    monkeypatch.setattr("shared.backend_config.BACKEND_CONFIG_PATH", config_path)
    save_backend_config({"backend": "local", "local_data_dir": str(tmp_path / "local_data")})

    client = create_client()

    assert isinstance(client, LocalStorageClient)
    assert client.data_dir == tmp_path / "local_data"


def test_configured_base_url_is_passed_to_api_client(monkeypatch, tmp_path):
    monkeypatch.setattr("shared.backend_config.BACKEND_CONFIG_PATH", tmp_path / ".backend_config.json")
    save_backend_config({"backend": "server", "base_url": "http://192.168.1.50:5000"})

    client = create_client()

    assert isinstance(client, ApiClient)
    assert client.base_url == "http://192.168.1.50:5000"


def test_configured_api_key_is_passed_to_api_client(monkeypatch, tmp_path):
    monkeypatch.setattr("shared.backend_config.BACKEND_CONFIG_PATH", tmp_path / ".backend_config.json")
    save_backend_config({"backend": "server", "api_key": "secret-token"})

    client = create_client()

    assert isinstance(client, ApiClient)
    assert client.api_key == "secret-token"


def test_a_corrupt_config_file_falls_back_to_defaults(monkeypatch, tmp_path):
    config_path = tmp_path / ".backend_config.json"
    config_path.write_text("{not valid json")
    monkeypatch.setattr("shared.backend_config.BACKEND_CONFIG_PATH", config_path)

    config = load_backend_config()

    assert config["backend"] == "server"
    assert config["base_url"] == "http://127.0.0.1:5000"
