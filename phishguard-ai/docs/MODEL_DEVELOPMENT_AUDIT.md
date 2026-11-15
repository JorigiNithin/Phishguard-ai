# MODEL DEVELOPMENT AND SELECTION AUDIT REPORT
## PhishGuard AI — Multimodal Phishing Detection System

**Author / Project:** PhishGuard AI  
**Document Target:** Model Development, Evaluation & Selection (B.Tech Project Report)  
**Date of Audit:** November 15, 2026  
**Audited Artifacts:**
- Model Binary: `phishguard-ai/models/url_detector.joblib`
- Metadata: `phishguard-ai/models/url_detector_meta.json`
- Training Script: `phishguard-ai/backend/scripts/train_url_model.py`
- Inference Engine: `phishguard-ai/backend/app/services/url_predictor.py`
- Multimodal Fusion Service: `phishguard-ai/backend/app/services/fusion.py`
- Analyzers: `email_detector.py`, `screenshot_detector.py`, `html_detector.py`

---

## 1. Executive Summary & Faculty-Ready Statement

### Formal Audit Finding:
> In PhishGuard AI, **exactly one statistical machine learning model was trained, evaluated, and serialized**: a **Random Forest Classifier** for lexical/structural **URL phishing detection**. The other three detection modules (**Email**, **Screenshot**, and **HTML**) are engineered as **expert heuristic and rule-based inspection engines**, not supervised statistical models. All four modalities feed into a configurable **Weighted Multimodal Fusion Engine** that computes a unified risk score.
>
> **No baseline model** (such as Logistic Regression, Decision Stump, or Naive Bayes) was implemented or evaluated prior to selecting Random Forest.

### Short Faculty-Ready Explanation:
> *"For the URL phishing detection modality, we developed and trained a Scikit-Learn Random Forest Classifier utilizing 17 lexical, syntactic, and information-theoretic features extracted without initiating outbound network requests. On the 7,330-sample synthetic benchmark dataset (80/20 stratified split), the ensemble achieved 100% precision and recall in 0.27s training time, benefiting from the clear geometric separation in lexical indicators like Shannon entropy, URL length, and digit density. For Email, Screenshot, and HTML vectors, rather than training opaque black-box models on unverified corpora, we implemented deterministic rule-based engines (regular expression semantic triggers, Tesseract OCR text extraction, and BeautifulSoup DOM AST parsing). A domain-weighted Multimodal Fusion Engine dynamically integrates available modality outputs (weights: URL 0.30, Email 0.30, HTML 0.25, Screenshot 0.15) into a normalized 0–100 risk score, providing high explainability while ensuring missing modalities are never presumed safe."*

---

## 2. Models Actually Trained

Strict code and filesystem inspection reveals that **only one model** was actually trained and saved in this repository:

| Specification Attribute | Recorded Implementation Details |
|---|---|
| **Model Identifier** | `url_detector` |
| **Exact Algorithm** | `sklearn.ensemble.RandomForestClassifier` |
| **Modality** | **URL Only** |
| **Source Script** | `backend/scripts/train_url_model.py` |
| **Training Dataset** | `datasets/url_dataset_clean.csv` (7,330 total samples: 5,000 phishing, 2,330 legitimate) |
| **Features Used** | 17 numerical features (`url_features.py`) |
| **Train / Test Split** | 80% Train ($N = 5,864$) / 20% Test ($N = 1,466$), `stratify=y`, `random_state=42` |
| **Hyperparameters** | `n_estimators=100`, `max_depth=20`, `min_samples_split=5`, `min_samples_leaf=2`, `random_state=42`, `n_jobs=-1` |
| **Training Execution Time**| **0.27 seconds** (recorded in `models/url_detector_meta.json`) |
| **Training Status** | **Successfully Trained & Persisted** (File timestamp: Nov 10, 2026, 05:41 PM) |
| **Saved Model File** | `models/url_detector.joblib` (Size: 118,201 bytes) |
| **Saved Metadata File** | `models/url_detector_meta.json` (Size: 950 bytes) |

> [!NOTE]
> No supervised statistical models were trained for Email, Screenshot, HTML, or Multimodal modalities. They are deterministic heuristic analyzers and rule-based pipelines.

---

## 3. Baseline Model Audit

- **Finding:** **No baseline model was implemented or evaluated in the repository.**
- **Evaluation Details:**
  - Baseline Algorithm: **None implemented**
  - Accuracy: **Not recorded**
  - Precision: **Not recorded**
  - Recall: **Not recorded**
  - F1-Score: **Not recorded**
  - Confusion Matrix: **Not recorded**
  - Baseline Dataset Size: **Not applicable**

### Technical Context for Faculty:
In standard academic practice, a baseline such as `DummyClassifier(strategy="most_frequent")` (which would yield 68.21% accuracy on this dataset) or a linear `LogisticRegression` model is used as a benchmark. In this project, development progressed directly to the non-linear Random Forest ensemble to capture complex feature combinations (such as the joint interaction between high Shannon entropy, non-standard ports, and credential keywords).

---

## 4. Selected Model per Modality

| Modality | Models Evaluated | Selected Model / Engine | Validation / Test Performance | Reason for Selection |
|---|---|---|---|---|
| **URL** | Random Forest Classifier (1 candidate evaluated) | **Random Forest Classifier** (`models/url_detector.joblib`) | **Test Set ($N=1,466$):**<br>• Accuracy: 1.0000<br>• Precision: 1.0000<br>• Recall: 1.0000<br>• F1-Score: 1.0000<br>• ROC-AUC: 1.0000 | Non-linear tree ensemble handles heterogeneous scale features (counts, lengths, entropy); robust to outliers; sub-millisecond inference time. |
| **Email** | Rule-Based Heuristic Parser (no ML models trained) | **`EmailDetector`** (`backend/app/services/email_detector.py`) | Evaluated via unit test suite (`test_email.py`): 7/7 tests passed. | Avoids privacy violations of storing user emails; provides transparent, immediate explainability for urgency and credential lures. |
| **Screenshot** | Computer Vision OCR Pipeline (no ML models trained) | **`ScreenshotDetector`** (`backend/app/services/screenshot_detector.py`) | Evaluated via unit test suite (`test_screenshot.py`): 7/7 tests passed. | Extracts textual indicators using Tesseract OCR and Pillow without requiring heavy GPU vision transformers. |
| **HTML** | Static AST DOM Parser (no ML models trained) | **`HtmlDetector`** (`backend/app/services/html_detector.py`) | Evaluated via unit test suite (`test_html.py`): 10/10 tests passed. | Parses raw DOM using BeautifulSoup4; guarantees zero JavaScript execution and zero outbound network calls (XSS/SSRF immune). |
| **Multimodal** | Weighted Score Fusion Engine (no ML meta-classifier) | **`WeightedMultimodalFusion`** (`backend/app/services/fusion.py`) | Evaluated via integration test suite (`test_section4_multimodal.py`): 11/11 tests passed. | Transparent mathematical formula; handles arbitrary missing modalities without presuming safe status; deduplicates overlapping indicators. |

---

## 5. Model Selection Rationale (URL Modality)

### 5.1 Test Set Evaluation Metrics (Recorded in `models/url_detector_meta.json`)
The held-out evaluation set comprised $20\%$ of the 7,330 samples ($N = 1,466$ URLs: 466 legitimate, 1,000 phishing):

```json
"metrics": {
  "accuracy": 1.0,
  "precision": 1.0,
  "recall": 1.0,
  "f1_score": 1.0,
  "roc_auc": 1.0,
  "confusion_matrix": [
    [466, 0],
    [0, 1000]
  ]
}
```

- **True Negatives (Legitimate correctly identified):** 466 (100.0%)
- **False Positives (Legitimate misclassified as Phishing):** 0 (0.0%)
- **False Negatives (Phishing misclassified as Legitimate):** 0 (0.0%)
- **True Positives (Phishing correctly identified):** 1,000 (100.0%)

### 5.2 Rationale Criteria
1. **Validation F1-Score & Accuracy:** The classifier scored a perfect `1.0000` across all evaluation metrics on the held-out split.
2. **Computational Efficiency:** Training time was **0.27 seconds** for 100 trees on 5,864 rows. Inference takes $< 1\text{ ms}$ per URL, making it suitable for real-time API serving.
3. **Overfitting Controls:** The script explicitly enforced regularization parameters:
   - `max_depth=20`: Limits tree depth to prevent leaf overfitting on specific hash substrings.
   - `min_samples_split=5`: Requires at least 5 samples to consider an internal split.
   - `min_samples_leaf=2`: Ensures terminal nodes generalize over multiple observations.
4. **Data Artifact Context:** As documented in the Exploratory Data Analysis (`docs/EDA_RESULTS.md`), the 100% test performance is an empirical consequence of the synthetic benchmark dataset, where lexical features (`entropy`, `url_length`, `digit_count`) are strongly separable. In real-world environments, this ML detector is reinforced by the multimodal fusion pipeline.

---

## 6. Multimodal Fusion Engine Configuration

The multimodal fusion service is implemented in `backend/app/services/fusion.py`:

### 6.1 Modalities Included
- `url`: Random Forest lexical model output (normalized to 0–100 scale).
- `email`: Heuristic email detector output (0–100 risk score).
- `screenshot`: Optical character OCR detector output (0–100 risk score).
- `html`: Static DOM parsing detector output (0–100 risk score).

### 6.2 Mathematical Fusion Formula
$$\text{Overall Risk} = \text{round}\left(\frac{\sum_{i \in \text{Available}} w_i \times S_i}{\sum_{i \in \text{Available}} w_i}\right)$$

Where $S_i \in [0, 100]$ is the normalized risk score of modality $i$, and $w_i$ is its assigned weight.

### 6.3 Configured Modality Weights
The weights are configured in `backend/app/services/fusion.py#L35-L40`:
- **`url`:** `0.30` (30%) — Core primary indicator, low false-positive baseline.
- **`email`:** `0.30` (30%) — Direct attack vector for social engineering lures.
- **`html`:** `0.25` (25%) — Definitive source of form submission targets and hidden scripts.
- **`screenshot`:** `0.15` (15%) — Supplementary visual text, lower weight due to OCR noise/resolution dependence.

### 6.4 Optimization Methodology
> **Finding:** The fusion weights were **manually configured based on domain risk hierarchy and detector reliability**. They were **not** empirically optimized via logistic regression, grid-search, or Bayesian optimization.

### 6.5 Classification Thresholds
- $\text{Overall Risk} \ge 60 \implies \textbf{"phishing"}$
- $30 \le \text{Overall Risk} < 60 \implies \textbf{"suspicious"}$
- $\text{Overall Risk} < 30 \implies \textbf{"safe"}$

### 6.6 Missing Modality Handling
- **Dynamic Normalization:** Missing modalities are omitted from both the numerator and denominator ($\sum_{i \in \text{Available}} w_i$).
- **No Zero-Imputation:** Missing data is **never assumed to be safe** (i.e. not treated as 0 risk). If only the URL is provided, the overall risk is 100% determined by the URL score ($w_{\text{total}} = 0.30$).
- **Transparent Logging:** The explanation engine appends an explicit informational notice indicating which modalities were omitted from the analysis.
- **Confidence Metric:** The output strictly labels the result as a heuristic score with `confidence = null`, explicitly avoiding the misrepresentation of a weighted score as a calibrated Bayesian probability.

---

## 7. Evidence & Source Code References

| Finding / Item | Primary Source File | Lines / Metadata |
|---|---|---|
| Trained URL Model Class | `backend/scripts/train_url_model.py` | Lines 81–95 |
| URL Model Hyperparameters | `backend/scripts/train_url_model.py` | Lines 84–91 |
| Evaluation Metrics & Confusion Matrix | `models/url_detector_meta.json` | Lines 30–46 |
| Training Dataset Split | `models/url_detector_meta.json` | Lines 25–28 |
| Email Detector (Rule-Based) | `backend/app/services/email_detector.py` | Lines 6–8 |
| Screenshot OCR Pipeline | `backend/app/services/screenshot_detector.py` | Lines 1–14 |
| HTML Static DOM Parser | `backend/app/services/html_detector.py` | Lines 1–11 |
| Multimodal Fusion Weights & Formula | `backend/app/services/fusion.py` | Lines 6–25 & 35–40 |
| Threshold Logic & Missing Modality | `backend/app/services/fusion.py` | Lines 70–105 |

---

## 8. Summary Checklist for B.Tech Submission

- [x] Documented all models actually trained (1 model: Random Forest URL detector).
- [x] Confirmed absence of baseline models (explicitly stated).
- [x] Clarified distinction between ML URL detector and heuristic Email/Screenshot/HTML engines.
- [x] Documented exact evaluation metrics (100% on 1,466 test samples) and confusion matrix.
- [x] Documented multimodal fusion formula, weights, thresholds, and missing modality rules.
- [x] Verified all findings against repository source files without fabricating metrics.

