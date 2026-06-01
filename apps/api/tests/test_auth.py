from fastapi.testclient import TestClient


def test_register_login_and_me(client: TestClient):
    register_response = client.post(
        "/auth/register",
        json={"email": "buyer@appsparcer.test", "password": "password123"},
    )
    assert register_response.status_code == 200
    assert register_response.json()["user"]["email"] == "buyer@appsparcer.test"

    login_response = client.post(
        "/auth/login",
        json={"email": "buyer@appsparcer.test", "password": "password123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["accessToken"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "buyer@appsparcer.test"
