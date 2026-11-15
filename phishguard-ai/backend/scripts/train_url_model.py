"""Train a Random Forest classifier for URL phishing detection.

Usage:
    python -m scripts.train_url_model

Reads the cleaned dataset, extracts features, trains, evaluates, and saves
the model + metadata to the models/ directory.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

# Allow imports from the backend package
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from app.services.url_features import FEATURE_NAMES, extract_features, features_to_vector
from scripts.prepare_dataset import prepare_dataset

_PROJECT_ROOT = _BACKEND_DIR.parent
_MODELS_DIR = _PROJECT_ROOT / "models"
_MODEL_PATH = _MODELS_DIR / "url_detector.joblib"
_META_PATH = _MODELS_DIR / "url_detector_meta.json"

RANDOM_SEED = 42
TEST_SIZE = 0.2


def train() -> None:
    # 1. Prepare dataset
    csv_path = prepare_dataset()
    df = pd.read_csv(csv_path)
    print(f"\n[train] Dataset: {len(df)} rows")
    print(f"[train] Label distribution:\n{df['label'].value_counts().to_string()}")

    # 2. Extract features
    print("\n[train] Extracting features…")
    feature_rows: list[list[float]] = []
    labels: list[int] = []
    skipped = 0

    for _, row in df.iterrows():
        try:
            feats = extract_features(row["url"])
            feature_rows.append(features_to_vector(feats))
            labels.append(1 if row["label"] == "bad" else 0)
        except (ValueError, Exception):
            skipped += 1

    X = np.array(feature_rows, dtype=np.float64)
    y = np.array(labels, dtype=np.int32)
    print(f"[train] Features extracted: {X.shape[0]} samples, {X.shape[1]} features")
    if skipped:
        print(f"[train] Skipped {skipped} malformed URLs")

    # 3. Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y,
    )
    print(f"[train] Train: {X_train.shape[0]}, Test: {X_test.shape[0]}")

    # 4. Train Random Forest
    print("\n[train] Training Random Forest…")
    t0 = time.time()
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)
    train_time = time.time() - t0
    print(f"[train] Training completed in {train_time:.2f}s")

    # 5. Evaluate
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred).tolist()

    print(f"\n{'='*50}")
    print("EVALUATION RESULTS (held-out test set)")
    print(f"{'='*50}")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1-score:  {f1:.4f}")
    print(f"  ROC-AUC:   {roc:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"  {cm}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["legitimate", "phishing"]))

    # 6. Save model
    _MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, _MODEL_PATH)
    print(f"[train] Model saved to {_MODEL_PATH}")

    # 7. Save metadata
    meta = {
        "model_type": "RandomForestClassifier",
        "feature_names": FEATURE_NAMES,
        "n_features": len(FEATURE_NAMES),
        "n_estimators": 100,
        "random_seed": RANDOM_SEED,
        "test_size": TEST_SIZE,
        "dataset_size": len(df),
        "train_size": int(X_train.shape[0]),
        "test_size_actual": int(X_test.shape[0]),
        "training_time_seconds": round(train_time, 2),
        "metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc, 4),
            "confusion_matrix": cm,
        },
        "labels": {"0": "legitimate", "1": "phishing"},
    }
    with open(_META_PATH, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[train] Metadata saved to {_META_PATH}")
    print("\n[train] Done.")


if __name__ == "__main__":
    train()

