"""SQLAlchemy ORM models for scan history."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.db.database import Base


class ScanRecord(Base):
    """Persisted scan result."""

    __tablename__ = "scan_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_type = Column(String(20), nullable=False, index=True)       # url, email, screenshot, html, multimodal
    prediction = Column(String(20), nullable=False, index=True)      # phishing, suspicious, safe, legitimate
    risk_score = Column(Integer, nullable=False, default=0)
    confidence = Column(Float, nullable=True)
    model_used = Column(String(100), nullable=True)
    target_summary = Column(String(500), nullable=True)              # e.g. truncated URL or subject line
    indicators_json = Column(Text, nullable=True)                    # JSON string of indicators
    explanation_json = Column(Text, nullable=True)                   # JSON string of explanation lines
    modality_results_json = Column(Text, nullable=True)              # JSON string of per-modality results (multimodal)
    status = Column(String(20), nullable=False, default="completed")
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<ScanRecord id={self.id!r} type={self.scan_type!r} prediction={self.prediction!r}>"

