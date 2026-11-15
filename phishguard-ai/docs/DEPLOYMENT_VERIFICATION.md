# DEPLOYMENT AND ENVIRONMENT VERIFICATION REPORT
## PhishGuard AI — Multimodal Phishing Detection System

**Project:** PhishGuard AI  
**Document Target:** Deployment & Environment Audit (B.Tech Project Report)  
**Verification Date:** November 15, 2026  
**Environment Mode:** Local Development (`APP_ENV=development`)  
**Auditor:** Automated System Audit  

---

## 1. Executive Summary & Verification Matrix

The deployment readiness, hosting topology, database configuration, model artifacts, and end-to-end workflows of PhishGuard AI were audited. The findings are categorized according to formal audit criteria:
- **Verified:** Explicitly confirmed via code inspection, file presence, or executed test.
- **Not verified:** Code exists but lacks execution or corroborating test evidence.
- **Not implemented:** Feature, infrastructure, or configuration is absent by design.
- **Not recorded:** Metadata, timestamp, or URL does not exist in project files.

### Master Verification Matrix

| # | Audit Item | Verification Status | Exact Configuration / Finding |
|---|---|---|---|
| **1** | **Frontend Development URL & Hosting** | **Verified** | Local dev server at `http://localhost:5173` (Vite 6 + React 18). Proxy targets `http://localhost:8000`. Production bundle built in `frontend/dist/`. Public cloud hosting is **Not implemented**. |
| **2** | **Backend Development URL & Hosting** | **Verified** | Local ASGI server at `http://localhost:8000` (FastAPI 0.104 on Uvicorn, binding `0.0.0.0:8000`). OpenAPI docs at `http://localhost:8000/docs`. Public cloud server is **Not implemented**. |
| **3** | **Public Deployment vs. Local Execution** | **Verified (Local Only)** | Application runs **strictly locally in a development environment (`APP_ENV=development`)**. No public domain, reverse proxy (Nginx), or cloud hosting is configured. |
| **4** | **Database Type & File Path** | **Verified** | **SQLite 3** via SQLAlchemy 2.0 ORM (`sqlite:///...`). File path: `backend/data/phishguard.db` (61,440 bytes, active and initialized). |
| **5** | **Saved Model Filenames & Metadata** | **Verified** | ML Binary: `models/url_detector.joblib` (118,201 bytes). Metadata: `models/url_detector_meta.json` (Random Forest, 17 features, 100 estimators). Heuristic engines v1.0. |
| **6** | **GitHub Repository URL (Git Remote)** | **Not recorded** | Git is not initialized (`.git` absent); no Git remote is configured in repository files. |
| **7** | **Actual Deployment Date** | **Not recorded** | No cloud hosting logs or CI/CD deployment timestamps exist. Local verification and build executed on **November 15, 2026** (initial model artifact trained November 10, 2026). |
| **8** | **Frontend & Backend Concurrent Execution** | **Verified** | Vite proxy passes `/api` calls to FastAPI; FastAPI CORS middleware whitelists frontend localhost origins; TypeScript schemas match Pydantic models. |
| **9** | **End-to-End Workflow Verification** | **Verified** | Automated 14-step integration test (`tests/test_section5_e2e.py`) verified all workflows: URL, Email, Screenshot, HTML, Multimodal Fusion, Explainable AI, and History. |

---

## 2. Detailed Technical Findings

### 2.1 Frontend Development & Hosting Configuration
- **Status:** **Verified**
- **Configuration File:** `frontend/vite.config.ts`
- **Development Server:** Vite 6.4.5 serving React 18.2.0 + TypeScript.
- **Port & Host:** Port `5173` (`http://localhost:5173`).
- **Reverse Proxy:** Configured in `vite.config.ts#L14-L19`:
  ```typescript
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  }
  ```
- **API Base URL Resolution:** `frontend/src/services/api.ts#L25` defines `BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''`. In local development, empty `BASE_URL` routes calls through the Vite reverse proxy to port 8000, preventing CORS complications.
- **Production Static Build:** Verified via `npm run build` producing optimized assets in `frontend/dist/` (HTML, minified CSS: 18.49 kB, minified JS bundle: 600.55 kB).
- **Public Cloud Hosting:** **Not implemented.** No Vercel, Netlify, AWS S3, or Cloudflare Pages configuration files are present.

---

### 2.2 Backend Development & Hosting Configuration
- **Status:** **Verified**
- **Configuration File:** `backend/app/core/config.py` & `.env.example`
- **ASGI Server:** FastAPI 0.104.1 running on Uvicorn.
- **Host & Port:** `HOST=0.0.0.0`, `PORT=8000` (`http://localhost:8000`).
- **Interactive Documentation:** Swagger UI at `http://localhost:8000/docs`, ReDoc at `http://localhost:8000/redoc`.
- **CORS Policy:** Whitelists frontend development ports (`http://localhost:5173`, `http://localhost:5174`, `http://localhost:3000`, `http://127.0.0.1:5173`).
- **Public Cloud Hosting:** **Not implemented.** No Dockerfile, docker-compose, Procfile, Kubernetes manifest, or cloud deployment templates exist.

---

### 2.3 Public vs. Local Deployment Status
- **Status:** **Verified (Local Execution Only)**
- **Operating Environment:** The application is architected and executed as a **local standalone workstation application**.
- **Evidence:**
  - `APP_ENV=development` in `backend/app/core/config.py#L21`.
  - No public DNS records, reverse proxies (Nginx/Apache), or SSL/TLS certificates configured.
  - SQLite local file storage is used rather than a managed cloud database (e.g. AWS RDS PostgreSQL).

---

### 2.4 Database Type and Storage Path
- **Status:** **Verified**
- **Database Engine:** **SQLite 3** via SQLAlchemy 2.0.23 ORM.
- **Database URL:** `sqlite:///C:\Users\YOGA\OneDrive\Desktop\Multi_Model_Phishing_Detection\phishguard-ai\backend\data\phishguard.db`.
- **File System Verification:**
  - Directory: `backend/data/`
  - File: `phishguard.db` (Size: 61,440 bytes).
  - Persistence verified across application reboots.
- **Table Schema:** `scan_records` storing `id` (UUID), `scan_type`, `prediction`, `risk_score`, `confidence`, `model_used`, `target_summary`, `indicators_json`, `explanation_json`, `modality_results_json`, `status`, and `created_at`.
- **Privacy Enforcement:** Raw email bodies, full HTML markup, and binary screenshot bytes are scrubbed prior to storage.

---

### 2.5 Saved Model Artifacts and Versions
- **Status:** **Verified**
- **URL Machine Learning Model:**
  - Binary File: `phishguard-ai/models/url_detector.joblib` (118,201 bytes).
  - Metadata File: `phishguard-ai/models/url_detector_meta.json` (950 bytes).
  - Model Architecture: `sklearn.ensemble.RandomForestClassifier` (100 estimators, max depth 20, 17 features).
  - Evaluation Split: 80% Train ($N=5,864$) / 20% Test ($N=1,466$).
  - Training Timestamp: November 10, 2026, 05:41 PM.
- **Heuristic & Rule-Based Engines:**
  - Email Module: `Rule-based Email Analyzer v1.0` (`app/services/email_detector.py`).
  - Screenshot Module: `Rule-based Screenshot Analyzer v1.0` (`app/services/screenshot_detector.py`).
  - HTML Module: `Rule-based HTML Analyzer v1.0` (`app/services/html_detector.py`).
  - Multimodal Fusion: `Weighted Multimodal Fusion Engine v1.0` (`app/services/fusion.py`).

---

### 2.6 GitHub Repository Configuration (Git Remote)
- **Status:** **Not recorded / Not configured**
- **Git Remote Check:**
  ```powershell
  git remote -v
  # Result: fatal: not a git repository (or any of the parent directories): .git
  ```
- **Finding:** No `.git` metadata directory exists in `Multi_Model_Phishing_Detection` or `phishguard-ai`. A production-ready `.gitignore` file is in place, but a remote repository has not been initialized or pushed to GitHub.

---

### 2.7 Deployment Date Records
- **Status:** **Not recorded**
- **Finding:** No cloud deployment logs, CI/CD pipeline runs, or release tagging logs exist.
- **Local Milestones:**
  - Initial model training & dataset preparation: **November 10, 2026, 05:41 PM**.
  - Final full-system verification and test completion: **November 15, 2026**.

---

### 2.8 Frontend and Backend Concurrent Execution
- **Status:** **Verified**
- **Verification Evidence:**
  1. Frontend build completes cleanly via `npm run build` without TypeScript errors (2,209 modules transformed).
  2. Vite development proxy is configured to seamlessly forward all `/api` traffic to `http://localhost:8000`.
  3. FastAPI CORS middleware allows browser origins matching `http://localhost:5173`.
  4. Both subsystems run on non-conflicting standard ports (`5173` for React, `8000` for FastAPI).

---

### 2.9 End-to-End Workflow Verification
- **Status:** **Verified**
- **Automated Test Suite:** `backend/tests/test_section5_e2e.py` (Passed in 1.04s).
- **Workflows Verified:**

| Workflow Step | Modality / Operation | Test Action & Verification Result |
|---|---|---|
| **Step 1** | Dashboard Baseline | Queried initial statistics via `GET /api/dashboard/statistics`. Verified empty initial state. |
| **Step 2** | URL Phishing Scan | Submitted URL -> Extracted 17 lexical features -> Evaluated via Random Forest -> Flagged as phishing (Risk: 90) -> Persisted to DB with UUID. |
| **Step 3** | Email Phishing Scan | Submitted email lure -> Evaluated urgency & credential regex patterns -> Flagged as suspicious (Risk: 30) -> Persisted to DB. |
| **Step 4** | Screenshot Scan | Uploaded synthetic PNG -> Binary magic-byte verified -> OCR text inspected -> Evaluated -> Persisted to DB. |
| **Step 5** | HTML Phishing Scan | Submitted HTML form pointing to direct IP -> Static DOM parsing via BeautifulSoup -> Flagged as suspicious (Risk: 40) -> Persisted to DB. |
| **Step 6** | Multimodal Fusion | Ingested URL, Email, and HTML simultaneously -> Calculated dynamic weighted risk score -> Deduplicated indicators -> Produced unified risk assessment (`overall_risk: 84`, `phishing`). |
| **Step 7** | Explainable AI (XAI) | Queried `GET /api/scans/{scan_id}/explain` -> Verified presence of categorized indicators with source modality attribution. |
| **Step 8** | History Pagination | Queried `GET /api/scans/history` -> Verified all 5 executed scans returned with correct metadata. |
| **Step 9** | History Filtering | Filtered by `scan_type=email` -> Verified exact match returned. |
| **Step 10** | Detail Inspection | Queried `GET /api/scans/{scan_id}` -> Retrieved full scan breakdown without sensitive raw inputs. |
| **Step 11** | Scan Deletion | Executed `DELETE /api/scans/{scan_id}` -> Verified subsequent query returns HTTP 404 Not Found. |
| **Step 12** | Dashboard Metric Update | Re-queried dashboard statistics -> Verified count decremented to 4 scans. |
| **Step 13** | Database Persistence | Re-opened raw SQLite connection -> Verified persistence of remaining 4 scan UUIDs across session boundaries. |
| **Step 14** | API Consistency | Confirmed updated history persists via `GET /api/scans/history`. |

---

## 3. Recommended Actions for Final B.Tech Submission

1. **Local Deployment Clarification:** In the project report and viva presentation, clearly state that PhishGuard AI is deployed as a **local workstation client-server architecture** (`localhost:5173` frontend communicating with `localhost:8000` backend).
2. **Git Repository Initialization:** Before final project submission, initialize Git and push to your private or institutional GitHub repository:
   ```powershell
   cd c:\Users\YOGA\OneDrive\Desktop\Multi_Model_Phishing_Detection\phishguard-ai
   git init
   git add .
   git commit -m "feat: complete PhishGuard AI multimodal phishing detection system"
   git remote add origin https://github.com/<your-username>/phishguard-ai.git
   git push -u origin main
   ```
3. **Database Portability:** The SQLite database file (`backend/data/phishguard.db`) is self-contained and zero-configuration, meaning evaluators can clone and run the system without provisioning external database servers.

