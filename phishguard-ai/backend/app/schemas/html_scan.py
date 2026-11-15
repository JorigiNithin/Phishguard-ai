"""Pydantic schemas for POST /api/scans/html."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class HTMLScanRequest(BaseModel):
    """Request body for HTML phishing analysis."""

    html: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="Raw HTML source code to analyse (max 500 KB)",
    )

    @field_validator("html")
    @classmethod
    def html_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("HTML content must not be blank")
        return v

