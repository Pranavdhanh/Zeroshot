"""
Feature builder: orchestrates incremental feature computation
over a sorted transaction stream.

Combines behavioural + context + graph features into a single feature matrix
suitable for model training and inference.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from features.behavioral import BehavioralFeatureEngine
from features.context import compute_context_features
from features.graph import GraphFeatureEngine


# ── Behavioral Features ───────────────────────────────────────────
BEHAVIORAL_FEATURES = [
    "amount_z_score",
    "amount_ratio_to_max",
    "hour_deviation",
    "is_new_payee",
    "payee_first_seen_days",
    "is_new_device",
    "is_new_city",
    "velocity_1min",
    "velocity_1hr",
    "velocity_24hr",
    "new_payee_count_1hr",
    "amount",
    "user_txn_count",
]

# ── Context Features ──────────────────────────────────────────────
CONTEXT_FEATURES = [
    "is_collect_request",
    "is_merchant_txn",
    "call_active_flag",
    "screen_share_active",
    "txn_new_device_flag",
    "txn_new_city_flag",
    "sim_swap_flag",
    "sender_account_age_days",
    "receiver_account_age_days",
    "receiver_is_young",
    "screen_share_and_new_device",
    "triple_ato_signal",
    "call_and_new_payee",
]

# ── Graph Features ────────────────────────────────────────────────
GRAPH_FEATURES = [
    "sender_in_degree",
    "sender_out_degree",
    "receiver_in_degree",
    "receiver_out_degree",
    "receiver_fan_in_ratio",
    "sender_fan_out_ratio",
    "receiver_pass_through_ratio",
    "sender_pass_through_ratio",
    "receiver_funds_dwell_time_seconds",
    "receiver_distinct_senders_1hr",
    "receiver_network_age_days",
    "receiver_hop_to_flagged",
    "sender_hop_to_flagged",
    "min_hop_to_flagged",
    "same_community",
]

# Subsets for ablation studies
BEHAVIORAL_ONLY = list(BEHAVIORAL_FEATURES)
BEHAVIORAL_PLUS_CONTEXT = BEHAVIORAL_FEATURES + CONTEXT_FEATURES
FULL_FEATURES = BEHAVIORAL_FEATURES + CONTEXT_FEATURES + GRAPH_FEATURES
ALL_FEATURES = FULL_FEATURES


def build_feature_matrix(
    transactions_df: pd.DataFrame,
    progress_interval: int = 50000,
    include_graph: bool = True,
) -> pd.DataFrame:
    """
    Process transactions in chronological order and compute features
    incrementally for each transaction.

    Parameters
    ----------
    transactions_df : pd.DataFrame
        Must be sorted by timestamp.
    progress_interval : int
        Print progress every N transactions.
    include_graph : bool
        Whether to compute graph features.

    Returns
    -------
    pd.DataFrame with columns: txn_id + feature columns + is_fraud + fraud_typology
    """
    df = transactions_df.sort_values("timestamp").reset_index(drop=True)
    timestamps = pd.to_datetime(df["timestamp"])
    min_ts = timestamps.min()
    train_cutoff = min_ts + pd.Timedelta(days=60)

    behav_engine = BehavioralFeatureEngine()
    if include_graph:
        graph_engine = GraphFeatureEngine()
    else:
        graph_engine = None

    rows: List[Dict[str, Any]] = []
    total = len(df)
    print(f"Building features for {total:,} transactions (graph={include_graph})...")
    records = df.to_dict("records")

    for idx, txn in enumerate(records):
        # 1. Compute behavioural features (before state update)
        behav_feats = behav_engine.compute(txn)

        # 2. Compute context features
        ctx_feats = compute_context_features(txn)
        ctx_feats["call_and_new_payee"] = (
            ctx_feats["call_active_flag"] * behav_feats["is_new_payee"]
        )

        # 3. Compute graph features if enabled
        if include_graph and graph_engine is not None:
            graph_feats = graph_engine.compute(txn)
        else:
            graph_feats = {}

        # 4. Merge features
        combined: Dict[str, Any] = {}
        combined["txn_id"] = txn["txn_id"]

        for feat_name in BEHAVIORAL_FEATURES:
            combined[feat_name] = behav_feats.get(feat_name, 0.0)

        for feat_name in CONTEXT_FEATURES:
            combined[feat_name] = ctx_feats.get(feat_name, 0.0)

        if include_graph:
            for feat_name in GRAPH_FEATURES:
                combined[feat_name] = graph_feats.get(feat_name, 0.0)

        combined["is_fraud"] = txn["is_fraud"]
        combined["fraud_typology"] = txn["fraud_typology"]
        combined["timestamp"] = txn["timestamp"]
        combined["sender_vpa"] = txn["sender_vpa"]
        combined["receiver_vpa"] = txn["receiver_vpa"]

        rows.append(combined)

        # 5. Update state
        behav_engine.update(txn)

        if include_graph and graph_engine is not None:
            graph_engine.update(txn)

            # Strictly restrict ground-truth account flagging to the training window (< day 60)
            # This completely prevents test set label leakage
            if txn["is_fraud"]:
                ts = txn["timestamp"]
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                if ts < train_cutoff:
                    recv_vpa = str(txn["receiver_vpa"])
                    graph_engine.flag_account(recv_vpa, ts)

            # Periodic community detection every 100,000 transactions
            processed_count = idx + 1
            if processed_count % 100000 == 0:
                graph_engine.run_community_detection()

        processed_count = idx + 1
        if processed_count % progress_interval == 0:
            print(f"  Processed {processed_count:,} / {total:,} transactions")

    print("  Feature computation complete.")
    result = pd.DataFrame(rows)
    return result
