"""
LightGBM model training with temporal split, calibration, and SHAP.

Design decisions:
  - Temporal split: train on first 60 days, validate on days 61-75, test on days 76-90.
  - Typology holdout: train on subset of typologies, test on unseen ones.
  - Isotonic calibration on validation set.
  - SHAP TreeExplainer for per-prediction explanations.
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import (
    precision_recall_curve,
    average_precision_score,
    precision_score,
    recall_score,
    confusion_matrix,
    roc_curve,
    auc,
)
from typing import Dict, Any, List, Tuple, Optional


# Typology split for seen/unseen evaluation
# Train on these 5 typologies:
SEEN_TYPOLOGIES = [
    "fake_collect_request",
    "impersonation_vishing",
    "rapid_burst",
    "remote_access",
    "mule_chain",
]
# Test on these 2 (unseen during training):
UNSEEN_TYPOLOGIES = [
    "qr_swap",
    "account_takeover",
]


def temporal_split(
    feature_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data temporally: train (first 60 days), val (days 61-75), test (days 76-90).

    Returns
    -------
    (train_df, val_df, test_df)
    """
    feature_df = feature_df.copy()
    feature_df["timestamp"] = pd.to_datetime(feature_df["timestamp"])
    min_date = feature_df["timestamp"].min()

    day_60 = min_date + pd.Timedelta(days=60)
    day_75 = min_date + pd.Timedelta(days=75)

    train_mask = feature_df["timestamp"] < day_60
    val_mask = (feature_df["timestamp"] >= day_60) & (feature_df["timestamp"] < day_75)
    test_mask = feature_df["timestamp"] >= day_75

    train_df = feature_df[train_mask].copy()
    val_df = feature_df[val_mask].copy()
    test_df = feature_df[test_mask].copy()

    print(f"Temporal split:")
    print(f"  Train: {len(train_df):,} txns (< day 60), fraud: {train_df['is_fraud'].sum()}")
    print(f"  Val:   {len(val_df):,} txns (days 60-75), fraud: {val_df['is_fraud'].sum()}")
    print(f"  Test:  {len(test_df):,} txns (>= day 75), fraud: {test_df['is_fraud'].sum()}")

    return train_df, val_df, test_df


def filter_seen_typologies(df: pd.DataFrame) -> pd.DataFrame:
    """
    For training: keep only genuine txns and fraud from SEEN typologies.
    This ensures the model never sees unseen typologies during training.
    """
    genuine_mask = df["is_fraud"] == False
    seen_fraud_mask = df["fraud_typology"].isin(SEEN_TYPOLOGIES)
    return df[genuine_mask | seen_fraud_mask].copy()


def train_lightgbm(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    feature_columns: List[str],
    model_dir: str = "model/artifacts",
) -> Tuple[lgb.Booster, Any]:
    """
    Train a LightGBM model on the training set, with early stopping on validation.

    Returns
    -------
    (booster, calibrator)
    """
    os.makedirs(model_dir, exist_ok=True)

    X_train = train_df[feature_columns].values
    y_train = train_df["is_fraud"].astype(int).values

    X_val = val_df[feature_columns].values
    y_val = val_df["is_fraud"].astype(int).values

    # Compute scale_pos_weight for class imbalance
    n_pos = int(y_train.sum())
    n_neg = len(y_train) - n_pos
    if n_pos > 0:
        scale_pos_weight = n_neg / n_pos
    else:
        scale_pos_weight = 1.0

    print(f"\nTraining LightGBM:")
    print(f"  Features: {len(feature_columns)}")
    print(f"  Train: {len(X_train):,} samples ({n_pos} positive)")
    print(f"  Val:   {len(X_val):,} samples ({int(y_val.sum())} positive)")
    print(f"  scale_pos_weight: {scale_pos_weight:.1f}")

    train_data = lgb.Dataset(X_train, label=y_train, feature_name=feature_columns)
    val_data = lgb.Dataset(X_val, label=y_val, feature_name=feature_columns, reference=train_data)

    params = {
        "objective": "binary",
        "metric": ["binary_logloss", "auc"],
        "boosting_type": "gbdt",
        "num_leaves": 63,
        "learning_rate": 0.05,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "scale_pos_weight": scale_pos_weight,
        "min_child_samples": 20,
        "verbose": -1,
        "seed": 42,
    }

    callbacks = [
        lgb.early_stopping(50, verbose=True),
        lgb.log_evaluation(50),
    ]

    booster = lgb.train(
        params,
        train_data,
        num_boost_round=500,
        valid_sets=[train_data, val_data],
        valid_names=["train", "val"],
        callbacks=callbacks,
    )

    print(f"  Best iteration: {booster.best_iteration}")

    # Save model
    model_path = os.path.join(model_dir, "lgbm_model.txt")
    booster.save_model(model_path)
    print(f"  Model saved to {model_path}")

    # ── Calibration (isotonic regression on validation set) ───────
    print(f"\nCalibrating probabilities (isotonic)...")
    raw_probs_val = booster.predict(X_val)
    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(raw_probs_val, y_val)

    calibrator_path = os.path.join(model_dir, "calibrator.pkl")
    with open(calibrator_path, "wb") as f:
        pickle.dump(calibrator, f)
    print(f"  Calibrator saved to {calibrator_path}")

    # Save feature columns
    with open(os.path.join(model_dir, "feature_columns.json"), "w") as f:
        json.dump(feature_columns, f)

    return booster, calibrator


def predict_calibrated(
    booster: lgb.Booster,
    calibrator: Any,
    X: np.ndarray,
) -> np.ndarray:
    """Return calibrated probabilities."""
    raw_probs = booster.predict(X)
    calibrated = calibrator.transform(raw_probs)
    return calibrated


def evaluate_model(
    booster: lgb.Booster,
    calibrator: Any,
    test_df: pd.DataFrame,
    feature_columns: List[str],
    label: str = "test",
) -> Dict[str, Any]:
    """
    Full evaluation on a test set.

    Returns a dict with all metrics.
    """
    X_test = test_df[feature_columns].values
    y_test = test_df["is_fraud"].astype(int).values

    probs = predict_calibrated(booster, calibrator, X_test)

    # PR curve
    precision_arr, recall_arr, thresholds = precision_recall_curve(y_test, probs)
    pr_auc = average_precision_score(y_test, probs)

    # ROC curve
    fpr_arr, tpr_arr, roc_thresholds = roc_curve(y_test, probs)
    roc_auc = auc(fpr_arr, tpr_arr)

    # Recall at fixed FPR levels
    recall_at_fpr = {}
    for target_fpr in [0.001, 0.005, 0.01]:
        # Find threshold that gives closest FPR
        valid_indices = np.where(fpr_arr <= target_fpr)[0]
        if len(valid_indices) > 0:
            best_idx = valid_indices[-1]  # highest TPR at this FPR
            recall_at_fpr[f"recall_at_fpr_{target_fpr}"] = float(tpr_arr[best_idx])
        else:
            recall_at_fpr[f"recall_at_fpr_{target_fpr}"] = 0.0

    # Find operating point: threshold that maximizes F1
    f1_scores = []
    for i in range(len(thresholds)):
        if precision_arr[i] + recall_arr[i] > 0:
            f1 = 2.0 * precision_arr[i] * recall_arr[i] / (precision_arr[i] + recall_arr[i])
        else:
            f1 = 0.0
        f1_scores.append(f1)
    best_f1_idx = np.argmax(f1_scores)
    best_threshold = float(thresholds[best_f1_idx])

    y_pred = (probs >= best_threshold).astype(int)
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    precision_val = precision_score(y_test, y_pred, zero_division=0)
    recall_val = recall_score(y_test, y_pred, zero_division=0)
    if (fp + tn) > 0:
        fpr_val = fp / (fp + tn)
    else:
        fpr_val = 0.0

    metrics = {
        "label": label,
        "total_samples": len(y_test),
        "total_fraud": int(y_test.sum()),
        "pr_auc": float(pr_auc),
        "roc_auc": float(roc_auc),
        "best_threshold": best_threshold,
        "precision": float(precision_val),
        "recall": float(recall_val),
        "fpr": float(fpr_val),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
    }
    metrics.update(recall_at_fpr)

    # Precision@k
    n_fraud = int(y_test.sum())
    if n_fraud > 0:
        for k_mult in [1, 2, 5]:
            k = n_fraud * k_mult
            if k > len(probs):
                k = len(probs)
            top_k_indices = np.argsort(probs)[::-1][:k]
            top_k_labels = y_test[top_k_indices]
            precision_at_k = float(top_k_labels.sum()) / k
            metrics[f"precision_at_{k_mult}x_fraud"] = precision_at_k

    return metrics


def evaluate_by_typology(
    booster: lgb.Booster,
    calibrator: Any,
    test_df: pd.DataFrame,
    feature_columns: List[str],
) -> pd.DataFrame:
    """
    Evaluate detection rate per fraud typology.

    Returns a DataFrame with per-typology recall.
    """
    X_test = test_df[feature_columns].values
    probs = predict_calibrated(booster, calibrator, X_test)

    # Use the overall best F1 threshold
    y_test = test_df["is_fraud"].astype(int).values
    precision_arr, recall_arr, thresholds = precision_recall_curve(y_test, probs)
    f1_scores = []
    for i in range(len(thresholds)):
        if precision_arr[i] + recall_arr[i] > 0:
            f1 = 2.0 * precision_arr[i] * recall_arr[i] / (precision_arr[i] + recall_arr[i])
        else:
            f1 = 0.0
        f1_scores.append(f1)
    best_f1_idx = np.argmax(f1_scores)
    threshold = float(thresholds[best_f1_idx])

    test_with_preds = test_df.copy()
    test_with_preds["prob"] = probs
    test_with_preds["pred"] = (probs >= threshold).astype(int)

    results = []
    for typology in test_with_preds["fraud_typology"].unique():
        if typology == "genuine":
            continue
        subset = test_with_preds[test_with_preds["fraud_typology"] == typology]
        n_total = len(subset)
        n_detected = int(subset["pred"].sum())
        if n_total > 0:
            recall = n_detected / n_total
        else:
            recall = 0.0
        avg_prob = float(subset["prob"].mean())
        is_seen = typology in SEEN_TYPOLOGIES

        results.append({
            "typology": typology,
            "seen_in_training": is_seen,
            "total": n_total,
            "detected": n_detected,
            "recall": recall,
            "avg_score": avg_prob,
        })

    return pd.DataFrame(results)


def get_feature_importance(booster: lgb.Booster, feature_columns: List[str]) -> pd.DataFrame:
    """Return feature importance as a sorted DataFrame."""
    importance = booster.feature_importance(importance_type="gain")
    df = pd.DataFrame({
        "feature": feature_columns,
        "importance": importance,
    })
    df = df.sort_values("importance", ascending=False).reset_index(drop=True)
    return df
