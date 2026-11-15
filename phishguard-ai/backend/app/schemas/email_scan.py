"""Pydantic schemas for POST /api/scans/email."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class EmailScanRequest(BaseModel):
    """Request body for email phishing analysis."""

    sender: str = Field(
        ..., min_length=1, max_length=512, description="Sender email address"
    )
    subject: str = Field(
        ..., min_length=0, max_length=2048, description="Email subject line"
    )
    body: str = Field(
        ..., min_length=1, max_length=100_000, description="Email body text"
    )
    headers: Optional[dict[str, str]] = Field(
        None, description="Optional raw email headers"
    )

    @field_validator("sender")
    @classmethod
    def sender_must_look_like_email(cls, v: str) -> str:
        v = v.strip()
        if "@" not in v:
            raise ValueError("Sender must contain an '@' character")
        return v

    @field_validator("body")
    @classmethod
    def body_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Email body must not be blank")
        return v

