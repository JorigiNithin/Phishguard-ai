"""Unit tests for URL feature extraction module."""

from __future__ import annotations

import pytest

from app.services.url_features import (
    FEATURE_NAMES,
    extract_features,
    features_to_vector,
)


def test_feature_names_order_and_count():
    assert len(FEATURE_NAMES) == 17
    assert "url_length" in FEATURE_NAMES
    assert "domain_length" in FEATURE_NAMES
    assert "has_ip_address" in FEATURE_NAMES
    assert "is_shortened" in FEATURE_NAMES
    assert "entropy" in FEATURE_NAMES


def test_extract_features_normal_url():
    features = extract_features("https://www.google.com/search?q=test")
    assert features["is_https"] == 1
    assert features["has_ip_address"] == 0
    assert features["is_shortened"] == 0
    assert features["domain_length"] > 0
    assert features["num_dots"] >= 2
    assert features["entropy"] > 0


def test_extract_features_ip_address():
    features = extract_features("http://192.168.1.1:8080/login.php")
    assert features["has_ip_address"] == 1
    assert features["has_port"] == 1
    assert features["is_https"] == 0
    assert features["num_suspicious_keywords"] >= 1


def test_extract_features_shortened_url():
    features = extract_features("https://bit.ly/3xYqz")
    assert features["is_shortened"] == 1


def test_extract_features_at_sign_and_hyphen():
    features = extract_features("http://legit-site.com@evil-site.com/signin")
    assert features["has_at_sign"] == 1
    assert features["num_hyphens"] >= 2
    assert features["num_suspicious_keywords"] >= 1


def test_extract_features_empty_or_invalid():
    with pytest.raises(ValueError):
        extract_features("")

    with pytest.raises(ValueError):
        extract_features("   ")


def test_features_to_vector_ordering():
    features = extract_features("https://example.com")
    vector = features_to_vector(features)
    assert len(vector) == len(FEATURE_NAMES)
    for i, name in enumerate(FEATURE_NAMES):
        assert vector[i] == float(features[name])

