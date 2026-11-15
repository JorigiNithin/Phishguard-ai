"""Verification script for all PhishGuard AI API endpoints.

Tests each route via FastAPI TestClient, verifying:
- Router registration & exact HTTP method/path
- Request/response schemas
- Success codes and expected error responses (422, 400, 404)
- Absence of authentication requirement
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# Add backend package to path
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from fastapi.testclient import TestClient
from PIL import Image
from app.main import app

client = TestClient(app)


def test_endpoint(name: str, method: str, url: str, **kwargs):
    print(f"\n--- Testing [{method}] {url} ({name}) ---")
    if method == "GET":
        resp = client.get(url, **kwargs)
    elif method == "POST":
        resp = client.post(url, **kwargs)
    elif method == "DELETE":
        resp = client.delete(url, **kwargs)
    else:
        raise ValueError(f"Unsupported method: {method}")
    print(f"Status: {resp.status_code}")
    return resp


def main():
    print("=================================================================")
    print("PHISHGUARD AI — API ENDPOINT VERIFICATION")
    print("=================================================================")

    # 1. GET /api/health
    r1 = test_endpoint("Health Check", "GET", "/api/health")
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}"
    data1 = r1.json()
    assert data1.get("status") == "ok"
    assert "version" in data1
    assert "timestamp" in data1
    print("  ✓ Success response verified:", data1)

    # 2. POST /api/scans/url
    # Valid test
    r2 = test_endpoint("URL Scan (Valid)", "POST", "/api/scans/url", json={"url": "http://164.176.108.250/secure/update-account/ccca50df7901e47e767"})
    assert r2.status_code == 200, f"Expected 200, got {r2.status_code}"
    data2 = r2.json()
    assert data2.get("prediction") in ("phishing", "legitimate")
    assert "confidence" in data2
    assert "risk_level" in data2
    assert "scan_id" in data2
    created_scan_id = data2.get("scan_id")
    print(f"  ✓ Success response verified (scan_id={created_scan_id}, risk={data2.get('risk_level')}):")
    print(f"    prediction={data2.get('prediction')}, confidence={data2.get('confidence')}")

    # Invalid URL test (error handling)
    r2_err = test_endpoint("URL Scan (Empty Body / Invalid)", "POST", "/api/scans/url", json={"url": ""})
    assert r2_err.status_code == 422
    print("  ✓ Error handling verified: 422 Unprocessable Entity for empty URL")

    # 3. POST /api/scans/email
    # Valid test
    r3 = test_endpoint(
        "Email Scan (Valid)",
        "POST",
        "/api/scans/email",
        json={
            "sender": "security-alert@paypal-update.xyz",
            "subject": "Urgent: Account Suspended",
            "body": "Your account has been suspended. Please verify your password immediately.",
        },
    )
    assert r3.status_code == 200, f"Expected 200, got {r3.status_code}"
    data3 = r3.json()
    assert data3.get("prediction") in ("phishing", "suspicious")
    assert "risk_score" in data3
    assert "indicators" in data3
    email_scan_id = data3.get("scan_id")
    print(f"  ✓ Success response verified (scan_id={email_scan_id}, risk_score={data3.get('risk_score')}):")
    print(f"    prediction={data3.get('prediction')}, indicators_count={len(data3.get('indicators', []))}")

    # Missing required sender (error handling)
    r3_err = test_endpoint("Email Scan (Missing Sender)", "POST", "/api/scans/email", json={"body": "Test body without sender"})
    assert r3_err.status_code == 422
    print("  ✓ Error handling verified: 422 Unprocessable Entity for missing required field")

    # 4. POST /api/scans/screenshot
    # Valid PNG image upload
    img = Image.new("RGB", (200, 200), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    files = {"file": ("test.png", buf, "image/png")}
    r4 = test_endpoint("Screenshot Scan (Valid PNG)", "POST", "/api/scans/screenshot", files=files)
    assert r4.status_code == 200, f"Expected 200, got {r4.status_code}"
    data4 = r4.json()
    assert "risk_score" in data4
    assert "prediction" in data4
    screenshot_scan_id = data4.get("scan_id")
    print(f"  ✓ Success response verified (scan_id={screenshot_scan_id}, prediction={data4.get('prediction')})")

    # Corrupt file test (error handling)
    corrupt_buf = io.BytesIO(b"not an image binary payload")
    r4_err = test_endpoint("Screenshot Scan (Corrupt)", "POST", "/api/scans/screenshot", files={"file": ("fake.png", corrupt_buf, "image/png")})
    assert r4_err.status_code == 422
    print("  ✓ Error handling verified: 422 Unprocessable Entity for corrupt image")

    # 5. POST /api/scans/html
    # Valid HTML test
    r5 = test_endpoint(
        "HTML Scan (Valid)",
        "POST",
        "/api/scans/html",
        json={"html": "<html><body><form action='http://192.168.1.100/submit'><input type='password' name='pass'></form></body></html>"},
    )
    assert r5.status_code == 200, f"Expected 200, got {r5.status_code}"
    data5 = r5.json()
    assert data5.get("prediction") in ("phishing", "suspicious", "safe")
    assert "risk_score" in data5
    html_scan_id = data5.get("scan_id")
    print(f"  ✓ Success response verified (scan_id={html_scan_id}, risk_score={data5.get('risk_score')})")

    # Empty body test (error handling)
    r5_err = test_endpoint("HTML Scan (Empty)", "POST", "/api/scans/html", json={"html": ""})
    assert r5_err.status_code == 422
    print("  ✓ Error handling verified: 422 Unprocessable Entity for blank HTML")

    # 6. POST /api/scans/multimodal
    # Multi-modality fusion test
    r6 = test_endpoint(
        "Multimodal Fusion (Valid)",
        "POST",
        "/api/scans/multimodal",
        json={
            "url": "http://192.168.1.1/login.php",
            "email": {
                "sender": "alerts@banking-update.xyz",
                "subject": "Urgent Security Action Required",
                "body": "Click here to login and update your password immediately.",
            },
            "html": "<html><body><form action='http://10.0.0.1/auth'><input type='password'></form></body></html>",
        },
    )
    assert r6.status_code == 200, f"Expected 200, got {r6.status_code}"
    data6 = r6.json()
    assert "overall_risk_score" in data6
    assert "overall_prediction" in data6
    assert "contributing_indicators" in data6
    assert "explanation" in data6
    fusion_scan_id = data6.get("scan_id")
    print(f"  ✓ Success response verified (scan_id={fusion_scan_id}, overall_risk={data6.get('overall_risk_score')}):")
    print(f"    overall_prediction={data6.get('overall_prediction')}, modalities={data6.get('modalities_analyzed')}")

    # Empty payload (error handling)
    r6_err = test_endpoint("Multimodal Fusion (Empty)", "POST", "/api/scans/multimodal", json={})
    assert r6_err.status_code == 422
    print("  ✓ Error handling verified: 422 Unprocessable Entity when zero modalities are provided")

    # 7. GET /api/scans/history
    r7 = test_endpoint("Scan History (Pagination & Filter)", "GET", "/api/scans/history?page=1&page_size=10&prediction=phishing")
    assert r7.status_code == 200, f"Expected 200, got {r7.status_code}"
    data7 = r7.json()
    assert "scans" in data7
    assert "total" in data7
    assert "page" in data7
    assert "page_size" in data7
    assert "total_pages" in data7
    assert data7.get("total") >= 1
    print(f"  ✓ Success response verified: total_scans={data7.get('total')}, scans_returned={len(data7.get('scans'))}")

    # 8. GET /api/scans/{scan_id}
    # Retrieve existing scan details
    target_id = fusion_scan_id or created_scan_id
    r8 = test_endpoint(f"Scan Detail ({target_id})", "GET", f"/api/scans/{target_id}")
    assert r8.status_code == 200, f"Expected 200, got {r8.status_code}"
    data8 = r8.json()
    assert data8.get("id") == target_id
    assert "risk_score" in data8
    assert "prediction" in data8
    print(f"  ✓ Success response verified: id={data8.get('id')}, type={data8.get('scan_type')}, prediction={data8.get('prediction')}")

    # 404 test for non-existent scan
    r8_404 = test_endpoint("Scan Detail (Missing ID)", "GET", "/api/scans/non-existent-uuid-12345")
    assert r8_404.status_code == 404
    print("  ✓ Error handling verified: 404 Not Found for non-existent scan_id")

    print("\n=================================================================")
    print("ALL 8 ENDPOINTS FULLY VERIFIED WITH 200 OK & ERROR HANDLING!")
    print("=================================================================")


if __name__ == "__main__":
    main()
