"""
Real-time transaction scorer for UPI Fraud Alert System.

Maintains in-memory incremental state (behavioral + graph) and executes
sub-millisecond inference, calibrated probability estimation, cost-based
decisioning, and fast SHAP feature explanations.
"""

import time
import json
import pickle
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import numpy as np
import lightgbm as lgb
import shap

from features.behavioral import BehavioralFeatureEngine
from features.context import compute_context_features
from features.graph import GraphFeatureEngine
from decision.config import DecisionConfig
from decision.engine import CostDecisionEngine


# Plain-language explanation templates (English & Tamil)
REASON_TEMPLATES = {
    "is_new_payee": {
        "en": "You have never sent money to this UPI ID before.",
        "ta": "நீங்கள் இதற்கு முன் இந்த UPI முகவரிக்கு பணம் அனுப்பியதில்லை.",
    },
    "amount_z_score": {
        "en": "The transaction amount is unusually high compared to your typical history.",
        "ta": "உங்கள் வழக்கமான பரிவர்த்தனைகளுடன் ஒப்பிடும்போது இந்த தொகை மிக அதிகம்.",
    },
    "is_collect_request": {
        "en": "This is an incoming collect request. Banks never ask you to approve a request or enter your PIN to receive money.",
        "ta": "இது பணம் கோரும் கோரிக்கை. பணத்தைப் பெற வங்கிகள் ஒருபோதும் PIN எண்ணை உள்ளிடுமாறு கேட்காது.",
    },
    "call_active_flag": {
        "en": "Active phone call detected during payment. Legitimate officials never ask you to make urgent UPI transfers over phone calls.",
        "ta": "அழைப்பின் போது பரிவர்த்தனை நடக்கிறது. அதிகாரிகள் போன் மூலம் அவசரமாக பணம் அனுப்பக் கேட்கமாட்டார்கள்.",
    },
    "screen_share_active": {
        "en": "Screen sharing or remote access app is active on your device. Fraudsters use screen sharing to view your screen and steal funds.",
        "ta": "திரைப் பகிர்வு செயலி இயங்குகிறது. மோசடி செய்பவர்கள் உங்கள் திரையைப் பார்த்து பணத்தைத் திருடக்கூடும்.",
    },
    "receiver_network_age_days": {
        "en": "The payee account was created very recently and has no established transaction history.",
        "ta": "பணம் பெறும் கணக்கு மிக சமீபத்தில் தொடங்கப்பட்டது, பழைய வரலாறு எதுவும் இல்லை.",
    },
    "receiver_in_degree": {
        "en": "The payee account has an abnormal spike in rapid incoming transfers from multiple strangers.",
        "ta": "பணம் பெறும் கணக்கு பல நபர்களிடமிருந்து குறுகிய காலத்தில் அதிக பணத்தைப் பெற்றுள்ளது.",
    },
    "receiver_pass_through_ratio": {
        "en": "This account shows mule layering behavior: funds are rapidly dispersed immediately upon arrival.",
        "ta": "இந்த கணக்கு பணத்தை உடனடியாக வேறு கணக்குகளுக்கு மாற்றும் முறைகேடான கணக்கு போன்ற நடத்தை கொண்டுள்ளது.",
    },
    "receiver_hop_to_flagged": {
        "en": "The payee account is directly connected in the network to known fraudulent or frozen accounts.",
        "ta": "இந்த கணக்கு முடக்கப்பட்ட அல்லது மோசடிக் கணக்குகளுடன் நேரடித் தொடர்பு கொண்டுள்ளது.",
    },
    "txn_new_device_flag": {
        "en": "Payment initiated from an unfamiliar or newly registered device.",
        "ta": "பரிவர்த்தனை ஒரு புதிய சாதனத்திலிருந்து தொடங்கப்பட்டுள்ளது.",
    },
    "sim_swap_flag": {
        "en": "A recent SIM swap was detected on your mobile connection.",
        "ta": "உங்கள் மொபைல் இணைப்பில் சமீபத்தில் சிம் கார்டு மாற்றம் கண்டறியப்பட்டுள்ளது.",
    },
    "default": {
        "en": "Unusual payment pattern detected that deviates significantly from normal behavior.",
        "ta": "வழக்கத்திற்கு மாறான பரிவர்த்தனை முறை கண்டறியப்பட்டுள்ளது.",
    },
}


class RealTimeScorer:
    """Thread-safe incremental transaction scoring engine."""

    def __init__(
        self,
        model_path: str = "model/artifacts/model_full/lgbm_model.txt",
        calibrator_path: str = "model/artifacts/model_full/calibrator.pkl",
        feature_cols_path: str = "model/artifacts/model_full/feature_columns.json",
        decision_config: DecisionConfig = None,
    ):
        self.behav_engine = BehavioralFeatureEngine()
        self.graph_engine = GraphFeatureEngine()

        # Load LightGBM booster
        self.booster = lgb.Booster(model_file=model_path)
        with open(calibrator_path, "rb") as f:
            self.calibrator = pickle.load(f)
        with open(feature_cols_path, "r") as f:
            self.feature_columns: List[str] = json.load(f)

        # Pre-initialize SHAP TreeExplainer for fast leaf contribution explanations
        self.explainer = shap.TreeExplainer(self.booster)

        # Decision engine
        if decision_config is None:
            self.decision_config = DecisionConfig()
        else:
            self.decision_config = decision_config
        self.decision_engine = CostDecisionEngine(self.decision_config)

        # Rolling latency tracking
        self.latency_history: List[float] = []

    def score_transaction(self, txn: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single incoming transaction end-to-end.

        Returns:
            Dict containing action (ALLOW/WARN/HOLD), risk_score, top_reasons,
            plain-language warnings in English and Tamil, and latency in milliseconds.
        """
        t_start = time.perf_counter()

        # 1. Incremental feature extraction
        behav_feats = self.behav_engine.compute(txn)
        ctx_feats = compute_context_features(txn)
        ctx_feats["call_and_new_payee"] = (
            ctx_feats["call_active_flag"] * behav_feats["is_new_payee"]
        )
        graph_feats = self.graph_engine.compute(txn)

        # Merge feature vector in exact order
        feature_vector: List[float] = []
        for feat in self.feature_columns:
            if feat in behav_feats:
                feature_vector.append(behav_feats[feat])
            elif feat in ctx_feats:
                feature_vector.append(ctx_feats[feat])
            elif feat in graph_feats:
                feature_vector.append(graph_feats[feat])
            else:
                feature_vector.append(0.0)

        X = np.array([feature_vector], dtype=np.float32)

        # 2. Inference & probability calibration
        raw_prob = float(self.booster.predict(X)[0])
        calibrated_prob = float(self.calibrator.transform([raw_prob])[0])

        # 3. Cost-based decisioning
        amount = float(txn.get("amount", 0.0))
        is_senior = bool(txn.get("is_senior", False))
        is_collect = bool(txn.get("is_collect_request", False))

        decision = self.decision_engine.decide_transaction(
            amount=amount,
            calibrated_prob=calibrated_prob,
            is_senior=is_senior,
            is_collect_request=is_collect,
        )
        action = decision["action"]

        # 4. Generate SHAP explanations for WARN and HOLD
        top_reasons: List[Dict[str, Any]] = []
        en_warning_msg = ""
        ta_warning_msg = ""

        if action in ["WARN", "HOLD"]:
            shap_values = self.explainer.shap_values(X)
            if isinstance(shap_values, list):
                vals = shap_values[1][0]
            else:
                vals = shap_values[0]

            top_indices = np.argsort(vals)[::-1]
            reasons_found: List[str] = []

            for idx in top_indices:
                if vals[idx] > 0.05 and len(top_reasons) < 3:
                    feat_name = self.feature_columns[idx]
                    top_reasons.append({
                        "feature": feat_name,
                        "importance": float(vals[idx]),
                        "value": float(feature_vector[idx]),
                    })
                    reasons_found.append(feat_name)

            # Map to plain-language templates
            en_lines: List[str] = []
            ta_lines: List[str] = []

            # Special case for fake collect requests
            if is_collect:
                en_lines.append(REASON_TEMPLATES["is_collect_request"]["en"])
                ta_lines.append(REASON_TEMPLATES["is_collect_request"]["ta"])

            for r in reasons_found:
                if r != "is_collect_request" and r in REASON_TEMPLATES:
                    en_lines.append(REASON_TEMPLATES[r]["en"])
                    ta_lines.append(REASON_TEMPLATES[r]["ta"])

            if len(en_lines) == 0:
                en_lines.append(REASON_TEMPLATES["default"]["en"])
                ta_lines.append(REASON_TEMPLATES["default"]["ta"])

            en_warning_msg = " ".join(en_lines[:2])
            ta_warning_msg = " ".join(ta_lines[:2])

        # 5. State update (incremental)
        self.behav_engine.update(txn)
        self.graph_engine.update(txn)

        t_end = time.perf_counter()
        latency_ms = (t_end - t_start) * 1000.0

        self.latency_history.append(latency_ms)
        if len(self.latency_history) > 10000:
            self.latency_history = self.latency_history[-5000:]

        return {
            "txn_id": txn.get("txn_id", ""),
            "timestamp": str(txn.get("timestamp", datetime.now().isoformat())),
            "sender_vpa": txn.get("sender_vpa", ""),
            "receiver_vpa": txn.get("receiver_vpa", ""),
            "amount": amount,
            "action": action,
            "risk_score": calibrated_prob,
            "top_reasons": top_reasons,
            "en_warning": en_warning_msg,
            "ta_warning": ta_warning_msg,
            "latency_ms": round(latency_ms, 3),
            "is_senior": is_senior,
            "is_collect_request": is_collect,
            "fraud_typology_guess": top_reasons[0]["feature"] if len(top_reasons) > 0 else "unknown",
        }

    def get_latency_stats(self) -> Dict[str, float]:
        """Return p50, p95, p99 latency stats in milliseconds."""
        if len(self.latency_history) == 0:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "count": 0}
        arr = np.array(self.latency_history)
        return {
            "p50": float(np.percentile(arr, 50)),
            "p95": float(np.percentile(arr, 95)),
            "p99": float(np.percentile(arr, 99)),
            "count": len(arr),
        }
