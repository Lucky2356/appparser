from fastapi.testclient import TestClient


def test_image_proxy_rejects_untrusted_hosts(client: TestClient):
    response = client.get("/images/proxy", params={"url": "https://example.org/image.webp"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Image host is not allowed"
