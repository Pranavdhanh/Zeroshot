"""
Context features for UPI fraud detection.

These are direct flags or simple derivations from the transaction metadata,
not computed from historical state.
"""

from typing import Dict, Any


def compute_context_features(txn: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract context features from a single transaction record.

    Parameters
    ----------
    txn : dict with keys matching the synthetic data schema

    Returns
    -------
    dict of feature_name -> float
    """
    features: Dict[str, float] = {}

    # -- Binary context flags -------------------------------------
    if txn.get("is_collect_request", False):
        features["is_collect_request"] = 1.0
    else:
        features["is_collect_request"] = 0.0

    if txn.get("is_merchant_txn", False):
        features["is_merchant_txn"] = 1.0
    else:
        features["is_merchant_txn"] = 0.0

    if txn.get("call_active_flag", False):
        features["call_active_flag"] = 1.0
    else:
        features["call_active_flag"] = 0.0

    if txn.get("screen_share_active", False):
        features["screen_share_active"] = 1.0
    else:
        features["screen_share_active"] = 0.0

    # -- Device/location flags from transaction metadata ----------
    if txn.get("new_device_flag", False):
        features["txn_new_device_flag"] = 1.0
    else:
        features["txn_new_device_flag"] = 0.0

    if txn.get("new_city_flag", False):
        features["txn_new_city_flag"] = 1.0
    else:
        features["txn_new_city_flag"] = 0.0

    if txn.get("sim_swap_flag", False):
        features["sim_swap_flag"] = 1.0
    else:
        features["sim_swap_flag"] = 0.0

    # -- Account age features -------------------------------------
    sender_age = txn.get("sender_account_age_days", 365)
    features["sender_account_age_days"] = float(sender_age)

    receiver_age = txn.get("receiver_account_age_days", 365)
    if receiver_age < 0:
        receiver_age = 365
    features["receiver_account_age_days"] = float(receiver_age)

    # -- Derived: receiver is young account -----------------------
    if receiver_age < 30:
        features["receiver_is_young"] = 1.0
    else:
        features["receiver_is_young"] = 0.0

    # -- Compound risk signals ------------------------------------
    features["call_and_new_payee"] = 0.0
    features["screen_share_and_new_device"] = (
        features["screen_share_active"] * features["txn_new_device_flag"]
    )
    features["triple_ato_signal"] = (
        features["txn_new_device_flag"]
        * features["txn_new_city_flag"]
        * features["sim_swap_flag"]
    )

    return features
