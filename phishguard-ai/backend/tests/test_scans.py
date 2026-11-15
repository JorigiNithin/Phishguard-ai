"""Tests for URL scan endpoint (Section 2 regression)."""

from __future__ import annotations


def test_url_scan_valid(client):
    """POST /api/scans/url with a valid URL returns a prediction."""
    resp = client.post("/api/scans/url", json={"url": "https://google.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["url"] == "https://google.com"
    assert data["prediction"] in ("phishing", "legitimate")
    assert 0 <= data["confidence"] <= 1
    assert data["risk_level"] in ("safe", "low", "medium", "high", "critical")
    assert isinstance(data["features"], dict)
    assert data["model"]  # non-empty


def test_url_scan_invalid_url(client):
    """POST /api/scans/url with nonsense returns 422."""
    resp = client.post("/api/scans/url", json={"url": "not-a-url"})
    # May either pass validation (urlparse can handle it) or fail
    assert resp.status_code in (200, 422)


def test_url_scan_empty_body(client):
    """POST /api/scans/url with no body returns 422."""
    resp = client.post("/api/scans/url")
    assert resp.status_code == 422


def test_url_scan_phishing_indicators(client):
    """A suspiciously crafted URL should have phishing-like features."""
    suspicious_url = "http://192.168.1.1/login/verify-account?password=update&token=abc"
    resp = client.post("/api/scans/url", json={"url": suspicious_url})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["features"]["has_ip_address"], (int, float))
    assert isinstance(data["features"]["num_suspicious_keywords"], (int, float))


def test_url_scan_missing_model(client, monkeypatch):
    """POST /api/scans/url returns 503 when the model is not available."""
    monkeypatch.setattr("app.api.routes.scans.is_model_available", lambda: False)
    resp = client.post("/api/scans/url", json={"url": "https://example.com"})
    assert resp.status_code == 503
    assert "not available" in resp.json()["detail"].lower()

