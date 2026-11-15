"""URL prediction service – loads the trained model and runs inference."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.core.logging import logger
from app.services.url_features import FEATURE_NAMES, extract_features, features_to_vector

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_MODEL_PATH = _PROJECT_ROOT / "models" / "url_detector.joblib"
_META_PATH = _PROJECT_ROOT / "models" / "url_detector_meta.json"

# Module-level cache
_clf: Any | None = None
_meta: dict[str, Any] | None = None


def _load_model() -> tuple[Any, dict[str, Any]]:
    """Load the model and metadata from disk (cached after first call)."""
    global _clf, _meta
    if _clf is not None and _meta is not None:
        return _clf, _meta

    if not _MODEL_PATH.exists():
        raise FileNotFoundError(
            f"URL detector model not found at {_MODEL_PATH}. "
            "Run `python scripts/train_url_model.py` to train it."
        )

    logger.info("Loading URL detector model from %s", _MODEL_PATH)
    _clf = joblib.load(_MODEL_PATH)

    if _META_PATH.exists():
        with open(_META_PATH) as f:
            _meta = json.load(f)
    else:
        _meta = {"model_type": "RandomForestClassifier", "metrics": {}}

    return _clf, _meta


def is_model_available() -> bool:
    """Check whether the trained model file exists."""
    return _MODEL_PATH.exists()


def get_model_metrics() -> dict[str, Any]:
    """Return training metrics from the metadata file."""
    if _META_PATH.exists():
        with open(_META_PATH) as f:
            meta = json.load(f)
        return meta.get("metrics", {})
    return {}


def predict_url(url: str) -> dict[str, Any]:
    """Run phishing prediction on a single URL.

    Returns a dict with prediction, confidence, and extracted features.
    Raises FileNotFoundError if the model is not trained.
    Raises ValueError if the URL cannot be parsed.
    """
    clf, meta = _load_model()

    # Extract features
    features = extract_features(url)
    vector = features_to_vector(features)
    X = np.array([vector], dtype=np.float64)

    # Predict
    pred = clf.predict(X)[0]
    proba = clf.predict_proba(X)[0]

    label = "phishing" if pred == 1 else "legitimate"
    confidence = float(proba[pred])

    return {
        "url": url,
        "prediction": label,
        "confidence": round(confidence, 4),
        "risk_level": _risk_from_confidence(pred, confidence),
        "features": features,
        "model": meta.get("model_type", "RandomForestClassifier"),
    }


def _risk_from_confidence(pred: int, confidence: float) -> str:
    """Map prediction + confidence to a risk level string."""
    if pred == 0:  # legitimate
        if confidence >= 0.8:
            return "safe"
        return "low"
    else:  # phishing
        if confidence >= 0.9:
            return "critical"
        if confidence >= 0.7:
            return "high"
        return "medium"

