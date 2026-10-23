"""
Integration and End-to-End API Tests for UPI Shield AI
"""

import pytest
import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import database
from main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(tmp_path_factory):
    """
    Sets up an isolated SQLite test database for the entire test session.
    """
    tmp_dir = tmp_path_factory.mktemp("api_data")
    test_db = str(tmp_dir / "test_api_shield.db")
    os.environ["UPI_SHIELD_DB_PATH"] = test_db
    database.init_db(test_db)
    yield
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except Exception:
            pass


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    """
    GET /health should return 200 OK with model status and timestamp.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_status" in data
    assert "timestamp" in data


def test_score_valid_transaction(client):
    """
    POST /api/transactions/score with frontend contract example.
    """
    payload = {
        "sender_id": "U001",
        "recipient_id": "U009",
        "amount": 15000.0,
        "timestamp": "2026-10-23T22:30:00",
        "device_changed": True
    }
    response = client.post("/api/transactions/score", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "transaction_id" in data
    assert isinstance(data["transaction_id"], str)
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 100.0
    assert data["decision"] in ["ALLOW", "WARN", "HOLD"]
    assert isinstance(data["reasons"], list)
    assert "latency_ms" in data
    assert data["latency_ms"] >= 0.0


def test_score_invalid_amount(client):
    """
    Amount must be strictly positive (> 0).
    """
    payload = {
        "sender_id": "U001",
        "recipient_id": "U009",
        "amount": -50.0
    }
    response = client.post("/api/transactions/score", json=payload)
    assert response.status_code == 422
    assert "Validation error" in response.json()["detail"]

    # Zero amount
    payload["amount"] = 0.0
    response = client.post("/api/transactions/score", json=payload)
    assert response.status_code == 422


def test_score_same_sender_recipient(client):
    """
    Sender and recipient cannot be identical.
    """
    payload = {
        "sender_id": "U001",
        "recipient_id": "U001",
        "amount": 500.0
    }
    response = client.post("/api/transactions/score", json=payload)
    assert response.status_code == 422
    err_text = str(response.json())
    assert "cannot be the same" in err_text


def test_transactions_endpoint_and_filtering(client):
    """
    GET /api/transactions should retrieve stored records with pagination.
    """
    # Score a known transaction
    client.post("/api/transactions/score", json={
        "sender_id": "FILTER_USER_A",
        "recipient_id": "FILTER_USER_B",
        "amount": 750.0
    })

    # Test filtering by sender_id
    response = client.get("/api/transactions?sender_id=FILTER_USER_A")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert any(tx["sender_id"] == "FILTER_USER_A" for tx in data["items"])


def test_dashboard_summary_endpoint(client):
    """
    GET /api/dashboard/summary derives accurate aggregates from stored records.
    """
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert "allow_count" in data
    assert "warn_count" in data
    assert "hold_count" in data
    assert "total_volume" in data
    assert "avg_risk_score" in data
    assert data["total_transactions"] == (data["allow_count"] + data["warn_count"] + data["hold_count"])


def test_alerts_endpoint(client):
    """
    GET /api/alerts returns WARN and HOLD transactions with correct severity.
    """
    # Trigger a HOLD alert with high risk overrides
    client.post("/api/transactions/score", json={
        "sender_id": "ALERT_SENDER",
        "recipient_id": "MULE_RECIPIENT_TEST",
        "amount": 80000.0,
        "device_changed": True,
        "simulated_features": {
            "amount_vs_avg": 20.0,
            "is_new_payee": 1,
            "transactions_last_10min": 5,
            "recipient_risk": 0.9,
            "network_risk": 0.9
        }
    })

    response = client.get("/api/alerts?limit=10")
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)
    assert len(alerts) >= 1
    for a in alerts:
        assert a["decision"] in ["WARN", "HOLD"]
        if a["decision"] == "HOLD":
            assert a["severity"] == "HIGH"
        else:
            assert a["severity"] == "MEDIUM"


def test_network_graph_endpoint(client):
    """
    GET /api/network returns directed graph nodes and edges.
    """
    response = client.get("/api/network")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "mule_count" in data
    assert len(data["nodes"]) >= 1


def test_case_management_lifecycle(client):
    """
    Test GET /api/cases and PATCH /api/cases/{case_id}
    """
    # Score a HOLD transaction to auto-generate a case
    res = client.post("/api/transactions/score", json={
        "sender_id": "CASE_TEST_SENDER",
        "recipient_id": "CASE_TEST_MULE",
        "amount": 95000.0,
        "device_changed": True,
        "simulated_features": {
            "amount_vs_avg": 25.0,
            "is_new_payee": 1,
            "network_risk": 0.95,
            "recipient_risk": 0.95
        }
    })
    tx_id = res.json()["transaction_id"]

    # Retrieve cases
    cases_resp = client.get("/api/cases?status=OPEN")
    assert cases_resp.status_code == 200
    cases = cases_resp.json()
    target_case = next((c for c in cases if c["transaction_id"] == tx_id), None)
    assert target_case is not None
    case_id = target_case["case_id"]

    # 1. Update to INVESTIGATING
    patch1 = client.patch(f"/api/cases/{case_id}", json={
        "status": "INVESTIGATING",
        "notes": "Analyst assigned to trace recipient UPI VPA."
    })
    assert patch1.status_code == 200
    assert patch1.json()["status"] == "INVESTIGATING"
    assert "Analyst assigned" in patch1.json()["notes"]

    # 2. Update to CLOSED
    patch2 = client.patch(f"/api/cases/{case_id}", json={
        "status": "CLOSED",
        "notes": "Mule account frozen in collaboration with partner bank."
    })
    assert patch2.status_code == 200
    assert patch2.json()["status"] == "CLOSED"

    # 3. Invalid status returns 422
    patch_bad = client.patch(f"/api/cases/{case_id}", json={"status": "INVALID_STATUS"})
    assert patch_bad.status_code == 422

    # 4. Non-existent case returns 404
    patch_404 = client.patch("/api/cases/NON_EXISTENT_CASE", json={"status": "CLOSED"})
    assert patch_404.status_code == 404
