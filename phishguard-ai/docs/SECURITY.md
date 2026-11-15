# PhishGuard AI Security Policy & Controls

## 1. Security Architecture & Threat Model

PhishGuard AI is an automated phishing analysis platform designed to inspect potentially malicious user-submitted artifacts (URLs, emails, screenshots, and HTML source). Because inputs are assumed to be hostile, strict boundary controls are enforced across all layers.

---

## 2. Core Security Controls

### 2.1 Safe URL Processing
- **No Outbound Network Navigation:** The URL detection engine operates purely through static lexical and structural feature extraction. The backend **never visits, fetches, resolves DNS for, or follows redirects from submitted URLs**.
- **No Execution of Remote Scripts:** Target URLs are treated solely as ASCII string sequences for feature computation.

### 2.2 File Upload & Screenshot Security
- **MIME & Content Verification:** Uploads to `POST /api/scans/screenshot` are validated using Pillow (`Image.open` and `img.verify()`) to ensure the byte stream represents a valid PNG or JPEG image. File extension spoofing is mitigated because file content bytes are verified directly.
- **Strict Size Limits:** Enforced maximum payload limit of **10 MB** (`MAX_IMAGE_BYTES = 10 * 1024 * 1024`). Uploads exceeding this return HTTP `413 Payload Too Large`.
- **Sandboxed OCR:** Text extraction is delegated to Tesseract OCR via `pytesseract`. If Tesseract is unavailable or encounters parsing errors, exceptions are caught gracefully and return an informational warning without crashing the service or exposing filesystem paths.
- **Non-Execution:** Uploaded screenshot files are processed strictly in-memory (`io.BytesIO`) and are never written to executable directories or executed.

### 2.3 HTML Handling & Injection Defense
- **Static AST Parsing:** HTML source submitted to `POST /api/scans/html` is parsed statically using BeautifulSoup (`html.parser`).
- **No JavaScript Execution:** Neither Node, V8, nor a headless browser is invoked. Script elements are analyzed as static strings via regular expression pattern matchers.
- **Payload Size Boundary:** Enforced limit of **500 KB** on raw HTML submissions.
- **No Remote Fetching:** `<link>`, `<script src="...">`, or `<img>` references are never fetched over the network.
- **XSS Prevention in Frontend:** The React user interface uses JSX text interpolation throughout (`<div>{text}</div>`). No untrusted user data is ever rendered via `dangerouslySetInnerHTML`.

### 2.4 SQL Injection Defense
- Database interactions use **SQLAlchemy ORM** with parameterized queries (`db.query(ScanRecord).filter(...)`). Raw SQL string formatting and concatenation are strictly prohibited.

### 2.5 Data Privacy & Sensitive Information Scrubbing
- **Payload Redaction:** The backend sanitization routine (`_sanitize_modality_results`) strips bulky and sensitive raw input fields (`body`, `email_body`, `html`, `raw_html`, `ocr_text`) before persisting scan records to SQLite.
- **Minimal Metadata Retention:** The SQLite database (`backend/data/phishguard.db`) stores only target summaries (e.g. domain name or truncated subject), overall risk scores, detected indicators, and model identifiers.
- **User Control:** Users can permanently delete individual scan records at any time via `DELETE /api/scans/{scan_id}`.

### 2.6 Error Handling & Information Leakage
- A global exception handler in `main.py` catches all unhandled exceptions and returns a generic JSON response (`{"detail": "An internal server error occurred."}`) with HTTP 500, preventing stack traces, system paths, or environment variables from leaking to clients.

---

## 3. Dependency Vulnerability Audit

### npm Audit (Frontend)
- `npm audit` reported 9 moderate-severity advisories:
  - `minimatch`: development dependency under `@typescript-eslint`.
  - `react-router-dom`: moderate advisory (GHSA-wrjc-x8rr-h8h6 / GHSA-337j-9hxr-rhxg).
  - *Recommendation:* Upgrading `react-router-dom` to version 7+ involves breaking API changes across route components. Following security guidelines, breaking dependency updates were not blindly applied to preserve application stability.

### Python Environment (Backend)
- Stable, pinned package versions are maintained in `requirements.txt`.
- In production, run regular automated vulnerability scans (e.g., via GitHub Dependabot or `pip-audit`) and test dependency updates in a staging environment prior to deployment.
