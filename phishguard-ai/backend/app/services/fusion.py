"""Multimodal fusion engine.

Combines results from multiple phishing detection modalities into a single
overall risk assessment.

Fusion formula (documented):
    overall_risk = Σ (weight_i × normalized_score_i) / Σ weight_i

Default weights (configurable):
    url:        0.30
    email:      0.30
    screenshot: 0.15
    html:       0.25

Missing modalities are excluded from the sum — their weight does not
count toward the denominator. Missing data is never treated as safe.

Thresholds:
    overall_risk >= 60  →  "phishing"
    overall_risk >= 30  →  "suspicious"
    overall_risk <  30  →  "safe"

This fusion produces a *heuristic weighted risk score*, NOT a calibrated
probability. The ``confidence`` field is always ``null``.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Default modality weights
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS: dict[str, float] = {
    "url": 0.30,
    "email": 0.30,
    "screenshot": 0.15,
    "html": 0.25,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def fuse_modalities(
    modality_results: dict[str, dict[str, Any]],
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Combine multiple modality scan results into one overall assessment.

    Parameters
    ----------
    modality_results:
        Dict mapping modality name (``"url"``, ``"email"``, etc.) to its
        individual scan result dict. Each result must contain at least
        ``risk_score`` (int 0-100) and ``prediction`` (str). URL results
        use ``risk_level`` instead of ``risk_score`` and are normalized.
    weights:
        Optional custom modality weights. Defaults to ``DEFAULT_WEIGHTS``.

    Returns
    -------
    dict matching the ``MultimodalFusionResponse`` schema.
    """
    w = weights or DEFAULT_WEIGHTS

    # --- Normalize and collect available modality scores --------------------
    available: dict[str, float] = {}
    for modality, result in modality_results.items():
        score = _normalize_score(modality, result)
        if score is not None:
            available[modality] = score

    if not available:
        return {
            "overall_risk_score": 0,
            "overall_prediction": "safe",
            "modalities_analyzed": [],
            "modality_results": modality_results,
            "contributing_indicators": [],
            "explanation": ["No modality results available for fusion."],
            "fusion_weights": w,
            "confidence": None,
            "model": "Weighted Multimodal Fusion Engine v1.0",
        }

    # --- Weighted average ---------------------------------------------------
    total_weight = sum(w.get(m, 0.10) for m in available)
    if total_weight == 0:
        total_weight = 1.0  # safety

    weighted_sum = sum(w.get(m, 0.10) * score for m, score in available.items())
    overall_risk = round(weighted_sum / total_weight)
    overall_risk = max(0, min(100, overall_risk))

    # --- Prediction ---------------------------------------------------------
    if overall_risk >= 60:
        overall_prediction = "phishing"
    elif overall_risk >= 30:
        overall_prediction = "suspicious"
    else:
        overall_prediction = "safe"

    # --- Aggregate indicators (deduplicated) --------------------------------
    contributing_indicators = _collect_indicators(modality_results)

    # --- Explanation --------------------------------------------------------
    explanation = _build_explanation(available, modality_results, overall_risk, overall_prediction, w)

    return {
        "overall_risk_score": overall_risk,
        "overall_prediction": overall_prediction,
        "modalities_analyzed": list(available.keys()),
        "modality_results": modality_results,
        "contributing_indicators": contributing_indicators,
        "explanation": explanation,
        "fusion_weights": w,
        "confidence": None,  # Heuristic — not a calibrated probability
        "model": "Weighted Multimodal Fusion Engine v1.0",
    }


# ---------------------------------------------------------------------------
# Score normalization
# ---------------------------------------------------------------------------


def _normalize_score(modality: str, result: dict[str, Any]) -> float | None:
    """Normalize a modality result to a 0-100 risk score.

    URL results use ``risk_level`` + ``confidence`` rather than ``risk_score``.
    """
    # Section 3 detectors already have risk_score 0-100
    if "risk_score" in result:
        return float(result["risk_score"])

    # Section 2 URL detector uses risk_level + confidence
    if "risk_level" in result and "prediction" in result:
        return _url_result_to_score(result)

    return None


def _url_result_to_score(result: dict[str, Any]) -> float:
    """Convert URL detector output to a 0-100 risk score."""
    prediction = result.get("prediction", "")
    confidence = result.get("confidence", 0.5)
    risk_level = result.get("risk_level", "low")

    # Map risk_level to base scores
    level_map = {
        "safe": 5,
        "low": 20,
        "medium": 50,
        "high": 75,
        "critical": 95,
    }
    base = level_map.get(risk_level, 50)

    # If phishing with high confidence, push score up
    if prediction == "phishing":
        return max(base, min(100, int(confidence * 100)))
    else:
        return min(base, int((1 - confidence) * 100))


# ---------------------------------------------------------------------------
# Indicator aggregation (deduplicated)
# ---------------------------------------------------------------------------


def _collect_indicators(
    modality_results: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect indicators from all modalities, deduplicating by name."""
    seen_names: set[str] = set()
    collected: list[dict[str, Any]] = []

    for modality, result in modality_results.items():
        indicators = result.get("indicators", [])
        # For URL results, features are not indicators in the same format
        if isinstance(indicators, list):
            for ind in indicators:
                name = ind.get("name", "")
                # Deduplicate by indicator name across modalities
                if name and name not in seen_names:
                    seen_names.add(name)
                    collected.append({
                        **ind,
                        "source": modality,
                    })

    # Sort by severity: high first
    severity_order = {"high": 0, "medium": 1, "low": 2}
    collected.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))

    return collected


# ---------------------------------------------------------------------------
# Explanation builder
# ---------------------------------------------------------------------------


def _build_explanation(
    available: dict[str, float],
    modality_results: dict[str, dict[str, Any]],
    overall_risk: int,
    overall_prediction: str,
    weights: dict[str, float],
) -> list[str]:
    """Build human-readable explanation lines."""
    lines: list[str] = []

    lines.append(
        f"Overall risk score: {overall_risk}/100 ({overall_prediction}). "
        f"Based on {len(available)} modality/modalities."
    )

    for modality, score in available.items():
        weight_pct = int(weights.get(modality, 0.10) * 100)
        result = modality_results.get(modality, {})
        pred = result.get("prediction", "unknown")
        lines.append(
            f"  • {modality.upper()}: risk score {int(score)}/100, prediction '{pred}' (weight {weight_pct}%)"
        )

    # Note missing modalities
    all_modalities = {"url", "email", "screenshot", "html"}
    missing = all_modalities - set(available.keys())
    if missing:
        lines.append(
            f"Missing modalities (not analysed): {', '.join(sorted(missing))}. "
            f"Missing data is excluded, not treated as safe."
        )

    return lines

