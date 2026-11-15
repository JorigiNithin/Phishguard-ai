"""HTML phishing scan endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.html_scan import HTMLScanRequest
from app.schemas.scan_common import MultimodalScanResponse
from app.services.html_detector import analyze_html
from app.services.scan_history import save_detector_scan

router = APIRouter(tags=["scans"])


@router.post("/scans/html", response_model=MultimodalScanResponse)
async def scan_html(
    body: HTMLScanRequest,
    db: Session = Depends(get_db),
) -> MultimodalScanResponse:
    """Analyse raw HTML source for phishing indicators using static analysis."""
    try:
        result = analyze_html(body.html)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    record = save_detector_scan(
        db,
        scan_type="html",
        result=result,
        target_summary="HTML analysis",
    )
    result["scan_id"] = record.id
    return MultimodalScanResponse(**result)
