"""Detection-model status endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import ModelsResponse
from app.services.model_registry import model_registry

router = APIRouter(tags=["models"])


@router.get("/models", response_model=ModelsResponse)
async def list_models() -> ModelsResponse:
    """Return the status of all registered detection models."""
    models = model_registry.list_models()
    return ModelsResponse(models=models, total=len(models))
