"""
UPI Shield AI — Model Training Pipeline
Track 4: FinTech & GovTech Intelligence

Trains a scikit-learn classifier on labelled synthetic transactions,
evaluates on a held-out test set to prevent leakage, and persists
the trained artifact to backend/models/fraud_model.joblib.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

# Ensure backend directory is in python search path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from data_generator import generate_synthetic_dataset, FEATURE_COLUMNS

# Artifact location
MODELS_DIR = CURRENT_DIR / "models"
MODEL_PATH = MODELS_DIR / "fraud_model.joblib"


def train_fraud_model(
    n_samples: int = 7500,
    random_seed: int = 42,
    save_artifact: bool = True
) -> dict:
    """
    Executes end-to-end model training:
    1. Generates reproducible synthetic dataset
    2. Splits into train and held-out test set (80/20)
    3. Trains a RandomForestClassifier with balanced class weighting
    4. Evaluates performance without data leakage
    5. Saves model artifact and feature contract
    """
    print(f"[*] Generating {n_samples} synthetic UPI transaction samples (seed={random_seed})...")
    df = generate_synthetic_dataset(n_samples=n_samples, random_seed=random_seed)

    X = df[FEATURE_COLUMNS]
    y = df["is_fraud"]

    print(f"[*] Features used ({len(FEATURE_COLUMNS)}): {FEATURE_COLUMNS}")
    print(f"[*] Label distribution: {y.value_counts().to_dict()}")

    # Stratified 80/20 train/test split to prevent data leakage
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=random_seed, stratify=y
    )

    print(f"[*] Training RandomForestClassifier on {len(X_train)} samples...")
    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=10,
        min_samples_split=4,
        class_weight="balanced",
        random_state=random_seed,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)

    # Evaluate on held-out test set
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    auc_score = float(roc_auc_score(y_test, y_prob))
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    # Feature importances
    importances = dict(zip(FEATURE_COLUMNS, [round(float(x), 4) for x in clf.feature_importances_]))

    print("\n--- Test Set Evaluation (Synthetic Simulation) ---")
    print(f"ROC-AUC:   {auc_score:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"FPR:       {fpr:.4f}")
    print(f"Confusion Matrix: [TN={tn}, FP={fp}, FN={fn}, TP={tp}]")
    print(f"Feature Importances: {importances}\n")

    artifact = {
        "model": clf,
        "feature_names": FEATURE_COLUMNS,
        "trained_at": datetime.utcnow().isoformat(),
        "model_version": "1.0.0-synthetic-rf",
        "algorithm": "RandomForestClassifier",
        "parameters": {
            "n_estimators": 120,
            "max_depth": 10,
            "min_samples_split": 4,
            "class_weight": "balanced"
        },
        "metrics": {
            "test_sample_count": len(y_test),
            "roc_auc": round(auc_score, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "fpr": round(fpr, 4),
            "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
            "feature_importances": importances
        }
    }

    if save_artifact:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(artifact, MODEL_PATH)
        print(f"[OK] Model artifact successfully saved to: {MODEL_PATH}")

    return artifact


if __name__ == "__main__":
    train_fraud_model()
