"""Tests for email scan endpoint (Section 3)."""

from __future__ import annotations


def test_email_scan_safe(client):
    """A benign email should be classified as safe."""
    resp = client.post("/api/scans/email", json={
        "sender": "john@company.com",
        "subject": "Team meeting tomorrow",
        "body": "Hi team, reminder about our standup at 10am. See you there!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["scan_type"] == "email"
    assert data["prediction"] in ("safe", "suspicious", "phishing")
    assert 0 <= data["risk_score"] <= 100
    assert data["confidence"] is None  # rule-based
    assert isinstance(data["indicators"], list)
    assert isinstance(data["explanation"], list)
    assert data["model"]


def test_email_scan_phishing(client):
    """An obviously phishing email should be flagged."""
    resp = client.post("/api/scans/email", json={
        "sender": "security123@gmail.com",
        "subject": "URGENT: Your PayPal account will be suspended!!!",
        "body": (
            "Dear Customer, Your account has been compromised. "
            "Click here immediately to verify your password and update your credentials: "
            "http://192.168.1.1/paypal-login "
            "If you do not act now, your account will be terminated within 24 hours. "
            "Please wire transfer $500 via bitcoin to unlock your account."
        ),
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["prediction"] in ("phishing", "suspicious")
    assert data["risk_score"] >= 30
    assert len(data["indicators"]) > 0


def test_email_scan_missing_sender(client):
    """Missing sender field returns 422."""
    resp = client.post("/api/scans/email", json={
        "subject": "Test",
        "body": "Hello",
    })
    assert resp.status_code == 422


def test_email_scan_invalid_sender(client):
    """Sender without @ returns 422."""
    resp = client.post("/api/scans/email", json={
        "sender": "not-an-email",
        "subject": "Test",
        "body": "Hello",
    })
    assert resp.status_code == 422


def test_email_scan_empty_body(client):
    """Blank email body returns 422."""
    resp = client.post("/api/scans/email", json={
        "sender": "a@b.com",
        "subject": "Test",
        "body": "   ",
    })
    assert resp.status_code == 422


def test_email_scan_with_headers(client):
    """Email with mismatched Reply-To should flag it."""
    resp = client.post("/api/scans/email", json={
        "sender": "support@bank.com",
        "subject": "Account verification",
        "body": "Please verify your account by clicking the link.",
        "headers": {
            "Reply-To": "hacker@evil.com",
        },
    })
    assert resp.status_code == 200
    data = resp.json()
    indicator_names = {i["name"] for i in data["indicators"]}
    assert "reply_to_mismatch" in indicator_names


def test_email_scan_url_mismatch(client):
    """Email with display-vs-actual URL mismatch should flag it."""
    resp = client.post("/api/scans/email", json={
        "sender": "info@company.com",
        "subject": "Click here",
        "body": 'Visit <a href="http://evil.com/steal">http://paypal.com/login</a> to continue.',
    })
    assert resp.status_code == 200
    data = resp.json()
    indicator_names = {i["name"] for i in data["indicators"]}
    assert "url_display_mismatch" in indicator_names

