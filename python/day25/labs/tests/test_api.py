"""API tests for ops_api."""
from __future__ import annotations

from fastapi.testclient import TestClient

from ops_api import create_app

client = TestClient(create_app())
AUTH = {"Authorization": "Bearer handbook-lab"}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_list_hosts():
    response = client.get("/api/v1/hosts")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_deploy_requires_auth():
    response = client.post(
        "/api/v1/deploys",
        json={"name": "web", "env": "staging", "replicas": 2, "image": "nginx:1.27"},
    )
    assert response.status_code == 401


def test_create_deploy():
    response = client.post(
        "/api/v1/deploys",
        json={"name": "web", "env": "staging", "replicas": 2, "image": "nginx:1.27"},
        headers=AUTH,
    )
    assert response.status_code == 202
    deploy_id = response.json()["id"]
    detail = client.get(f"/api/v1/deploys/{deploy_id}")
    assert detail.status_code == 200
