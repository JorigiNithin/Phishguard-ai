"""Pydantic schemas for multimodal fusion and scan history."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Multimodal fusion
# ---------------------------------------------------------------------------

class MultimodalFusionRequest(BaseModel):
    """Request body for POST /api/scans/multimodal."""

    url: Optional[Any] = Field(None, description="URL string or a URL detector result payload")
    email: Optional[Any] = Field(None, description="Email content or a completed email-detector result")
    screenshot: Optional[Any] = Field(None, description="Screenshot detector payload or image metadata")
    html: Optional[Any] = Field(None, description="HTML source or a completed HTML-detector result")


class MultimodalFusionResponse(BaseModel):
    """Response for multimodal fusion scan."""
    model_config = {"protected_namespaces": ()}

    overall_risk_score: int = Field(..., ge=0, le=100)
    overall_prediction: str
    modalities_analyzed: list[str]
    modality_results: dict[str, Any]
    contributing_indicators: list[dict[str, Any]]
    explanation: list[str]
    fusion_weights: dict[str, float]
    confidence: Optional[float] = None
    model: str
    scan_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Explainability
# ---------------------------------------------------------------------------

class ExplainableIndicator(BaseModel):
    """A single explainable indicator."""

    indicator: str
    source: str
    impact: str
    reason: str


class ExplainResponse(BaseModel):
    """Response for the explain endpoint."""

    explanation: list[ExplainableIndicator]


# ---------------------------------------------------------------------------
# Scan history
# ---------------------------------------------------------------------------

class ScanHistoryItem(BaseModel):
    """A single scan history entry (summary)."""

    id: str
    scan_type: str
    prediction: str
    risk_score: int
    target_summary: Optional[str] = None
    status: str
    created_at: str


class ScanHistoryResponse(BaseModel):
    """Paginated scan history response."""

    scans: list[ScanHistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ScanDetailResponse(BaseModel):
    """Detailed scan result from history."""
    model_config = {"protected_namespaces": ()}

    id: str
    scan_type: str
    prediction: str
    risk_score: int
    confidence: Optional[float] = None
    model_used: Optional[str] = None
    target_summary: Optional[str] = None
    indicators: list[dict[str, Any]] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)
    modality_results: Optional[dict[str, Any]] = None
    status: str
    created_at: str


class DashboardStatistics(BaseModel):
    """Dashboard statistics from the database."""

    total_scans: int = 0
    high_risk: int = 0
    suspicious: int = 0
    safe: int = 0
    models_available: int = 0
    risk_distribution: list[dict[str, Any]] = Field(default_factory=list)
    modality_usage: dict[str, int] = Field(default_factory=dict)
    recent_scans: list[ScanHistoryItem] = Field(default_factory=list)

