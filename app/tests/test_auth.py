import os
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.main import app  # noqa: E402


def test_register_and_login_and_me():
    with TestClient(app) as client:
        email = "testuser@example.com"
        payload = {"email": email, "full_name": "Test User", "password": "pass12345"}
        r = client.post("/auth/register", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["email"] == email

        r = client.post("/auth/login", json={"email": email, "password": "pass12345"})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]

        r = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        me = r.json()
        assert me["email"] == email