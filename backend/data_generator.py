"""
UPI Shield AI — Synthetic Transaction & Mule Network Data Generator
Track 4: FinTech & GovTech Intelligence

DISCLAIMER & ETHICS NOTICE:
All accounts, VPA IDs, transactions, and behavioral patterns generated in this module
are purely synthetic simulations designed for academic research and hackathon demonstration.
No real personal, banking, UPI, or financial institution data is used.
Notice: High evaluation metrics on synthetic data are NOT proof of real-world operational effectiveness.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np


# Standard feature columns used for ML modeling (excludes identifiers and leakage labels)
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


def generate_synthetic_dataset(
    n_samples: int = 6000,
    fraud_ratio: float = 0.18,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates a reproducible dataset of labelled genuine and fraudulent UPI transactions.
    
    Includes documented fraud scenarios:
    1. unusual_large_transfer: amount 5x to 20x higher than sender's normal average
    2. rapid_payments_to_new_recipients: rapid velocity burst to unknown payees with new device
    3. money_moving_rapidly_through_multiple_accounts: multi-hop mule layering
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    records: List[Dict[str, Any]] = []
    base_time = datetime(2026, 10, 20, 8, 0, 0)

    # Synthetic pool of genuine users
    genuine_users = [f"U{i:04d}" for i in range(1, 251)]
    # Mule and high risk entity pool
    flagged_entities = [f"MULE_{i:03d}" for i in range(1, 41)]

    # Sender profile averages (e.g. ₹200 to ₹4000)
    user_avg_amounts = {
        u: round(float(np.random.gamma(shape=3.0, scale=350.0)), 2)
        for u in genuine_users
    }

    n_fraud = int(n_samples * fraud_ratio)
    n_genuine = n_samples - n_fraud

    # 1. Generate Genuine Transactions
    for i in range(n_genuine):
        sender = random.choice(genuine_users)
        # 80% to known or peer user, 20% to random merchant or new peer
        is_new_payee = 1 if random.random() < 0.22 else 0
        recipient = random.choice([u for u in genuine_users if u != sender])
        
        # Genuine amounts fluctuate normally around user's avg
        user_avg = user_avg_amounts[sender]
        amount_ratio = float(np.random.lognormal(mean=0.0, sigma=0.4))
        # Cap realistic genuine transactions
        amount_ratio = min(max(amount_ratio, 0.2), 3.0)
        amount = round(user_avg * amount_ratio, 2)
        if amount < 10.0:
            amount = 10.0

        # Normal hours: predominantly 7 AM to 11 PM
        hour_weights = np.array([
            0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.04, 0.06, 0.08, 0.09, 0.08, 0.08,
            0.08, 0.07, 0.07, 0.07, 0.07, 0.08, 0.06, 0.05, 0.03, 0.02, 0.01, 0.01
        ])
        hour_probs = hour_weights / hour_weights.sum()
        hour = int(np.random.choice([h for h in range(24)], p=hour_probs))
        is_unusual_hour = 1 if (hour < 5 or hour >= 23) else 0

        # Genuine device changes are rare (new phone/SIM swap: ~3%)
        device_changed = 1 if random.random() < 0.03 else 0

        # Genuine transaction burst is low (0 or 1 recent tx)
        tx_last_10min = int(np.random.choice([0, 1, 2], p=[0.85, 0.12, 0.03]))

        # Genuine recipient risk is minimal
        recipient_risk = round(float(np.random.beta(a=1, b=15)), 3)
        network_risk = round(float(np.random.beta(a=1, b=20)), 3)

        tx_time = base_time + timedelta(minutes=i * 2 + random.randint(0, 180))

        records.append({
            "transaction_id": f"TX_GEN_{i:06d}",
            "sender_id": sender,
            "recipient_id": recipient,
            "amount": amount,
            "amount_vs_avg": round(amount / user_avg, 3),
            "is_new_payee": is_new_payee,
            "transactions_last_10min": tx_last_10min,
            "is_unusual_hour": is_unusual_hour,
            "device_changed": device_changed,
            "recipient_risk": recipient_risk,
            "network_risk": network_risk,
            "scenario": "genuine_normal",
            "is_fraud": 0,
            "timestamp": tx_time.isoformat()
        })

    # 2. Generate Fraud Scenarios
    fraud_scenarios = [
        "unusual_large_transfer",
        "rapid_payments_to_new_recipients",
        "mule_chain_layering"
    ]

    for j in range(n_fraud):
        scenario = fraud_scenarios[j % len(fraud_scenarios)]
        sender = random.choice(genuine_users)
        user_avg = user_avg_amounts[sender]
        tx_time = base_time + timedelta(minutes=j * 3 + random.randint(0, 240))

        if scenario == "unusual_large_transfer":
            # Scenario 1: Sudden massive draining transfer (5x to 25x average)
            amount_ratio = round(float(np.random.uniform(5.5, 22.0)), 2)
            amount = round(user_avg * amount_ratio, 2)
            amount = max(amount, 15000.0)
            recipient = random.choice(flagged_entities)
            is_new_payee = 1
            device_changed = 1 if random.random() < 0.65 else 0
            is_unusual_hour = 1 if random.random() < 0.45 else 0
            tx_last_10min = random.randint(0, 2)
            recipient_risk = round(float(np.random.uniform(0.65, 0.95)), 3)
            network_risk = round(float(np.random.uniform(0.50, 0.88)), 3)

        elif scenario == "rapid_payments_to_new_recipients":
            # Scenario 2: Account takeover or social engineering burst
            amount_ratio = round(float(np.random.uniform(1.8, 6.0)), 2)
            amount = round(user_avg * amount_ratio, 2)
            recipient = f"NEW_VPA_{random.randint(100, 999)}@bank"
            is_new_payee = 1
            device_changed = 1 if random.random() < 0.85 else 0
            is_unusual_hour = 1 if random.random() < 0.55 else 0
            tx_last_10min = random.randint(4, 9)  # Rapid payments in last 10 minutes
            recipient_risk = round(float(np.random.uniform(0.55, 0.90)), 3)
            network_risk = round(float(np.random.uniform(0.60, 0.92)), 3)

        else:  # mule_chain_layering
            # Scenario 3: Layering through mule networks
            amount = round(float(np.random.uniform(25000.0, 95000.0)), 2)
            amount_ratio = round(amount / user_avg, 2)
            recipient = random.choice(flagged_entities)
            is_new_payee = 1
            device_changed = 1 if random.random() < 0.40 else 0
            is_unusual_hour = 1 if random.random() < 0.35 else 0
            tx_last_10min = random.randint(2, 6)
            recipient_risk = round(float(np.random.uniform(0.75, 0.98)), 3)
            network_risk = round(float(np.random.uniform(0.80, 0.99)), 3)

        records.append({
            "transaction_id": f"TX_FRD_{j:06d}",
            "sender_id": sender,
            "recipient_id": recipient,
            "amount": amount,
            "amount_vs_avg": amount_ratio,
            "is_new_payee": is_new_payee,
            "transactions_last_10min": tx_last_10min,
            "is_unusual_hour": is_unusual_hour,
            "device_changed": device_changed,
            "recipient_risk": recipient_risk,
            "network_risk": network_risk,
            "scenario": scenario,
            "is_fraud": 1,
            "timestamp": tx_time.isoformat()
        })

    df = pd.DataFrame(records)
    # Shuffle deterministically
    df = df.sample(frac=1.0, random_state=random_seed).reset_index(drop=True)
    return df


def generate_network_seed_data(random_seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generates deterministic graph seed transactions designed to showcase
    clear, explainable mule account patterns for hackathon demonstration:
    - Fan-In Hub (Mule Aggregator: many accounts sending to one collector)
    - Fan-Out Disperser (Layering Smurf: one account dispersing to many new mules)
    - Multi-Hop Transfer Chain (A -> B -> C -> D rapid pass-through)
    - Normal peer-to-peer and merchant edges for realistic contrast
    """
    random.seed(random_seed)
    seed_edges: List[Dict[str, Any]] = []
    base_t = datetime(2026, 10, 20, 10, 0, 0)

    # 1. FAN-IN MULE AGGREGATOR (Collector: MULE_COLLECTOR_01 receives from 7 accounts)
    aggregator = "MULE_COLLECTOR_01"
    senders = [f"VICTIM_{i:02d}" for i in range(1, 8)]
    for i, s in enumerate(senders):
        t = base_t + timedelta(minutes=i * 5)
        seed_edges.append({
            "sender_id": s,
            "recipient_id": aggregator,
            "amount": 12000.0 + (i * 1500),
            "timestamp": t.isoformat(),
            "decision": "HOLD" if i > 3 else "WARN",
            "risk_score": 75.0 + (i * 2.5)
        })

    # 2. FAN-OUT DISPERSER (MULE_DISPERSER_02 rapidly disperses funds to 6 distinct cash-out accounts)
    disperser = "MULE_DISPERSER_02"
    cashout_recipients = [f"CASHOUT_{i:02d}" for i in range(1, 7)]
    for i, rec in enumerate(cashout_recipients):
        t = base_t + timedelta(minutes=40 + i * 2)
        seed_edges.append({
            "sender_id": disperser,
            "recipient_id": rec,
            "amount": 9500.0,
            "timestamp": t.isoformat(),
            "decision": "HOLD",
            "risk_score": 84.0
        })

    # 3. MULTI-HOP TRANSFER CHAIN (Layering chain: HOP_A -> HOP_B -> HOP_C -> HOP_D)
    chain_hops = ["HOP_ACCOUNT_A", "HOP_ACCOUNT_B", "HOP_ACCOUNT_C", "HOP_ACCOUNT_D"]
    for i in range(len(chain_hops) - 1):
        t = base_t + timedelta(minutes=80 + i * 3)  # Rapid 3-minute hops
        seed_edges.append({
            "sender_id": chain_hops[i],
            "recipient_id": chain_hops[i+1],
            "amount": 48500.0 - (i * 500),  # Slight cut taken at each hop
            "timestamp": t.isoformat(),
            "decision": "HOLD",
            "risk_score": 88.0 + i
        })

    # 4. NORMAL P2P & MERCHANT EDGES (Baseline genuine interactions)
    normal_pairs = [
        ("USER_ALICE", "USER_BOB", 850.0),
        ("USER_BOB", "USER_CHARLIE", 420.0),
        ("USER_CHARLIE", "MERCHANT_GROCERY", 1250.0),
        ("USER_DAVID", "MERCHANT_CAFE", 310.0),
        ("USER_EMMA", "USER_ALICE", 1500.0),
        ("USER_FRANK", "MERCHANT_GROCERY", 680.0),
        ("USER_GRACE", "USER_DAVID", 500.0)
    ]
    for s, r, amt in normal_pairs:
        t = base_t + timedelta(minutes=random.randint(5, 120))
        seed_edges.append({
            "sender_id": s,
            "recipient_id": r,
            "amount": amt,
            "timestamp": t.isoformat(),
            "decision": "ALLOW",
            "risk_score": 12.0
        })

    return seed_edges


if __name__ == "__main__":
    df = generate_synthetic_dataset(1000)
    print(f"Generated {len(df)} synthetic transactions.")
    print("Class balance:")
    print(df["is_fraud"].value_counts(normalize=True))
    print("\nSample records:")
    print(df[FEATURE_COLUMNS + ["is_fraud", "scenario"]].head(5))
