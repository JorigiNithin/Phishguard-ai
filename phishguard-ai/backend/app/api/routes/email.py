"""Email phishing scan endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.email_scan import EmailScanRequest
from app.schemas.scan_common import MultimodalScanResponse
from app.services.email_detector import analyze_email
from app.services.scan_history import save_detector_scan

router = APIRouter(tags=["scans"])


@router.post("/scans/email", response_model=MultimodalScanResponse)
async def scan_email(
    body: EmailScanRequest,
    db: Session = Depends(get_db),
) -> MultimodalScanResponse:
    """Analyse an email for phishing indicators using rule-based detection."""
    try:
        result = analyze_email(
            sender=body.sender,
            subject=body.subject,
            body=body.body,
            headers=body.headers,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    record = save_detector_scan(
        db,
        scan_type="email",
        result=result,
        target_summary="Email analysis",
    )
    result["scan_id"] = record.id
    return MultimodalScanResponse(**result)
