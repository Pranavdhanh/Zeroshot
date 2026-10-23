"""
Mule network evaluation metrics:
  1. Fraction of mule accounts correctly flagged
  2. Cluster / community purity
  3. Time-to-detect a mule chain after its first transaction
"""

from typing import Dict, Any, List, Set, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
import networkx as nx


def evaluate_mule_detection(
    predictions_df: pd.DataFrame,
    mule_accounts_df: pd.DataFrame,
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Compute mule network detection metrics.

    Parameters
    ----------
    predictions_df : pd.DataFrame with columns:
        txn_id, sender_vpa, receiver_vpa, amount, timestamp,
        is_fraud, fraud_typology, prob (calibrated risk score)
    mule_accounts_df : pd.DataFrame with mule account VPAs
    threshold : decision threshold for flagging an alert
    """
    mule_vpas: Set[str] = set(mule_accounts_df["vpa"].tolist())

    # 1. Fraction of mule accounts correctly flagged
    # An account is flagged if it receives a transaction with prob >= threshold
    flagged_txns = predictions_df[predictions_df["prob"] >= threshold]
    flagged_receivers = set(flagged_txns["receiver_vpa"].tolist())
    flagged_senders = set(flagged_txns["sender_vpa"].tolist())
    all_flagged_accounts = flagged_receivers.union(flagged_senders)

    flagged_mules = mule_vpas.intersection(all_flagged_accounts)
    mules_in_test = set()
    for _, row in predictions_df.iterrows():
        if row["receiver_vpa"] in mule_vpas:
            mules_in_test.add(row["receiver_vpa"])
        if row["sender_vpa"] in mule_vpas:
            mules_in_test.add(row["sender_vpa"])

    if len(mules_in_test) > 0:
        fraction_mules_flagged = len(flagged_mules) / float(len(mules_in_test))
    else:
        fraction_mules_flagged = 0.0

    # 2. Cluster / Community Purity
    # Build graph of all flagged transactions
    flagged_graph = nx.Graph()
    for _, row in flagged_txns.iterrows():
        flagged_graph.add_edge(str(row["sender_vpa"]), str(row["receiver_vpa"]))

    cluster_purities: List[float] = []
    if flagged_graph.number_of_nodes() > 0:
        connected_components = list(nx.connected_components(flagged_graph))
        for comp in connected_components:
            if len(comp) > 1:
                # Count nodes that are either known mules or victims in fraud txns
                mule_count = len([node for node in comp if node in mule_vpas])
                purity = float(mule_count) / float(len(comp))
                cluster_purities.append(purity)

    if len(cluster_purities) > 0:
        avg_cluster_purity = float(np.mean(cluster_purities))
    else:
        avg_cluster_purity = 1.0

    # 3. Time-to-detect a mule chain after its first transaction
    # Filter mule chain transactions
    chain_txns = predictions_df[predictions_df["fraud_typology"] == "mule_chain"].copy()
    chain_txns = chain_txns.sort_values("timestamp").reset_index(drop=True)

    detection_delays: List[float] = []
    # Group chains by victim / sender of first hop
    # Chains are generated within small time windows
    if len(chain_txns) > 0:
        chain_txns["timestamp"] = pd.to_datetime(chain_txns["timestamp"])

        # Identify separate chain episodes by looking at time gaps > 1 hour
        episodes: List[List[pd.Series]] = []
        current_episode: List[pd.Series] = []

        for _, row in chain_txns.iterrows():
            if len(current_episode) == 0:
                current_episode.append(row)
            else:
                last_time = current_episode[-1]["timestamp"]
                if (row["timestamp"] - last_time).total_seconds() > 3600:
                    episodes.append(current_episode)
                    current_episode = [row]
                else:
                    current_episode.append(row)

        if len(current_episode) > 0:
            episodes.append(current_episode)

        for ep in episodes:
            start_time = ep[0]["timestamp"]
            detected = False
            for hop in ep:
                if hop["prob"] >= threshold:
                    detected_time = hop["timestamp"]
                    delay_seconds = (detected_time - start_time).total_seconds()
                    detection_delays.append(delay_seconds)
                    detected = True
                    break
            if not detected:
                # Not detected within the chain
                pass

    if len(detection_delays) > 0:
        median_time_to_detect = float(np.median(detection_delays))
        mean_time_to_detect = float(np.mean(detection_delays))
        first_hop_detection_rate = float(np.mean([1.0 if d == 0.0 else 0.0 for d in detection_delays]))
    else:
        median_time_to_detect = 0.0
        mean_time_to_detect = 0.0
        first_hop_detection_rate = 0.0

    return {
        "total_mule_accounts": len(mule_accounts_df),
        "mules_active_in_test": len(mules_in_test),
        "mules_flagged": len(flagged_mules),
        "fraction_mules_flagged": fraction_mules_flagged,
        "average_cluster_purity": avg_cluster_purity,
        "median_time_to_detect_seconds": median_time_to_detect,
        "mean_time_to_detect_seconds": mean_time_to_detect,
        "first_hop_detection_rate": first_hop_detection_rate,
    }
