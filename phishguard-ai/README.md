# PhishGuard AI: Multimodal Phishing Detection System

PhishGuard AI is an enterprise-grade cybersecurity application that detects phishing attacks across multiple attack vectors: suspicious URLs, fraudulent emails, login screenshot captures, and malicious HTML source code. It features a FastAPI backend, a modern React/TypeScript dashboard, SQLite scan history, and a multimodal fusion engine that correlates indicators to deliver an explainable risk assessment.

---

## 1. Problem Statement & Objectives

### The Problem
Modern phishing campaigns no longer rely on single-vector lures. Attackers combine obfuscated URLs, spoofed sender domains, brand logo impersonation in screenshot lures, and credential-harvesting forms embedded in HTML. Traditional defenses analyzing only single modalities frequently fail to detect multi-stage evasions.

### Project Objectives
1. **Multimodal Analysis:** Provide targeted detection across four modalities (URL lexical features, email heuristics, screenshot OCR, and static HTML code audit).
2. **Machine Learning URL Classification:** Train and deploy a high-performance supervised Random Forest classifier using 17 structural and lexical features.
3. **Multimodal Fusion Engine:** Combine heterogeneous evidence using a documented weighted scoring strategy that handles missing inputs without assuming uninspected vectors are safe.
4. **Explainable AI (XAI):** Deliver human-readable explanations and severity ratings for security analysts rather than black-box labels.
5. **Persistent History & Analytics:** Maintain an auditable SQLite database of scans with search, filtering, pagination, and dashboard metrics.

---

## 2. Technology Stack

- **Frontend:**
  - React 18, TypeScript, Vite
  - Tailwind CSS (Dark Navy & Teal SaaS aesthetic)
  - React Router v6
  - Recharts (Interactive Risk Distribution analytics)
  - Lucide React icons
- **Backend:**
  - Python 3.11+, FastAPI, Uvicorn
  - Pydantic v2 (Data validation & schemas)
  - SQLAlchemy 2.0 (ORM & SQLite persistence)
  - Scikit-Learn (Random Forest model)
  - BeautifulSoup4 (Static HTML parsing)
  - Pillow & pytesseract (Image validation & OCR)
  - pytest & HTTPX (Automated test suite)

---

## 3. Architecture Overview

```text
React Dashboard (Port 5173)
  ├── Pages: Dashboard, Analyze, History, Models, Settings
  └── Services: api.ts
        │
        ▼  HTTP REST (/api)
FastAPI Backend (Port 8000)
  ├── Lifespan / Model Registry / SQLite Database Initialization
  ├── Routers:
  │     ├── /api/health & /api/version
  │     ├── /api/models & /api/statistics
  │     ├── /api/scans/url         ──> Random Forest ML Classifier
  │     ├── /api/scans/email       ──> Heuristic Email Rule Engine
  │     ├── /api/scans/screenshot  ──> Pillow Image Audit + Tesseract OCR
  │     ├── /api/scans/html        ──> BeautifulSoup Static Parser
  │     ├── /api/scans/multimodal  ──> Weighted Fusion & XAI Engine
  │     └── /api/scans/history     ──> SQLite Search, Filter, Pagination & Deletion
  └── Database:
        └── backend/data/phishguard.db (SQLAlchemy ORM)
```

---

## 4. Installation & Setup

### Prerequisites
- Python 3.11 or compatible supported version
- Node.js 18+ and npm
- (Optional) Tesseract OCR installed on system PATH for screenshot text extraction

### 4.1 Backend Setup
```bash
# Navigate to backend directory
cd phishguard-ai/backend

# Create and activate virtual environment
python -m venv .venv
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env

# Start FastAPI development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4.2 Frontend Setup
```bash
# Navigate to frontend directory
cd phishguard-ai/frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
The application will be accessible at `http://localhost:5173`.

---

## 5. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check endpoint returning status, timestamp, and environment |
| `GET` | `/api/version` | Application name and version information |
| `GET` | `/api/models` | Status of all 4 detection models |
| `GET` | `/api/statistics` | Overview statistics for dashboard |
| `POST` | `/api/scans/url` | Evaluates URL using Random Forest classifier |
| `POST` | `/api/scans/email` | Evaluates email using 10 heuristic inspection rules |
| `POST` | `/api/scans/screenshot` | Validates uploaded image and extracts text via OCR |
| `POST` | `/api/scans/html` | Statically parses HTML for credential forms and redirects |
| `POST` | `/api/scans/multimodal`| Fuses multiple modalities into a single overall risk score |
| `GET` | `/api/scans/history` | Returns paginated, searchable, and filterable scan history |
| `GET` | `/api/scans/{scan_id}` | Retrieves full detail for a persisted scan record |
| `GET` | `/api/scans/{scan_id}/explain`| Returns Explainable AI breakdown for a scan record |
| `DELETE` | `/api/scans/{scan_id}`| Deletes a scan from database history |
| `GET` | `/api/dashboard/statistics` | Real-time statistics aggregated from database |

Interactive Swagger documentation is available at `http://localhost:8000/docs`.

---

## 6. Model Training & Evaluation

To retrain the URL phishing classifier:
```bash
cd phishguard-ai/backend
python -m scripts.train_url_model
```
- **Dataset:** 7,330 cleaned URLs (`datasets/url_dataset_clean.csv`).
- **Features:** 17 lexical and structural features.
- **Model:** `RandomForestClassifier(n_estimators=100, max_depth=20, random_state=42)`.
- **Output:** Serialized model to `models/url_detector.joblib` and metrics to `models/url_detector_meta.json`.

Detailed metrics and error analysis are documented in [docs/ML_EVALUATION.md](docs/ML_EVALUATION.md).

---

## 7. Testing & Verification

### Automated Backend Test Suite
```bash
cd phishguard-ai/backend
python -m pytest -v
```
**Test Results:** 56 passed test cases covering health, models, statistics, all four detection modalities, multimodal fusion, explainability, SQLite persistence, history filters, pagination, and input validation.

### Frontend Production Build
```bash
cd phishguard-ai/frontend
npm run build
```
Executes TypeScript type-check (`tsc -b`) and Vite production bundle generation.

---

## 8. Security Controls & Safe Processing

- **No Outbound Requests:** URLs in scans are analyzed strictly offline through lexical patterns; the backend never navigates to external phishing hosts.
- **No Untrusted Execution:** HTML and JavaScript are parsed as static text structures with BeautifulSoup; scripts are never executed.
- **Upload Hardening:** Screenshot files are verified by byte-content inspection (PNG/JPEG) with a 10 MB ceiling.
- **Data Privacy:** Raw email bodies, full HTML, and OCR texts are scrubbed before persistence to SQLite.

Detailed security architecture is available in [docs/SECURITY.md](docs/SECURITY.md).

---

## 9. Known Limitations

1. **Synthetic Training Benchmark:** The current URL training script uses synthetic template URLs when a raw Kaggle CSV is not provided. Users should supply genuine feeds in `datasets/phishing_site_urls.csv` for production retraining.
2. **OCR System Binary:** Screenshot text extraction requires Tesseract-OCR binary installed on the host. When absent, the system degrades gracefully with heuristic image checks.
3. **Heuristic vs Calibrated Confidence:** Email, screenshot, and HTML analyzers are rule-based and report `confidence: null` to accurately reflect heuristic rather than probabilistic confidence.
