"""Tests for screenshot scan endpoint (Section 3)."""

from __future__ import annotations

import io

from PIL import Image


def _make_png_bytes(width: int = 100, height: int = 100, color: str = "white") -> bytes:
    """Create a minimal valid PNG image in memory."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_jpeg_bytes(width: int = 100, height: int = 100) -> bytes:
    """Create a minimal valid JPEG image in memory."""
    img = Image.new("RGB", (width, height), "white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_screenshot_scan_valid_png(client):
    """Upload a valid PNG → should get a scan result."""
    png = _make_png_bytes()
    resp = client.post(
        "/api/scans/screenshot",
        files={"file": ("test.png", io.BytesIO(png), "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scan_type"] == "screenshot"
    assert data["prediction"] in ("safe", "suspicious", "phishing")
    assert 0 <= data["risk_score"] <= 100
    assert data["confidence"] is None
    assert isinstance(data["indicators"], list)
    assert data["model"]


def test_screenshot_scan_valid_jpeg(client):
    """Upload a valid JPEG → should get a scan result."""
    jpeg = _make_jpeg_bytes()
    resp = client.post(
        "/api/scans/screenshot",
        files={"file": ("test.jpg", io.BytesIO(jpeg), "image/jpeg")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scan_type"] == "screenshot"


def test_screenshot_scan_invalid_content_type(client):
    """Upload with unsupported content type → 422."""
    resp = client.post(
        "/api/scans/screenshot",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 422


def test_screenshot_scan_empty_file(client):
    """Upload an empty file → 422."""
    resp = client.post(
        "/api/scans/screenshot",
        files={"file": ("test.png", io.BytesIO(b""), "image/png")},
    )
    assert resp.status_code == 422


def test_screenshot_scan_corrupt_image(client):
    """Upload corrupt bytes as PNG → 422."""
    resp = client.post(
        "/api/scans/screenshot",
        files={"file": ("test.png", io.BytesIO(b"not-an-image"), "image/png")},
    )
    assert resp.status_code == 422


def test_screenshot_scan_no_file(client):
    """POST without file → 422."""
    resp = client.post("/api/scans/screenshot")
    assert resp.status_code == 422


def test_screenshot_scan_response_has_details(client):
    """Response should include details with OCR info."""
    png = _make_png_bytes()
    resp = client.post(
        "/api/scans/screenshot",
        files={"file": ("test.png", io.BytesIO(png), "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()
    if data.get("details"):
        assert "image_format" in data["details"]
        assert "image_size_bytes" in data["details"]

