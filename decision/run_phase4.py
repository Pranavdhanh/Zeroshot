"""
Phase 4 Gate Check: Cost-Based Decision Engine & Friction Trade-off Curve.

Outputs:
  - Baseline decision matrix (ALLOW / WARN / HOLD breakdown)
  - Fraud caught vs customer friction curve
  - Optimal operating point maximizing net rupee savings
  - Senior citizen protection mode comparison
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pandas as pd
import numpy as np
from tabulate import tabulate

from decision.config import DecisionConfig
from decision.engine import CostDecisionEngine
from model.train import predict_calibrated
import lightgbm as lgb
import pickle


def run_phase4():
    """Execute Phase 4 gate check."""
    print("=" * 60)
    print("PHASE 4: Cost-Based Decision Layer + Friction Curve")
    print("=" * 60)

    # -- Step 1: Load test data and trained model ---------------------
    print("\n[1/4] Loading test dataset and trained model...")
    feature_df = pd.read_parquet("data/features_full.parquet")
    feature_df["timestamp"] = pd.to_datetime(feature_df["timestamp"])
    min_date = feature_df["timestamp"].min()
    day_75 = min_date + pd.Timedelta(days=75)
    test_df = feature_df[feature_df["timestamp"] >= day_75].copy().reset_index(drop=True)

    with open("model/artifacts/model_full/feature_columns.json", "r") as f:
        feature_cols = json.load(f)

    booster = lgb.Booster(model_file="model/artifacts/model_full/lgbm_model.txt")
    with open("model/artifacts/model_full/calibrator.pkl", "rb") as f:
        calibrator = pickle.load(f)

    # Generate calibrated probabilities
    X_test = test_df[feature_cols].values
    probs = predict_calibrated(booster, calibrator, X_test)
    test_df["prob"] = probs

    # Load user profiles to get is_senior flag
    user_profiles = pd.read_parquet("data/user_profiles.parquet")
    senior_vpas = set(user_profiles[user_profiles["is_senior"] == True]["vpa"].tolist())
    test_df["is_senior"] = test_df["sender_vpa"].isin(senior_vpas)

    print(f"  Test set: {len(test_df):,} transactions ({int(test_df['is_fraud'].sum())} fraud)")

    # -- Step 2: Baseline Cost-Based Decision -------------------------
    print("\n[2/4] Evaluating Baseline Decision Policy...")
    config = DecisionConfig()
    engine = CostDecisionEngine(config)

    amounts = test_df["amount"].values
    y_fraud = test_df["is_fraud"].values
    is_senior = test_df["is_senior"].values
    is_collect = test_df["is_collect_request"].values

    stats = engine.evaluate_batch(amounts, probs, y_fraud, is_senior, is_collect)
    test_df["action"] = stats["actions"]

    action_counts = test_df.groupby(["action", "is_fraud"]).size().unstack(fill_value=0)
    print("\n  ACTION ROUTING BREAKDOWN (Test Set):")
    action_table = []
    for act in ["ALLOW", "WARN", "HOLD"]:
        if act in action_counts.index:
            n_gen = action_counts.loc[act, False] if False in action_counts.columns else 0
            n_frd = action_counts.loc[act, True] if True in action_counts.columns else 0
        else:
            n_gen = 0
            n_frd = 0
        total_act = n_gen + n_frd
        action_table.append([act, f"{n_gen:,}", f"{n_frd:,}", f"{total_act:,}"])
    print(tabulate(action_table, headers=["Action", "Genuine", "Fraud", "Total"], tablefmt="grid"))

    print("\n  FINANCIAL & FRICTION IMPACT:")
    impact_table = [
        ["Total Fraud Amount at Risk", f"Rs. {stats['total_fraud_amount']:,.0f}"],
        ["Fraud Amount Successfully Prevented", f"Rs. {stats['prevented_fraud_amount']:,.0f}"],
        ["Fraud Amount Prevented (%)", f"{stats['fraud_amount_prevented_pct']:.2f}%"],
        ["Genuine Payments Flagged (WARN)", f"{stats['genuine_warn_count']:,} (Rs. 50 friction penalty)"],
        ["Genuine Payments Delayed (HOLD)", f"{stats['genuine_hold_count']:,} (Rs. 600 friction penalty)"],
        ["Total Friction Penalty Cost", f"Rs. {stats['total_friction_cost']:,.0f}"],
        ["NET FINANCIAL SAVINGS", f"Rs. {stats['net_value_saved']:,.0f}"],
    ]
    print(tabulate(impact_table, headers=["Metric", "Value"], tablefmt="grid"))

    # -- Step 3: Fraud Caught vs Customer Friction Curve --------------
    print("\n[3/4] Generating Fraud Caught vs Friction Trade-Off Curve...")
    curve = engine.generate_friction_curve(amounts, probs, y_fraud, num_points=12)

    curve_rows = []
    for pt in curve:
        curve_rows.append([
            f"{pt['friction_multiplier']:.2f}x",
            f"Rs. {pt['warn_friction_cost']:.0f}",
            f"Rs. {pt['hold_friction_cost']:.0f}",
            f"Rs. {pt['prevented_fraud_amount']:,.0f}",
            pt['genuine_friction_count'],
            f"{pt['fraud_recall_pct']:.1f}%",
            f"Rs. {pt['net_value_saved']:,.0f}",
        ])
    print(tabulate(
        curve_rows,
        headers=["Multiplier", "Warn Cost", "Hold Cost", "Fraud Prevented", "Friction Count", "Fraud Recall", "Net Saved"],
        tablefmt="grid",
    ))

    # Identify optimal operating point
    best_point = max(curve, key=lambda x: x["net_value_saved"])
    print(f"\n  OPTIMAL OPERATING POINT:")
    print(f"    Friction multiplier: {best_point['friction_multiplier']}x")
    print(f"    Fraud Prevented: Rs. {best_point['prevented_fraud_amount']:,.0f} ({best_point['fraud_recall_pct']}% recall)")
    print(f"    Genuine Customer Friction Count: {best_point['genuine_friction_count']}")
    print(f"    Maximum Net Financial Savings: Rs. {best_point['net_value_saved']:,.0f}")

    # -- Step 4: Senior Citizen Protection Mode -----------------------
    print("\n[4/4] Senior Citizen Protection Mode Impact...")
    senior_txns = test_df[test_df["is_senior"] == True]
    if len(senior_txns) > 0:
        senior_fraud = senior_txns[senior_txns["is_fraud"] == True]
        senior_detected = len(senior_fraud[senior_fraud["action"].isin(["WARN", "HOLD"])])
        senior_recall = senior_detected / max(1, len(senior_fraud)) * 100.0
        print(f"  Senior citizen transactions: {len(senior_txns):,}")
        print(f"  Senior citizen fraud events: {len(senior_fraud)}")
        print(f"  Senior fraud caught (WARN/HOLD): {senior_detected} ({senior_recall:.1f}%)")
    else:
        print("  No senior citizen transactions in test partition.")

    # Save Phase 4 results
    os.makedirs("decision/artifacts", exist_ok=True)
    results = {
        "baseline_stats": {
            "total_fraud_amount": stats["total_fraud_amount"],
            "prevented_fraud_amount": stats["prevented_fraud_amount"],
            "fraud_amount_prevented_pct": stats["fraud_amount_prevented_pct"],
            "genuine_friction_count": stats["genuine_friction_count"],
            "total_friction_cost": stats["total_friction_cost"],
            "net_value_saved": stats["net_value_saved"],
        },
        "friction_curve": curve,
        "optimal_point": best_point,
    }
    with open("decision/artifacts/decision_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Save live config
    with open("decision/artifacts/decision_config.json", "w") as f:
        json.dump(config.__dict__, f, indent=2)
    print("\n  Saved Phase 4 results to decision/artifacts/decision_results.json")

    print("\n" + "=" * 60)
    print("PHASE 4 GATE CHECK: COMPLETE")
    print("=" * 60)
    return results


if __name__ == "__main__":
    run_phase4()
