"""
UPI Shield AI — Real-Time Transaction Scoring & Fraud Engine
Track 4: FinTech & GovTech Intelligence

Extracts behavioural features from observed SQLite history, incorporates graph intelligence,
executes ML model inference, generates explainable reasons, and applies decision thresholds.
"""

import time
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import joblib
import pandas as pd
import numpy as np

# Add parent directory for imports
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from schemas import (
    THRESHOLD_ALLOW_MAX,
    THRESHOLD_WARN_MAX,
    DecisionType
)
import database
from graph_engine import graph_engine

logger = logging.getLogger("upi_shield.fraud_engine")

FEATURE_COLUMNS = [
    "amount",
    "amount_vs_avg",
    "is_new_payee",
    "transactions_last_10min",
    "is_unusual_hour",
    "device_changed",
    "recipient_risk",
    "network_risk"
]


class FraudScoringEngine:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or str(CURRENT_DIR / "models" / "fraud_model.joblib")
        self.model = None
        self.model_metadata: Dict[str, Any] = {}
        self.is_ml_loaded = False
        self.load_model()

    def load_model(self) -> bool:
        """
        Loads the trained scikit-learn model artifact from disk.
        If missing, activates a sensible, documented rule-based heuristic fallback.
        """
        if os.path.exists(self.model_path):
            try:
                artifact = joblib.load(self.model_path)
                self.model = artifact["model"]
                self.model_metadata = {
                    "version": artifact.get("model_version", "1.0.0"),
                    "algorithm": artifact.get("algorithm", "RandomForestClassifier"),
                    "trained_at": artifact.get("trained_at"),
                    "feature_names": artifact.get("feature_names", FEATURE_COLUMNS)
                }
                self.is_ml_loaded = True
                logger.info(f"[OK] ML Fraud Model successfully loaded from {self.model_path}")
                return True
            except Exception as e:
                logger.error(f"[!] Failed to load model artifact from {self.model_path}: {e}")
                self.is_ml_loaded = False
        else:
            logger.warning(
                f"[!] Model artifact not found at {self.model_path}. "
                "Operating in Heuristic Rule-Based Fallback Mode until train_model.py is executed."
            )
            self.is_ml_loaded = False

        self.model = None
        self.model_metadata = {
            "version": "0.1.0-heuristic-fallback",
            "algorithm": "RuleBasedHeuristicEngine",
            "notice": "Fallback scoring in effect. Model artifact not yet trained."
        }
        return False

    def extract_features(
        self,
        sender_id: str,
        recipient_id: str,
        amount: float,
        timestamp_str: Optional[str] = None,
        device_changed: bool = False,
        simulated_overrides: Optional[Dict[str, Any]] = None,
        db_path: Optional[str] = None
    ) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """
        Calculates behavioural features combining:
        1. Historical database baseline (sender's avg, past payees, 10-min velocity)
        2. Transaction payload (amount, device flag, time-of-day)
        3. Graph intelligence (network risk of recipient)
        4. Explicit simulation overrides (for test scenario replication)
        """
        simulated_overrides = simulated_overrides or {}

        # 1. Parse timestamp and determine unusual hours (11 PM - 5 AM)
        if timestamp_str:
            try:
                tx_dt = datetime.fromisoformat(timestamp_str)
            except Exception:
                tx_dt = datetime.utcnow()
        else:
            tx_dt = datetime.utcnow()

        hour = tx_dt.hour
        is_unusual_hour_computed = 1.0 if (hour < 5 or hour >= 23) else 0.0

        # 2. Query observed SQLite history for baseline
        history = database.get_sender_history_stats(sender_id, tx_dt.isoformat(), db_path=db_path)
        hist_avg = history["historical_avg_amount"]
        known_recipients = history["known_recipients"]
        tx_count_10m = history["transactions_last_10min"]

        # Amount vs Average ratio
        if "amount_vs_avg" in simulated_overrides:
            amount_vs_avg = float(simulated_overrides["amount_vs_avg"])
        elif hist_avg and hist_avg > 0:
            amount_vs_avg = round(amount / hist_avg, 3)
        else:
            # Baseline assumption if sender is newly seen: assume nominal baseline ₹1,500
            amount_vs_avg = round(amount / 1500.0, 3)

        # New payee indicator
        if "is_new_payee" in simulated_overrides:
            is_new_payee = 1.0 if simulated_overrides["is_new_payee"] else 0.0
        else:
            is_new_payee = 1.0 if (recipient_id not in known_recipients) else 0.0

        # Rapid payments in last 10 minutes
        if "transactions_last_10min" in simulated_overrides:
            transactions_last_10min = float(simulated_overrides["transactions_last_10min"])
        else:
            transactions_last_10min = float(tx_count_10m)

        # Device change
        if "device_changed" in simulated_overrides:
            device_changed_flag = 1.0 if simulated_overrides["device_changed"] else 0.0
        else:
            device_changed_flag = 1.0 if device_changed else 0.0

        # Unusual hour
        if "is_unusual_hour" in simulated_overrides:
            is_unusual_hour = 1.0 if simulated_overrides["is_unusual_hour"] else 0.0
        else:
            is_unusual_hour = is_unusual_hour_computed

        # Graph Network Risk
        if "network_risk" in simulated_overrides:
            network_risk = float(simulated_overrides["network_risk"])
        else:
            network_risk = graph_engine.get_node_network_risk(recipient_id)

        # Recipient risk
        if "recipient_risk" in simulated_overrides:
            recipient_risk = float(simulated_overrides["recipient_risk"])
        else:
            # Check if recipient ID has known keywords or is a mule node
            if "MULE" in recipient_id.upper() or "CASHOUT" in recipient_id.upper():
                recipient_risk = 0.85
            else:
                recipient_risk = max(0.05, network_risk * 0.8)

        feature_vector = {
            "amount": float(amount),
            "amount_vs_avg": float(amount_vs_avg),
            "is_new_payee": float(is_new_payee),
            "transactions_last_10min": float(transactions_last_10min),
            "is_unusual_hour": float(is_unusual_hour),
            "device_changed": float(device_changed_flag),
            "recipient_risk": float(recipient_risk),
            "network_risk": float(network_risk)
        }

        context = {
            "historical_avg": hist_avg,
            "past_tx_count": history["historical_tx_count"],
            "timestamp_used": tx_dt.isoformat(),
            "has_simulated_overrides": bool(simulated_overrides)
        }

        return feature_vector, context

    def _score_with_fallback(self, features: Dict[str, float]) -> Tuple[float, List[str]]:
        """
        Documented heuristic rule-based scoring fallback used ONLY when the ML artifact is absent.
        Combines weighted heuristic factors and generates explainable reasons.
        """
        risk_components: float = 5.0  # Base natural noise
        reasons: List[str] = []

        # 1. Amount ratio factor
        ratio = features["amount_vs_avg"]
        if ratio >= 6.0:
            risk_components += 30.0
            reasons.append(f"Amount is unusually high ({ratio:.1f}x sender's historic average)")
        elif ratio >= 3.0:
            risk_components += 16.0
            reasons.append(f"Amount is above normal range ({ratio:.1f}x historic average)")

        # 2. Velocity burst in 10 minutes
        velocity = features["transactions_last_10min"]
        if velocity >= 4:
            risk_components += 26.0
            reasons.append(f"Rapid velocity burst ({int(velocity)} transfers in last 10 minutes)")
        elif velocity >= 2:
            risk_components += 12.0
            reasons.append(f"Elevated frequency ({int(velocity)} transfers recently)")

        # 3. New payee
        if features["is_new_payee"] > 0:
            risk_components += 15.0
            reasons.append("New recipient (first-time transfer)")

        # 4. Device changed
        if features["device_changed"] > 0:
            risk_components += 18.0
            reasons.append("Unfamiliar device or altered client environment")

        # 5. Unusual hour
        if features["is_unusual_hour"] > 0:
            risk_components += 8.0
            reasons.append("Transaction initiated during unusual night hours (11 PM - 5 AM)")

        # 6. Recipient / Network Risk
        net_risk = features["network_risk"]
        rec_risk = features["recipient_risk"]
        if net_risk >= 0.60 or rec_risk >= 0.60:
            risk_components += 25.0
            reasons.append("Recipient account flagged by graph intelligence (mule or layering pattern)")
        elif net_risk >= 0.35:
            risk_components += 10.0
            reasons.append("Recipient is adjacent to high-risk payment network flow")

        # Normalize score to 0 - 100
        final_score = min(99.0, max(1.0, risk_components))
        if not reasons and final_score < THRESHOLD_ALLOW_MAX:
            reasons.append("Transaction matches sender's normal behavioral baseline")

        return round(final_score, 1), reasons

    def _generate_reasons_for_features(
        self,
        features: Dict[str, float],
        risk_score: float
    ) -> List[str]:
        """
        Produces human-readable, deterministic explanation strings for ML predictions.
        Never infers fraud solely based on one isolated feature.
        """
        reasons: List[str] = []

        ratio = features["amount_vs_avg"]
        if ratio >= 5.0:
            reasons.append(f"Amount is unusually high ({ratio:.1f}x sender's historic average)")
        elif ratio >= 3.0:
            reasons.append(f"Amount exceeds standard transaction pattern ({ratio:.1f}x average)")

        if features["is_new_payee"] > 0:
            reasons.append("New recipient (no prior payment history)")

        if features["device_changed"] > 0:
            reasons.append("Unfamiliar device detected")

        velocity = features["transactions_last_10min"]
        if velocity >= 3:
            reasons.append(f"High transaction frequency ({int(velocity)} payments in last 10 minutes)")

        if features["is_unusual_hour"] > 0:
            reasons.append("Transaction initiated during unusual night hours (11 PM - 5 AM)")

        if features["network_risk"] >= 0.55:
            reasons.append("Recipient associated with suspicious graph structure (mule hub or pass-through)")
        elif features["recipient_risk"] >= 0.55:
            reasons.append("Recipient profile carries elevated risk indicators")

        if not reasons or (risk_score < THRESHOLD_ALLOW_MAX and len(reasons) <= 1):
            if risk_score < THRESHOLD_ALLOW_MAX:
                reasons = ["Transaction matches sender's standard behavioral pattern"]

        return reasons

    def score_transaction(
        self,
        sender_id: str,
        recipient_id: str,
        amount: float,
        timestamp_str: Optional[str] = None,
        device_changed: bool = False,
        simulated_overrides: Optional[Dict[str, Any]] = None,
        db_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes scoring for a single incoming UPI transaction:
        1. Feature extraction with historical baseline
        2. ML model inference (or heuristic fallback)
        3. Threshold classification (ALLOW / WARN / HOLD)
        4. Explainability generation
        5. Actual server-side latency measurement
        """
        start_perf = time.perf_counter()

        features, context = self.extract_features(
            sender_id=sender_id,
            recipient_id=recipient_id,
            amount=amount,
            timestamp_str=timestamp_str,
            device_changed=device_changed,
            simulated_overrides=simulated_overrides,
            db_path=db_path
        )

        if self.is_ml_loaded and self.model is not None:
            # Model prediction pipeline
            feature_df = pd.DataFrame([features])[FEATURE_COLUMNS]
            prob_fraud = float(self.model.predict_proba(feature_df)[0, 1])
            risk_score = round(prob_fraud * 100.0, 1)
            reasons = self._generate_reasons_for_features(features, risk_score)
            model_type = "ml_prediction"
        else:
            # Documented heuristic fallback
            risk_score, reasons = self._score_with_fallback(features)
            model_type = "heuristic_fallback"

        # Apply configurable decision thresholds
        # ALLOW below 30, WARN from 30 to below 70, HOLD at 70 and above
        if risk_score < THRESHOLD_ALLOW_MAX:
            decision: DecisionType = "ALLOW"
        elif risk_score < THRESHOLD_WARN_MAX:
            decision: DecisionType = "WARN"
        else:
            decision: DecisionType = "HOLD"

        latency_ms = round((time.perf_counter() - start_perf) * 1000.0, 2)

        return {
            "risk_score": risk_score,
            "decision": decision,
            "reasons": reasons,
            "latency_ms": max(0.1, latency_ms),
            "features_used": features,
            "scoring_engine": model_type,
            "context": context
        }


# Global engine instance
fraud_engine = FraudScoringEngine()
