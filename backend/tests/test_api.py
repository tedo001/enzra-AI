"""API smoke tests via FastAPI TestClient."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "RailVision AI"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "detector_backend" in body


def test_analytics_daily(client):
    r = client.get("/api/analytics/daily")
    assert r.status_code == 200
    assert "obstacle_frequency" in r.json()
