"""
Unit tests for Fraud Scoring Engine & Feature Engineering
"""

import pytest
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from schemas import THRESHOLD_ALLOW_MAX, THRESHOLD_WARN_MAX
from fraud_engine import FraudScoringEngine
import database


@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "test_fraud.db")
    database.init_db(db_file)
    return db_file


@pytest.fixture
def engine():
    return FraudScoringEngine()


def test_feature_extraction_without_history(engine, temp_db):
    """
    Test that baseline assumptions work gracefully for brand-new users.
    """
    features, context = engine.extract_features(
        sender_id="NEW_USER_01",
        recipient_id="NEW_USER_02",
        amount=1500.0,
        timestamp_str="2026-10-23T14:30:00",
        device_changed=False,
        db_path=temp_db
    )

    assert features["amount"] == 1500.0
    assert features["amount_vs_avg"] == 1.0  # Assumed nominal baseline ₹1500
    assert features["is_new_payee"] == 1.0
    assert features["transactions_last_10min"] == 0.0
    assert features["is_unusual_hour"] == 0.0
    assert features["device_changed"] == 0.0


def test_feature_extraction_with_observed_history(engine, temp_db):
    """
    Test that historical transactions in SQLite dynamically alter computed features.
    """
    # Seed 3 prior transactions: average amount = 500
    database.save_transaction({
        "transaction_id": "TX_HIST_01",
        "sender_id": "REGULAR_USER",
        "recipient_id": "FRIEND_BOB",
        "amount": 400.0,
        "timestamp": "2026-10-23T10:00:00",
        "device_changed": False,
        "channel": "P2P",
        "risk_score": 10.0,
        "decision": "ALLOW",
        "reasons": [],
        "latency_ms": 1.0
    }, db_path=temp_db)

    database.save_transaction({
        "transaction_id": "TX_HIST_02",
        "sender_id": "REGULAR_USER",
        "recipient_id": "FRIEND_BOB",
        "amount": 600.0,
        "timestamp": "2026-10-23T10:05:00",
        "device_changed": False,
        "channel": "P2P",
        "risk_score": 12.0,
        "decision": "ALLOW",
        "reasons": [],
        "latency_ms": 1.0
    }, db_path=temp_db)

    # Now test scoring a new transaction at 10:08 (within 10 minutes)
    features, context = engine.extract_features(
        sender_id="REGULAR_USER",
        recipient_id="FRIEND_BOB",
        amount=5000.0,  # 10x historical average of 500!
        timestamp_str="2026-10-23T10:08:00",
        device_changed=True,
        db_path=temp_db
    )

    assert context["historical_avg"] == 500.0
    assert features["amount_vs_avg"] == 10.0
    assert features["is_new_payee"] == 0.0  # Bob is a known payee!
    assert features["transactions_last_10min"] == 2.0  # Both prior txs were in last 10m
    assert features["device_changed"] == 1.0


def test_decision_thresholds(engine):
    """
    Verify strict threshold enforcement:
    ALLOW: < 30
    WARN: 30 to < 70
    HOLD: >= 70
    """
    low_risk = engine.score_transaction(
        sender_id="ALICE",
        recipient_id="BOB",
        amount=250.0,
        timestamp_str="2026-10-23T12:00:00",
        device_changed=False,
        simulated_overrides={"amount_vs_avg": 1.0, "is_new_payee": 0, "transactions_last_10min": 0, "network_risk": 0.05}
    )
    assert low_risk["risk_score"] < THRESHOLD_ALLOW_MAX
    assert low_risk["decision"] == "ALLOW"

    high_risk = engine.score_transaction(
        sender_id="ALICE",
        recipient_id="MULE_ACCOUNT_99",
        amount=85000.0,
        timestamp_str="2026-10-23T02:30:00",
        device_changed=True,
        simulated_overrides={
            "amount_vs_avg": 18.0,
            "is_new_payee": 1,
            "transactions_last_10min": 6,
            "is_unusual_hour": 1,
            "device_changed": 1,
            "recipient_risk": 0.95,
            "network_risk": 0.95
        }
    )
    assert high_risk["risk_score"] >= THRESHOLD_WARN_MAX
    assert high_risk["decision"] == "HOLD"
    assert len(high_risk["reasons"]) >= 2


def test_deterministic_scoring(engine):
    """
    Scoring must be 100% deterministic for identical inputs.
    """
    res1 = engine.score_transaction(
        sender_id="U100",
        recipient_id="U200",
        amount=12000.0,
        timestamp_str="2026-10-23T15:00:00",
        device_changed=True,
        simulated_overrides={"amount_vs_avg": 4.5, "is_new_payee": 1}
    )

    res2 = engine.score_transaction(
        sender_id="U100",
        recipient_id="U200",
        amount=12000.0,
        timestamp_str="2026-10-23T15:00:00",
        device_changed=True,
        simulated_overrides={"amount_vs_avg": 4.5, "is_new_payee": 1}
    )

    assert res1["risk_score"] == res2["risk_score"]
    assert res1["decision"] == res2["decision"]
    assert res1["reasons"] == res2["reasons"]


def test_no_single_feature_causes_automatic_hold(engine):
    """
    Rule: Never infer that a person is fraudulent solely because of one feature.
    A single device change or single new payee on an otherwise normal ₹100 transaction
    should NOT be labeled HOLD.
    """
    single_change = engine.score_transaction(
        sender_id="SAFE_USER",
        recipient_id="KNOWN_STORE",
        amount=120.0,
        timestamp_str="2026-10-23T14:00:00",
        device_changed=True,  # Only device changed
        simulated_overrides={"amount_vs_avg": 1.0, "is_new_payee": 0, "transactions_last_10min": 0, "network_risk": 0.05}
    )
    assert single_change["decision"] != "HOLD"
