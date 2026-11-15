"""Pydantic schemas shared across the application."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ModelStatus(str, Enum):
    """Possible statuses for a detection model."""
    NOT_IMPLEMENTED = "not_implemented"
    IMPLEMENTED = "implemented"
    TRAINING = "training"
    TRAINED = "trained"
    ERROR = "error"


class RiskLevel(str, Enum):
    """Possible risk levels for a scan result."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Modality(str, Enum):
    """Input modality for a detection model."""
    URL = "url"
    EMAIL = "email"
    SCREENSHOT = "screenshot"
    HTML = "html"
    MULTIMODAL = "multimodal"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Health-check response."""
    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    environment: str


# ---------------------------------------------------------------------------
# Model info
# ---------------------------------------------------------------------------

class DetectionModelInfo(BaseModel):
    """Status information for a single detection model."""
    model_config = {"protected_namespaces": ()}

    id: str
    name: str
    modality: Modality
    status: ModelStatus
    model_type: Optional[str] = None
    training_status: Optional[str] = None
    available: bool = False
    description: str = ""


class ModelsResponse(BaseModel):
    """Response for the models endpoint."""
    models: list[DetectionModelInfo]
    total: int


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

class StatisticsResponse(BaseModel):
    """Aggregated scan statistics."""
    total_scans: int = 0
    high_risk: int = 0
    suspicious: int = 0
    safe: int = 0
    models_available: int = 0
    risk_distribution: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Scans / History
# ---------------------------------------------------------------------------

class ScanRecord(BaseModel):
    """A single historical scan record."""
    model_config = {"protected_namespaces": ()}

    id: str
    input_type: Modality
    target: str
    risk_level: RiskLevel
    timestamp: datetime
    model_used: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class ScansResponse(BaseModel):
    """Response for the scans endpoint."""
    scans: list[ScanRecord] = Field(default_factory=list)
    total: int = 0


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

class VersionResponse(BaseModel):
    """Application version information."""
    name: str
    version: str
    environment: str


# ---------------------------------------------------------------------------
# Generic error
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """Standard error payload."""
    detail: str
    status_code: int = 500
