"""API smoke tests with authentication.

Run:  pytest tests/test_api.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, SessionLocal
from backend import models
from backend.auth import hash_password


client = TestClient(app)


def _ensure_test_user():
    """Make sure a test user exists so /me works."""
    db = SessionLocal()
    try:
        if not db.query(models.User).filter(models.User.username == "testadmin").first():
            db.add(models.User(
                username="testadmin",
                email="[email protected]",
                full_name="Test Admin",
                hashed_password=hash_password("Test@1234"),
                role="admin",
                is_active=1,
            ))
            db.commit()
    finally:
        db.close()


def setup_module(module):
    init_db()
    _ensure_test_user()


def _login():
    r = client.post("/api/v1/auth/login", data={
        "username": "testadmin", "password": "Test@1234",
    })
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["app"] == "Retail Demand Forecasting System"


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_and_me():
    tok = _login()
    r = client.get("/api/v1/auth/me", headers=_h(tok))
    assert r.status_code == 200
    assert r.json()["username"] == "testadmin"


def test_list_products_requires_auth():
    # No token → 401
    r = client.get("/api/v1/products")
    assert r.status_code == 401


def test_list_products_with_auth():
    tok = _login()
    r = client.get("/api/v1/products", headers=_h(tok))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_and_delete_product():
    tok = _login()
    payload = {
        "sku": "TEST-SKU-001",
        "name": "Test Product",
        "category": "Test",
        "unit_cost": 10,
        "unit_price": 20,
        "lead_time_days": 3,
    }
    r = client.post("/api/v1/products", json=payload, headers=_h(tok))
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    r = client.delete(f"/api/v1/products/{pid}", headers=_h(tok))
    assert r.status_code == 200


def test_forecast_models_endpoint():
    tok = _login()
    r = client.get("/api/v1/forecast/models", headers=_h(tok))
    assert r.status_code == 200
    names = {m["name"] for m in r.json()["models"]}
    assert names == {"prophet", "xgboost", "lstm"}


def test_inventory_list():
    tok = _login()
    r = client.get("/api/v1/inventory", headers=_h(tok))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_dashboard_summary():
    tok = _login()
    r = client.get("/api/v1/dashboard/summary", headers=_h(tok))
    assert r.status_code == 200
    data = r.json()
    assert "total_products" in data
    assert "total_revenue" in data
