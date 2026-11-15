"""Tests for statistics and scans endpoints."""

from __future__ import annotations

import pytest
from app.db.database import SessionLocal
from app.db.models import ScanRecord


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    db.query(ScanRecord).delete()
    db.commit()
    db.close()
    yield
    db = SessionLocal()
    db.query(ScanRecord).delete()
    db.commit()
    db.close()


def test_statistics_returns_valid_structure(client):
    resp = client.get("/api/statistics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_scans"] == 0
    assert data["high_risk"] == 0
    assert data["suspicious"] == 0
    assert data["safe"] == 0
    # models_available depends on how many models registered as available
    assert isinstance(data["models_available"], int)
    assert isinstance(data["risk_distribution"], list)


def test_scans_returns_empty(client):
    resp = client.get("/api/scans")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scans"] == []
    assert data["total"] == 0


def test_unknown_route_returns_404(client):
    resp = client.get("/api/nonexistent")
    assert resp.status_code == 404
