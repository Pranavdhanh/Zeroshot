"""
UPI Shield AI — Measurable Model Evaluation Pipeline
Track 4: FinTech & GovTech Intelligence

Evaluates fraud detection performance on a held-out test set:
- Precision, Recall, False Positive Rate (FPR), ROC-AUC
- Confusion matrix counts
- Individual transaction scoring latency statistics (median, p95, mean)
- Generates backend/evaluation_report.json

DISCLAIMER:
Evaluated on synthetic simulation data. High performance on synthetic test sets
does not constitute proof of real-world operational efficacy.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, roc_auc_score

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from data_generator import generate_synthetic_dataset, FEATURE_COLUMNS
from fraud_engine import FraudScoringEngine

REPORT_PATH = CURRENT_DIR / "evaluation_report.json"


def run_evaluation(
    n_samples: int = 5000,
    random_seed: int = 99,
    output_path: Path = REPORT_PATH
) -> Dict[str, Any]:
    """
    Runs full evaluation:
    1. Loads trained model (or tests fallback if un-trained)
    2. Tests on an independent held-out synthetic dataset
    3. Measures precise single-transaction scoring latencies using perf_counter
    4. Computes performance metrics and saves JSON report
    """
    engine = FraudScoringEngine()
    print("=" * 65)
    print("UPI SHIELD AI -- MODEL EVALUATION (SYNTHETIC BENCHMARK)")
    print("=" * 65)
    print(f"Scoring Engine Mode: {'ML Random Forest' if engine.is_ml_loaded else 'Heuristic Fallback'}")
    print(f"Model Metadata: {engine.model_metadata}")

    print(f"\n[*] Generating independent held-out evaluation dataset ({n_samples} samples, seed={random_seed})...")
    df = generate_synthetic_dataset(n_samples=n_samples, random_seed=random_seed)

    X = df[FEATURE_COLUMNS]
    y_true = df["is_fraud"].values

    latencies_ms: List[float] = []
    y_pred_binary: List[int] = []
    y_scores: List[float] = []

    print(f"[*] Running individual transaction latency & prediction benchmark...")
    # Benchmark per-transaction scoring latency
    # Timing encompasses feature dictionary lookup, dataframe creation, and model inference
    for idx, row in X.iterrows():
        t0 = time.perf_counter()
        if engine.is_ml_loaded and engine.model is not None:
            # Single sample inference
            row_df = pd.DataFrame([row.to_dict()])
            prob = float(engine.model.predict_proba(row_df)[0, 1])
        else:
            prob, _ = engine._score_with_fallback(row.to_dict())
            prob = prob / 100.0

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)
        y_scores.append(prob)
        # Decision boundary: risk_score >= 50 or HOLD threshold (70)
        y_pred_binary.append(1 if prob >= 0.50 else 0)

    # Compute classification metrics
    cm = confusion_matrix(y_true, y_pred_binary)
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]

    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    auc = float(roc_auc_score(y_true, y_scores)) if len(set(y_true)) > 1 else 0.5

    # Latency percentiles
    lat_array = np.array(latencies_ms)
    lat_median = float(np.median(lat_array))
    lat_p95 = float(np.percentile(lat_array, 95))
    lat_p99 = float(np.percentile(lat_array, 99))
    lat_mean = float(np.mean(lat_array))
    lat_min = float(np.min(lat_array))
    lat_max = float(np.max(lat_array))

    report = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "data_notice": "SYNTHETIC_DATA_ONLY - Metrics reflect synthetic behavior, not real-world effectiveness",
        "model_version": engine.model_metadata.get("version", "unknown"),
        "algorithm": engine.model_metadata.get("algorithm", "unknown"),
        "is_ml_loaded": engine.is_ml_loaded,
        "test_sample_count": len(y_true),
        "class_distribution": {
            "genuine_count": int(np.sum(y_true == 0)),
            "fraud_count": int(np.sum(y_true == 1))
        },
        "performance_metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "false_positive_rate": round(fpr, 4),
            "roc_auc": round(auc, 4),
            "f1_score": round(2 * precision * recall / (precision + recall), 4) if (precision + recall) > 0 else 0.0
        },
        "confusion_matrix": {
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp
        },
        "scoring_latency_ms": {
            "mean": round(lat_mean, 3),
            "median": round(lat_median, 3),
            "p95": round(lat_p95, 3),
            "p99": round(lat_p99, 3),
            "min": round(lat_min, 3),
            "max": round(lat_max, 3),
            "target_sla_ms": 200.0,
            "sla_met": bool(lat_p95 < 200.0)
        }
    }

    # Print summary table
    print("\n" + "-" * 40)
    print("EVALUATION RESULTS")
    print("-" * 40)
    print(f"Test Samples:     {report['test_sample_count']}")
    print(f"Precision:        {report['performance_metrics']['precision'] * 100:.2f}%")
    print(f"Recall:           {report['performance_metrics']['recall'] * 100:.2f}%")
    print(f"FPR:              {report['performance_metrics']['false_positive_rate'] * 100:.2f}%")
    print(f"ROC-AUC:          {report['performance_metrics']['roc_auc']:.4f}")
    print(f"Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print(f"\nLatency Performance:")
    print(f"Median:           {report['scoring_latency_ms']['median']:.2f} ms")
    print(f"p95:              {report['scoring_latency_ms']['p95']:.2f} ms (Target: < 200 ms)")
    print(f"SLA Met:          {'YES [OK]' if report['scoring_latency_ms']['sla_met'] else 'NO [!]'}")
    print("-" * 40)

    # Save to disk
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n[OK] Evaluation report written to: {output_path}")

    return report


if __name__ == "__main__":
    run_evaluation()
