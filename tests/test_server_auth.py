import server.app as server_app


def test_requests_pass_through_when_no_api_key_configured(client):
    response = client.get("/classes", query_string={"instructor_id": "x"})
    assert response.status_code == 200


def test_missing_api_key_is_rejected_when_configured(client, monkeypatch):
    monkeypatch.setattr(server_app, "API_KEY", "secret")
    response = client.get("/classes", query_string={"instructor_id": "x"})
    assert response.status_code == 401


def test_wrong_api_key_is_rejected(client, monkeypatch):
    monkeypatch.setattr(server_app, "API_KEY", "secret")
    response = client.get(
        "/classes",
        query_string={"instructor_id": "x"},
        headers={"X-API-Key": "wrong"},
    )
    assert response.status_code == 401


def test_correct_api_key_is_accepted(client, monkeypatch):
    monkeypatch.setattr(server_app, "API_KEY", "secret")
    response = client.get(
        "/classes",
        query_string={"instructor_id": "x"},
        headers={"X-API-Key": "secret"},
    )
    assert response.status_code == 200


def test_health_endpoint_is_exempt_even_when_api_key_configured(client, monkeypatch):
    monkeypatch.setattr(server_app, "API_KEY", "secret")
    response = client.get("/health")
    assert response.status_code == 200
