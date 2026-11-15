"""Rule-based email phishing detector.

Analyses email sender, subject, body and optional headers for phishing
indicators using pattern matching and heuristic rules.

This is a *rule-based* detector — it does NOT use a trained ML model.
It should be documented accordingly and must not claim ML confidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Indicator data class
# ---------------------------------------------------------------------------


@dataclass
class _Indicator:
    name: str
    description: str
    severity: str  # "low" | "medium" | "high"


# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

_URGENT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(urgent|immediately|right\s*away|act\s*now)\b", re.I),
    re.compile(r"\b(limited\s*time|expire[sd]?|expiring|within\s+\d+\s*(hour|day|minute)s?)\b", re.I),
    re.compile(r"\b(account\s*(will\s+be\s+)?(suspend|terminat|clos|restrict|lock|delet|deactivat))", re.I),
    re.compile(r"\b(final\s*warning|last\s*chance|immediate\s*action)\b", re.I),
    re.compile(r"!{3,}"),
]

_CREDENTIAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(password|passwd|pass\s*code|pin\s*code)\b", re.I),
    re.compile(r"\b(verify|confirm|validate|update)\s+(your\s+)?(account|identity|information|credentials?)\b", re.I),
    re.compile(r"\b(log\s*in|sign\s*in|authentication)\s+(here|now|required|needed)\b", re.I),
    re.compile(r"\b(ssn|social\s*security\s*(number)?)\b", re.I),
    re.compile(r"\b(credit\s*card|debit\s*card|card\s*number|cvv|expir(y|ation)\s*date)\b", re.I),
]

_FINANCIAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(wire\s*transfer|bank\s*transfer|western\s*union|moneygram)\b", re.I),
    re.compile(r"\b(bitcoin|cryptocurrency|crypto\s*wallet|btc|ethereum)\b", re.I),
    re.compile(r"\b(gift\s*card|itunes\s*card|google\s*play\s*card|steam\s*card)\b", re.I),
    re.compile(r"\b(won|winner|lottery|prize|jackpot|inheritance|beneficiary)\b", re.I),
    re.compile(r"\b(invoice\s*(attached|enclosed|overdue)|outstanding\s*payment)\b", re.I),
]

_BRAND_NAMES: frozenset[str] = frozenset({
    "paypal", "amazon", "apple", "microsoft", "google", "netflix",
    "facebook", "instagram", "whatsapp", "linkedin", "twitter",
    "bank of america", "chase", "wells fargo", "citibank",
    "dropbox", "adobe", "docusign", "outlook", "office 365",
    "dhl", "fedex", "ups", "usps", "irs", "hmrc",
})

_SUSPICIOUS_EXTENSIONS: frozenset[str] = frozenset({
    ".exe", ".scr", ".bat", ".cmd", ".vbs", ".js", ".wsf",
    ".pif", ".msi", ".com", ".hta", ".cpl", ".ps1", ".jar",
})

_FREE_EMAIL_PROVIDERS: frozenset[str] = frozenset({
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "aol.com", "mail.com", "protonmail.com", "tutanota.com",
    "yandex.com", "zoho.com", "mail.ru", "gmx.com",
})

_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)

_HREF_MISMATCH_RE = re.compile(
    r"""<a\s[^>]*href\s*=\s*["']([^"']+)["'][^>]*>(.*?)</a>""",
    re.I | re.S,
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_email(
    sender: str,
    subject: str,
    body: str,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Analyse an email for phishing indicators.

    Returns a dict matching the ``MultimodalScanResponse`` schema.
    """
    indicators: list[_Indicator] = []
    full_text = f"{subject} {body}"

    # --- 1. Sender checks ---------------------------------------------------
    _check_sender(sender, full_text, indicators)

    # --- 2. Urgency / pressure -----------------------------------------------
    _check_urgency(full_text, indicators)

    # --- 3. Credential requests ----------------------------------------------
    _check_credentials(full_text, indicators)

    # --- 4. Financial lures --------------------------------------------------
    _check_financial(full_text, indicators)

    # --- 5. Suspicious links -------------------------------------------------
    _check_links(body, indicators)

    # --- 6. Brand impersonation ----------------------------------------------
    _check_brand_impersonation(sender, full_text, indicators)

    # --- 7. Suspicious attachments -------------------------------------------
    _check_attachments(full_text, indicators)

    # --- 8. Display-vs-actual URL mismatch -----------------------------------
    _check_url_mismatch(body, indicators)

    # --- 9. Header anomalies (if provided) -----------------------------------
    if headers:
        _check_headers(sender, headers, indicators)

    # --- 10. Generic greeting ------------------------------------------------
    _check_generic_greeting(body, indicators)

    # --- Score ---------------------------------------------------------------
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
        else ["No phishing indicators detected in this email."]
    )

    return {
        "scan_type": "email",
        "prediction": prediction,
        "risk_score": risk_score,
        "confidence": None,  # Rule-based — no calibrated confidence
        "indicators": [
            {"name": i.name, "description": i.description, "severity": i.severity}
            for i in indicators
        ],
        "explanation": explanation,
        "model": "Rule-based Email Analyzer v1.0",
    }


# ---------------------------------------------------------------------------
# Private checkers
# ---------------------------------------------------------------------------


def _check_sender(sender: str, full_text: str, indicators: list[_Indicator]) -> None:
    """Check sender address for suspicious patterns."""
    sender_lower = sender.lower().strip()
    domain = sender_lower.split("@")[-1] if "@" in sender_lower else ""

    # Free email provider impersonating a brand
    if domain in _FREE_EMAIL_PROVIDERS:
        text_lower = full_text.lower()
        for brand in _BRAND_NAMES:
            if brand in text_lower and brand not in domain:
                indicators.append(
                    _Indicator(
                        name="sender_domain_mismatch",
                        description=f"Email mentions '{brand}' but is sent from a free email provider ({domain}).",
                        severity="high",
                    )
                )
                break

    # Suspicious characters in local part
    local = sender_lower.split("@")[0] if "@" in sender_lower else sender_lower
    if re.search(r"[0-9]{5,}", local):
        indicators.append(
            _Indicator(
                name="suspicious_sender_local",
                description="Sender local part contains a long digit sequence, common in throwaway addresses.",
                severity="low",
            )
        )


def _check_urgency(text: str, indicators: list[_Indicator]) -> None:
    matches = 0
    for pat in _URGENT_PATTERNS:
        if pat.search(text):
            matches += 1
    if matches >= 2:
        indicators.append(
            _Indicator(
                name="high_urgency",
                description="Multiple urgency or threatening phrases detected (e.g. 'act now', 'account suspended').",
                severity="high",
            )
        )
    elif matches == 1:
        indicators.append(
            _Indicator(
                name="urgency_language",
                description="Urgency or threatening language detected.",
                severity="medium",
            )
        )


def _check_credentials(text: str, indicators: list[_Indicator]) -> None:
    matches = sum(1 for pat in _CREDENTIAL_PATTERNS if pat.search(text))
    if matches >= 2:
        indicators.append(
            _Indicator(
                name="credential_request",
                description="Multiple credential or personal-information requests detected.",
                severity="high",
            )
        )
    elif matches == 1:
        indicators.append(
            _Indicator(
                name="credential_mention",
                description="A credential or personal-information term was mentioned.",
                severity="medium",
            )
        )


def _check_financial(text: str, indicators: list[_Indicator]) -> None:
    matches = sum(1 for pat in _FINANCIAL_PATTERNS if pat.search(text))
    if matches >= 2:
        indicators.append(
            _Indicator(
                name="financial_request",
                description="Multiple financial or payment-related requests detected.",
                severity="high",
            )
        )
    elif matches == 1:
        indicators.append(
            _Indicator(
                name="financial_mention",
                description="Financial or payment-related language detected.",
                severity="medium",
            )
        )


def _check_links(body: str, indicators: list[_Indicator]) -> None:
    """Check URLs found in the email body."""
    urls = _URL_RE.findall(body)
    if not urls:
        return

    suspicious_count = 0
    for url in urls:
        try:
            parsed = urlparse(url)
            hostname = (parsed.hostname or "").lower()
        except Exception:
            suspicious_count += 1
            continue

        # IP address URL
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname):
            indicators.append(
                _Indicator(
                    name="ip_address_link",
                    description=f"Email contains a link to an IP address: {hostname}",
                    severity="high",
                )
            )
            continue

        # Very long URL
        if len(url) > 200:
            suspicious_count += 1

        # Suspicious TLDs
        if hostname.endswith((".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".buzz")):
            suspicious_count += 1

    if suspicious_count > 0:
        indicators.append(
            _Indicator(
                name="suspicious_links",
                description=f"{suspicious_count} suspicious URL(s) found in the email body.",
                severity="medium",
            )
        )


def _check_brand_impersonation(
    sender: str, text: str, indicators: list[_Indicator]
) -> None:
    text_lower = text.lower()
    sender_lower = sender.lower()
    for brand in _BRAND_NAMES:
        if brand in text_lower and brand not in sender_lower:
            # Already handled by sender_domain_mismatch for free providers
            domain = sender_lower.split("@")[-1] if "@" in sender_lower else ""
            if domain not in _FREE_EMAIL_PROVIDERS:
                # Official-looking domain that doesn't match the brand
                if brand.replace(" ", "") not in domain:
                    indicators.append(
                        _Indicator(
                            name="brand_impersonation",
                            description=f"Email references '{brand}' but sender domain '{domain}' does not match.",
                            severity="high",
                        )
                    )
                    return  # One indicator is enough


def _check_attachments(text: str, indicators: list[_Indicator]) -> None:
    text_lower = text.lower()
    found = [ext for ext in _SUSPICIOUS_EXTENSIONS if ext in text_lower]
    if found:
        indicators.append(
            _Indicator(
                name="suspicious_attachment",
                description=f"Mentions potentially dangerous file type(s): {', '.join(found)}.",
                severity="high",
            )
        )


def _check_url_mismatch(body: str, indicators: list[_Indicator]) -> None:
    """Detect <a href="X">Y</a> where Y looks like a URL different from X."""
    for match in _HREF_MISMATCH_RE.finditer(body):
        href = match.group(1).strip()
        display = match.group(2).strip()
        # Only check if the display text itself looks like a URL
        if not re.match(r"https?://", display, re.I):
            continue
        try:
            href_host = urlparse(href).hostname or ""
            display_host = urlparse(display).hostname or ""
        except Exception:
            continue
        if href_host and display_host and href_host.lower() != display_host.lower():
            indicators.append(
                _Indicator(
                    name="url_display_mismatch",
                    description=f"Link displays '{display_host}' but actually points to '{href_host}'.",
                    severity="high",
                )
            )
            return  # Report once


def _check_headers(
    sender: str, headers: dict[str, str], indicators: list[_Indicator]
) -> None:
    """Check email headers for anomalies."""
    reply_to = headers.get("Reply-To", headers.get("reply-to", ""))
    if reply_to:
        reply_domain = reply_to.split("@")[-1].strip().lower() if "@" in reply_to else ""
        sender_domain = sender.split("@")[-1].strip().lower() if "@" in sender else ""
        if reply_domain and sender_domain and reply_domain != sender_domain:
            indicators.append(
                _Indicator(
                    name="reply_to_mismatch",
                    description=f"Reply-To domain ({reply_domain}) differs from sender domain ({sender_domain}).",
                    severity="high",
                )
            )

    return_path = headers.get("Return-Path", headers.get("return-path", ""))
    if return_path and "@" in return_path:
        rp_domain = return_path.split("@")[-1].strip("<> ").lower()
        sender_domain = sender.split("@")[-1].strip().lower() if "@" in sender else ""
        if rp_domain and sender_domain and rp_domain != sender_domain:
            indicators.append(
                _Indicator(
                    name="return_path_mismatch",
                    description=f"Return-Path domain ({rp_domain}) differs from sender domain ({sender_domain}).",
                    severity="medium",
                )
            )


def _check_generic_greeting(body: str, indicators: list[_Indicator]) -> None:
    """Flag emails that use generic greetings instead of addressing the recipient by name."""
    first_200 = body[:200].lower()
    generic = [
        r"\bdear\s+(customer|user|account\s*holder|member|sir|madam|valued)\b",
        r"\bhello\s+(customer|user|member)\b",
        r"\battention\s+(customer|user|account\s*holder)\b",
    ]
    for pat in generic:
        if re.search(pat, first_200, re.I):
            indicators.append(
                _Indicator(
                    name="generic_greeting",
                    description="Uses a generic greeting instead of addressing you by name.",
                    severity="low",
                )
            )
            return

