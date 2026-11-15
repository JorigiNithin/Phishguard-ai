"""Tests for models endpoint — updated for Sections 2 and 3."""

from __future__ import annotations


def test_models_returns_four(client):
    resp = client.get("/api/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 4
    assert len(data["models"]) == 4


def test_models_have_expected_ids(client):
    resp = client.get("/api/models")
    ids = {m["id"] for m in resp.json()["models"]}
    assert ids == {"url_detector", "email_detector", "screenshot_detector", "html_detector"}


def test_url_detector_is_trained(client):
    """URL detector should be marked as trained and available (Section 2)."""
    resp = client.get("/api/models")
    models = {m["id"]: m for m in resp.json()["models"]}
    url = models["url_detector"]
    assert url["status"] == "trained"
    assert url["available"] is True
    assert url["model_type"] == "Random Forest"


def test_section3_detectors_are_implemented(client):
    """Email, screenshot, and HTML detectors should be implemented (Section 3)."""
    resp = client.get("/api/models")
    models = {m["id"]: m for m in resp.json()["models"]}

    for det_id in ("email_detector", "screenshot_detector", "html_detector"):
        det = models[det_id]
        assert det["status"] == "implemented", f"{det_id} status should be 'implemented'"
        assert det["available"] is True, f"{det_id} should be available"
        assert det["model_type"] is not None, f"{det_id} should have a model_type"
