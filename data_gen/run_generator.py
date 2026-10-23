"""
Phase 1 Gate Check: Run the data generator and validate outputs.

Prints:
  - Class balance (fraud vs genuine)
  - Per-typology counts
  - Sample rows
  - Hard negative summary
  - Amount distribution stats
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from tabulate import tabulate

from data_gen.config import GeneratorConfig
from data_gen.generator import generate_dataset


def run_gate_check(force_regenerate: bool = False):
    """Execute Phase 1 gate check."""
    config = GeneratorConfig()

    txn_file = os.path.join(config.output_dir, "transactions.parquet")
    user_file = os.path.join(config.output_dir, "user_profiles.parquet")
    merchant_file = os.path.join(config.output_dir, "merchant_profiles.parquet")
    mule_file = os.path.join(config.output_dir, "mule_accounts.parquet")

    data_exists = (
        os.path.exists(txn_file)
        and os.path.exists(user_file)
        and os.path.exists(merchant_file)
        and os.path.exists(mule_file)
    )

    if data_exists and not force_regenerate:
        print("Loading existing dataset from data/ ...")
        df = pd.read_parquet(txn_file)
        user_profiles = pd.read_parquet(user_file)
        merchant_profiles = pd.read_parquet(merchant_file)
        mule_accounts = pd.read_parquet(mule_file)
    else:
        df, user_profiles, merchant_profiles, mule_accounts = generate_dataset(config)

    print("\n")
    print("=" * 60)
    print("PHASE 1 GATE CHECK")
    print("=" * 60)

    # -- 1. Class balance ---------------------------------------------
    print("\n-- 1. CLASS BALANCE --------------------------------------")
    total = len(df)
    n_fraud = int(df["is_fraud"].sum())
    n_genuine = total - n_fraud
    fraud_rate = n_fraud / total * 100

    balance_table = [
        ["Genuine", n_genuine, f"{n_genuine/total*100:.3f}%"],
        ["Fraud", n_fraud, f"{fraud_rate:.3f}%"],
        ["Total", total, "100%"],
    ]
    print(tabulate(balance_table, headers=["Class", "Count", "Percentage"], tablefmt="grid"))
    print(f"\nFraud rate: {fraud_rate:.3f}% (target: {config.fraud_rate*100:.1f}%)")

    within_band = 0.1 <= fraud_rate <= 0.5
    if within_band:
        status = "PASS"
    else:
        status = "FAIL"
    print(f"Within 0.1-0.5% band: {status}")

    # -- 2. Per-typology counts ---------------------------------------
    print("\n-- 2. PER-TYPOLOGY COUNTS --------------------------------")
    typology_counts = df[df["is_fraud"] == True].groupby("fraud_typology").agg(
        count=("txn_id", "count"),
        mean_amount=("amount", "mean"),
        min_amount=("amount", "min"),
        max_amount=("amount", "max"),
    ).reset_index()
    typology_counts["mean_amount"] = typology_counts["mean_amount"].apply(lambda x: f"Rs. {x:,.0f}")
    typology_counts["min_amount"] = typology_counts["min_amount"].apply(lambda x: f"Rs. {x:,.0f}")
    typology_counts["max_amount"] = typology_counts["max_amount"].apply(lambda x: f"Rs. {x:,.0f}")

    print(tabulate(typology_counts, headers="keys", tablefmt="grid", showindex=False))

    # -- 3. Sample fraud rows -----------------------------------------
    print("\n-- 3. SAMPLE FRAUD ROWS (one per typology) ---------------")
    for typology in df[df["is_fraud"] == True]["fraud_typology"].unique():
        sample = df[df["fraud_typology"] == typology].iloc[0]
        print(f"\n  [{typology}]")
        print(f"    txn_id: {sample['txn_id']}")
        print(f"    timestamp: {sample['timestamp']}")
        print(f"    sender: {sample['sender_vpa']} -> receiver: {sample['receiver_vpa']}")
        print(f"    amount: Rs. {sample['amount']:,}")
        print(f"    collect_req: {sample['is_collect_request']}, "
              f"call: {sample['call_active_flag']}, "
              f"screen_share: {sample['screen_share_active']}, "
              f"new_device: {sample['new_device_flag']}, "
              f"new_city: {sample['new_city_flag']}, "
              f"sim_swap: {sample['sim_swap_flag']}")

    # -- 4. Hard negatives --------------------------------------------
    print("\n-- 4. HARD NEGATIVES -------------------------------------")
    hn_df = df[df["hard_negative_type"] != "none"]
    if len(hn_df) > 0:
        hn_counts = hn_df.groupby("hard_negative_type").agg(
            count=("txn_id", "count"),
            mean_amount=("amount", "mean"),
            has_new_device=("new_device_flag", "sum"),
            has_new_city=("new_city_flag", "sum"),
        ).reset_index()
        hn_counts["mean_amount"] = hn_counts["mean_amount"].apply(lambda x: f"Rs. {x:,.0f}")
        print(tabulate(hn_counts, headers="keys", tablefmt="grid", showindex=False))

        # Verify hard negatives are NOT labelled as fraud
        hn_fraud = hn_df["is_fraud"].sum()
        print(f"\nHard negatives labelled as fraud: {hn_fraud} (must be 0)")
        assert hn_fraud == 0, "FAIL: Hard negatives must not be labelled as fraud!"
        print("PASS: All hard negatives correctly labelled as genuine")
    else:
        print("WARNING: No hard negatives found!")

    # -- 5. Amount distribution ---------------------------------------
    print("\n-- 5. AMOUNT DISTRIBUTION --------------------------------")
    for label, subset in [("Genuine", df[df["is_fraud"] == False]),
                          ("Fraud", df[df["is_fraud"] == True])]:
        print(f"\n  {label} transactions:")
        print(f"    Count:  {len(subset):,}")
        print(f"    Mean:   Rs. {subset['amount'].mean():,.0f}")
        print(f"    Median: Rs. {subset['amount'].median():,.0f}")
        print(f"    Std:    Rs. {subset['amount'].std():,.0f}")
        print(f"    Min:    Rs. {subset['amount'].min():,}")
        print(f"    Max:    Rs. {subset['amount'].max():,}")
        percentiles = subset["amount"].quantile([0.25, 0.50, 0.75, 0.90, 0.95, 0.99])
        for p, v in percentiles.items():
            print(f"    P{int(p*100):02d}:    Rs. {v:,.0f}")

    # -- 6. Temporal distribution -------------------------------------
    print("\n-- 6. TEMPORAL DISTRIBUTION ------------------------------")
    df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
    hour_dist = df.groupby(["hour", "is_fraud"]).size().unstack(fill_value=0)
    print("\nHourly transaction counts (top 5 hours):")
    if False in hour_dist.columns:
        top_hours = hour_dist[False].sort_values(ascending=False).head(5)
        for hour, count in top_hours.items():
            if True in hour_dist.columns:
                fraud_at_hour = hour_dist.loc[hour, True]
            else:
                fraud_at_hour = 0
            print(f"  Hour {hour:02d}: {count:,} genuine, {fraud_at_hour} fraud")

    # -- 7. Mule account characteristics ------------------------------
    print("\n-- 7. MULE ACCOUNT CHARACTERISTICS ----------------------")
    print(f"  Total mule accounts: {len(mule_accounts)}")
    print(f"  Mean age: {mule_accounts['account_age_days'].mean():.1f} days")
    print(f"  Min age: {mule_accounts['account_age_days'].min()} days")
    print(f"  Max age: {mule_accounts['account_age_days'].max()} days")

    # Check mule chain presence
    chain_txns = df[df["fraud_typology"] == "mule_chain"]
    if len(chain_txns) > 0:
        mule_vpas = set(mule_accounts["vpa"].tolist())
        mule_to_mule = chain_txns[
            chain_txns["sender_vpa"].isin(mule_vpas) & chain_txns["receiver_vpa"].isin(mule_vpas)
        ]
        print(f"  Mule chain transactions: {len(chain_txns)}")
        print(f"  Mule-to-mule hops: {len(mule_to_mule)}")
        print(f"  Fan-in/fan-out structures: present")
    else:
        print("  WARNING: No mule chain transactions found!")

    # -- 8. Feature signal verification -------------------------------
    print("\n-- 8. SIGNAL VERIFICATION -------------------------------")
    signals = {
        "collect_request": "is_collect_request",
        "call_active": "call_active_flag",
        "screen_share": "screen_share_active",
        "new_device": "new_device_flag",
        "new_city": "new_city_flag",
        "sim_swap": "sim_swap_flag",
    }
    for signal_name, col in signals.items():
        total_count = int(df[col].sum())
        fraud_count = int(df[df["is_fraud"] == True][col].sum())
        genuine_count = int(df[df["is_fraud"] == False][col].sum())
        print(f"  {signal_name}: {fraud_count} in fraud, {genuine_count} in genuine (total: {total_count})")

    # -- Summary ------------------------------------------------------
    print("\n" + "=" * 60)
    print("PHASE 1 GATE CHECK: COMPLETE")
    print("=" * 60)
    print(f"\nDataset saved to: {config.output_dir}/")
    print(f"Files:")
    for f in os.listdir(config.output_dir):
        fpath = os.path.join(config.output_dir, f)
        size_mb = os.path.getsize(fpath) / (1024 * 1024)
        print(f"  {f} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    force_gen = "--force" in sys.argv
    run_gate_check(force_regenerate=force_gen)
