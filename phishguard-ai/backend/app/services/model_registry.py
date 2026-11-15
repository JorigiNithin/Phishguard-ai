"""Registry that tracks the status of all detection models.

Models are initially marked as *not_implemented*. As models are built
they are registered here with their actual status.
"""

from __future__ import annotations

from app.schemas.common import DetectionModelInfo, Modality, ModelStatus

# ---------------------------------------------------------------------------
# Default model definitions
# ---------------------------------------------------------------------------

_DEFAULT_MODELS: list[DetectionModelInfo] = [
    DetectionModelInfo(
        id="url_detector",
        name="URL Detector",
        modality=Modality.URL,
        status=ModelStatus.TRAINED,
        model_type="Random Forest",
        training_status="Trained on synthetic dataset (7330 URLs)",
        available=False,  # Updated dynamically at startup
        description="Analyses URLs for phishing indicators using lexical and structural features.",
    ),
    DetectionModelInfo(
        id="email_detector",
        name="Email Detector",
        modality=Modality.EMAIL,
        status=ModelStatus.NOT_IMPLEMENTED,
        model_type=None,
        training_status="Not implemented",
        available=False,
        description="Analyses email content for phishing patterns. Coming in a later development section.",
    ),
    DetectionModelInfo(
        id="screenshot_detector",
        name="Screenshot Detector",
        modality=Modality.SCREENSHOT,
        status=ModelStatus.NOT_IMPLEMENTED,
        model_type=None,
        training_status="Not implemented",
        available=False,
        description="Analyses screenshots for visual phishing cues. Coming in a later development section.",
    ),
    DetectionModelInfo(
        id="html_detector",
        name="HTML Detector",
        modality=Modality.HTML,
        status=ModelStatus.NOT_IMPLEMENTED,
        model_type=None,
        training_status="Not implemented",
        available=False,
        description="Analyses raw HTML for phishing structures. Coming in a later development section.",
    ),
]


class ModelRegistry:
    """In-memory registry for detection model metadata."""

    def __init__(self) -> None:
        self._models: dict[str, DetectionModelInfo] = {
            m.id: m for m in _DEFAULT_MODELS
        }

    # -- queries -----------------------------------------------------------

    def list_models(self) -> list[DetectionModelInfo]:
        """Return all registered models."""
        return list(self._models.values())

    def get_model(self, model_id: str) -> DetectionModelInfo | None:
        """Return a single model by ID, or None."""
        return self._models.get(model_id)

    def available_count(self) -> int:
        """Count of models that are currently available for inference."""
        return sum(1 for m in self._models.values() if m.available)

    # -- mutations (used in later sections) --------------------------------

    def register(self, model: DetectionModelInfo) -> None:
        """Register or update a model entry."""
        self._models[model.id] = model


# Singleton instance shared across the app.
model_registry = ModelRegistry()
