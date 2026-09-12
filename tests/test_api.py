import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from main import app

client = TestClient(app)

def get_token():
    """Helper to get a valid JWT token for authenticated tests."""
    response = client.post("/token", data={"username": "admin", "password": "admin123"})
    return response.json()["access_token"]

def test_login_success():
    response = client.post("/token", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_failure():
    response = client.post("/token", data={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 401

def test_ingest_without_auth():
    response = client.post("/ingest", json={"@timestamp": "2026-09-09T20:00:00Z", "tenant": "demoA", "source": "test", "event_type": "test"})
    assert response.status_code == 401

def test_search_without_auth():
    response = client.get("/search")
    assert response.status_code == 401

def test_ingest_with_auth():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "@timestamp": "2026-09-09T20:00:00Z",
        "tenant": "demoA",
        "source": "pytest",
        "event_type": "TestEvent",
        "user": "admin",
        "src_ip": "127.0.0.1"
    }
    response = client.post("/ingest", json=payload, headers=headers)
    # 201 if OpenSearch is running, 500 if not.
    # We assert it's not 401 or 403 to prove AuthZ works.
    assert response.status_code in [201, 500]

def test_search_with_auth():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/search?tenant=demoA&timeRange=24h", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "total" in data
