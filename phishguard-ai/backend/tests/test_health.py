"""Tests for health and version endpoints."""

from __future__ import annotations


def test_health_returns_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data
    assert "environment" in data


def test_version_returns_info(client):
    resp = client.get("/api/version")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "PhishGuard AI"
    assert "version" in data
    assert "environment" in data
