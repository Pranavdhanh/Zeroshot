"""
Incremental behavioural feature computation for UPI fraud detection.

Maintains per-user state (rolling counters, amount history) and computes
features for each transaction WITHOUT rebuilding any global state.

Features computed:
  - amount_z_score: how unusual is this amount relative to user history
  - amount_ratio_to_max: amount / user's historical max
  - hour_deviation: distance from user's typical active hour
  - is_new_payee: has user ever paid this VPA before
  - payee_first_seen_days: days since user first paid this VPA (0 if new)
  - is_new_device: different device from user's known devices
  - is_new_city: different city from user's home city
  - velocity_1min: transactions by this sender in the last 60 seconds
  - velocity_1hr: transactions by this sender in the last 3600 seconds
  - velocity_24hr: transactions by this sender in the last 86400 seconds
  - new_payee_count_1hr: number of new payees in the last hour
"""

import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set, List, Tuple


class UserState:
    """Tracks rolling state for a single user."""

    def __init__(self):
        self.amount_sum: float = 0.0
        self.amount_sq_sum: float = 0.0
        self.amount_count: int = 0
        self.amount_max: float = 0.0

        self.known_payees: Set[str] = set()
        self.payee_first_seen: Dict[str, datetime] = {}
        self.known_devices: Set[str] = set()
        self.home_city: Optional[str] = None

        # Active hours histogram (24 bins)
        self.hour_counts: List[int] = [0] * 24

        # Rolling timestamp windows for velocity
        self.recent_timestamps: List[datetime] = []
        self.recent_new_payee_timestamps: List[datetime] = []

    def get_amount_mean(self) -> float:
        """Return running mean of transaction amounts."""
        if self.amount_count == 0:
            return 0.0
        return self.amount_sum / self.amount_count

    def get_amount_std(self) -> float:
        """Return running std of transaction amounts."""
        if self.amount_count < 2:
            return 1.0  # avoid division by zero
        mean = self.get_amount_mean()
        variance = (self.amount_sq_sum / self.amount_count) - (mean * mean)
        if variance < 0:
            variance = 0.0
        return math.sqrt(variance)

    def get_peak_hour(self) -> int:
        """Return the hour with the most transactions."""
        if max(self.hour_counts) == 0:
            return 12  # default to noon
        return self.hour_counts.index(max(self.hour_counts))


class BehavioralFeatureEngine:
    """
    Computes behavioural features incrementally for each transaction.

    Usage:
        engine = BehavioralFeatureEngine()
        for txn in sorted_transactions:
            features = engine.compute(txn)
            engine.update(txn)
    """

    def __init__(self):
        self.user_states: Dict[str, UserState] = defaultdict(UserState)

    def compute(self, txn: Dict[str, Any]) -> Dict[str, float]:
        """
        Compute behavioural features for a transaction BEFORE updating state.

        Parameters
        ----------
        txn : dict with keys: sender_id, sender_vpa, receiver_vpa, amount,
              timestamp (datetime), sender_city, sender_device

        Returns
        -------
        dict of feature_name -> float
        """
        sender_id = txn["sender_id"]
        state = self.user_states[sender_id]
        amount = float(txn["amount"])
        timestamp = txn["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        features: Dict[str, float] = {}

        # ── Amount z-score ───────────────────────────────────────
        mean = state.get_amount_mean()
        std = state.get_amount_std()
        if state.amount_count >= 2 and std > 0:
            features["amount_z_score"] = (amount - mean) / std
        else:
            features["amount_z_score"] = 0.0

        # ── Amount ratio to max ──────────────────────────────────
        if state.amount_max > 0:
            features["amount_ratio_to_max"] = amount / state.amount_max
        else:
            features["amount_ratio_to_max"] = 1.0

        # ── Hour deviation ───────────────────────────────────────
        current_hour = timestamp.hour
        peak_hour = state.get_peak_hour()
        hour_diff = abs(current_hour - peak_hour)
        if hour_diff > 12:
            hour_diff = 24 - hour_diff
        features["hour_deviation"] = float(hour_diff)

        # ── New payee ────────────────────────────────────────────
        receiver_vpa = txn["receiver_vpa"]
        is_new_payee = receiver_vpa not in state.known_payees
        if is_new_payee:
            features["is_new_payee"] = 1.0
        else:
            features["is_new_payee"] = 0.0

        # ── Payee first seen days ────────────────────────────────
        if receiver_vpa in state.payee_first_seen:
            delta = timestamp - state.payee_first_seen[receiver_vpa]
            features["payee_first_seen_days"] = max(0.0, delta.total_seconds() / 86400.0)
        else:
            features["payee_first_seen_days"] = 0.0

        # ── New device ───────────────────────────────────────────
        sender_device = txn.get("sender_device", "")
        is_new_device = len(state.known_devices) > 0 and sender_device not in state.known_devices
        if is_new_device:
            features["is_new_device"] = 1.0
        else:
            features["is_new_device"] = 0.0

        # ── New city ─────────────────────────────────────────────
        sender_city = txn.get("sender_city", "")
        if state.home_city is not None:
            is_new_city = sender_city != state.home_city
        else:
            is_new_city = False
        if is_new_city:
            features["is_new_city"] = 1.0
        else:
            features["is_new_city"] = 0.0

        # ── Velocity (1 min / 1 hr / 24 hr) ─────────────────────
        cutoff_1min = timestamp - timedelta(seconds=60)
        cutoff_1hr = timestamp - timedelta(seconds=3600)
        cutoff_24hr = timestamp - timedelta(seconds=86400)

        count_1min = 0
        count_1hr = 0
        count_24hr = 0
        for ts in state.recent_timestamps:
            if ts >= cutoff_1min:
                count_1min = count_1min + 1
                count_1hr = count_1hr + 1
                count_24hr = count_24hr + 1
            elif ts >= cutoff_1hr:
                count_1hr = count_1hr + 1
                count_24hr = count_24hr + 1
            elif ts >= cutoff_24hr:
                count_24hr = count_24hr + 1

        features["velocity_1min"] = float(count_1min)
        features["velocity_1hr"] = float(count_1hr)
        features["velocity_24hr"] = float(count_24hr)

        # ── New payee count in last hour ─────────────────────────
        new_payee_1hr = 0
        for ts in state.recent_new_payee_timestamps:
            if ts >= cutoff_1hr:
                new_payee_1hr = new_payee_1hr + 1

        features["new_payee_count_1hr"] = float(new_payee_1hr)

        # ── Amount (raw, for downstream) ─────────────────────────
        features["amount"] = amount

        # ── User history depth ───────────────────────────────────
        features["user_txn_count"] = float(state.amount_count)

        return features

    def update(self, txn: Dict[str, Any]) -> None:
        """
        Update user state AFTER computing features.
        Must be called after compute() for each transaction.
        """
        sender_id = txn["sender_id"]
        state = self.user_states[sender_id]
        amount = float(txn["amount"])
        timestamp = txn["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        # Update amount stats
        state.amount_sum = state.amount_sum + amount
        state.amount_sq_sum = state.amount_sq_sum + (amount * amount)
        state.amount_count = state.amount_count + 1
        if amount > state.amount_max:
            state.amount_max = amount

        # Update payee tracking
        receiver_vpa = txn["receiver_vpa"]
        is_new_payee = receiver_vpa not in state.known_payees
        if is_new_payee:
            state.known_payees.add(receiver_vpa)
            state.payee_first_seen[receiver_vpa] = timestamp
            state.recent_new_payee_timestamps.append(timestamp)

        # Update device and city
        sender_device = txn.get("sender_device", "")
        if sender_device:
            state.known_devices.add(sender_device)
        sender_city = txn.get("sender_city", "")
        if state.home_city is None and sender_city:
            state.home_city = sender_city

        # Update hour histogram
        state.hour_counts[timestamp.hour] = state.hour_counts[timestamp.hour] + 1

        # Update velocity window (keep last 24h of timestamps)
        state.recent_timestamps.append(timestamp)
        cutoff_24hr = timestamp - timedelta(seconds=86400)
        # Prune old entries periodically (every 100 txns)
        if state.amount_count % 100 == 0:
            state.recent_timestamps = [
                ts for ts in state.recent_timestamps if ts >= cutoff_24hr
            ]
            cutoff_1hr = timestamp - timedelta(seconds=3600)
            state.recent_new_payee_timestamps = [
                ts for ts in state.recent_new_payee_timestamps if ts >= cutoff_1hr
            ]
