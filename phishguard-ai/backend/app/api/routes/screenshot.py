"""Screenshot phishing scan endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.scan_common import MultimodalScanResponse
from app.services.screenshot_detector import analyze_screenshot, MAX_IMAGE_BYTES
from app.services.scan_history import save_detector_scan

router = APIRouter(tags=["scans"])

_ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
}


@router.post("/scans/screenshot", response_model=MultimodalScanResponse)
async def scan_screenshot(
    file: UploadFile = File(..., description="Screenshot image (PNG, JPEG)"),
    db: Session = Depends(get_db),
) -> MultimodalScanResponse:
    """Analyse a screenshot for phishing indicators using OCR and text analysis."""

    # Validate content type
    content_type = (file.content_type or "").lower()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{content_type}'. Accepted: PNG, JPEG.",
        )

    # Read file bytes with size guard
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {MAX_IMAGE_BYTES // (1024 * 1024)} MB.",
        )

    try:
        result = analyze_screenshot(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while analysing the screenshot.",
        )

    record = save_detector_scan(
        db,
        scan_type="screenshot",
        result=result,
        target_summary="Screenshot analysis",
    )
    result["scan_id"] = record.id
    return MultimodalScanResponse(**result)
