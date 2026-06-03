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
