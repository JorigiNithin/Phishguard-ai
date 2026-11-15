# Machine Learning Evaluation

## 1. Executive Summary

PhishGuard AI employs a hybrid phishing detection architecture:
- **Supervised ML (Random Forest):** Dedicated URL phishing classifier trained on extracted lexical and structural features.
- **Heuristic & Rule-Based Engines:** Dedicated analyzers for email content, screenshot visual/text cues (OCR-assisted), and static HTML structure.
- **Multimodal Fusion Engine:** Weighted risk score aggregation combining available evidence across modalities without fabricating probability distributions.

---

## 2. Dataset Provenance and Preprocessing

- **Dataset Identifier:** `url_dataset_clean.csv` (located in `datasets/`)
- **Origin & Schema:** Benchmark dataset structured in accordance with public phishing URL archives (e.g. Kaggle Phishing Site URLs dataset and PhishTank feeds). When a raw CSV (`datasets/phishing_site_urls.csv`) is absent, a deterministic benchmark generation script (`scripts/prepare_dataset.py`) generates benchmark URL samples based on known structural patterns documented in cybersecurity literature.
- **Dataset Size:** 7,330 total samples
- **Class Distribution:**
  - Legitimate (`good`): 2,330 samples (31.8%)
  - Phishing (`bad`): 5,000 samples (68.2%)
- **Preprocessing Pipeline:**
  1. Input sanitization (strip whitespace, trailing controls).
  2. URL structural validation via `urllib.parse.urlparse`.
  3. Deduplication: exact duplicate URLs removed to prevent data leakage.
  4. Missing values and unparseable rows rejected.
  5. Deterministic stratified 80/20 train/test split.

---

## 3. Feature Extraction Pipeline

17 lexical, syntactic, and structural features are extracted without initiating outbound network requests:

| # | Feature Name | Description | Rationale |
|---|---|---|---|
| 1 | `url_length` | Total character count of URL | Phishing URLs are frequently longer to conceal destination |
| 2 | `domain_length` | Character count of hostname | Typosquatting and subdomains inflate length |
| 3 | `num_dots` | Count of `.` characters | Excessive dots indicate nested subdomains |
| 4 | `num_subdomains` | Extracted subdomain depth | Mimicking legitimate domains via deep subdomain paths |
| 5 | `is_https` | Binary indicator (1 if HTTPS, 0 if HTTP) | Legacy heuristic (unencrypted sites carry higher risk) |
| 6 | `has_ip_address` | Hostname matches IPv4 / IPv6 regex | Legitimate brands rarely use direct IP hosts |
| 7 | `num_hyphens` | Count of `-` characters | Common in deceptive brand combination names |
| 8 | `has_at_sign` | Presence of `@` symbol | Browser authority interpretation obfuscation |
| 9 | `is_shortened` | Hostname in known URL shortener list | Shorteners obscure ultimate destination |
| 10 | `num_suspicious_keywords`| Count of keywords (`login`, `verify`, `banking`, etc.) | Phishing lures target authentication and financial accounts |
| 11 | `digit_count` | Number of numeric characters in URL | Generated hashes and dynamic tokens |
| 12 | `special_char_count` | Count of non-alphanumeric special characters | Evasion and obfuscation techniques |
| 13 | `path_length` | Length of URL path | Complex folder hierarchies |
| 14 | `query_length` | Length of query string | Parameter stuffing |
| 15 | `num_query_params` | Number of query parameters (`&` count + 1) | Tracking tokens and redirection parameters |
| 16 | `has_port` | Non-standard port specified (not 80/443) | Phishing kits frequently host on custom ports |
| 17 | `entropy` | Shannon entropy of full URL string | High entropy indicates randomized evasion strings |

---

## 4. Model Architecture & Hyperparameters

- **Algorithm:** `RandomForestClassifier` (`sklearn.ensemble`)
- **Implementation:** `backend/scripts/train_url_model.py`
- **Saved Artifacts:** `models/url_detector.joblib` and `models/url_detector_meta.json`
- **Hyperparameter Configuration:**
  - `n_estimators`: 100
  - `max_depth`: 20
  - `min_samples_split`: 5
  - `min_samples_leaf`: 2
  - `random_state`: 42
  - `n_jobs`: -1 (parallel CPU cores)

---

## 5. Evaluation Metrics (Held-Out Test Set)

The model was evaluated on 1,466 test samples (20% stratified holdout):

- **Accuracy:** `1.0000` (100.0%)
- **Precision:** `1.0000` (100.0%)
- **Recall:** `1.0000` (100.0%)
- **F1-Score:** `1.0000` (100.0%)
- **ROC-AUC:** `1.0000` (100.0%)

### Confusion Matrix:
```
                 Predicted Legitimate   Predicted Phishing
Actual Legitimate        466                     0
Actual Phishing            0                  1000
```

- **True Negatives (TN):** 466
- **False Positives (FP):** 0
- **False Negatives (FN):** 0
- **True Positives (TP):** 1000

---

## 6. Critical Error Analysis & Known Limitations

1. **Synthetic Benchmark Uniformity:**
   The benchmark dataset derived from pattern templates yields a 100% classification metric due to distinct separation between synthetic benign templates and phishing templates. This is an expected artifact of synthetic data and does not represent real-world generalization against novel zero-day adversarial obfuscations.
2. **Model Retraining with Real-World Feeds:**
   To train a production-grade model, operators should place a raw, heterogeneous feed into `datasets/phishing_site_urls.csv` (e.g. from OpenPhish, PhishTank, or Kaggle) and rerun:
   ```bash
   python -m scripts.train_url_model
   ```
3. **Distinction Between ML and Rule-Based Detectors:**
   - URL detection uses machine learning with calibrated confidence (`0.0`–`1.0`).
   - Email, Screenshot, and HTML modules use deterministic rule-based heuristic engines and return `confidence: null` to avoid misrepresenting heuristic severity as statistical probability.
   - Multimodal Fusion risk score (`0`–`100`) is a weighted heuristic risk index, **not** a calibrated Bayesian probability.
