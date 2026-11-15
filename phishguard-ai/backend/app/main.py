"""PhishGuard AI – FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import fusion, health, models, scans, statistics
from app.api.routes import email as email_route
from app.api.routes import screenshot as screenshot_route
from app.api.routes import html as html_route
from app.core.config import settings
from app.db.database import init_db
from app.core.logging import logger
from app.services.model_registry import model_registry
from app.services.url_predictor import is_model_available
from app.schemas.common import DetectionModelInfo, Modality, ModelStatus

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "%s v%s starting in %s mode",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.APP_ENV,
    )

    init_db()

    # --- Update model registry with actual availability ---------------------

    # URL detector: trained ML model
    if is_model_available():
        model_registry.register(
            DetectionModelInfo(
                id="url_detector",
                name="URL Detector",
                modality=Modality.URL,
                status=ModelStatus.TRAINED,
                model_type="Random Forest",
                training_status="Trained on synthetic dataset (7330 URLs)",
                available=True,
                description="Analyses URLs for phishing indicators using lexical and structural features.",
            )
        )
        logger.info("URL detector model loaded and available")

    # Email detector: rule-based (always available)
    model_registry.register(
        DetectionModelInfo(
            id="email_detector",
            name="Email Detector",
            modality=Modality.EMAIL,
            status=ModelStatus.IMPLEMENTED,
            model_type="Rule-based",
            training_status="Rule-based (no training required)",
            available=True,
            description="Analyses email content for phishing patterns using rule-based detection.",
        )
    )

    # Screenshot detector: rule-based + OCR (always available, OCR optional)
    from app.services.screenshot_detector import is_ocr_available

    ocr_status = "with Tesseract OCR" if is_ocr_available() else "without OCR (Tesseract not installed)"
    model_registry.register(
        DetectionModelInfo(
            id="screenshot_detector",
            name="Screenshot Detector",
            modality=Modality.SCREENSHOT,
            status=ModelStatus.IMPLEMENTED,
            model_type="Rule-based + OCR",
            training_status=f"Rule-based {ocr_status}",
            available=True,
            description=f"Analyses screenshots for phishing cues using image processing and OCR text extraction ({ocr_status}).",
        )
    )

    # HTML detector: rule-based (always available)
    model_registry.register(
        DetectionModelInfo(
            id="html_detector",
            name="HTML Detector",
            modality=Modality.HTML,
            status=ModelStatus.IMPLEMENTED,
            model_type="Rule-based",
            training_status="Rule-based (no training required)",
            available=True,
            description="Analyses raw HTML source for phishing structures using static analysis.",
        )
    )

    logger.info("All detection modules registered")

    yield
    logger.info("Shutting down %s", settings.APP_NAME)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multimodal Phishing Detection System",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler so stack traces are never leaked to clients."""
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(health.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(statistics.router, prefix="/api")
app.include_router(fusion.router, prefix="/api")
app.include_router(scans.router, prefix="/api")
app.include_router(email_route.router, prefix="/api")
app.include_router(screenshot_route.router, prefix="/api")
app.include_router(html_route.router, prefix="/api")
