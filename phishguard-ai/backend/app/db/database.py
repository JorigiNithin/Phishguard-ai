"""SQLAlchemy database setup and session management.

Uses SQLite for scan history persistence.
Database file: backend/data/phishguard.db
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

# ---------------------------------------------------------------------------
# Database path
# ---------------------------------------------------------------------------

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _BACKEND_ROOT / "data"
_DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = _DATA_DIR / "phishguard.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# ---------------------------------------------------------------------------
# Engine and session factory
# ---------------------------------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite + multi-thread
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

def get_db() -> Session:  # type: ignore[misc]
    """FastAPI dependency that yields a DB session and closes it afterward."""
    db = SessionLocal()
    try:
        yield db  # type: ignore[misc]
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they do not exist."""
    from app.db import models as _models  # noqa: F401 — import triggers table registration
    Base.metadata.create_all(bind=engine)

