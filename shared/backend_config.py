"""Chooses which storage backend the GUI talks to (ROADMAP.md Phase 2):
the Flask/SQLite server over HTTP (ApiClient - the default, so behavior is
unchanged unless this is explicitly configured), or a local JSON/.xlsx
store with zero server process involved (LocalStorageClient). Mirrors
shared/hardware_config.py's file-based config pattern (#50).

This is also the one configurable point for ApiClient's base_url, which
used to be hardcoded in services/api_client.py.
"""

import json
from pathlib import Path

BACKEND_CONFIG_PATH = Path(__file__).resolve().parent.parent / ".backend_config.json"

DEFAULT_CONFIG = {
    "backend": "server",
    "base_url": "http://127.0.0.1:5000",
    "local_data_dir": "local_data",
}


def load_backend_config():
    if not BACKEND_CONFIG_PATH.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with open(BACKEND_CONFIG_PATH) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)
    config = dict(DEFAULT_CONFIG)
    config.update(data)
    return config


def save_backend_config(config):
    with open(BACKEND_CONFIG_PATH, "w") as f:
        json.dump(config, f)


def create_client():
    """Builds whichever client AccountManager/ClassManager should use by
    default, per the current config - the one place this decision is made,
    so callers just do AccountManager()/ClassManager() without knowing or
    caring which backend is active."""
    config = load_backend_config()
    if config["backend"] == "local":
        from services.local_storage_client import LocalStorageClient
        return LocalStorageClient(data_dir=config["local_data_dir"])
    from services.api_client import ApiClient
    return ApiClient(base_url=config["base_url"])
