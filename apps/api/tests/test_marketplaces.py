from fastapi.testclient import TestClient


def test_marketplaces_report_source_access_without_secret_values(client: TestClient, monkeypatch):
    monkeypatch.setenv("PARSER_MODE", "real")
    monkeypatch.delenv("PARSER_HTTP_PROXY", raising=False)
    monkeypatch.setenv("OZON_COOKIES", "session=secret-value")
    monkeypatch.delenv("WILDBERRIES_COOKIES", raising=False)
    monkeypatch.setenv("PARSER_BROWSER_FALLBACK", "true")

    response = client.get("/marketplaces")

    assert response.status_code == 200
    assert "secret-value" not in response.text
    payload = {item["id"]: item for item in response.json()}
    assert payload["ozon"]["accessConfigured"] is True
    assert payload["ozon"]["browserFallbackEnabled"] is True
    assert "cookie" not in payload["ozon"]["statusNote"].lower()
    assert payload["wildberries"]["accessConfigured"] is True


def test_marketplaces_do_not_treat_missing_ozon_storage_as_configured(client: TestClient, monkeypatch, tmp_path):
    monkeypatch.setenv("PARSER_MODE", "real")
    monkeypatch.delenv("PARSER_HTTP_PROXY", raising=False)
    monkeypatch.delenv("OZON_COOKIES", raising=False)
    monkeypatch.delenv("OZON_COOKIES_FILE", raising=False)
    monkeypatch.setenv("OZON_STORAGE_STATE_FILE", str(tmp_path / "missing-state.json"))
    monkeypatch.setenv("PARSER_BROWSER_FALLBACK", "true")

    response = client.get("/marketplaces")

    assert response.status_code == 200
    payload = {item["id"]: item for item in response.json()}
    assert payload["ozon"]["accessConfigured"] is False


def test_marketplaces_treat_ozon_external_provider_as_configured(client: TestClient, monkeypatch):
    monkeypatch.setenv("PARSER_MODE", "real")
    monkeypatch.delenv("PARSER_HTTP_PROXY", raising=False)
    monkeypatch.delenv("OZON_COOKIES", raising=False)
    monkeypatch.delenv("OZON_COOKIES_FILE", raising=False)
    monkeypatch.delenv("OZON_STORAGE_STATE_FILE", raising=False)
    monkeypatch.setenv("OZON_EXTERNAL_SEARCH_URL", "https://provider.example/search?q={query}")

    response = client.get("/marketplaces")

    assert response.status_code == 200
    payload = {item["id"]: item for item in response.json()}
    assert payload["ozon"]["accessConfigured"] is True
