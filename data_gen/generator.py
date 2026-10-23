"""
Main transaction generator for the UPI fraud simulator.

Generates genuine transactions with realistic patterns, injects
hard negatives, then injects fraud transactions from all 7 typologies.
Outputs a single DataFrame with ground-truth labels.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

from data_gen.config import GeneratorConfig
from data_gen.profiles import (
    generate_user_profiles,
    generate_merchant_profiles,
    generate_mule_accounts,
    assign_frequent_payees,
)
from data_gen.typologies import (
    generate_fake_collect_requests,
    generate_vishing_fraud,
    generate_qr_swap_fraud,
    generate_rapid_burst_fraud,
    generate_mule_chain_fraud,
    generate_remote_access_fraud,
    generate_account_takeover_fraud,
)


def _generate_genuine_transactions(
    config: GeneratorConfig,
    rng: np.random.Generator,
    user_profiles: pd.DataFrame,
    merchant_profiles: pd.DataFrame,
    payee_map: Dict[str, List[str]],
    time_start: datetime,
    time_end: datetime,
) -> List[Dict[str, Any]]:
    """
    Generate genuine (non-fraud) transactions with realistic per-user patterns.
    """
    transactions: List[Dict[str, Any]] = []
    total_days = (time_end - time_start).days
    hour_weights = np.array(config.active_hours_weights, dtype=float)
    hour_weights = hour_weights / hour_weights.sum()

    # Category selection
    cat_names = [c[0] for c in config.txn_categories]
    cat_probs = np.array([c[1] for c in config.txn_categories], dtype=float)
    cat_probs = cat_probs / cat_probs.sum()
    cat_params = {c[0]: (c[2], c[3], c[4], c[5]) for c in config.txn_categories}

    all_merchant_vpas = merchant_profiles["vpa"].tolist()

    target_count = config.num_transactions
    per_user_target = target_count / len(user_profiles)

    for _, user in user_profiles.iterrows():
        user_id = user["user_id"]
        user_vpa = user["vpa"]
        user_city = user["city"]
        user_device = user["device"]
        daily_rate = user["daily_txn_rate"]
        freq_payees = payee_map.get(user_id, [])
        account_age = user["account_age_days"]

        # Number of transactions for this user over the full period
        user_txn_count = int(rng.poisson(daily_rate * total_days))
        user_txn_count = max(1, min(user_txn_count, int(per_user_target * 3)))

        for _ in range(user_txn_count):
            # Pick a day
            day_offset = int(rng.integers(0, total_days))
            txn_date = time_start + timedelta(days=day_offset)

            # Pick hour based on user's active hours (personalised)
            personal_hour_weights = hour_weights.copy()
            center = int(user["active_hour_center"])
            spread = user["active_hour_spread"]
            for h in range(24):
                dist = min(abs(h - center), 24 - abs(h - center))
                boost = np.exp(-0.5 * (dist / spread) ** 2)
                personal_hour_weights[h] = personal_hour_weights[h] * (1.0 + boost)
            personal_hour_weights = personal_hour_weights / personal_hour_weights.sum()

            hour = int(rng.choice(24, p=personal_hour_weights))
            minute = int(rng.integers(0, 60))
            second = int(rng.integers(0, 60))
            timestamp = txn_date.replace(hour=hour, minute=minute, second=second)

            # Pick category
            category = rng.choice(cat_names, p=cat_probs)
            mean_amt, std_amt, min_amt, max_amt = cat_params[category]

            # Amount — log-normal for realism
            raw_amount = rng.lognormal(np.log(mean_amt), 0.5)
            amount = int(np.clip(raw_amount, min_amt, max_amt))

            # Pick payee
            is_merchant = category.startswith("merchant_") or category in ("bill_payment", "recharge")
            if is_merchant:
                receiver_vpa = rng.choice(all_merchant_vpas)
                is_merchant_txn = True
            else:
                if len(freq_payees) > 0 and rng.random() < 0.8:
                    receiver_vpa = rng.choice(freq_payees)
                else:
                    # Occasional payment to a random user
                    random_idx = rng.integers(0, len(user_profiles))
                    receiver_vpa = user_profiles.iloc[random_idx]["vpa"]
                    if receiver_vpa == user_vpa:
                        receiver_vpa = user_profiles.iloc[(random_idx + 1) % len(user_profiles)]["vpa"]
                is_merchant_txn = False

            # Realistic background noise in genuine transactions
            genuine_collect = rng.random() < 0.015
            genuine_call = rng.random() < 0.035
            genuine_screen = rng.random() < 0.007
            genuine_sim_swap = rng.random() < 0.004

            transactions.append({
                "timestamp": timestamp,
                "sender_id": user_id,
                "sender_vpa": user_vpa,
                "receiver_vpa": receiver_vpa,
                "receiver_id": "",  # will be resolved globally
                "amount": amount,
                "is_collect_request": genuine_collect,
                "is_merchant_txn": is_merchant_txn,
                "call_active_flag": genuine_call,
                "screen_share_active": genuine_screen,
                "new_device_flag": False,
                "new_city_flag": False,
                "sim_swap_flag": genuine_sim_swap,
                "sender_city": user_city,
                "sender_device": user_device,
                "sender_account_age_days": account_age,
                "receiver_account_age_days": -1,  # to be filled
                "is_fraud": False,
                "fraud_typology": "genuine",
                "note": "",
                "hard_negative_type": "none",
            })

    return transactions


def _inject_hard_negatives(
    config: GeneratorConfig,
    rng: np.random.Generator,
    transactions: List[Dict[str, Any]],
    user_profiles: pd.DataFrame,
    merchant_profiles: pd.DataFrame,
    time_start: datetime,
    time_end: datetime,
) -> List[Dict[str, Any]]:
    """
    Inject hard negatives: genuine transactions that look suspicious.
    Modifies transactions in-place and also appends new ones.
    """
    hard_negatives: List[Dict[str, Any]] = []
    target_count = int(len(transactions) * config.hard_negative_fraction)
    hn_per_type = max(1, target_count // 8)

    city_names = [c[0] for c in config.cities]
    all_merchant_vpas = merchant_profiles["vpa"].tolist()

    # ── Type 1: Rent payment (large, monthly, newish payee) ──────────
    for _ in range(hn_per_type):
        user_idx = rng.integers(0, len(user_profiles))
        user = user_profiles.iloc[user_idx]
        amount = int(rng.integers(8_000, 50_000))
        # Pick a "landlord" VPA (random user, not in frequent payees)
        landlord_idx = rng.integers(0, len(user_profiles))
        landlord = user_profiles.iloc[landlord_idx]
        timestamp = _hn_timestamp(rng, time_start, time_end)

        hard_negatives.append(_make_hn_txn(
            user, landlord["vpa"], amount, timestamp, "rent_payment",
        ))

    # ── Type 2: Gold / jewellery purchase (very large, first-time merchant) ──
    for _ in range(hn_per_type):
        user_idx = rng.integers(0, len(user_profiles))
        user = user_profiles.iloc[user_idx]
        amount = int(rng.integers(20_000, 200_000))
        receiver_vpa = rng.choice(all_merchant_vpas)
        timestamp = _hn_timestamp(rng, time_start, time_end)

        hard_negatives.append(_make_hn_txn(
            user, receiver_vpa, amount, timestamp, "gold_purchase",
            is_merchant=True,
        ))

    # ── Type 3: Hospital emergency (large, off-hours, new payee) ─────
    for _ in range(hn_per_type):
        user_idx = rng.integers(0, len(user_profiles))
        user = user_profiles.iloc[user_idx]
        amount = int(rng.integers(5_000, 100_000))
        receiver_vpa = rng.choice(all_merchant_vpas)
        # Off-hours
        base = _hn_timestamp(rng, time_start, time_end)
        hour = int(rng.choice([0, 1, 2, 3, 4, 22, 23]))
        timestamp = base.replace(hour=hour)

        hard_negatives.append(_make_hn_txn(
            user, receiver_vpa, amount, timestamp, "hospital_emergency",
            is_merchant=True,
        ))

    # ── Type 4: New device after phone upgrade ───────────────────────
    for _ in range(hn_per_type):
        user_idx = rng.integers(0, len(user_profiles))
        user = user_profiles.iloc[user_idx]
        amount = int(rng.integers(100, 5_000))
        # Normal payee, but new device flag
        receiver_vpa = rng.choice(all_merchant_vpas)
        timestamp = _hn_timestamp(rng, time_start, time_end)

        txn = _make_hn_txn(user, receiver_vpa, amount, timestamp, "phone_upgrade", is_merchant=True)
        txn["new_device_flag"] = True
        hard_negatives.append(txn)

    # ── Type 5: Travel to new city ───────────────────────────────────
    for _ in range(hn_per_type):
        user_idx = rng.integers(0, len(user_profiles))
        user = user_profiles.iloc[user_idx]
        amount = int(rng.integers(100, 5_000))
        receiver_vpa = rng.choice(all_merchant_vpas)
        other_cities = [c for c in city_names if c != user["city"]]
        travel_city = rng.choice(other_cities)
        timestamp = _hn_timestamp(rng, time_start, time_end)

        txn = _make_hn_txn(user, receiver_vpa, amount, timestamp, "travel_new_city", is_merchant=True)
        txn["new_city_flag"] = True
        txn["sender_city"] = travel_city
        hard_negatives.append(txn)

    # ── Type 6: First payment to new relative (wedding gift etc.) ────
    for _ in range(hn_per_type):
        user_idx = rng.integers(0, len(user_profiles))
        user = user_profiles.iloc[user_idx]
        amount = int(rng.integers(5_000, 51_000))
        # Pick a random user as "relative"
        relative_idx = rng.integers(0, len(user_profiles))
        relative = user_profiles.iloc[relative_idx]
        timestamp = _hn_timestamp(rng, time_start, time_end)

        hard_negatives.append(_make_hn_txn(
            user, relative["vpa"], amount, timestamp, "new_relative_payment",
        ))

    # ── Type 7: Salary payout (small biz — rapid multiple payments) ──
    for _ in range(max(1, hn_per_type // 3)):
        user_idx = rng.integers(0, len(user_profiles))
        user = user_profiles.iloc[user_idx]
        base_time = _hn_timestamp(rng, time_start, time_end)

        num_payouts = int(rng.integers(5, 12))
        for p in range(num_payouts):
            amount = int(rng.integers(8_000, 40_000))
            employee_idx = rng.integers(0, len(user_profiles))
            employee = user_profiles.iloc[employee_idx]
            offset = int(rng.integers(0, 600))
            timestamp = base_time + timedelta(seconds=offset)

            hard_negatives.append(_make_hn_txn(
                user, employee["vpa"], amount, timestamp, "salary_payout",
            ))

    # ── Type 8: Festival season shopping (multiple new merchants) ────
    for _ in range(hn_per_type):
        user_idx = rng.integers(0, len(user_profiles))
        user = user_profiles.iloc[user_idx]
        base_time = _hn_timestamp(rng, time_start, time_end)

        num_shops = int(rng.integers(3, 7))
        for s in range(num_shops):
            amount = int(rng.integers(500, 15_000))
            receiver_vpa = rng.choice(all_merchant_vpas)
            offset = int(rng.integers(0, 7200))  # within 2 hours
            timestamp = base_time + timedelta(seconds=offset)

            hard_negatives.append(_make_hn_txn(
                user, receiver_vpa, amount, timestamp, "festival_shopping",
                is_merchant=True,
            ))

    return hard_negatives


def _hn_timestamp(rng: np.random.Generator, start: datetime, end: datetime) -> datetime:
    """Random timestamp for a hard negative."""
    delta = int((end - start).total_seconds())
    offset = int(rng.integers(0, max(1, delta)))
    return start + timedelta(seconds=offset)


def _make_hn_txn(
    user: pd.Series,
    receiver_vpa: str,
    amount: int,
    timestamp: datetime,
    hn_type: str,
    is_merchant: bool = False,
) -> Dict[str, Any]:
    """Create a hard-negative transaction dict."""
    return {
        "timestamp": timestamp,
        "sender_id": user["user_id"],
        "sender_vpa": user["vpa"],
        "receiver_vpa": receiver_vpa,
        "receiver_id": "",
        "amount": amount,
        "is_collect_request": False,
        "is_merchant_txn": is_merchant,
        "call_active_flag": False,
        "screen_share_active": False,
        "new_device_flag": False,
        "new_city_flag": False,
        "sim_swap_flag": False,
        "sender_city": user["city"],
        "sender_device": user["device"],
        "sender_account_age_days": user["account_age_days"],
        "receiver_account_age_days": -1,
        "is_fraud": False,
        "fraud_typology": "genuine",
        "note": "",
        "hard_negative_type": hn_type,
    }


def generate_dataset(config: GeneratorConfig = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Master function: generates the full synthetic UPI dataset.

    Returns
    -------
    (transactions_df, user_profiles_df, merchant_profiles_df, mule_accounts_df)
    """
    if config is None:
        config = GeneratorConfig()

    rng = np.random.default_rng(config.seed)
    time_start = datetime.strptime(config.start_date, "%Y-%m-%d")
    time_end = datetime.strptime(config.end_date, "%Y-%m-%d")

    print("=" * 60)
    print("UPI Fraud Data Generator")
    print("=" * 60)

    # ── Step 1: Generate profiles ────────────────────────────────────
    print("\n[1/6] Generating user profiles...")
    user_profiles = generate_user_profiles(config, rng)
    print(f"  Created {len(user_profiles)} user profiles")
    print(f"  Senior citizens: {user_profiles['is_senior'].sum()}")

    print("\n[2/6] Generating merchant profiles...")
    merchant_profiles = generate_merchant_profiles(config, rng)
    print(f"  Created {len(merchant_profiles)} merchant profiles")

    print("\n[3/6] Generating mule accounts...")
    mule_accounts = generate_mule_accounts(config, rng)
    print(f"  Created {len(mule_accounts)} mule accounts")
    print(f"  Mean mule age: {mule_accounts['account_age_days'].mean():.1f} days")

    print("\n[4/6] Assigning frequent payees...")
    payee_map = assign_frequent_payees(user_profiles, merchant_profiles, rng)

    # ── Step 2: Generate genuine transactions ────────────────────────
    print("\n[5/6] Generating genuine transactions...")
    genuine_txns = _generate_genuine_transactions(
        config, rng, user_profiles, merchant_profiles, payee_map, time_start, time_end,
    )
    print(f"  Generated {len(genuine_txns)} genuine transactions")

    # ── Step 3: Inject hard negatives ────────────────────────────────
    print("  Injecting hard negatives...")
    hard_negatives = _inject_hard_negatives(
        config, rng, genuine_txns, user_profiles, merchant_profiles, time_start, time_end,
    )
    print(f"  Injected {len(hard_negatives)} hard-negative transactions")

    # Add hard_negative_type to genuine txns that don't have it
    for txn in genuine_txns:
        if "hard_negative_type" not in txn:
            txn["hard_negative_type"] = "none"

    all_genuine = genuine_txns + hard_negatives

    # ── Step 4: Generate fraud transactions ──────────────────────────
    print("\n[6/6] Generating fraud transactions...")

    total_genuine = len(all_genuine)
    # Target fraud count based on desired fraud rate
    target_fraud = int(total_genuine * config.fraud_rate / (1.0 - config.fraud_rate))
    print(f"  Target fraud count: {target_fraud} ({config.fraud_rate*100:.1f}% rate)")

    # Distribute across typologies (weighted by prevalence)
    typology_weights = {
        "fake_collect_request": 0.25,
        "impersonation_vishing": 0.15,
        "qr_swap": 0.15,
        "rapid_burst": 0.10,     # fewer events, but each produces many txns
        "mule_chain": 0.10,     # fewer events, but each produces many txns
        "remote_access": 0.15,
        "account_takeover": 0.10,
    }

    # For burst and chain, count is number of EVENTS not transactions
    # Each event produces multiple txns, so we reduce the event count

    all_fraud: List[Dict[str, Any]] = []

    # Fake collect
    n_collect = int(target_fraud * typology_weights["fake_collect_request"])
    fraud_collect = generate_fake_collect_requests(
        config, rng, user_profiles, mule_accounts, time_start, time_end, n_collect,
    )
    all_fraud.extend(fraud_collect)
    print(f"  Fake collect requests: {len(fraud_collect)} txns")

    # Vishing
    n_vishing = int(target_fraud * typology_weights["impersonation_vishing"])
    fraud_vishing = generate_vishing_fraud(
        config, rng, user_profiles, mule_accounts, time_start, time_end, n_vishing,
    )
    all_fraud.extend(fraud_vishing)
    print(f"  Impersonation/vishing: {len(fraud_vishing)} txns")

    # QR swap
    n_qr = int(target_fraud * typology_weights["qr_swap"])
    fraud_qr = generate_qr_swap_fraud(
        config, rng, user_profiles, merchant_profiles, mule_accounts,
        payee_map, time_start, time_end, n_qr,
    )
    all_fraud.extend(fraud_qr)
    print(f"  QR swap: {len(fraud_qr)} txns")

    # Rapid burst (events -> multiple txns)
    n_burst_events = max(2, int(target_fraud * typology_weights["rapid_burst"]) // 8)
    fraud_burst = generate_rapid_burst_fraud(
        config, rng, user_profiles, mule_accounts, time_start, time_end, n_burst_events,
    )
    all_fraud.extend(fraud_burst)
    print(f"  Rapid burst: {n_burst_events} events -> {len(fraud_burst)} txns")

    # Mule chain (events -> multiple txns)
    n_chain_events = max(2, int(target_fraud * typology_weights["mule_chain"]) // 4)
    fraud_chain = generate_mule_chain_fraud(
        config, rng, user_profiles, mule_accounts, time_start, time_end, n_chain_events,
    )
    all_fraud.extend(fraud_chain)
    print(f"  Mule chains: {n_chain_events} events -> {len(fraud_chain)} txns")

    # Remote access
    n_remote = int(target_fraud * typology_weights["remote_access"])
    fraud_remote = generate_remote_access_fraud(
        config, rng, user_profiles, mule_accounts, time_start, time_end, n_remote,
    )
    all_fraud.extend(fraud_remote)
    print(f"  Remote access: {len(fraud_remote)} txns")

    # Account takeover (events -> multiple txns)
    n_ato_events = max(2, int(target_fraud * typology_weights["account_takeover"]) // 5)
    fraud_ato = generate_account_takeover_fraud(
        config, rng, user_profiles, mule_accounts, time_start, time_end, n_ato_events,
    )
    all_fraud.extend(fraud_ato)
    print(f"  Account takeover: {n_ato_events} events -> {len(fraud_ato)} txns")

    # Add hard_negative_type to fraud txns
    for txn in all_fraud:
        if "hard_negative_type" not in txn:
            txn["hard_negative_type"] = "none"

    # Resolve receiver_account_age_days and receiver_id for all transactions
    vpa_to_age = {}
    vpa_to_id = {}
    for _, row in user_profiles.iterrows():
        vpa_to_age[row["vpa"]] = row["account_age_days"]
        vpa_to_id[row["vpa"]] = row["user_id"]
    for _, row in merchant_profiles.iterrows():
        vpa_to_age[row["vpa"]] = row["account_age_days"]
        vpa_to_id[row["vpa"]] = row["merchant_id"]
    for _, row in mule_accounts.iterrows():
        vpa_to_age[row["vpa"]] = row["account_age_days"]
        vpa_to_id[row["vpa"]] = row["mule_id"]

    for txn in all_genuine:
        recv_vpa = txn["receiver_vpa"]
        if recv_vpa in vpa_to_age:
            txn["receiver_account_age_days"] = vpa_to_age[recv_vpa]
            txn["receiver_id"] = vpa_to_id[recv_vpa]
        else:
            txn["receiver_account_age_days"] = 365

    # -- Combine and sort ---------------------------------------------
    all_transactions = all_genuine + all_fraud
    df = pd.DataFrame(all_transactions)

    # Generate transaction IDs
    df = df.sort_values("timestamp").reset_index(drop=True)
    df.insert(0, "txn_id", [f"TXN{i:08d}" for i in range(len(df))])

    # ── Save ─────────────────────────────────────────────────────────
    os.makedirs(config.output_dir, exist_ok=True)

    if config.output_format == "parquet":
        txn_path = os.path.join(config.output_dir, "transactions.parquet")
        df.to_parquet(txn_path, index=False)
    else:
        txn_path = os.path.join(config.output_dir, "transactions.csv")
        df.to_csv(txn_path, index=False)

    user_path = os.path.join(config.output_dir, "user_profiles.parquet")
    user_profiles.to_parquet(user_path, index=False)

    merchant_path = os.path.join(config.output_dir, "merchant_profiles.parquet")
    merchant_profiles.to_parquet(merchant_path, index=False)

    mule_path = os.path.join(config.output_dir, "mule_accounts.parquet")
    mule_accounts.to_parquet(mule_path, index=False)

    print(f"\n  Saved to {config.output_dir}/")
    print(f"  Total transactions: {len(df)}")
    print(f"  Fraud transactions: {df['is_fraud'].sum()}")
    actual_rate = df["is_fraud"].mean()
    print(f"  Actual fraud rate: {actual_rate*100:.3f}%")

    return df, user_profiles, merchant_profiles, mule_accounts
