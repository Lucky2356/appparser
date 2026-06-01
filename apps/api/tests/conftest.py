import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


TEST_DB_PATH = Path(__file__).parent / ".test_appsparcer.sqlite3"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["REDIS_URL"] = "redis://127.0.0.1:6390/0"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["CORS_ORIGINS"] = "http://testserver"
os.environ["PARSER_MODE"] = "mock"

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client: TestClient):
    response = client.post(
        "/auth/register",
        json={"email": "user@appsparcer.test", "password": "password123"},
    )
    assert response.status_code == 200
    token = response.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}
