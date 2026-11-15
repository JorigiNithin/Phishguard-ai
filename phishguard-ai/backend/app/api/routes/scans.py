"""URL scan endpoint."""

from __future__ import annotations

from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.url_scan import URLScanRequest, URLScanResponse
from app.services.url_predictor import is_model_available, predict_url
from app.services.scan_history import save_detector_scan

router = APIRouter(tags=["scans"])


@router.post("/scans/url", response_model=URLScanResponse)
async def scan_url(body: URLScanRequest, db: Session = Depends(get_db)) -> URLScanResponse:
    """Analyse a URL for phishing indicators using the trained model."""
    if not is_model_available():
        raise HTTPException(
            status_code=503,
            detail="URL detection model is not available. Train it first.",
        )

    try:
        result = predict_url(body.url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    host = urlparse(result["url"]).hostname or "URL analysis"
    record = save_detector_scan(
        db,
        scan_type="url",
        result=result,
        target_summary=host[:200],
    )
    result["scan_id"] = record.id
    return URLScanResponse(**result)
