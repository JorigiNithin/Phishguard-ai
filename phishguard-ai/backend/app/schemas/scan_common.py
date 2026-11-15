"""Common Pydantic schemas shared across all scan endpoints (email, screenshot, HTML)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ScanIndicator(BaseModel):
    """A single detected phishing indicator."""

    name: str = Field(..., description="Short identifier for the indicator")
    description: str = Field(..., description="Human-readable explanation")
    severity: str = Field(..., description="low, medium, or high")


class MultimodalScanResponse(BaseModel):
    """Consistent response structure for email, screenshot, and HTML scans."""

    scan_type: str = Field(..., description="email, screenshot, or html")
    prediction: str = Field(..., description="phishing, suspicious, or safe")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score 0-100")
    confidence: Optional[float] = Field(
        None,
        description="Calibrated model confidence (null for rule-based detectors)",
    )
    indicators: list[ScanIndicator] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)
    model: str = Field(..., description="Name of the detector that produced this result")
    details: Optional[dict[str, Any]] = Field(
        None, description="Additional detector-specific data"
    )
    scan_id: Optional[str] = Field(None, description="Persisted scan history identifier")
