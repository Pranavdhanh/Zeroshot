"""
Fraud typology injection for the UPI fraud simulator.

Each typology function receives user/merchant/mule profiles and RNG,
and returns a list of fraud transaction dicts with ground-truth labels.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from data_gen.config import GeneratorConfig


def _random_timestamp(rng: np.random.Generator, start: datetime, end: datetime) -> datetime:
    """Return a random datetime between start and end."""
    delta_seconds = int((end - start).total_seconds())
    offset = int(rng.integers(0, max(1, delta_seconds)))
    return start + timedelta(seconds=offset)


def _pick_victim(
    rng: np.random.Generator,
    user_profiles: pd.DataFrame,
    min_age: int = 0,
    max_lifetime_txns: int = 999999,
    is_senior: bool = False,
    min_income: int = 0,
) -> pd.Series:
    """Pick a victim user matching the criteria."""
    mask = pd.Series([True] * len(user_profiles))
    if is_senior:
        mask = mask & (user_profiles["is_senior"] == True)
    if min_age > 0:
        mask = mask & (user_profiles["age"] >= min_age)
    if min_income > 0:
        mask = mask & (user_profiles["monthly_income"] >= min_income)
    if max_lifetime_txns < 999999:
        # Use daily_txn_rate as a proxy for activity level
        max_daily = max_lifetime_txns / 90.0  # 90 days
        mask = mask & (user_profiles["daily_txn_rate"] <= max_daily)

    candidates = user_profiles[mask]
    if len(candidates) == 0:
        # Fallback: pick any user
        candidates = user_profiles
    idx = rng.integers(0, len(candidates))
    return candidates.iloc[idx]


def _pick_mule(rng: np.random.Generator, mule_accounts: pd.DataFrame) -> pd.Series:
    """Pick a random mule account."""
    idx = rng.integers(0, len(mule_accounts))
    return mule_accounts.iloc[idx]


def generate_fake_collect_requests(
    config: GeneratorConfig,
    rng: np.random.Generator,
    user_profiles: pd.DataFrame,
    mule_accounts: pd.DataFrame,
    time_start: datetime,
    time_end: datetime,
    count: int,
) -> List[Dict[str, Any]]:
    """
    Typology 1: Fake collect request.
    Victim approves an inbound collect request from a mule account.
    """
    frauds: List[Dict[str, Any]] = []

    for _ in range(count):
        victim = _pick_victim(
            rng, user_profiles,
            max_lifetime_txns=config.fake_collect_victim_max_lifetime_txns,
        )
        mule = _pick_mule(rng, mule_accounts)

        low, high = config.fake_collect_amount_range
        amount = int(rng.integers(low, high + 1))
        # Round to common amounts sometimes
        if rng.random() < 0.3:
            amount = int(round(amount / 100) * 100)

        timestamp = _random_timestamp(rng, time_start, time_end)

        notes = rng.choice([
            "Refund of Rs {amt}",
            "Cashback - approve to receive",
            "Prize money - claim now",
            "Payment reversal #{ref}",
            "Refund processed - approve",
        ])
        ref_num = rng.integers(100000, 999999)

        frauds.append({
            "timestamp": timestamp,
            "sender_id": victim["user_id"],
            "sender_vpa": victim["vpa"],
            "receiver_vpa": mule["vpa"],
            "receiver_id": mule["mule_id"],
            "amount": amount,
            "is_collect_request": True,
            "is_merchant_txn": False,
            "call_active_flag": False,
            "screen_share_active": False,
            "new_device_flag": False,
            "new_city_flag": False,
            "sim_swap_flag": False,
            "sender_city": victim["city"],
            "sender_device": victim["device"],
            "sender_account_age_days": victim["account_age_days"],
            "receiver_account_age_days": mule["account_age_days"],
            "is_fraud": True,
            "fraud_typology": "fake_collect_request",
            "note": str(notes).format(amt=amount, ref=ref_num),
        })

    return frauds


def generate_vishing_fraud(
    config: GeneratorConfig,
    rng: np.random.Generator,
    user_profiles: pd.DataFrame,
    mule_accounts: pd.DataFrame,
    time_start: datetime,
    time_end: datetime,
    count: int,
) -> List[Dict[str, Any]]:
    """
    Typology 2: Impersonation / vishing.
    Large transfer to new payee shortly after simulated call.
    """
    frauds: List[Dict[str, Any]] = []

    for _ in range(count):
        victim = _pick_victim(
            rng, user_profiles,
            min_age=config.vishing_victim_min_age,
            min_income=config.vishing_victim_min_balance,
        )
        mule = _pick_mule(rng, mule_accounts)

        low, high = config.vishing_amount_range
        amount = int(rng.integers(low, high + 1))
        if rng.random() < 0.4:
            amount = int(round(amount / 1000) * 1000)

        timestamp = _random_timestamp(rng, time_start, time_end)

        frauds.append({
            "timestamp": timestamp,
            "sender_id": victim["user_id"],
            "sender_vpa": victim["vpa"],
            "receiver_vpa": mule["vpa"],
            "receiver_id": mule["mule_id"],
            "amount": amount,
            "is_collect_request": False,
            "is_merchant_txn": False,
            "call_active_flag": True,
            "screen_share_active": False,
            "new_device_flag": False,
            "new_city_flag": False,
            "sim_swap_flag": False,
            "sender_city": victim["city"],
            "sender_device": victim["device"],
            "sender_account_age_days": victim["account_age_days"],
            "receiver_account_age_days": mule["account_age_days"],
            "is_fraud": True,
            "fraud_typology": "impersonation_vishing",
            "note": "",
        })

    return frauds


def generate_qr_swap_fraud(
    config: GeneratorConfig,
    rng: np.random.Generator,
    user_profiles: pd.DataFrame,
    merchant_profiles: pd.DataFrame,
    mule_accounts: pd.DataFrame,
    payee_map: Dict[str, List[str]],
    time_start: datetime,
    time_end: datetime,
    count: int,
) -> List[Dict[str, Any]]:
    """
    Typology 3: QR code swap.
    Payment goes to mule VPA instead of merchant's real VPA.
    Creates fan-in pattern on the mule account.
    """
    frauds: List[Dict[str, Any]] = []

    # Pick a few mule accounts to act as swapped QR targets
    num_qr_mules = max(1, count // 8)
    qr_mule_indices = rng.choice(len(mule_accounts), size=min(num_qr_mules, len(mule_accounts)), replace=False)
    qr_mules = [mule_accounts.iloc[idx] for idx in qr_mule_indices]

    for i in range(count):
        # Pick a mule that acts as the swapped QR
        qr_mule = qr_mules[i % len(qr_mules)]

        # Pick a victim (any user who frequents merchants)
        victim_idx = rng.integers(0, len(user_profiles))
        victim = user_profiles.iloc[victim_idx]

        low, high = config.qr_swap_amount_range
        amount = int(rng.integers(low, high + 1))

        # Cluster timestamps around a few time windows (simulating a busy shop)
        base_time = _random_timestamp(rng, time_start, time_end)
        offset_minutes = int(rng.integers(0, 120))
        timestamp = base_time + timedelta(minutes=offset_minutes)
        if timestamp > time_end:
            timestamp = time_end - timedelta(minutes=1)

        frauds.append({
            "timestamp": timestamp,
            "sender_id": victim["user_id"],
            "sender_vpa": victim["vpa"],
            "receiver_vpa": qr_mule["vpa"],
            "receiver_id": qr_mule["mule_id"],
            "amount": amount,
            "is_collect_request": False,
            "is_merchant_txn": True,
            "call_active_flag": False,
            "screen_share_active": False,
            "new_device_flag": False,
            "new_city_flag": False,
            "sim_swap_flag": False,
            "sender_city": victim["city"],
            "sender_device": victim["device"],
            "sender_account_age_days": victim["account_age_days"],
            "receiver_account_age_days": qr_mule["account_age_days"],
            "is_fraud": True,
            "fraud_typology": "qr_swap",
            "note": "",
        })

    return frauds


def generate_rapid_burst_fraud(
    config: GeneratorConfig,
    rng: np.random.Generator,
    user_profiles: pd.DataFrame,
    mule_accounts: pd.DataFrame,
    time_start: datetime,
    time_end: datetime,
    count: int,
) -> List[Dict[str, Any]]:
    """
    Typology 4: Rapid new-payee burst.
    Compromised account sends many transfers to new payees in minutes.
    *count* here is number of burst EVENTS, each producing multiple txns.
    """
    frauds: List[Dict[str, Any]] = []

    for _ in range(count):
        # Pick a victim (any active user with decent balance)
        victim = _pick_victim(rng, user_profiles, min_income=20_000)

        burst_start = _random_timestamp(rng, time_start, time_end - timedelta(hours=1))
        low_n, high_n = config.burst_transfer_count
        num_transfers = int(rng.integers(low_n, high_n + 1))

        for t in range(num_transfers):
            mule = _pick_mule(rng, mule_accounts)
            low_a, high_a = config.burst_amount_range
            amount = int(rng.integers(low_a, high_a + 1))
            # Add slight jitter to avoid round numbers
            amount = amount + int(rng.integers(-50, 50))
            amount = max(100, amount)

            # Spread transfers within the burst window
            offset_seconds = int(rng.integers(0, config.burst_window_minutes * 60))
            timestamp = burst_start + timedelta(seconds=offset_seconds)

            frauds.append({
                "timestamp": timestamp,
                "sender_id": victim["user_id"],
                "sender_vpa": victim["vpa"],
                "receiver_vpa": mule["vpa"],
                "receiver_id": mule["mule_id"],
                "amount": amount,
                "is_collect_request": False,
                "is_merchant_txn": False,
                "call_active_flag": False,
                "screen_share_active": False,
                "new_device_flag": rng.random() < 0.3,  # sometimes from new device
                "new_city_flag": False,
                "sim_swap_flag": rng.random() < 0.2,
                "sender_city": victim["city"],
                "sender_device": victim["device"],
                "sender_account_age_days": victim["account_age_days"],
                "receiver_account_age_days": mule["account_age_days"],
                "is_fraud": True,
                "fraud_typology": "rapid_burst",
                "note": "",
            })

    return frauds


def generate_mule_chain_fraud(
    config: GeneratorConfig,
    rng: np.random.Generator,
    user_profiles: pd.DataFrame,
    mule_accounts: pd.DataFrame,
    time_start: datetime,
    time_end: datetime,
    count: int,
) -> List[Dict[str, Any]]:
    """
    Typology 5: Mule chain layering (A→B→C→D).
    Each chain starts from a victim and passes through mule hops.
    """
    frauds: List[Dict[str, Any]] = []

    for _ in range(count):
        victim = _pick_victim(rng, user_profiles, min_income=30_000)
        chain_start = _random_timestamp(rng, time_start, time_end - timedelta(hours=1))

        low_len, high_len = config.mule_chain_length
        chain_len = int(rng.integers(low_len, high_len + 1))

        # Pick distinct mules for the chain
        if chain_len > len(mule_accounts):
            chain_len = len(mule_accounts)
        mule_indices = rng.choice(len(mule_accounts), size=chain_len, replace=False)
        chain_mules = [mule_accounts.iloc[idx] for idx in mule_indices]

        # Initial amount from victim
        amount = int(rng.integers(10_000, 80_000))
        current_time = chain_start

        # First hop: victim → mule[0]
        frauds.append({
            "timestamp": current_time,
            "sender_id": victim["user_id"],
            "sender_vpa": victim["vpa"],
            "receiver_vpa": chain_mules[0]["vpa"],
            "receiver_id": chain_mules[0]["mule_id"],
            "amount": amount,
            "is_collect_request": False,
            "is_merchant_txn": False,
            "call_active_flag": rng.random() < 0.3,
            "screen_share_active": False,
            "new_device_flag": False,
            "new_city_flag": False,
            "sim_swap_flag": False,
            "sender_city": victim["city"],
            "sender_device": victim["device"],
            "sender_account_age_days": victim["account_age_days"],
            "receiver_account_age_days": chain_mules[0]["account_age_days"],
            "is_fraud": True,
            "fraud_typology": "mule_chain",
            "note": "",
        })

        # Subsequent hops: mule[i] → mule[i+1]
        for hop in range(chain_len - 1):
            low_dwell, high_dwell = config.mule_chain_dwell_seconds
            dwell = int(rng.integers(low_dwell, high_dwell + 1))
            current_time = current_time + timedelta(seconds=dwell)

            # Slight amount reduction (mule skims a cut)
            skim = rng.uniform(0.0, 0.05)
            amount = int(amount * (1.0 - skim))
            amount = max(100, amount)

            sender_mule = chain_mules[hop]
            receiver_mule = chain_mules[hop + 1]

            frauds.append({
                "timestamp": current_time,
                "sender_id": sender_mule["mule_id"],
                "sender_vpa": sender_mule["vpa"],
                "receiver_vpa": receiver_mule["vpa"],
                "receiver_id": receiver_mule["mule_id"],
                "amount": amount,
                "is_collect_request": False,
                "is_merchant_txn": False,
                "call_active_flag": False,
                "screen_share_active": False,
                "new_device_flag": False,
                "new_city_flag": False,
                "sim_swap_flag": False,
                "sender_city": sender_mule["city"],
                "sender_device": "android_budget",
                "sender_account_age_days": sender_mule["account_age_days"],
                "receiver_account_age_days": receiver_mule["account_age_days"],
                "is_fraud": True,
                "fraud_typology": "mule_chain",
                "note": "",
            })

    return frauds


def generate_remote_access_fraud(
    config: GeneratorConfig,
    rng: np.random.Generator,
    user_profiles: pd.DataFrame,
    mule_accounts: pd.DataFrame,
    time_start: datetime,
    time_end: datetime,
    count: int,
) -> List[Dict[str, Any]]:
    """
    Typology 6: Remote access / screen-share scam.
    Victim has screen-share active + new device, makes transfer to mule.
    """
    frauds: List[Dict[str, Any]] = []

    for _ in range(count):
        victim = _pick_victim(rng, user_profiles, is_senior=(rng.random() < 0.5))
        mule = _pick_mule(rng, mule_accounts)

        low, high = config.remote_access_amount_range
        amount = int(rng.integers(low, high + 1))
        timestamp = _random_timestamp(rng, time_start, time_end)

        frauds.append({
            "timestamp": timestamp,
            "sender_id": victim["user_id"],
            "sender_vpa": victim["vpa"],
            "receiver_vpa": mule["vpa"],
            "receiver_id": mule["mule_id"],
            "amount": amount,
            "is_collect_request": False,
            "is_merchant_txn": False,
            "call_active_flag": rng.random() < 0.7,  # often on a call too
            "screen_share_active": True,
            "new_device_flag": True,
            "new_city_flag": False,
            "sim_swap_flag": False,
            "sender_city": victim["city"],
            "sender_device": victim["device"],
            "sender_account_age_days": victim["account_age_days"],
            "receiver_account_age_days": mule["account_age_days"],
            "is_fraud": True,
            "fraud_typology": "remote_access",
            "note": "",
        })

    return frauds


def generate_account_takeover_fraud(
    config: GeneratorConfig,
    rng: np.random.Generator,
    user_profiles: pd.DataFrame,
    mule_accounts: pd.DataFrame,
    time_start: datetime,
    time_end: datetime,
    count: int,
) -> List[Dict[str, Any]]:
    """
    Typology 7: Account takeover (new device + new city + SIM swap).
    Multiple transfers to mules within a short window.
    """
    frauds: List[Dict[str, Any]] = []
    city_names = [c[0] for c in config.cities]

    for _ in range(count):
        victim = _pick_victim(rng, user_profiles, min_income=30_000)
        ato_start = _random_timestamp(rng, time_start, time_end - timedelta(hours=2))

        low_n, high_n = config.ato_transfer_count
        num_transfers = int(rng.integers(low_n, high_n + 1))

        # Pick a different city for the takeover
        other_cities = [c for c in city_names if c != victim["city"]]
        takeover_city = rng.choice(other_cities)

        for t in range(num_transfers):
            mule = _pick_mule(rng, mule_accounts)
            low_a, high_a = config.ato_amount_range
            amount = int(rng.integers(low_a, high_a + 1))

            offset_seconds = int(rng.integers(0, config.ato_window_minutes * 60))
            timestamp = ato_start + timedelta(seconds=offset_seconds)

            frauds.append({
                "timestamp": timestamp,
                "sender_id": victim["user_id"],
                "sender_vpa": victim["vpa"],
                "receiver_vpa": mule["vpa"],
                "receiver_id": mule["mule_id"],
                "amount": amount,
                "is_collect_request": False,
                "is_merchant_txn": False,
                "call_active_flag": False,
                "screen_share_active": False,
                "new_device_flag": True,
                "new_city_flag": True,
                "sim_swap_flag": True,
                "sender_city": takeover_city,
                "sender_device": rng.choice(["android_budget", "android_mid"]),
                "sender_account_age_days": victim["account_age_days"],
                "receiver_account_age_days": mule["account_age_days"],
                "is_fraud": True,
                "fraud_typology": "account_takeover",
                "note": "",
            })

    return frauds
