"""
Phase 2 Gate Check: Feature pipeline + LightGBM + Evaluation.

Steps:
  1. Load the generated data
  2. Build feature matrix incrementally
  3. Temporal split
  4. Train LightGBM on seen typologies only
  5. Evaluate on full test set (seen vs unseen separately)
  6. Print gate check: metrics table
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from tabulate import tabulate
from datetime import datetime

from features.builder import build_feature_matrix, ALL_FEATURES, BEHAVIORAL_ONLY, BEHAVIORAL_PLUS_CONTEXT
from model.train import (
    temporal_split,
    filter_seen_typologies,
    train_lightgbm,
    evaluate_model,
    evaluate_by_typology,
    get_feature_importance,
    SEEN_TYPOLOGIES,
    UNSEEN_TYPOLOGIES,
)


def run_phase2():
    """Execute Phase 2: Feature pipeline + LightGBM + Evaluation."""

    print("=" * 60)
    print("PHASE 2: Feature Pipeline + LightGBM + Evaluation")
    print("=" * 60)

    # -- Step 1: Load data ----------------------------------------
    print("\n[1/5] Loading transaction data...")
    df = pd.read_parquet("data/transactions.parquet")
    print(f"  Loaded {len(df):,} transactions")
    df = df.sort_values("timestamp").reset_index(drop=True)

    # -- Step 2: Build features -----------------------------------
    print("\n[2/5] Building features incrementally...")
    feature_df = build_feature_matrix(df, progress_interval=100000)
    print(f"  Feature matrix shape: {feature_df.shape}")

    # Save feature matrix
    os.makedirs("data", exist_ok=True)
    feature_df.to_parquet("data/features.parquet", index=False)
    print("  Saved to data/features.parquet")

    # -- Step 3: Temporal split -----------------------------------
    print("\n[3/5] Temporal split...")
    train_df, val_df, test_df = temporal_split(feature_df)

    # Filter training data to only include seen typologies
    train_filtered = filter_seen_typologies(train_df)
    val_filtered = filter_seen_typologies(val_df)
    print(f"  Train (seen only): {len(train_filtered):,} txns, fraud: {train_filtered['is_fraud'].sum()}")
    print(f"  Val (seen only): {len(val_filtered):,} txns, fraud: {val_filtered['is_fraud'].sum()}")
    print(f"  Test (all): {len(test_df):,} txns, fraud: {test_df['is_fraud'].sum()}")
    print(f"  Seen typologies: {SEEN_TYPOLOGIES}")
    print(f"  Unseen typologies: {UNSEEN_TYPOLOGIES}")

    # -- Step 4: Train --------------------------------------------
    print("\n[4/5] Training LightGBM (behavioural + context features)...")
    feature_cols = ALL_FEATURES
    booster, calibrator = train_lightgbm(
        train_filtered, val_filtered, feature_cols, model_dir="model/artifacts",
    )

    # Feature importance
    importance_df = get_feature_importance(booster, feature_cols)
    print("\n  Top 10 features by gain:")
    print(tabulate(importance_df.head(10), headers="keys", tablefmt="grid", showindex=False))

    # -- Step 5: Evaluate -----------------------------------------
    print("\n[5/5] Evaluation...")

    # Overall test metrics
    overall_metrics = evaluate_model(booster, calibrator, test_df, feature_cols, label="overall_test")
    print("\n  OVERALL TEST METRICS:")
    metrics_table = [[k, v] for k, v in overall_metrics.items()]
    print(tabulate(metrics_table, headers=["Metric", "Value"], tablefmt="grid"))

    # Split test into seen and unseen
    test_seen = test_df[
        (test_df["is_fraud"] == False) | (test_df["fraud_typology"].isin(SEEN_TYPOLOGIES))
    ]
    test_unseen = test_df[
        (test_df["is_fraud"] == False) | (test_df["fraud_typology"].isin(UNSEEN_TYPOLOGIES))
    ]

    seen_metrics = evaluate_model(booster, calibrator, test_seen, feature_cols, label="seen_typologies")
    unseen_metrics = evaluate_model(booster, calibrator, test_unseen, feature_cols, label="unseen_typologies")

    print("\n  SEEN vs UNSEEN TYPOLOGY METRICS:")
    comparison = []
    for key in ["pr_auc", "roc_auc", "precision", "recall", "fpr",
                 "recall_at_fpr_0.001", "recall_at_fpr_0.005", "recall_at_fpr_0.01"]:
        comparison.append([key, f"{seen_metrics.get(key, 0):.4f}", f"{unseen_metrics.get(key, 0):.4f}"])
    print(tabulate(comparison, headers=["Metric", "Seen", "Unseen"], tablefmt="grid"))

    # Per-typology breakdown
    typology_df = evaluate_by_typology(booster, calibrator, test_df, feature_cols)
    print("\n  PER-TYPOLOGY DETECTION:")
    print(tabulate(typology_df, headers="keys", tablefmt="grid", showindex=False))

    # Confusion matrix
    print("\n  CONFUSION MATRIX (overall test):")
    print(f"    TP={overall_metrics['tp']}, FP={overall_metrics['fp']}")
    print(f"    FN={overall_metrics['fn']}, TN={overall_metrics['tn']}")

    # -- Leakage audit --------------------------------------------
    print("\n  LEAKAGE AUDIT:")
    if overall_metrics["pr_auc"] > 0.99:
        print("  WARNING: PR-AUC > 0.99 - possible leakage!")
        print("  Investigating feature distributions...")
        # Check if any single feature perfectly separates classes
        for feat in feature_cols:
            fraud_vals = test_df[test_df["is_fraud"] == True][feat]
            genuine_vals = test_df[test_df["is_fraud"] == False][feat]
            overlap = min(fraud_vals.max(), genuine_vals.max()) - max(fraud_vals.min(), genuine_vals.min())
            if overlap <= 0:
                print(f"    ALERT: Feature '{feat}' perfectly separates classes!")
    else:
        print("  PR-AUC is within reasonable range. No obvious leakage detected.")

    # Check unseen specifically
    if unseen_metrics.get("pr_auc", 0) > 0.99:
        print("  WARNING: Unseen PR-AUC > 0.99 - model may be learning generator artifacts.")
    else:
        print(f"  Unseen PR-AUC: {unseen_metrics.get('pr_auc', 0):.4f} - reasonable for unseen typologies.")

    # -- Save results ---------------------------------------------
    results = {
        "overall": overall_metrics,
        "seen": seen_metrics,
        "unseen": unseen_metrics,
        "per_typology": typology_df.to_dict(orient="records"),
        "feature_importance": importance_df.to_dict(orient="records"),
    }

    os.makedirs("model/artifacts", exist_ok=True)
    import json
    with open("model/artifacts/phase2_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\n  Results saved to model/artifacts/phase2_results.json")

    print("\n" + "=" * 60)
    print("PHASE 2 GATE CHECK: COMPLETE")
    print("=" * 60)

    return results


if __name__ == "__main__":
    run_phase2()
