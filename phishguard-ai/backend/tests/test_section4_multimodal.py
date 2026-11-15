"""Regression tests for Section 4: multimodal fusion, explainability, and history."""

from __future__ import annotations

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.db.database import SessionLocal
from app.db.models import ScanRecord
from app.services.fusion import fuse_modalities
from app.services.scan_history import save_scan


@pytest.fixture(autouse=True)
def clear_scan_history():
    db = SessionLocal()
    db.query(ScanRecord).delete()
    db.commit()
    db.close()
    yield
    db = SessionLocal()
    db.query(ScanRecord).delete()
    db.commit()
    db.close()


def test_multimodal_fusion_calculates_weighted_risk(client: TestClient):
    resp = client.post(
        "/api/scans/multimodal",
        json={
            "url": "https://paypal.com/verify-account",
            "email": {
                "sender": "alerts@paypal.com",
                "subject": "Urgent verification required",
                "body": "Act now and verify your password immediately.",
                "headers": {"x-test": "1"},
            },
            "html": "<form action='https://evil.example/login'><input type='password'/></form>",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["overall_prediction"] in {"phishing", "suspicious"}
    assert 0 <= data["overall_risk_score"] <= 100
    assert set(data["modalities_analyzed"]) >= {"url", "email", "html"}
    assert data["contributing_indicators"]
    assert data["explanation"]


def test_missing_modalities_are_logged_but_not_treated_as_safe(client: TestClient):
    resp = client.post(
        "/api/scans/multimodal",
        json={
            "email": {
                "sender": "security@bank.com",
                "subject": "Verify your password",
                "body": "Login now to update your password.",
            }
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["modalities_analyzed"] == ["email"]
    assert any("Missing modalities" in item or "Missing data is excluded" in item for item in data["explanation"])
    assert data["overall_prediction"] in {"suspicious", "phishing", "safe"}


def test_duplicate_indicators_are_deduplicated():
    result = fuse_modalities(
        {
            "email": {
                "risk_score": 70,
                "prediction": "phishing",
                "indicators": [
                    {"name": "credential_request", "description": "Request credentials", "severity": "high"},
                    {"name": "credential_request", "description": "Request credentials", "severity": "high"},
                ],
            },
            "html": {
                "risk_score": 65,
                "prediction": "phishing",
                "indicators": [
                    {"name": "credential_request", "description": "Request credentials", "severity": "high"},
                ],
            },
        }
    )
    names = [item["name"] for item in result["contributing_indicators"]]
    assert names.count("credential_request") == 1


def test_history_filters_and_pagination(client: TestClient):
    db = SessionLocal()
    save_scan(
        db,
        scan_type="multimodal",
        prediction="phishing",
        risk_score=90,
        target_summary="High-risk login",
        indicators=[{"name": "credential_request", "description": "Request credentials", "severity": "high"}],
        explanation=["High-risk login"],
    )
    save_scan(
        db,
        scan_type="multimodal",
        prediction="safe",
        risk_score=12,
        target_summary="Low-risk login",
        indicators=[],
        explanation=["No issue"],
    )
    db.close()

    resp = client.get("/api/scans/history?page=1&page_size=1&prediction=phishing")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["scans"]) == 1
    assert data["scans"][0]["prediction"] == "phishing"


def test_scan_detail_and_deletion(client: TestClient):
    db = SessionLocal()
    record = save_scan(
        db,
        scan_type="url",
        prediction="safe",
        risk_score=12,
        target_summary="https://example.com",
        indicators=[],
        explanation=["Safe URL"],
    )
    db.close()

    detail = client.get(f"/api/scans/{record.id}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["id"] == record.id

    deleted = client.delete(f"/api/scans/{record.id}")
    assert deleted.status_code == 200, deleted.text

    missing = client.get(f"/api/scans/{record.id}")
    assert missing.status_code == 404


def test_dashboard_statistics_match_persisted_records(client: TestClient):
    db = SessionLocal()
    save_scan(db, scan_type="multimodal", prediction="phishing", risk_score=85, target_summary="malicious")
    save_scan(db, scan_type="url", prediction="safe", risk_score=5, target_summary="good")
    save_scan(db, scan_type="email", prediction="suspicious", risk_score=35, target_summary="maybe")
    db.close()

    resp = client.get("/api/dashboard/statistics")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_scans"] == 3
    assert data["high_risk"] >= 1
    assert data["safe"] >= 1
    assert data["suspicious"] >= 1
    assert data["modality_usage"]


def test_individual_detector_scans_are_persisted_without_raw_inputs(client: TestClient):
    url = "https://example.com/account?secret=url-secret-marker"
    email_body = "Please review this harmless test message: email-secret-marker"
    html_source = "<html><body>html-secret-marker</body></html>"

    url_response = client.post("/api/scans/url", json={"url": url})
    email_response = client.post(
        "/api/scans/email",
        json={
            "sender": "sender@example.com",
            "subject": "Test message",
            "body": email_body,
        },
    )
    image = BytesIO()
    Image.new("RGB", (1, 1), color="white").save(image, format="PNG")
    screenshot_response = client.post(
        "/api/scans/screenshot",
        files={"file": ("test.png", image.getvalue(), "image/png")},
    )
    html_response = client.post("/api/scans/html", json={"html": html_source})

    responses = [url_response, email_response, screenshot_response, html_response]
    assert all(response.status_code == 200 for response in responses), [
        response.text for response in responses
    ]
    assert all(response.json()["scan_id"] for response in responses)

    history = client.get("/api/scans/history?page_size=10")
    assert history.status_code == 200
    assert history.json()["total"] == 4
    assert {scan["scan_type"] for scan in history.json()["scans"]} == {
        "url",
        "email",
        "screenshot",
        "html",
    }

    for response in responses:
        detail = client.get(f"/api/scans/{response.json()['scan_id']}")
        assert detail.status_code == 200
        serialized = detail.text
        assert "url-secret-marker" not in serialized
        assert "email-secret-marker" not in serialized
        assert "html-secret-marker" not in serialized
        assert "example.com/account" not in serialized


def test_explain_endpoint_returns_structured_explanations(client: TestClient):
    resp = client.post(
        "/api/scans/multimodal",
        json={
            "url": "https://paypal.com/verify-account",
            "html": "<form action='http://192.168.1.1/login'><input type='password'/></form>",
        },
    )
    assert resp.status_code == 200, resp.text
    scan_id = resp.json()["scan_id"]

    explain_resp = client.get(f"/api/scans/{scan_id}/explain")
    assert explain_resp.status_code == 200, explain_resp.text
    data = explain_resp.json()
    assert "explanation" in data
    assert len(data["explanation"]) > 0
    first_item = data["explanation"][0]
    assert "indicator" in first_item
    assert "source" in first_item
    assert "impact" in first_item
    assert "reason" in first_item


def test_explain_endpoint_404_for_missing_scan(client: TestClient):
    resp = client.get("/api/scans/non-existent-scan-id/explain")
    assert resp.status_code == 404


def test_multimodal_validation_empty_body(client: TestClient):
    resp = client.post("/api/scans/multimodal", json={})
    assert resp.status_code == 422


def test_risk_threshold_classification():
    # Test high risk -> phishing
    high = fuse_modalities({"email": {"risk_score": 85, "prediction": "phishing"}})
    assert high["overall_prediction"] == "phishing"
    assert high["overall_risk_score"] == 85

    # Test medium risk -> suspicious
    medium = fuse_modalities({"email": {"risk_score": 45, "prediction": "suspicious"}})
    assert medium["overall_prediction"] == "suspicious"
    assert medium["overall_risk_score"] == 45

    # Test low risk -> safe
    low = fuse_modalities({"email": {"risk_score": 15, "prediction": "safe"}})
    assert low["overall_prediction"] == "safe"
    assert low["overall_risk_score"] == 15
