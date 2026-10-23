"""
Unit tests for Graph Intelligence Engine & Mule Account Pattern Detection
"""

import pytest
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from graph_engine import GraphIntelligenceEngine


@pytest.fixture
def graph_engine():
    return GraphIntelligenceEngine()


def test_fan_in_aggregator_detection(graph_engine):
    """
    Fan-In: Many distinct accounts sending money into a single collector account.
    """
    edges = [
        {"sender_id": f"SENDER_{i}", "recipient_id": "MULE_COLLECTOR", "amount": 10000.0, "timestamp": f"2026-10-23T10:0{i}:00"}
        for i in range(1, 6)  # 5 distinct senders
    ]

    graph_engine.build_graph_from_transactions(edges)
    nodes, _ = graph_engine.detect_mule_patterns()

    aggregator = next((n for n in nodes if n["id"] == "MULE_COLLECTOR"), None)
    assert aggregator is not None
    assert aggregator["is_mule"] is True
    assert aggregator["role"] == "FAN_IN_AGGREGATOR"
    assert aggregator["in_degree"] == 5
    assert aggregator["out_degree"] == 0
    assert "Fan-In Aggregator" in aggregator["reasons"][0]


def test_fan_out_disperser_detection(graph_engine):
    """
    Fan-Out: One account rapidly dispersing funds to many new recipients (smurfing/cashout).
    """
    edges = [
        {"sender_id": "MULE_DISPERSER", "recipient_id": f"CASHOUT_{i}", "amount": 8000.0, "timestamp": f"2026-10-23T11:0{i}:00"}
        for i in range(1, 6)  # 5 distinct recipients
    ]

    graph_engine.build_graph_from_transactions(edges)
    nodes, _ = graph_engine.detect_mule_patterns()

    disperser = next((n for n in nodes if n["id"] == "MULE_DISPERSER"), None)
    assert disperser is not None
    assert disperser["is_mule"] is True
    assert disperser["role"] == "FAN_OUT_DISPERSER"
    assert disperser["out_degree"] == 5
    assert "Fan-Out Disperser" in disperser["reasons"][0]


def test_multi_hop_chain_detection(graph_engine):
    """
    Multi-hop chain: A -> B -> C -> D rapid pass-through layering.
    Intermediate nodes B and C should be flagged as chain mules.
    """
    edges = [
        {"sender_id": "CHAIN_A", "recipient_id": "CHAIN_B", "amount": 50000.0, "timestamp": "2026-10-23T12:00:00"},
        {"sender_id": "CHAIN_B", "recipient_id": "CHAIN_C", "amount": 49000.0, "timestamp": "2026-10-23T12:05:00"},
        {"sender_id": "CHAIN_C", "recipient_id": "CHAIN_D", "amount": 48000.0, "timestamp": "2026-10-23T12:10:00"},
    ]

    graph_engine.build_graph_from_transactions(edges)
    nodes, _ = graph_engine.detect_mule_patterns()

    node_b = next((n for n in nodes if n["id"] == "CHAIN_B"), None)
    node_c = next((n for n in nodes if n["id"] == "CHAIN_C"), None)

    assert node_b is not None
    assert node_b["is_mule"] is True
    assert node_b["role"] == "CHAIN_MULE"

    assert node_c is not None
    assert node_c["is_mule"] is True
    assert node_c["role"] == "CHAIN_MULE"


def test_normal_nodes_not_mule(graph_engine):
    """
    Do not automatically label every normal connected account as a mule.
    """
    edges = [
        {"sender_id": "GENUINE_USER_1", "recipient_id": "LOCAL_GROCERY", "amount": 450.0, "timestamp": "2026-10-23T09:00:00"},
        {"sender_id": "GENUINE_USER_2", "recipient_id": "LOCAL_GROCERY", "amount": 320.0, "timestamp": "2026-10-23T09:15:00"},
    ]

    graph_engine.build_graph_from_transactions(edges)
    nodes, _ = graph_engine.detect_mule_patterns()

    grocery = next((n for n in nodes if n["id"] == "LOCAL_GROCERY"), None)
    assert grocery is not None
    assert grocery["is_mule"] is False
    assert grocery["role"] == "NORMAL"
