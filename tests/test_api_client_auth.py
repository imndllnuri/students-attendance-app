"""Covers services/api_client.py: the API key, when set, is sent as an
X-API-Key header on every request; when unset, no header is added at all
(keeps default/local-dev behavior identical to before auth existed)."""

from services.api_client import ApiClient


class _FakeResponse:
    status_code = 200
    content = b"{}"

    def json(self):
        return {}


def test_api_key_is_sent_as_header_when_configured(monkeypatch):
    captured = {}

    def fake_request(method, url, timeout=5, **kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    monkeypatch.setattr("requests.request", fake_request)

    client = ApiClient(api_key="secret-token")
    client.check_health()

    assert captured["headers"]["X-API-Key"] == "secret-token"


def test_no_header_is_sent_when_api_key_is_unset(monkeypatch):
    captured = {}

    def fake_request(method, url, timeout=5, **kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    monkeypatch.setattr("requests.request", fake_request)

    client = ApiClient()
    client.check_health()

    assert "headers" not in captured
