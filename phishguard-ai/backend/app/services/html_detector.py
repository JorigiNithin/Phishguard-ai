"""Static HTML phishing detector.

Parses HTML source code and analyses it for phishing indicators such as
credential forms, suspicious scripts, cross-domain actions, hidden elements,
and brand impersonation.

Security:
- HTML is parsed statically with BeautifulSoup — never rendered or executed.
- JavaScript is pattern-matched, never evaluated.
- No external resources are fetched.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Comment

# ---------------------------------------------------------------------------
# Indicator data class
# ---------------------------------------------------------------------------


@dataclass
class _Indicator:
    name: str
    description: str
    severity: str


# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

_PASSWORD_INPUT_TYPES = {"password"}

_CREDENTIAL_FIELD_NAMES = re.compile(
    r"(password|passwd|pass|login|user|username|email|credential|ssn|pin|otp|token)",
    re.I,
)

_SUSPICIOUS_JS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\beval\s*\(", re.I), "eval()"),
    (re.compile(r"\bdocument\.cookie\b", re.I), "document.cookie access"),
    (re.compile(r"\bwindow\.location\s*=", re.I), "JavaScript redirect (window.location)"),
    (re.compile(r"\blocation\.href\s*=", re.I), "JavaScript redirect (location.href)"),
    (re.compile(r"\blocation\.replace\s*\(", re.I), "JavaScript redirect (location.replace)"),
    (re.compile(r"\batob\s*\(", re.I), "Base64 decoding (atob)"),
    (re.compile(r"\bString\.fromCharCode\b", re.I), "Character code obfuscation"),
    (re.compile(r"\bunescape\s*\(", re.I), "unescape() call"),
    (re.compile(r"\\x[0-9a-f]{2}", re.I), "Hex-encoded strings"),
    (re.compile(r"\bdocument\.write\s*\(", re.I), "document.write()"),
]

_BRAND_NAMES: frozenset[str] = frozenset({
    "paypal", "amazon", "apple", "microsoft", "google", "netflix",
    "facebook", "instagram", "whatsapp", "linkedin", "twitter",
    "bank of america", "chase", "wells fargo", "citibank",
    "dropbox", "adobe", "docusign", "outlook", "office 365",
    "dhl", "fedex", "ups", "usps",
})

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_html(html: str) -> dict[str, Any]:
    """Analyse raw HTML source for phishing indicators.

    Returns a dict matching the ``MultimodalScanResponse`` schema.
    """
    indicators: list[_Indicator] = []

    soup = BeautifulSoup(html, "html.parser")

    # --- 1. Password / credential inputs -----------------------------------
    _check_credential_inputs(soup, indicators)

    # --- 2. Form actions ----------------------------------------------------
    _check_form_actions(soup, indicators)

    # --- 3. Hidden elements -------------------------------------------------
    _check_hidden_elements(soup, indicators)

    # --- 4. Suspicious JavaScript -------------------------------------------
    _check_javascript(soup, html, indicators)

    # --- 5. External scripts ------------------------------------------------
    _check_external_scripts(soup, indicators)

    # --- 6. Meta-refresh redirects ------------------------------------------
    _check_meta_redirects(soup, indicators)

    # --- 7. Suspicious iframes ---------------------------------------------
    _check_iframes(soup, indicators)

    # --- 8. Brand impersonation ---------------------------------------------
    _check_brand_impersonation(soup, html, indicators)

    # --- 9. Suspicious embedded URLs ----------------------------------------
    _check_suspicious_urls(soup, indicators)

    # --- 10. Data exfiltration patterns -------------------------------------
    _check_data_exfiltration(html, indicators)

    # --- Score --------------------------------------------------------------
    severity_weights = {"high": 20, "medium": 10, "low": 5}
    risk_score = min(100, sum(severity_weights.get(i.severity, 5) for i in indicators))

    if risk_score >= 60:
        prediction = "phishing"
    elif risk_score >= 30:
        prediction = "suspicious"
    else:
        prediction = "safe"

    explanation: list[str] = (
        [ind.description for ind in indicators]
        if indicators
        else ["No phishing indicators detected in this HTML."]
    )

    return {
        "scan_type": "html",
        "prediction": prediction,
        "risk_score": risk_score,
        "confidence": None,  # Rule-based — no calibrated confidence
        "indicators": [
            {"name": i.name, "description": i.description, "severity": i.severity}
            for i in indicators
        ],
        "explanation": explanation,
        "model": "Rule-based HTML Analyzer v1.0",
    }


# ---------------------------------------------------------------------------
# Private checkers
# ---------------------------------------------------------------------------


def _check_credential_inputs(soup: BeautifulSoup, indicators: list[_Indicator]) -> None:
    """Detect password and credential input fields."""
    password_fields = soup.find_all("input", attrs={"type": "password"})
    if password_fields:
        indicators.append(
            _Indicator(
                name="password_input",
                description=f"Found {len(password_fields)} password input field(s).",
                severity="high",
            )
        )

    # Other credential-like inputs
    for inp in soup.find_all("input"):
        name_attr = (inp.get("name") or "") + " " + (inp.get("id") or "") + " " + (inp.get("placeholder") or "")
        if _CREDENTIAL_FIELD_NAMES.search(name_attr) and inp.get("type") != "password":
            indicators.append(
                _Indicator(
                    name="credential_field",
                    description=f"Input field with credential-related naming: '{name_attr.strip()[:60]}'.",
                    severity="medium",
                )
            )
            break  # Report once


def _check_form_actions(soup: BeautifulSoup, indicators: list[_Indicator]) -> None:
    """Check form submission destinations."""
    forms = soup.find_all("form")
    for form in forms:
        action = (form.get("action") or "").strip()
        if not action or action == "#":
            continue

        try:
            parsed = urlparse(action)
            hostname = (parsed.hostname or "").lower()
        except Exception:
            indicators.append(
                _Indicator(
                    name="malformed_form_action",
                    description=f"Form has an unparseable action URL.",
                    severity="medium",
                )
            )
            continue

        # Cross-domain form action
        if hostname and parsed.scheme in ("http", "https"):
            # IP address destination
            if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname):
                indicators.append(
                    _Indicator(
                        name="form_to_ip",
                        description=f"Form submits data to an IP address: {hostname}.",
                        severity="high",
                    )
                )
            else:
                indicators.append(
                    _Indicator(
                        name="external_form_action",
                        description=f"Form submits data to an external domain: {hostname}.",
                        severity="high",
                    )
                )

        # data: URI form action
        if action.startswith("data:"):
            indicators.append(
                _Indicator(
                    name="data_uri_form",
                    description="Form action uses a data: URI, a common phishing technique.",
                    severity="high",
                )
            )


def _check_hidden_elements(soup: BeautifulSoup, indicators: list[_Indicator]) -> None:
    """Flag excessive hidden elements."""
    hidden_inputs = soup.find_all("input", attrs={"type": "hidden"})
    hidden_divs = soup.find_all(style=re.compile(r"display\s*:\s*none", re.I))
    hidden_divs += soup.find_all(attrs={"hidden": True})

    total_hidden = len(hidden_inputs) + len(hidden_divs)
    if total_hidden > 5:
        indicators.append(
            _Indicator(
                name="excessive_hidden_elements",
                description=f"Found {total_hidden} hidden elements, which may conceal malicious content.",
                severity="medium",
            )
        )
    elif total_hidden > 0:
        # Check if any hidden element contains credential-like values
        for el in hidden_inputs:
            val = el.get("value", "")
            name = el.get("name", "")
            if _CREDENTIAL_FIELD_NAMES.search(name):
                indicators.append(
                    _Indicator(
                        name="hidden_credential_field",
                        description=f"Hidden input with credential-related name: '{name[:40]}'.",
                        severity="high",
                    )
                )
                return


def _check_javascript(
    soup: BeautifulSoup, raw_html: str, indicators: list[_Indicator]
) -> None:
    """Scan inline JavaScript for suspicious patterns."""
    js_sources: list[str] = []

    for script_tag in soup.find_all("script"):
        if script_tag.string:
            js_sources.append(script_tag.string)

    # Also check event-handler attributes
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr.lower().startswith("on"):
                js_sources.append(str(tag.attrs[attr]))

    all_js = "\n".join(js_sources)
    if not all_js:
        return

    found_patterns: list[str] = []
    for pattern, label in _SUSPICIOUS_JS_PATTERNS:
        if pattern.search(all_js):
            found_patterns.append(label)

    if len(found_patterns) >= 3:
        indicators.append(
            _Indicator(
                name="suspicious_javascript",
                description=f"Multiple suspicious JavaScript patterns detected: {', '.join(found_patterns[:5])}.",
                severity="high",
            )
        )
    elif found_patterns:
        indicators.append(
            _Indicator(
                name="suspicious_javascript",
                description=f"Suspicious JavaScript pattern(s): {', '.join(found_patterns)}.",
                severity="medium",
            )
        )


def _check_external_scripts(soup: BeautifulSoup, indicators: list[_Indicator]) -> None:
    """Flag external script sources."""
    suspicious = []
    for script in soup.find_all("script", src=True):
        src = script["src"]
        try:
            parsed = urlparse(src)
            host = (parsed.hostname or "").lower()
        except Exception:
            suspicious.append(src[:80])
            continue

        # Suspicious TLDs or IP addresses
        if host and (
            re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host)
            or host.endswith((".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".buzz"))
        ):
            suspicious.append(host)

    if suspicious:
        indicators.append(
            _Indicator(
                name="suspicious_external_script",
                description=f"External script(s) from suspicious source(s): {', '.join(suspicious[:3])}.",
                severity="high",
            )
        )


def _check_meta_redirects(soup: BeautifulSoup, indicators: list[_Indicator]) -> None:
    """Detect meta-refresh redirects."""
    for meta in soup.find_all("meta"):
        equiv = (meta.get("http-equiv") or "").lower()
        content = meta.get("content") or ""
        if equiv == "refresh" and "url=" in content.lower():
            indicators.append(
                _Indicator(
                    name="meta_redirect",
                    description="Page contains a meta-refresh redirect.",
                    severity="high",
                )
            )
            return


def _check_iframes(soup: BeautifulSoup, indicators: list[_Indicator]) -> None:
    """Flag suspicious iframes."""
    iframes = soup.find_all("iframe")
    for iframe in iframes:
        src = (iframe.get("src") or "").strip()
        # Hidden or zero-size iframes
        width = iframe.get("width", "")
        height = iframe.get("height", "")
        style = iframe.get("style", "")

        is_hidden = (
            width in ("0", "1")
            or height in ("0", "1")
            or "display:none" in style.replace(" ", "").lower()
            or "visibility:hidden" in style.replace(" ", "").lower()
        )
        if is_hidden:
            indicators.append(
                _Indicator(
                    name="hidden_iframe",
                    description="Page contains a hidden iframe, often used for credential theft.",
                    severity="high",
                )
            )
            return

    if len(iframes) > 3:
        indicators.append(
            _Indicator(
                name="multiple_iframes",
                description=f"Page contains {len(iframes)} iframes.",
                severity="medium",
            )
        )


def _check_brand_impersonation(
    soup: BeautifulSoup, raw_html: str, indicators: list[_Indicator]
) -> None:
    """Check title and visible text for known brand names."""
    title_tag = soup.find("title")
    title_text = title_tag.string.lower() if title_tag and title_tag.string else ""

    page_text = soup.get_text(separator=" ").lower()[:5000]

    found_brands = [b for b in _BRAND_NAMES if b in title_text or b in page_text]

    if found_brands:
        indicators.append(
            _Indicator(
                name="brand_reference",
                description=f"Page references brand(s): {', '.join(found_brands[:5])}. Verify this is an official page.",
                severity="medium",
            )
        )


def _check_suspicious_urls(soup: BeautifulSoup, indicators: list[_Indicator]) -> None:
    """Check embedded links for suspicious destinations."""
    suspicious_count = 0
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        try:
            parsed = urlparse(href)
            host = (parsed.hostname or "").lower()
        except Exception:
            continue

        if host and re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
            suspicious_count += 1
        elif host and host.endswith((".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top")):
            suspicious_count += 1

    if suspicious_count > 0:
        indicators.append(
            _Indicator(
                name="suspicious_urls",
                description=f"{suspicious_count} link(s) point to suspicious destinations.",
                severity="medium",
            )
        )


def _check_data_exfiltration(raw_html: str, indicators: list[_Indicator]) -> None:
    """Look for patterns suggesting data exfiltration."""
    # XMLHttpRequest / fetch with credential data
    exfil_patterns = [
        re.compile(r"XMLHttpRequest.*password", re.I | re.S),
        re.compile(r"fetch\s*\(.*credential", re.I | re.S),
        re.compile(r"navigator\.sendBeacon", re.I),
        re.compile(r"new\s+Image\(\)\.src\s*=.*\+.*(?:password|cookie|token)", re.I | re.S),
    ]
    for pat in exfil_patterns:
        if pat.search(raw_html[:50000]):
            indicators.append(
                _Indicator(
                    name="data_exfiltration_pattern",
                    description="Code pattern consistent with data exfiltration detected.",
                    severity="high",
                )
            )
            return

