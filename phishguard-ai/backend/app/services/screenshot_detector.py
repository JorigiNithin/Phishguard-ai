"""Screenshot phishing detector.

Accepts an uploaded image, validates it, extracts text via OCR,
and analyses the extracted text for phishing indicators.

OCR engine: pytesseract (requires Tesseract-OCR binary).
Image handling: Pillow.

Security:
- Uploaded files are never executed.
- URLs found in screenshots are analysed lexically, never visited.
- Corrupt or unsupported images are handled gracefully.
- Server filesystem paths are not exposed in error messages.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Any

from PIL import Image

# ---------------------------------------------------------------------------
# OCR availability check
# ---------------------------------------------------------------------------

_ocr_available = False
_ocr_error: str | None = None

try:
    import pytesseract

    # Quick availability check – pytesseract calls the binary
    pytesseract.get_tesseract_version()
    _ocr_available = True
except Exception as exc:
    _ocr_error = (
        "Tesseract OCR is not installed or not found on the system PATH. "
        "Install Tesseract-OCR to enable screenshot text extraction. "
        f"Error: {exc}"
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_FORMATS = {"PNG", "JPEG", "JPG"}

_URL_RE = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.I)

_CREDENTIAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(password|passwd|pass\s*word)\b", re.I),
    re.compile(r"\b(log\s*in|sign\s*in|sign\s*up)\b", re.I),
    re.compile(r"\b(user\s*name|email\s*address)\b", re.I),
    re.compile(r"\b(verify\s+(your\s+)?(account|identity))\b", re.I),
    re.compile(r"\b(enter\s+your\s+(credentials?|password|email))\b", re.I),
    re.compile(r"\b(forgot\s+password|reset\s+password)\b", re.I),
]

_URGENCY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(urgent|immediately|act\s*now|limited\s*time)\b", re.I),
    re.compile(r"\b(account\s*(suspend|terminat|lock|restrict|clos))\b", re.I),
    re.compile(r"\b(expire[sd]?|expiring)\b", re.I),
    re.compile(r"\b(final\s*warning|last\s*chance)\b", re.I),
]

_FINANCIAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(wire\s*transfer|bank\s*transfer)\b", re.I),
    re.compile(r"\b(bitcoin|cryptocurrency|gift\s*card)\b", re.I),
    re.compile(r"\b(payment|invoice|refund|billing)\b", re.I),
]

_BRAND_NAMES: frozenset[str] = frozenset({
    "paypal", "amazon", "apple", "microsoft", "google", "netflix",
    "facebook", "instagram", "whatsapp", "linkedin", "twitter",
    "chase", "wells fargo", "citibank", "bank of america",
    "dropbox", "adobe", "docusign",
})


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class _Indicator:
    name: str
    description: str
    severity: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def is_ocr_available() -> bool:
    """Return whether Tesseract OCR is available on this system."""
    return _ocr_available


def get_ocr_error() -> str | None:
    """Return the OCR unavailability reason, if any."""
    return _ocr_error


def analyze_screenshot(image_bytes: bytes) -> dict[str, Any]:
    """Analyse a screenshot image for phishing indicators.

    Parameters
    ----------
    image_bytes:
        Raw bytes of the uploaded image (PNG, JPEG).

    Returns
    -------
    dict matching the ``MultimodalScanResponse`` schema.

    Raises
    ------
    ValueError
        If the image is too large, corrupt, or in an unsupported format.
    """
    # --- Size check ---------------------------------------------------------
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError(
            f"Image exceeds maximum allowed size of {MAX_IMAGE_BYTES // (1024 * 1024)} MB."
        )

    # --- Validate image -----------------------------------------------------
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        # Re-open after verify (verify may close underlying data)
        img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise ValueError("Uploaded file is not a valid image or is corrupt.")

    fmt = (img.format or "").upper()
    if fmt not in ALLOWED_FORMATS:
        raise ValueError(
            f"Unsupported image format '{fmt}'. Accepted formats: {', '.join(sorted(ALLOWED_FORMATS))}."
        )

    indicators: list[_Indicator] = []
    ocr_text = ""
    urls_found: list[str] = []

    # --- OCR ----------------------------------------------------------------
    if _ocr_available:
        try:
            ocr_text = pytesseract.image_to_string(img).strip()
        except Exception:
            ocr_text = ""
            indicators.append(
                _Indicator(
                    name="ocr_failed",
                    description="OCR text extraction failed for this image.",
                    severity="low",
                )
            )
    else:
        indicators.append(
            _Indicator(
                name="ocr_unavailable",
                description="Tesseract OCR is not installed. Text-based analysis is limited.",
                severity="low",
            )
        )

    # --- Analyse extracted text ---------------------------------------------
    if ocr_text:
        # URLs in screenshot
        urls_found = _URL_RE.findall(ocr_text)
        if urls_found:
            _analyze_urls(urls_found, indicators)

        # Credential language
        _check_patterns(ocr_text, _CREDENTIAL_PATTERNS, "credential_language",
                        "Credential or login-related language detected in screenshot.",
                        indicators)

        # Urgency language
        _check_patterns(ocr_text, _URGENCY_PATTERNS, "urgency_language",
                        "Urgency or threatening language detected in screenshot.",
                        indicators)

        # Financial language
        _check_patterns(ocr_text, _FINANCIAL_PATTERNS, "financial_language",
                        "Financial or payment-related language detected in screenshot.",
                        indicators)

        # Brand references
        text_lower = ocr_text.lower()
        found_brands = [b for b in _BRAND_NAMES if b in text_lower]
        if found_brands:
            indicators.append(
                _Indicator(
                    name="brand_reference",
                    description=f"Screenshot references brand(s): {', '.join(found_brands[:5])}.",
                    severity="medium",
                )
            )

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
        else ["No phishing indicators detected in this screenshot."]
    )

    details: dict[str, Any] = {
        "ocr_available": _ocr_available,
        "ocr_text_length": len(ocr_text),
        "urls_found": urls_found[:20],
        "image_format": fmt,
        "image_size_bytes": len(image_bytes),
    }
    if ocr_text:
        # Return first 2000 chars of OCR text
        details["ocr_text_preview"] = ocr_text[:2000]

    return {
        "scan_type": "screenshot",
        "prediction": prediction,
        "risk_score": risk_score,
        "confidence": None,
        "indicators": [
            {"name": i.name, "description": i.description, "severity": i.severity}
            for i in indicators
        ],
        "explanation": explanation,
        "model": "Rule-based Screenshot Analyzer v1.0 (Tesseract OCR)"
        if _ocr_available
        else "Rule-based Screenshot Analyzer v1.0 (OCR unavailable)",
        "details": details,
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _analyze_urls(urls: list[str], indicators: list[_Indicator]) -> None:
    """Run basic analysis on URLs found in the screenshot."""
    from urllib.parse import urlparse as _urlparse

    suspicious = 0
    ip_urls = 0
    for url_str in urls:
        try:
            parsed = _urlparse(url_str if "://" in url_str else "http://" + url_str)
            host = (parsed.hostname or "").lower()
        except Exception:
            suspicious += 1
            continue

        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
            ip_urls += 1
        elif host.endswith((".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".buzz")):
            suspicious += 1

    if ip_urls:
        indicators.append(
            _Indicator(
                name="ip_address_url",
                description=f"Screenshot contains {ip_urls} URL(s) pointing to IP addresses.",
                severity="high",
            )
        )
    if suspicious:
        indicators.append(
            _Indicator(
                name="suspicious_urls",
                description=f"Screenshot contains {suspicious} URL(s) with suspicious domains.",
                severity="medium",
            )
        )
    if len(urls) > 0 and not ip_urls and not suspicious:
        indicators.append(
            _Indicator(
                name="urls_found",
                description=f"{len(urls)} URL(s) detected in the screenshot.",
                severity="low",
            )
        )


def _check_patterns(
    text: str,
    patterns: list[re.Pattern[str]],
    indicator_name: str,
    description: str,
    indicators: list[_Indicator],
) -> None:
    """Check text against a list of patterns and add an indicator if any match."""
    matches = sum(1 for pat in patterns if pat.search(text))
    if matches >= 2:
        indicators.append(_Indicator(name=indicator_name, description=description, severity="high"))
    elif matches == 1:
        indicators.append(_Indicator(name=indicator_name, description=description, severity="medium"))

