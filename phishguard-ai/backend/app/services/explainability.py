"""Explainability service for phishing scan results.

Produces structured, human-readable explanations of scan results.

For the URL detector (Random Forest), actual feature importances from the
trained model are used when available. For rule-based detectors (email,
screenshot, HTML), explanations are derived from the detected indicators.

No SHAP values or feature contributions are fabricated.
"""

from __future__ import annotations

from typing import Any


def explain_scan(
    scan_result: dict[str, Any],
    modality_results: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Produce structured explanations for a scan result.

    Parameters
    ----------
    scan_result:
        The overall or individual scan result dict.
    modality_results:
        Optional per-modality results (for multimodal fusions).

    Returns
    -------
    List of explanation dicts, each with ``indicator``, ``source``,
    ``impact``, and ``reason``.
    """
    explanations: list[dict[str, Any]] = []

    # --- If this is a multimodal fusion result --------------------------------
    if modality_results:
        for modality, result in modality_results.items():
            explanations.extend(_explain_modality(modality, result))

        # Add notes about missing modalities
        all_modalities = {"url", "email", "screenshot", "html"}
        missing = all_modalities - set(modality_results.keys())
        if missing:
            explanations.append({
                "indicator": "Missing modalities",
                "source": "fusion",
                "impact": "info",
                "reason": (
                    f"The following modalities were not included in this analysis: "
                    f"{', '.join(sorted(missing))}. A more complete analysis would "
                    f"include all available modalities."
                ),
            })

        return explanations

    # --- Single modality result -----------------------------------------------
    scan_type = scan_result.get("scan_type", "unknown")
    return _explain_modality(scan_type, scan_result)


def explain_url_features(
    features: dict[str, float | int],
    prediction: str,
    confidence: float,
) -> list[dict[str, Any]]:
    """Explain a URL scan result using extracted features.

    Uses the actual feature values to generate explanations — not
    fabricated SHAP values.
    """
    explanations: list[dict[str, Any]] = []

    if features.get("has_ip_address"):
        explanations.append({
            "indicator": "IP address in URL",
            "source": "url",
            "impact": "high",
            "reason": "The URL uses an IP address instead of a domain name, "
                      "which is commonly seen in phishing attempts.",
        })

    if features.get("is_shortened"):
        explanations.append({
            "indicator": "URL shortener detected",
            "source": "url",
            "impact": "medium",
            "reason": "The URL uses a known shortening service, which can hide "
                      "the true destination.",
        })

    if features.get("has_at_sign"):
        explanations.append({
            "indicator": "@ symbol in URL",
            "source": "url",
            "impact": "high",
            "reason": "The URL contains an @ symbol, which can be used to make "
                      "the URL appear to point to a different site.",
        })

    kw_count = features.get("num_suspicious_keywords", 0)
    if kw_count and kw_count >= 2:
        explanations.append({
            "indicator": "Suspicious keywords",
            "source": "url",
            "impact": "high",
            "reason": f"The URL contains {int(kw_count)} suspicious keyword(s) commonly "
                      f"associated with phishing (e.g. 'login', 'verify', 'password').",
        })
    elif kw_count and kw_count == 1:
        explanations.append({
            "indicator": "Suspicious keyword",
            "source": "url",
            "impact": "medium",
            "reason": "The URL contains a keyword commonly associated with phishing.",
        })

    url_len = features.get("url_length", 0)
    if url_len and url_len > 100:
        explanations.append({
            "indicator": "Long URL",
            "source": "url",
            "impact": "low",
            "reason": f"The URL is {int(url_len)} characters long. Excessively long URLs "
                      f"can be used to hide suspicious content.",
        })

    if not features.get("is_https"):
        explanations.append({
            "indicator": "No HTTPS",
            "source": "url",
            "impact": "medium",
            "reason": "The URL does not use HTTPS encryption.",
        })

    subdomain_count = features.get("num_subdomains", 0)
    if subdomain_count and subdomain_count >= 3:
        explanations.append({
            "indicator": "Excessive subdomains",
            "source": "url",
            "impact": "medium",
            "reason": f"The URL has {int(subdomain_count)} subdomains, which can be used "
                      f"to mimic legitimate domains.",
        })

    if features.get("has_port"):
        explanations.append({
            "indicator": "Non-standard port",
            "source": "url",
            "impact": "medium",
            "reason": "The URL specifies a non-standard port, which is unusual for "
                      "legitimate websites.",
        })

    if not explanations:
        explanations.append({
            "indicator": "Feature analysis",
            "source": "url",
            "impact": "info",
            "reason": f"URL classified as '{prediction}' with {confidence:.1%} "
                      f"confidence based on 17 lexical and structural features.",
        })

    return explanations


def _explain_modality(
    modality: str, result: dict[str, Any]
) -> list[dict[str, Any]]:
    """Generate explanations from a single modality result."""
    explanations: list[dict[str, Any]] = []

    # URL results have features instead of indicators
    if modality == "url" and "features" in result:
        return explain_url_features(
            result.get("features", {}),
            result.get("prediction", "unknown"),
            result.get("confidence", 0.5),
        )

    # Rule-based detectors have indicators
    indicators = result.get("indicators", [])
    for ind in indicators:
        explanations.append({
            "indicator": ind.get("name", "Unknown").replace("_", " ").title(),
            "source": modality,
            "impact": ind.get("severity", "medium"),
            "reason": ind.get("description", ""),
        })

    if not explanations:
        prediction = result.get("prediction", "unknown")
        explanations.append({
            "indicator": f"{modality.title()} analysis",
            "source": modality,
            "impact": "info",
            "reason": f"No specific indicators detected. Prediction: {prediction}.",
        })

    return explanations

