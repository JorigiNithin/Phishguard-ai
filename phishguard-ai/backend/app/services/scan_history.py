"""Scan history CRUD operations."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.db.models import ScanRecord
from app.services.explainability import explain_scan
from app.services.fusion import fuse_modalities


def save_scan(
    db: Session,
    *,
    scan_type: str,
    prediction: str,
    risk_score: int,
    confidence: float | None = None,
    model_used: str | None = None,
    target_summary: str | None = None,
    indicators: list[dict[str, Any]] | None = None,
    explanation: list[str] | None = None,
    modality_results: dict[str, Any] | None = None,
    status: str = "completed",
) -> ScanRecord:
    """Persist a scan result and return the record."""
    sanitized_modality_results = _sanitize_modality_results(modality_results)
    record = ScanRecord(
        scan_type=scan_type,
        prediction=prediction,
        risk_score=risk_score,
        confidence=confidence,
        model_used=model_used,
        target_summary=_truncate(target_summary, 500) if target_summary else None,
        indicators_json=json.dumps(indicators) if indicators else None,
        explanation_json=json.dumps(explanation) if explanation else None,
        modality_results_json=json.dumps(sanitized_modality_results) if sanitized_modality_results else None,
        status=status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def save_detector_scan(
    db: Session,
    *,
    scan_type: str,
    result: dict[str, Any],
    target_summary: str,
) -> ScanRecord:
    """Persist a single-modality result without retaining its raw input."""
    fusion = fuse_modalities({scan_type: result})
    structured_explanation = explain_scan(result)
    indicators = [
        {
            "name": item["indicator"],
            "description": item["reason"],
            "severity": item["impact"] if item["impact"] in {"low", "medium", "high"} else "low",
            "source": item["source"],
        }
        for item in structured_explanation
        if item["impact"] != "info"
    ]

    return save_scan(
        db,
        scan_type=scan_type,
        prediction=fusion["overall_prediction"],
        risk_score=fusion["overall_risk_score"],
        confidence=result.get("confidence"),
        model_used=result.get("model"),
        target_summary=target_summary,
        indicators=indicators,
        explanation=[item["reason"] for item in structured_explanation],
        modality_results={scan_type: result},
    )


def get_scan(db: Session, scan_id: str) -> ScanRecord | None:
    """Get a single scan by ID."""
    return db.query(ScanRecord).filter(ScanRecord.id == scan_id).first()


def list_scans(
    db: Session,
    *,
    scan_type: str | None = None,
    prediction: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ScanRecord], int]:
    """List scans with optional filters and pagination.

    Returns (records, total_count).
    """
    query = db.query(ScanRecord)

    if scan_type:
        query = query.filter(ScanRecord.scan_type == scan_type)
    if prediction:
        query = query.filter(ScanRecord.prediction == prediction)
    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            ScanRecord.target_summary.ilike(like_pattern)
            | ScanRecord.scan_type.ilike(like_pattern)
        )

    total = query.count()
    records = (
        query.order_by(desc(ScanRecord.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return records, total


def delete_scan(db: Session, scan_id: str) -> bool:
    """Delete a scan by ID. Returns True if deleted."""
    record = db.query(ScanRecord).filter(ScanRecord.id == scan_id).first()
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def get_statistics(db: Session) -> dict[str, Any]:
    """Compute aggregated statistics from persisted scans."""
    total = db.query(func.count(ScanRecord.id)).scalar() or 0

    phishing = (
        db.query(func.count(ScanRecord.id))
        .filter(ScanRecord.prediction.in_(["phishing"]))
        .scalar()
        or 0
    )
    suspicious = (
        db.query(func.count(ScanRecord.id))
        .filter(ScanRecord.prediction == "suspicious")
        .scalar()
        or 0
    )
    safe = (
        db.query(func.count(ScanRecord.id))
        .filter(ScanRecord.prediction.in_(["safe", "legitimate"]))
        .scalar()
        or 0
    )

    # Risk distribution
    risk_dist = [
        {"name": "Safe", "value": safe, "color": "#10b981"},
        {"name": "Suspicious", "value": suspicious, "color": "#f59e0b"},
        {"name": "Phishing", "value": phishing, "color": "#ef4444"},
    ]

    # Per-modality breakdown
    modality_usage_rows = (
        db.query(ScanRecord.scan_type, func.count(ScanRecord.id))
        .group_by(ScanRecord.scan_type)
        .all()
    )
    modality_usage = {row[0]: row[1] for row in modality_usage_rows}

    # Recent scans (last 10)
    recent = (
        db.query(ScanRecord)
        .order_by(desc(ScanRecord.created_at))
        .limit(10)
        .all()
    )

    return {
        "total_scans": total,
        "high_risk": phishing,
        "suspicious": suspicious,
        "safe": safe,
        "risk_distribution": risk_dist,
        "modality_usage": modality_usage,
        "recent_scans": [_record_to_summary(r) for r in recent],
    }


def _record_to_summary(record: ScanRecord) -> dict[str, Any]:
    """Convert a ScanRecord to a JSON-serializable summary dict."""
    return {
        "id": record.id,
        "scan_type": record.scan_type,
        "prediction": record.prediction,
        "risk_score": record.risk_score,
        "target_summary": record.target_summary,
        "status": record.status,
        "created_at": record.created_at.isoformat() if isinstance(record.created_at, datetime) else str(record.created_at),
    }


def _truncate(s: str, max_len: int) -> str:
    """Truncate a string, adding '…' if truncated."""
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def _sanitize_modality_results(modality_results: dict[str, Any] | None) -> dict[str, Any] | None:
    """Avoid persisting bulky or sensitive detail that is not necessary for history."""
    if not modality_results:
        return modality_results

    sensitive_keys = {
        "body",
        "email_body",
        "html",
        "html_source",
        "raw_content",
        "raw_html",
        "ocr_text",
        "ocr_text_preview",
        "url",
        "urls_found",
    }

    def scrub(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: scrub(item)
                for key, item in value.items()
                if key.lower() not in sensitive_keys
            }
        if isinstance(value, list):
            return [scrub(item) for item in value]
        return value

    return scrub(modality_results)
