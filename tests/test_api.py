import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from main import app

client = TestClient(app)

def test_login_success():
    response = client.post("/token", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_failure():
    response = client.post("/token", data={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 401

def test_ingest_without_auth():
    response = client.post("/ingest", json={"tenant": "demoA", "source": "test", "event_type": "test"})
    assert response.status_code == 401

def test_search_without_auth():
    response = client.get("/search")
    assert response.status_code == 401
