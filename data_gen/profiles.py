"""
User and account profile generation for the UPI fraud simulator.
Each user gets a behavioural fingerprint: income, typical amounts,
active hours, device, city, frequent payees, and periodic patterns.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any
from data_gen.config import GeneratorConfig


def _weighted_choice(rng: np.random.Generator, items: list, weights: list, size: int = 1):
    """Draw *size* items from *items* according to *weights*."""
    probabilities = np.array(weights, dtype=float)
    probabilities = probabilities / probabilities.sum()
    indices = rng.choice(len(items), size=size, p=probabilities)
    if size == 1:
        return items[indices[0]]
    return [items[i] for i in indices]


def generate_user_profiles(config: GeneratorConfig, rng: np.random.Generator) -> pd.DataFrame:
    """
    Create a DataFrame of user profiles.

    Returns
    -------
    pd.DataFrame with columns:
        user_id, vpa, city, age, income_bracket, monthly_income,
        device, daily_txn_rate, typical_amount_mean, typical_amount_std,
        active_hour_center, active_hour_spread, num_frequent_payees,
        account_age_days, is_senior, is_mule
    """
    n = config.num_users
    records: List[Dict[str, Any]] = []

    # Pre-compute city choices
    city_names = [c[0] for c in config.cities]
    city_weights = [c[1] for c in config.cities]

    # Pre-compute income bracket choices
    bracket_names = [b[0] for b in config.income_brackets]
    bracket_weights = [b[3] for b in config.income_brackets]
    bracket_ranges = {b[0]: (b[1], b[2]) for b in config.income_brackets}

    for i in range(n):
        user_id = f"U{i:06d}"
        vpa = f"user{i:06d}@upi"

        city = _weighted_choice(rng, city_names, city_weights)

        # Age — truncated normal
        age_min, age_max, age_mean, age_std = config.age_distribution
        raw_age = rng.normal(age_mean, age_std)
        age = int(np.clip(raw_age, age_min, age_max))
        is_senior = age >= 60

        # Income bracket
        bracket = _weighted_choice(rng, bracket_names, bracket_weights)
        inc_low, inc_high = bracket_ranges[bracket]
        monthly_income = int(rng.integers(inc_low, inc_high))

        # Device
        device = _weighted_choice(rng, config.device_types, config.device_weights)

        # Daily transaction rate (gamma distributed)
        daily_txn_rate = float(rng.gamma(config.daily_txn_shape,
                                          config.daily_txn_mean / config.daily_txn_shape))
        daily_txn_rate = max(0.1, daily_txn_rate)

        # Typical transaction amount — tied to income
        typical_amount_mean = monthly_income * rng.uniform(0.01, 0.05)
        typical_amount_std = typical_amount_mean * rng.uniform(0.3, 0.8)

        # Active hour centre and spread
        hour_weights = np.array(config.active_hours_weights)
        active_hour_center = float(rng.choice(24, p=hour_weights / hour_weights.sum()))
        active_hour_spread = rng.uniform(2.0, 6.0)

        # Frequent payees (more for active users)
        num_frequent_payees = int(rng.integers(2, min(20, max(3, int(daily_txn_rate * 5)))))

        # Account age in days (young accounts exist realistically)
        account_age_days = int(rng.integers(5, 1500))

        records.append({
            "user_id": user_id,
            "vpa": vpa,
            "city": city,
            "age": age,
            "income_bracket": bracket,
            "monthly_income": monthly_income,
            "device": device,
            "daily_txn_rate": round(daily_txn_rate, 2),
            "typical_amount_mean": round(typical_amount_mean, 2),
            "typical_amount_std": round(typical_amount_std, 2),
            "active_hour_center": round(active_hour_center, 1),
            "active_hour_spread": round(active_hour_spread, 1),
            "num_frequent_payees": num_frequent_payees,
            "account_age_days": account_age_days,
            "is_senior": is_senior,
            "is_mule": False,
        })

    profiles_df = pd.DataFrame(records)
    return profiles_df


def generate_merchant_profiles(config: GeneratorConfig, rng: np.random.Generator) -> pd.DataFrame:
    """
    Create merchant profiles with VPAs and typical transaction ranges.
    """
    merchant_categories = [
        ("grocery", 0.20, 50, 2000),
        ("restaurant", 0.15, 100, 3000),
        ("fuel", 0.10, 200, 5000),
        ("electronics", 0.08, 500, 50000),
        ("clothing", 0.10, 200, 10000),
        ("pharmacy", 0.08, 50, 5000),
        ("utility", 0.10, 100, 8000),
        ("telecom", 0.05, 50, 1000),
        ("jewellery", 0.04, 1000, 200000),
        ("hospital", 0.05, 500, 100000),
        ("education", 0.05, 1000, 50000),
    ]

    records: List[Dict[str, Any]] = []
    city_names = [c[0] for c in config.cities]
    city_weights = [c[1] for c in config.cities]

    cat_names = [c[0] for c in merchant_categories]
    cat_weights = [c[1] for c in merchant_categories]
    cat_ranges = {c[0]: (c[2], c[3]) for c in merchant_categories}

    for i in range(config.num_merchants):
        merchant_id = f"M{i:05d}"
        vpa = f"merchant{i:05d}@upi"
        city = _weighted_choice(rng, city_names, city_weights)
        category = _weighted_choice(rng, cat_names, cat_weights)
        amt_low, amt_high = cat_ranges[category]
        account_age_days = int(rng.integers(60, 2000))

        records.append({
            "merchant_id": merchant_id,
            "vpa": vpa,
            "city": city,
            "category": category,
            "amount_low": amt_low,
            "amount_high": amt_high,
            "account_age_days": account_age_days,
        })

    return pd.DataFrame(records)


def generate_mule_accounts(config: GeneratorConfig, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate mule account profiles — young accounts used in fraud chains.
    """
    records: List[Dict[str, Any]] = []
    city_names = [c[0] for c in config.cities]
    city_weights = [c[1] for c in config.cities]

    for i in range(config.num_mule_accounts):
        mule_id = f"MULE{i:04d}"
        vpa = f"mule{i:04d}@upi"
        city = _weighted_choice(rng, city_names, city_weights)
        age_low, age_high = config.mule_age_range_days
        account_age_days = int(rng.integers(age_low, age_high + 1))

        records.append({
            "mule_id": mule_id,
            "vpa": vpa,
            "city": city,
            "account_age_days": account_age_days,
            "is_mule": True,
        })

    return pd.DataFrame(records)


def assign_frequent_payees(
    user_profiles: pd.DataFrame,
    merchant_profiles: pd.DataFrame,
    rng: np.random.Generator,
) -> Dict[str, List[str]]:
    """
    For each user, assign a set of frequent payees (mix of other users and merchants).
    Returns a dict mapping user_id → list of payee VPAs.
    """
    all_user_vpas = user_profiles["vpa"].tolist()
    all_merchant_vpas = merchant_profiles["vpa"].tolist()
    all_payees = all_user_vpas + all_merchant_vpas

    payee_map: Dict[str, List[str]] = {}
    for _, row in user_profiles.iterrows():
        uid = row["user_id"]
        own_vpa = row["vpa"]
        num_payees = row["num_frequent_payees"]

        # Pick payees (excluding self)
        candidates = [v for v in all_payees if v != own_vpa]
        chosen_indices = rng.choice(len(candidates), size=min(num_payees, len(candidates)), replace=False)
        payee_map[uid] = [candidates[idx] for idx in chosen_indices]

    return payee_map
