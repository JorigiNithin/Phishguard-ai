"""Pydantic schemas for URL scan requests and responses."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class URLScanRequest(BaseModel):
    """Request body for POST /api/scans/url."""

    url: str = Field(..., min_length=1, max_length=4096, description="URL to analyse")

    @field_validator("url")
    @classmethod
    def url_must_be_parseable(cls, v: str) -> str:
        from urllib.parse import urlparse

        v = v.strip()
        if not v:
            raise ValueError("URL must not be empty")
        parsed = urlparse(v)
        if not parsed.scheme:
            # Try with a scheme
            parsed = urlparse("http://" + v)
        if not parsed.hostname:
            raise ValueError("Invalid URL: cannot extract hostname")
        return v


class URLScanResponse(BaseModel):
    """Response body for POST /api/scans/url."""
    model_config = {"protected_namespaces": ()}

    scan_id: Optional[str] = None
    url: str
    prediction: str
    confidence: float
    risk_level: str
    features: dict[str, Any]
    model: str
