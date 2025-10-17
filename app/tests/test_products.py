import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.main import app  # noqa: E402
from app.database import SessionLocal
from app.models import User


def make_admin(email: str):
    db: Session = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        if u:
            u.role = "admin"
            db.add(u)
            db.commit()
    finally:
        db.close()


def auth_headers(client: TestClient, email: str, password: str):
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_product_crud_and_list():
    with TestClient(app) as client:
        email = "admin@example.com"
        password = "pass12345"

        # Register and elevate
        r = client.post("/auth/register", json={"email": email, "full_name": "Admin", "password": password})
        assert r.status_code == 200, r.text
        make_admin(email)

        headers = auth_headers(client, email, password)

        # Create product
        prod = {
            "name": "Chicken Meal",
            "slug": "chicken-meal",
            "price": 9.99,
            "stock": 100,
            "species_tags": ["dog"],
            "subscription_available": True,
        }
        r = client.post("/products/", json=prod, headers=headers)
        assert r.status_code == 200, r.text
        created = r.json()
        assert created["slug"] == "chicken-meal"

        # List products
        r = client.get("/products/?species=dog&sort_by=price&order=asc&page=1&page_size=10")
        assert r.status_code == 200, r.text
        items = r.json()
        assert any(p["slug"] == "chicken-meal" for p in items)

        # Update product
        r = client.put(f"/products/{created['id']}", json={"stock": 90}, headers=headers)
        assert r.status_code == 200, r.text

        # Delete product
        r = client.delete(f"/products/{created['id']}", headers=headers)
        assert r.status_code == 200, r.text