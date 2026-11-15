"""Minimal smoke test – run directly with python."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from starlette.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)

results = []

def check(name, fn):
    try:
        fn()
        results.append((name, "PASS"))
        print(f"  PASS  {name}")
    except AssertionError as e:
        results.append((name, f"FAIL: {e}"))
        print(f"  FAIL  {name}: {e}")
    except Exception as e:
        results.append((name, f"ERROR: {e}"))
        print(f"  ERROR {name}: {e}")

# --- Health ---
def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200, f"status={r.status_code}"
    d = r.json()
    assert d["status"] == "ok"
    assert "version" in d
    assert "timestamp" in d
    assert "environment" in d
check("GET /api/health", test_health)

# --- Version ---
def test_version():
    r = client.get("/api/version")
    assert r.status_code == 200
    d = r.json()
    assert d["name"] == "PhishGuard AI"
    assert "version" in d
check("GET /api/version", test_version)

# --- Models ---
def test_models():
    r = client.get("/api/models")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 4
    assert len(d["models"]) == 4
    ids = {m["id"] for m in d["models"]}
    assert ids == {"url_detector", "email_detector", "screenshot_detector", "html_detector"}
    for m in d["models"]:
        assert m["status"] == "not_implemented", f'{m["id"]} status={m["status"]}'
        assert m["available"] is False, f'{m["id"]} available={m["available"]}'
check("GET /api/models", test_models)

# --- Statistics ---
def test_statistics():
    r = client.get("/api/statistics")
    assert r.status_code == 200
    d = r.json()
    assert d["total_scans"] == 0
    assert d["high_risk"] == 0
    assert d["suspicious"] == 0
    assert d["safe"] == 0
    assert d["models_available"] == 0
    assert isinstance(d["risk_distribution"], list)
check("GET /api/statistics", test_statistics)

# --- Scans ---
def test_scans():
    r = client.get("/api/scans")
    assert r.status_code == 200
    d = r.json()
    assert d["scans"] == []
    assert d["total"] == 0
check("GET /api/scans", test_scans)

# --- 404 ---
def test_404():
    r = client.get("/api/nonexistent")
    assert r.status_code == 404
check("GET /api/nonexistent → 404", test_404)

# --- CORS header check ---
def test_cors():
    r = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    acl = r.headers.get("access-control-allow-origin", "")
    assert acl == "http://localhost:5173", f"CORS origin={acl!r}"
check("CORS allows localhost:5173", test_cors)

# --- No fake data check ---
def test_no_fake_data():
    stats = client.get("/api/statistics").json()
    assert stats["total_scans"] == 0, "total_scans should be 0"
    models = client.get("/api/models").json()
    for m in models["models"]:
        assert m["status"] == "not_implemented", f"Model {m['id']} shouldn't claim implemented"
        assert m["available"] is False, f"Model {m['id']} shouldn't claim available"
    scans = client.get("/api/scans").json()
    assert len(scans["scans"]) == 0, "Scans should be empty"
check("No fake predictions/stats", test_no_fake_data)

print(f"\n{'='*50}")
passed = sum(1 for _, s in results if s == "PASS")
total = len(results)
print(f"Results: {passed}/{total} passed")
if passed < total:
    sys.exit(1)

