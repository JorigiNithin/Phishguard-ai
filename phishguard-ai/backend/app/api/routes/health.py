"""Health and version endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthResponse, VersionResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return application health status."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )


@router.get("/version", response_model=VersionResponse)
async def get_version() -> VersionResponse:
    """Return application version information."""
    return VersionResponse(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )
