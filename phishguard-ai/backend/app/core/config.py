"""Application configuration loaded from environment variables."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from backend root
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)


class Settings:
    """Centralised application settings."""

    APP_NAME: str = os.getenv("APP_NAME", "PhishGuard AI")
    APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

        # CORS
    _raw_origins = os.getenv(
        "CORS_ORIGINS",
        '["http://localhost:5173","http://localhost:5174","http://localhost:5175","http://localhost:3000","http://127.0.0.1:5173","http://127.0.0.1:5174","http://127.0.0.1:5175"]',
    )
    CORS_ORIGINS: list[str] = []
    if _raw_origins:
        try:
            parsed = json.loads(_raw_origins)
            if isinstance(parsed, list):
                CORS_ORIGINS = [str(origin) for origin in parsed]
            else:
                CORS_ORIGINS = [origin.strip() for origin in str(parsed).split(',') if origin.strip()]
        except json.JSONDecodeError:
            CORS_ORIGINS = [origin.strip() for origin in _raw_origins.split(',') if origin.strip()]

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
