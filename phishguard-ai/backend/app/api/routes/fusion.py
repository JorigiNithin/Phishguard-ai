"""Multimodal fusion and scan history API routes."""

from __future__ import annotations

import json
from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.fusion import (
    DashboardStatistics,
    ExplainResponse,
    MultimodalFusionRequest,
    MultimodalFusionResponse,
    ScanDetailResponse,
    ScanHistoryItem,
    ScanHistoryResponse,
)
from app.services.fusion import fuse_modalities
from app.services.explainability import explain_scan
from app.services.scan_history import (
    delete_scan,
    get_scan,
    get_statistics,
    list_scans,
    save_scan,
)
from app.services.email_detector import analyze_email
from app.services.html_detector import analyze_html
from app.services.url_predictor import is_model_available, predict_url
from app.services.model_registry import model_registry
from app.services.screenshot_detector import analyze_screenshot

router = APIRouter(tags=["fusion"])


# ---------------------------------------------------------------------------
# POST /api/scans/multimodal
# ---------------------------------------------------------------------------


@router.post("/scans/multimodal", response_model=MultimodalFusionResponse)
async def scan_multimodal(
    body: MultimodalFusionRequest,
    db: Session = Depends(get_db),
) -> MultimodalFusionResponse:
    """Run multiple detectors and fuse their results."""
    modality_results: dict[str, Any] = {}
    errors: list[str] = []

    # --- URL ---
    if body.url is not None:
        if isinstance(body.url, str):
            try:
                if is_model_available():
                    modality_results["url"] = predict_url(body.url)
                else:
                    errors.append("URL detector model is not available.")
            except (ValueError, FileNotFoundError) as exc:
                errors.append(f"URL analysis failed: {exc}")
        elif isinstance(body.url, dict):
            modality_results["url"] = body.url
        else:
            errors.append("URL input must be a string URL or a detector result object.")

    # --- Email ---
    if body.email is not None:
        try:
            email_data = body.email
            if isinstance(email_data, dict) and (
                "risk_score" in email_data or "prediction" in email_data or "indicators" in email_data
            ):
                modality_results["email"] = email_data
            elif isinstance(email_data, dict):
                modality_results["email"] = analyze_email(
                    sender=email_data.get("sender", ""),
                    subject=email_data.get("subject", ""),
                    body=email_data.get("body", ""),
                    headers=email_data.get("headers"),
                )
            else:
                errors.append("Email input must be an object with email fields or a completed detector result.")
        except Exception as exc:
            errors.append(f"Email analysis failed: {exc}")

    # --- Screenshot ---
    if body.screenshot is not None:
        try:
            screenshot_data = body.screenshot
            if isinstance(screenshot_data, dict):
                modality_results["screenshot"] = screenshot_data
            else:
                errors.append("Screenshot input must be a detector result object.")
        except Exception as exc:
            errors.append(f"Screenshot analysis failed: {exc}")

    # --- HTML ---
    if body.html is not None:
        try:
            if isinstance(body.html, str):
                modality_results["html"] = analyze_html(body.html)
            elif isinstance(body.html, dict):
                modality_results["html"] = body.html
            else:
                errors.append("HTML input must be a string or a detector result object.")
        except Exception as exc:
            errors.append(f"HTML analysis failed: {exc}")

    if not modality_results:
        raise HTTPException(
            status_code=422,
            detail="No valid inputs provided. Supply at least one modality (url, email, screenshot, html)."
            + (f" Errors: {'; '.join(errors)}" if errors else ""),
        )

    # --- Fuse ---
    fusion_result = fuse_modalities(modality_results)

    if errors:
        fusion_result["explanation"].extend(
            [f"[Warning] {e}" for e in errors]
        )

    # --- Persist ---
    included = ", ".join(fusion_result["modalities_analyzed"])
    target = f"Multimodal analysis ({included})" if included else "Multimodal analysis"

    record = save_scan(
        db,
        scan_type="multimodal",
        prediction=fusion_result["overall_prediction"],
        risk_score=fusion_result["overall_risk_score"],
        confidence=None,
        model_used=fusion_result["model"],
        target_summary=target or "Multimodal scan",
        indicators=fusion_result["contributing_indicators"],
        explanation=fusion_result["explanation"],
        modality_results=modality_results,
    )

    fusion_result["scan_id"] = record.id
    return MultimodalFusionResponse(**fusion_result)


# ---------------------------------------------------------------------------
# GET /api/scans/history
# ---------------------------------------------------------------------------


@router.get("/scans/history", response_model=ScanHistoryResponse)
async def get_scan_history(
    scan_type: Optional[str] = Query(None, description="Filter by scan type"),
    prediction: Optional[str] = Query(None, description="Filter by prediction"),
    search: Optional[str] = Query(None, description="Search in target summary"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> ScanHistoryResponse:
    """Retrieve paginated scan history."""
    records, total = list_scans(
        db,
        scan_type=scan_type,
        prediction=prediction,
        search=search,
        page=page,
        page_size=page_size,
    )

    total_pages = max(1, (total + page_size - 1) // page_size)

    items = [
        ScanHistoryItem(
            id=r.id,
            scan_type=r.scan_type,
            prediction=r.prediction,
            risk_score=r.risk_score,
            target_summary=r.target_summary,
            status=r.status,
            created_at=r.created_at.isoformat() if isinstance(r.created_at, datetime) else str(r.created_at),
        )
        for r in records
    ]

    return ScanHistoryResponse(
        scans=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ---------------------------------------------------------------------------
# GET /api/scans/{scan_id}/explain
# ---------------------------------------------------------------------------


@router.get("/scans/{scan_id}/explain", response_model=ExplainResponse)
async def explain_scan_record(
    scan_id: str,
    db: Session = Depends(get_db),
) -> ExplainResponse:
    """Retrieve explainable AI breakdown for a scan."""
    record = get_scan(db, scan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scan not found.")

    modality_results = (
        json.loads(record.modality_results_json)
        if record.modality_results_json
        else None
    )
    indicators = (
        json.loads(record.indicators_json)
        if record.indicators_json
        else []
    )
    scan_dict = {
        "scan_type": record.scan_type,
        "prediction": record.prediction,
        "risk_score": record.risk_score,
        "confidence": record.confidence,
        "indicators": indicators,
    }
    explanations = explain_scan(scan_dict, modality_results=modality_results)
    return ExplainResponse(explanation=explanations)


# ---------------------------------------------------------------------------
# GET /api/scans/{scan_id}
# ---------------------------------------------------------------------------


@router.get("/scans/{scan_id}", response_model=ScanDetailResponse)
async def get_scan_detail(
    scan_id: str,
    db: Session = Depends(get_db),
) -> ScanDetailResponse:
    """Retrieve a single scan's full details."""
    record = get_scan(db, scan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scan not found.")

    return ScanDetailResponse(
        id=record.id,
        scan_type=record.scan_type,
        prediction=record.prediction,
        risk_score=record.risk_score,
        confidence=record.confidence,
        model_used=record.model_used,
        target_summary=record.target_summary,
        indicators=json.loads(record.indicators_json) if record.indicators_json else [],
        explanation=json.loads(record.explanation_json) if record.explanation_json else [],
        modality_results=json.loads(record.modality_results_json) if record.modality_results_json else None,
        status=record.status,
        created_at=record.created_at.isoformat() if isinstance(record.created_at, datetime) else str(record.created_at),
    )


# ---------------------------------------------------------------------------
# DELETE /api/scans/{scan_id}
# ---------------------------------------------------------------------------


@router.delete("/scans/{scan_id}")
async def delete_scan_record(
    scan_id: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a scan from history."""
    deleted = delete_scan(db, scan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return {"detail": "Scan deleted.", "id": scan_id}


# ---------------------------------------------------------------------------
# GET /api/dashboard/statistics
# ---------------------------------------------------------------------------


@router.get("/dashboard/statistics", response_model=DashboardStatistics)
async def get_dashboard_statistics(
    db: Session = Depends(get_db),
) -> DashboardStatistics:
    """Compute dashboard statistics from persisted scan data."""
    stats = get_statistics(db)
    stats["models_available"] = model_registry.available_count()
    return DashboardStatistics(**stats)
