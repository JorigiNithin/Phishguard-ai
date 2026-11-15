"""URL feature extraction for phishing detection.

Extracts lexical and structural features from URLs without visiting them.
No network requests are made.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Known URL-shortener domains
# ---------------------------------------------------------------------------
_SHORTENERS = frozenset({
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "adf.ly", "tiny.cc", "lnkd.in", "db.tt", "qr.ae",
    "rebrand.ly", "bl.ink", "short.io", "cutt.ly", "rb.gy",
})

_SUSPICIOUS_KEYWORDS = frozenset({
    "login", "signin", "verify", "account", "update", "secure",
    "banking", "confirm", "password", "credential", "suspend",
    "authenticate", "wallet", "ebayisapi", "webscr", "paypal",
})

_IP_RE = re.compile(
    r"^(?:\d{1,3}\.){3}\d{1,3}$"          # IPv4
    r"|^\[?[0-9a-fA-F:]+\]?$"              # IPv6
)

# Feature names in the order the model expects
FEATURE_NAMES: list[str] = [
    "url_length",
    "domain_length",
    "num_dots",
    "num_subdomains",
    "is_https",
    "has_ip_address",
    "num_hyphens",
    "has_at_sign",
    "is_shortened",
    "num_suspicious_keywords",
    "digit_count",
    "special_char_count",
    "path_length",
    "query_length",
    "num_query_params",
    "has_port",
    "entropy",
]


def _shannon_entropy(s: str) -> float:
    """Compute Shannon entropy of a string."""
    from math import log2
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(s)
    return -sum((c / length) * log2(c / length) for c in freq.values())


def extract_features(url: str) -> dict[str, float | int]:
    """Extract numerical features from a URL string.

    Returns a dict whose keys match ``FEATURE_NAMES``.
    Raises ``ValueError`` for completely unparseable input.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    url_stripped = url.strip()

    # Attempt to parse
    parsed = urlparse(url_stripped)
    hostname = (parsed.hostname or "").lower()
    path = parsed.path or ""
    query = parsed.query or ""

    # If no scheme was given, try adding one for better parsing
    if not parsed.scheme:
        parsed = urlparse("http://" + url_stripped)
        hostname = (parsed.hostname or "").lower()
        path = parsed.path or ""
        query = parsed.query or ""

    if not hostname:
        raise ValueError(f"Cannot extract hostname from URL: {url_stripped!r}")

    domain_parts = hostname.split(".")
    num_subdomains = max(0, len(domain_parts) - 2)  # e.g. a.b.example.com → 2

    # Count suspicious keywords in the full URL (case-insensitive)
    url_lower = url_stripped.lower()
    suspicious_kw_count = sum(1 for kw in _SUSPICIOUS_KEYWORDS if kw in url_lower)

    # Query parameters
    num_query_params = 0
    if query:
        num_query_params = query.count("&") + 1

    features: dict[str, float | int] = {
        "url_length": len(url_stripped),
        "domain_length": len(hostname),
        "num_dots": url_stripped.count("."),
        "num_subdomains": num_subdomains,
        "is_https": int(parsed.scheme == "https"),
        "has_ip_address": int(bool(_IP_RE.match(hostname))),
        "num_hyphens": url_stripped.count("-"),
        "has_at_sign": int("@" in url_stripped),
        "is_shortened": int(hostname in _SHORTENERS),
        "num_suspicious_keywords": suspicious_kw_count,
        "digit_count": sum(c.isdigit() for c in url_stripped),
        "special_char_count": sum(
            1 for c in url_stripped
            if not c.isalnum() and c not in (".", "/", ":", "-", "_")
        ),
        "path_length": len(path),
        "query_length": len(query),
        "num_query_params": num_query_params,
        "has_port": int(parsed.port is not None and parsed.port not in (80, 443)),
        "entropy": round(_shannon_entropy(url_stripped), 4),
    }

    return features


def features_to_vector(features: dict[str, float | int]) -> list[float]:
    """Convert a feature dict to an ordered list matching FEATURE_NAMES."""
    return [float(features[name]) for name in FEATURE_NAMES]

