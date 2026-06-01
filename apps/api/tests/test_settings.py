from fastapi.testclient import TestClient


def test_user_can_update_notification_settings(client: TestClient, auth_headers: dict[str, str]):
    response = client.put(
        "/settings",
        headers=auth_headers,
        json={"telegramChatId": "123456789", "telegramNotificationsEnabled": True},
    )
    assert response.status_code == 200
    assert response.json()["telegramChatId"] == "123456789"
    assert response.json()["telegramNotificationsEnabled"] is True

    me = client.get("/auth/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json()["telegramChatId"] == "123456789"

    test_response = client.post("/settings/test-telegram", headers=auth_headers)
    assert test_response.status_code == 200
    assert test_response.json()["sent"] is False
