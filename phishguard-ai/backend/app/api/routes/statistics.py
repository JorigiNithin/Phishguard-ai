"""Statistics and scan-history endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.common import ScansResponse, StatisticsResponse
from app.services.model_registry import model_registry
from app.services.scan_history import get_statistics as get_db_statistics, list_scans as list_scan_records

router = APIRouter(tags=["analytics"])


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    db: Session = Depends(get_db),
) -> StatisticsResponse:
    """Return aggregated scan statistics from the persisted database."""
    stats = get_db_statistics(db)
    stats["models_available"] = model_registry.available_count()
    return StatisticsResponse(**stats)


@router.get("/scans", response_model=ScansResponse)
async def list_scans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ScansResponse:
    """Return a paginated list of scan history records."""
    records, total = list_scan_records(
        db,
        page=page,
        page_size=page_size,
    )
    scans = [
        {
            "id": record.id,
            "input_type": record.scan_type,
            "target": record.target_summary or record.scan_type,
            "risk_level": {
                "phishing": "high",
                "suspicious": "medium",
                "safe": "safe",
                "legitimate": "safe",
            }.get(record.prediction, "safe"),
            "timestamp": record.created_at,
            "model_used": record.model_used,
            "details": {"status": record.status, "risk_score": record.risk_score},
        }
        for record in records
    ]
    return ScansResponse(scans=scans, total=total)
