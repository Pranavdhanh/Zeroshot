"""
Configuration for the synthetic UPI transaction data generator.
All parameters are centralised here for reproducibility and tuning.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class GeneratorConfig:
    """Master configuration for the synthetic data generator."""

    # ── Reproducibility ──────────────────────────────────────────────
    seed: int = 42

    # ── Scale ────────────────────────────────────────────────────────
    num_users: int = 5000
    num_merchants: int = 500
    num_mule_accounts: int = 150          # dedicated mule VPAs
    num_transactions: int = 500_000       # total genuine transactions
    fraud_rate: float = 0.003             # 0.3 % — within 0.1-0.5 % band

    # ── Time window ──────────────────────────────────────────────────
    start_date: str = "2025-01-01"
    end_date: str = "2025-03-31"          # 90 days

    # ── User profile distributions ───────────────────────────────────
    # Monthly income bracket probabilities (bracket_name → (low, high, prob))
    income_brackets: List[Tuple[str, int, int, float]] = field(default_factory=lambda: [
        ("low",      8_000,    20_000,  0.30),
        ("mid_low",  20_001,   40_000,  0.30),
        ("mid",      40_001,   80_000,  0.20),
        ("mid_high", 80_001,  1_50_000, 0.12),
        ("high",    1_50_001,  5_00_000, 0.08),
    ])

    # Age distribution (min, max, mean, std)
    age_distribution: Tuple[int, int, float, float] = (18, 80, 35.0, 12.0)

    # Cities with relative population weight
    cities: List[Tuple[str, float]] = field(default_factory=lambda: [
        ("Mumbai", 0.14), ("Delhi", 0.12), ("Bangalore", 0.10),
        ("Hyderabad", 0.08), ("Chennai", 0.08), ("Pune", 0.07),
        ("Kolkata", 0.06), ("Ahmedabad", 0.05), ("Jaipur", 0.04),
        ("Lucknow", 0.04), ("Coimbatore", 0.03), ("Surat", 0.03),
        ("Kochi", 0.03), ("Indore", 0.02), ("Chandigarh", 0.02),
        ("Patna", 0.02), ("Bhopal", 0.02), ("Nagpur", 0.02),
        ("Visakhapatnam", 0.02), ("Thiruvananthapuram", 0.01),
    ])

    # Active hours distribution (hour → relative weight for genuine txns)
    active_hours_weights: List[float] = field(default_factory=lambda: [
        # 0-5: very low, 6-9: morning ramp, 10-13: lunch, 14-17: afternoon,
        # 18-21: evening peak, 22-23: wind down
        0.005, 0.003, 0.002, 0.002, 0.003, 0.008,     # 0-5
        0.02,  0.04,  0.06,  0.08,  0.09,  0.09,       # 6-11
        0.08,  0.07,  0.06,  0.05,  0.04,  0.05,       # 12-17
        0.07,  0.08,  0.06,  0.04,  0.02,  0.01,       # 18-23
    ])

    # Devices
    device_types: List[str] = field(default_factory=lambda: [
        "android_budget", "android_mid", "android_flagship",
        "iphone_old", "iphone_new",
    ])
    device_weights: List[float] = field(default_factory=lambda: [
        0.35, 0.30, 0.12, 0.10, 0.13,
    ])

    # ── Transaction patterns ─────────────────────────────────────────
    # Per-user average daily transactions (sampled from gamma)
    daily_txn_mean: float = 2.5
    daily_txn_shape: float = 2.0       # gamma shape → right-skewed

    # Amount distributions by category
    # (category, probability, amount_mean, amount_std, amount_min, amount_max)
    txn_categories: List[Tuple[str, float, float, float, float, float]] = field(
        default_factory=lambda: [
            ("small_p2p",       0.30,    200,    150,    10,   1_000),
            ("medium_p2p",      0.15,  2_000,  1_500,   500,  10_000),
            ("merchant_small",  0.25,    150,    100,    20,     800),
            ("merchant_medium", 0.12,  1_000,    600,   200,   5_000),
            ("bill_payment",    0.08,  1_500,  1_000,   100,   8_000),
            ("recharge",        0.05,    200,    150,    10,     999),
            ("large_p2p",       0.03, 15_000, 10_000, 5_000,  50_000),
            ("salary_credit",   0.02, 30_000, 15_000, 8_000, 1_50_000),
        ]
    )

    # Periodic payments (rent, salary, subscription)
    periodic_payers_fraction: float = 0.3  # fraction of users who make periodic payments
    periodic_amount_range: Tuple[int, int] = (5_000, 50_000)

    # ── Hard negative parameters ─────────────────────────────────────
    hard_negative_fraction: float = 0.01  # 1% of genuine txns are hard negatives

    # ── Fraud typology parameters ────────────────────────────────────
    # Typology 1: Fake collect request
    fake_collect_amount_range: Tuple[int, int] = (500, 9_999)
    fake_collect_victim_max_lifetime_txns: int = 20

    # Typology 2: Impersonation / vishing
    vishing_amount_range: Tuple[int, int] = (10_000, 1_00_000)
    vishing_call_window_minutes: int = 10
    vishing_victim_min_balance: int = 50_000
    vishing_victim_min_age: int = 45

    # Typology 3: QR swap
    qr_swap_amount_range: Tuple[int, int] = (50, 2_000)
    qr_swap_fan_in_count: Tuple[int, int] = (5, 20)

    # Typology 4: Rapid new-payee burst
    burst_transfer_count: Tuple[int, int] = (5, 15)
    burst_window_minutes: int = 30
    burst_amount_range: Tuple[int, int] = (1_000, 15_000)

    # Typology 5: Mule chain
    mule_chain_length: Tuple[int, int] = (3, 5)
    mule_chain_dwell_seconds: Tuple[int, int] = (30, 300)
    mule_account_max_age_days: int = 30

    # Typology 6: Remote access / screen share
    remote_access_amount_range: Tuple[int, int] = (5_000, 50_000)

    # Typology 7: Account takeover
    ato_amount_range: Tuple[int, int] = (5_000, 1_00_000)
    ato_transfer_count: Tuple[int, int] = (3, 8)
    ato_window_minutes: int = 30

    # -- Mule account parameters --------------------------------------
    mule_age_range_days: Tuple[int, int] = (1, 90)
    mule_pass_through_ratio: float = 0.85

    # ── Output ───────────────────────────────────────────────────────
    output_dir: str = "data"
    output_format: str = "parquet"      # "parquet" or "csv"
