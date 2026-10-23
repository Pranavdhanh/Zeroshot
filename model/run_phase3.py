"""
Phase 3 Gate Check: Graph Features + Ablation Study + Mule Detection Metrics.

Compares 3 models:
  1. Behavioural only (13 features)
  2. Behavioural + Context (26 features)
  3. Full: Behavioural + Context + Graph (41 features)

Outputs:
  - Ablation table proving graph contribution (especially on mule chains and QR swap)
  - Mule network metrics (fraction of mules flagged, cluster purity, time to detect)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pandas as pd
import numpy as np
from tabulate import tabulate

from features.builder import (
    build_feature_matrix,
    BEHAVIORAL_ONLY,
    BEHAVIORAL_PLUS_CONTEXT,
    FULL_FEATURES,
)
from model.train import (
    temporal_split,
    filter_seen_typologies,
    train_lightgbm,
    evaluate_model,
    evaluate_by_typology,
    predict_calibrated,
    get_feature_importance,
    SEEN_TYPOLOGIES,
    UNSEEN_TYPOLOGIES,
)
from eval.mule_metrics import evaluate_mule_detection


def run_phase3():
    """Execute Phase 3 gate check."""
    print("=" * 60)
    print("PHASE 3: Graph Features + Ablation Study + Mule Network Metrics")
    print("=" * 60)

    # -- Step 1: Load data and build full feature matrix ---------------
    print("\n[1/5] Loading transactions and computing full feature matrix...")
    features_full_path = "data/features_full.parquet"
    if os.path.exists(features_full_path):
        print(f"  Loading existing full feature matrix from {features_full_path}...")
        feature_df = pd.read_parquet(features_full_path)
    else:
        df = pd.read_parquet("data/transactions.parquet")
        print(f"  Loaded {len(df):,} transactions")
        feature_df = build_feature_matrix(df, progress_interval=100000, include_graph=True)
        feature_df.to_parquet(features_full_path, index=False)
        print(f"  Saved to {features_full_path}")

    print(f"  Feature matrix shape: {feature_df.shape}")

    # -- Step 2: Temporal split ---------------------------------------
    print("\n[2/5] Temporal split...")
    train_df, val_df, test_df = temporal_split(feature_df)

    train_filtered = filter_seen_typologies(train_df)
    val_filtered = filter_seen_typologies(val_df)

    print(f"  Train: {len(train_filtered):,} txns (seen only)")
    print(f"  Val:   {len(val_filtered):,} txns (seen only)")
    print(f"  Test:  {len(test_df):,} txns (all typologies)")

    # Test sets for seen and unseen
    test_seen = test_df[
        (test_df["is_fraud"] == False) | (test_df["fraud_typology"].isin(SEEN_TYPOLOGIES))
    ]
    test_unseen = test_df[
        (test_df["is_fraud"] == False) | (test_df["fraud_typology"].isin(UNSEEN_TYPOLOGIES))
    ]

    # -- Step 3: Train and evaluate all 3 configurations (Ablation) ---
    print("\n[3/5] Running Ablation Experiments...")
    configs = [
        ("Behavioural Only", BEHAVIORAL_ONLY, "model/artifacts/ablation_behav"),
        ("Behavioural + Context", BEHAVIORAL_PLUS_CONTEXT, "model/artifacts/ablation_ctx"),
        ("Full (+ Graph Features)", FULL_FEATURES, "model/artifacts/model_full"),
    ]

    ablation_rows = []
    trained_models = {}

    for name, feat_cols, mdir in configs:
        print(f"\n  Training: {name} ({len(feat_cols)} features)...")
        booster, calibrator = train_lightgbm(
            train_filtered, val_filtered, feat_cols, model_dir=mdir,
        )
        trained_models[name] = (booster, calibrator, feat_cols)

        # Evaluate
        eval_overall = evaluate_model(booster, calibrator, test_df, feat_cols, label=name)
        eval_seen = evaluate_model(booster, calibrator, test_seen, feat_cols, label=f"{name}_seen")
        eval_unseen = evaluate_model(booster, calibrator, test_unseen, feat_cols, label=f"{name}_unseen")
        per_typ = evaluate_by_typology(booster, calibrator, test_df, feat_cols)

        # Typology specific recalls
        mule_chain_row = per_typ[per_typ["typology"] == "mule_chain"]
        mule_recall = mule_chain_row["recall"].values[0] if len(mule_chain_row) > 0 else 0.0

        qr_swap_row = per_typ[per_typ["typology"] == "qr_swap"]
        qr_recall = qr_swap_row["recall"].values[0] if len(qr_swap_row) > 0 else 0.0

        ablation_rows.append({
            "Configuration": name,
            "Features": len(feat_cols),
            "PR-AUC (All)": f"{eval_overall['pr_auc']:.4f}",
            "ROC-AUC (All)": f"{eval_overall['roc_auc']:.4f}",
            "Precision": f"{eval_overall['precision']:.4f}",
            "Recall": f"{eval_overall['recall']:.4f}",
            "FPR": f"{eval_overall['fpr']:.5f}",
            "Seen PR-AUC": f"{eval_seen['pr_auc']:.4f}",
            "Unseen PR-AUC": f"{eval_unseen['pr_auc']:.4f}",
            "Mule Chain Recall": f"{mule_recall*100:.1f}%",
            "QR Swap Recall": f"{qr_recall*100:.1f}%",
        })

    print("\n" + "=" * 60)
    print("ABLATION STUDY RESULTS")
    print("=" * 60)
    ablation_table = tabulate(ablation_rows, headers="keys", tablefmt="grid")
    print(ablation_table)

    # -- Step 4: Full model detailed breakdown -------------------------
    print("\n[4/5] Detailed Breakdown for Full Model (+ Graph Features)...")
    full_booster, full_calibrator, full_cols = trained_models["Full (+ Graph Features)"]

    importance_df = get_feature_importance(full_booster, full_cols)
    print("\n  Top 12 Features by Gain (showing graph feature impact):")
    print(tabulate(importance_df.head(12), headers="keys", tablefmt="grid", showindex=False))

    full_typology_df = evaluate_by_typology(full_booster, full_calibrator, test_df, full_cols)
    print("\n  Per-Typology Detection (Full Model):")
    print(tabulate(full_typology_df, headers="keys", tablefmt="grid", showindex=False))

    # -- Step 5: Mule Network Metrics ----------------------------------
    print("\n[5/5] Computing Mule Network Metrics...")
    # Add calibrated probabilities to test dataframe
    X_test_full = test_df[full_cols].values
    test_preds_df = test_df.copy()
    test_preds_df["prob"] = predict_calibrated(full_booster, full_calibrator, X_test_full)

    mule_accounts_df = pd.read_parquet("data/mule_accounts.parquet")
    mule_metrics = evaluate_mule_detection(test_preds_df, mule_accounts_df, threshold=0.5)

    print("\n  MULE NETWORK METRICS:")
    mule_table = [
        ["Total mule accounts in registry", mule_metrics["total_mule_accounts"]],
        ["Active mule accounts in test set", mule_metrics["mules_active_in_test"]],
        ["Mule accounts correctly flagged", mule_metrics["mules_flagged"]],
        ["Fraction of mule accounts flagged", f"{mule_metrics['fraction_mules_flagged']*100:.1f}%"],
        ["Average cluster purity", f"{mule_metrics['average_cluster_purity']*100:.1f}%"],
        ["First-hop detection rate", f"{mule_metrics['first_hop_detection_rate']*100:.1f}%"],
        ["Median time to detect chain", f"{mule_metrics['median_time_to_detect_seconds']:.1f}s"],
        ["Mean time to detect chain", f"{mule_metrics['mean_time_to_detect_seconds']:.1f}s"],
    ]
    print(tabulate(mule_table, headers=["Metric", "Value"], tablefmt="grid"))

    # Save Phase 3 results
    results = {
        "ablation": ablation_rows,
        "mule_metrics": mule_metrics,
        "per_typology_full": full_typology_df.to_dict(orient="records"),
        "top_features": importance_df.head(15).to_dict(orient="records"),
    }
    with open("model/artifacts/phase3_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\n  Saved Phase 3 results to model/artifacts/phase3_results.json")

    print("\n" + "=" * 60)
    print("PHASE 3 GATE CHECK: COMPLETE")
    print("=" * 60)
    return results


if __name__ == "__main__":
    run_phase3()
