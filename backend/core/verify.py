import asyncio
import sys
import os
import json
from fastapi.testclient import TestClient

# Ensure the project root is on sys.path when run as a module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.main import app
from backend.database import SessionLocal, engine
from backend import models

client = TestClient(app)

def verify_crud():
    print("Verifying CRUD endpoints...")
    
    # Pre-clean test data if exists
    db = SessionLocal()
    db.query(models.HSTaxonomy).filter(models.HSTaxonomy.hs_code_prefix == "123456").delete()
    db.commit()
    db.close()

    # Create
    resp = client.post("/api/taxonomy", json={
        "hs_code_prefix": "123456",
        "dong_sp": "SP TEST",
        "industry_name": "Test Industry",
        "default_type": "NC"
    }, headers={"Authorization": "Bearer admin"})  # Mock token if needed, or bypass if not strictly enforced in test environment
    
    # Note: If auth is strict, we might need to mock auth dependency
    # Let's bypass auth for this test by overriding dependency
    from backend.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: models.User(id=1, username="test_admin", role="admin")
    
    resp = client.post("/api/taxonomy", json={
        "hs_code_prefix": "123456",
        "dong_sp": "SP TEST",
        "industry_name": "Test Industry",
        "default_type": "NC"
    })
    print(f"Create response: {resp.status_code}")
    assert resp.status_code == 200
    item_id = resp.json()["id"]

    # Read
    resp = client.get("/api/taxonomy")
    assert resp.status_code == 200
    data = resp.json()["taxonomy"]
    found = next((item for item in data if item["hs_code_prefix"] == "123456"), None)
    assert found is not None
    assert found["dong_sp"] == "SP TEST"

    # Update
    resp = client.put(f"/api/taxonomy/{item_id}", json={
        "dong_sp": "SP UPDATED",
        "industry_name": "Test Industry",
        "default_type": "NC"
    })
    assert resp.status_code == 200

    # Read again to verify update
    resp = client.get("/api/taxonomy")
    found = next((item for item in data if item["hs_code_prefix"] == "123456"), None)
    # Note: data was from previous request, need new request
    data = client.get("/api/taxonomy").json()["taxonomy"]
    found = next((item for item in data if item["hs_code_prefix"] == "123456"), None)
    assert found["dong_sp"] == "SP UPDATED"

    # Delete
    resp = client.delete(f"/api/taxonomy/{item_id}")
    assert resp.status_code == 200
    
    print("CRUD endpoints work perfectly!")

if __name__ == "__main__":
    verify_crud()
