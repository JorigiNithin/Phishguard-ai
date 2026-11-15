# PhishGuard AI Architecture

## Overview

PhishGuard AI follows a layered design separating the user interface, detection services, and persisted data access. Each modality is processed by a dedicated detector, and the output is then fused into a single multimodal risk assessment.

```text
React frontend
  └─ pages/Analyze, Dashboard, History, Models, Settings
      └─ services/api.ts
          └─ FastAPI backend
               ├─ /api/health
               ├─ /api/models
               ├─ /api/statistics
               ├─ /api/scans/{...}
               ├─ detection routes
               ├─ fusion & explainability services
               └─ SQLite database
```

## Frontend structure

- `frontend/src/pages/`: Dashboard, Analyze, History, Models, Settings
- `frontend/src/services/api.ts`: API access layer for REST requests
- `frontend/src/types/api.ts`: request and response typings
- `frontend/src/components/`: reusable UI elements and charts

The frontend loads real backend data rather than static mock values. It uses fetch-based API calls and renders empty states when no scans are available.

## Backend structure

- `backend/app/main.py`: FastAPI app, startup lifecycle, CORS, route registration
- `backend/app/api/routes/`: endpoint definitions for health, models, stats, scans, and detectors
- `backend/app/services/`: detector implementations and fusion/explainability logic
- `backend/app/db/`: SQLAlchemy models and database initialization
- `backend/app/schemas/`: request/response models
- `backend/app/core/config.py`: environment-based app settings

## Detection modules

1. URL detector
   - Uses a trained Random Forest model stored in `models/url_detector.joblib`
   - Features include URL length, domain depth, suspicious keywords, entropy, and query parameters

2. Email detector
   - Performs rule-based checks across sender, subject, and body content

3. Screenshot detector
   - Uses image checks and optional OCR text extraction if Tesseract is available

4. HTML detector
   - Parses HTML for credential forms, remote actions, suspicious URLs, script injection patterns, and login indicators

## Multimodal fusion

Risk scores are normalized to a common 0-100 scale and combined using a weighted average:

```
overall_risk = (Σ weight_i × normalized_score_i) / (Σ weight_i for available modalities)
```

Default modality weights:

- URL: 0.30
- Email: 0.30
- Screenshot: 0.15
- HTML: 0.25

The implementation explicitly excludes missing modalities from the denominator and does not treat missing data as safe.

## Explainability

Each explanation item includes:

- indicator name
- source modality
- impact severity
- reason string

The explainability layer summarizes the strongest contributors and highlights any missing modalities as a limitation rather than a positive signal.

## Database architecture

The app uses SQLite with SQLAlchemy and stores records in `scan_records`.

Persisted fields include:

- id
- scan_type
- prediction
- risk_score
- confidence
- model_used
- target_summary
- indicators_json
- explanation_json
- modality_results_json
- status
- created_at

Sensitive or bulky payloads are sanitized before persistence, avoiding raw HTML, email body text, and OCR previews unless explicitly required.

## API flow

1. Frontend sends request to `/api/...`.
2. FastAPI validates request payloads with Pydantic.
3. Detector service runs one or more modality checks.
4. Fusion service combines available results into an overall risk assessment.
5. Explainability service summarizes contributing indicators.
6. Result is saved to SQLite history and returned to the client.

## Operational notes

- App startup initializes the database automatically.
- CORS is configured via environment variables and the default allowlist.
- The app catches unexpected exceptions and returns a generic 500 error instead of exposing internal stack traces.

