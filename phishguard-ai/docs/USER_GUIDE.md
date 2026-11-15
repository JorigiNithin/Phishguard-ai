# PhishGuard AI User Guide

Welcome to **PhishGuard AI** — a multimodal phishing detection platform combining machine learning and heuristic inspection to analyze suspicious URLs, emails, screenshots, and HTML files.

---

## 1. Getting Started

### 1.1 Starting the Services
1. **Backend:**
   ```powershell
   cd phishguard-ai\backend
   .\.venv\Scripts\Activate.ps1
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. **Frontend:**
   ```powershell
   cd phishguard-ai\frontend
   npm run dev
   ```
3. Open your browser and navigate to `http://localhost:5173`.

---

## 2. Detection Modes

Navigate to the **Analyze** page using the sidebar navigation.

### 2.1 URL Analysis (Machine Learning)
1. Select the **URL** tab.
2. Enter the target web address (e.g. `https://example-security-update.com/login`).
3. Click **Analyze**.
4. The system runs the 17-feature Random Forest model and presents:
   - Prediction badge (`Legitimate` or `Phishing`).
   - Confidence percentage (calibrated ML model probability).
   - Expandable feature table detailing all 17 extracted numerical indicators (e.g., entropy, subdomain depth, IP address presence, suspicious keyword count).

### 2.2 Email Analysis (Heuristic Rule Engine)
1. Select the **Email** tab.
2. Enter the **Sender Address** (e.g. `support@sec-update.com`).
3. Enter the **Subject Line** (e.g. `Immediate Action: Account Suspended`).
4. Paste the **Email Body** content.
5. Click **Analyze**.
6. The engine inspects for urgency language, credential harvesting, brand spoofing, and mismatched reply headers, reporting detected indicators with severity ratings (`High`, `Medium`, `Low`).

### 2.3 Screenshot Analysis (OCR + Visual Inspection)
1. Select the **Screenshot** tab.
2. Click the upload dropzone or drag-and-drop a PNG or JPEG file (maximum 10 MB).
3. Confirm the image preview.
4. Click **Analyze**.
5. The system performs image validation, text extraction via Tesseract OCR (if installed), and scans the extracted text for phishing lures and embedded suspicious domains.

### 2.4 HTML Analysis (Static Code Audit)
1. Select the **HTML** tab.
2. Paste the raw HTML source code of the webpage into the textarea (maximum 500 KB).
3. Click **Analyze**.
4. The static parser evaluates form submission targets (detecting off-domain or raw IP destinations), hidden password inputs, redirect scripts, and meta-refresh tags without rendering or executing untrusted code.

### 2.5 Multimodal Fusion Analysis (All-in-One)
1. Select the **Fusion** tab.
2. Enter any combination of inputs:
   - Target URL
   - Email sender, subject, and body
   - HTML source code
3. Click **Analyze**.
4. The Multimodal Fusion Engine normalizes scores, computes a weighted composite risk index, lists deduplicated contributing indicators across all modalities, and provides an explainability summary explaining why the content was flagged.

---

## 3. Interpreting Risk Scores & Predictions

| Risk Score | Prediction | Recommended Action |
|---|---|---|
| **0 – 29** | `Safe` | No significant phishing indicators detected. |
| **30 – 59** | `Suspicious` | Moderate indicators detected (e.g. urgent tone, unverified sender domain). Exercise caution. |
| **60 – 100** | `Phishing` | High-confidence malicious patterns detected (e.g. credential harvesting forms, known shorteners, IP host). Do not interact. |

> [!NOTE]
> The overall risk score in Multimodal Fusion is a heuristic weighted score combining evidence from available detectors. It represents threat intensity rather than a Bayesian statistical probability.

---

## 4. Scan History & Persistent Auditing

Navigate to the **History** page:
- **Search:** Query target domains or scan types using the search bar.
- **Filter:** Narrow records by modality (`URL`, `Email`, `Screenshot`, `HTML`, `Multimodal`) or prediction status (`Phishing`, `Suspicious`, `Safe`).
- **Pagination:** Navigate through historical scans page by page.
- **Inspect Details:** Click on any Scan ID to open the detail panel displaying timestamp, model used, detected indicators, and Explainable AI breakdown.
- **Delete Record:** Click **Delete** next to any record and confirm the dialog to permanently remove it from the SQLite database.

---

## 5. Dashboard Overview

The **Dashboard** displays live metrics computed from your scan history:
- **Total Scans:** Lifetime analyses performed.
- **Phishing Detections:** Critical threat count.
- **Safe & Suspicious Detections:** Neutral and warning counts.
- **Risk Distribution Chart:** Interactive pie chart breakdown.
- **Recent Scans Table:** Quick view of the 10 most recent investigations.
- **System Status:** Real-time health indicators for API connectivity, SQLite database readiness, and registered detection modules.
