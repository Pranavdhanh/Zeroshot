"""
UPI Shield AI — Real-Time UPI Fraud Detection & Mule Intelligence API
Track 4: FinTech & GovTech Intelligence
"""

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import time
import uuid
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, Path as FastPath, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from schemas import (
    TransactionScoreRequest,
    TransactionScoreResponse,
    TransactionsListResponse,
    DashboardSummary,
    AlertRecord,
    NetworkGraphResponse,
    CaseRecord,
    CaseUpdateRequest
)
import database
from fraud_engine import fraud_engine
from graph_engine import graph_engine
from data_generator import generate_network_seed_data

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("upi_shield.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup & shutdown events:
    - Initializes SQLite database schema & indexes
    - Loads the ML model once at startup (not per transaction)
    - Seeds deterministic graph scenario if database is fresh
    """
    logger.info("[*] Starting UPI Shield AI Backend...")
    database.init_db()

    # Load ML model once
    fraud_engine.load_model()

    # Check if network edges exist; if not, populate deterministic demo network
    existing_edges = database.get_all_edges_for_graph()
    if len(existing_edges) < 5:
        logger.info("[*] Seeding deterministic graph intelligence scenario for hackathon demo...")
        seed_data = generate_network_seed_data(random_seed=42)
        for edge_tx in seed_data:
            tx_id = f"TX_SEED_{uuid.uuid4().hex[:8].upper()}"
            database.save_transaction({
                "transaction_id": tx_id,
                "sender_id": edge_tx["sender_id"],
                "recipient_id": edge_tx["recipient_id"],
                "amount": edge_tx["amount"],
                "timestamp": edge_tx["timestamp"],
                "device_changed": False,
                "channel": "P2P",
                "risk_score": edge_tx["risk_score"],
                "decision": edge_tx["decision"],
                "reasons": ["Seeded graph pattern for demonstration"],
                "latency_ms": 1.5
            })
        existing_edges = database.get_all_edges_for_graph()

    # Build graph and analyze mule structures
    graph_engine.build_graph_from_transactions(existing_edges)
    graph_engine.detect_mule_patterns()
    logger.info(f"[OK] Network graph initialized with {len(graph_engine.G.nodes)} nodes and {len(graph_engine.G.edges)} edges.")

    yield
    logger.info("[*] Shutting down UPI Shield AI Backend.")


app = FastAPI(
    title="UPI Shield AI Backend",
    description="Real-Time UPI Fraud Detection & Mule Account Intelligence API (Track 4: FinTech & GovTech)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration for local React + Vite + Tailwind frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler for request validation (sanitizes output, no raw traceback)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        errors.append(f"{field}: {msg}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error in request payload", "errors": errors}
    )


# Generic exception handler preventing internal traceback leaks
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}", exc_info=False)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred during transaction processing."}
    )


# --- HEALTH ENDPOINT ---
@app.get("/health", tags=["System"])
def health_check():
    """
    Returns system status, active ML model info, and SQLite database health.
    """
    return {
        "status": "healthy",
        "service": "UPI Shield AI -- Fraud Detection & Mule Intelligence",
        "timestamp": datetime.utcnow().isoformat(),
        "model_status": {
            "loaded": fraud_engine.is_ml_loaded,
            "engine": "Machine Learning (RandomForest)" if fraud_engine.is_ml_loaded else "Heuristic Fallback Engine",
            "metadata": fraud_engine.model_metadata
        },
        "graph_intelligence": {
            "total_nodes": len(graph_engine.G.nodes),
            "total_edges": len(graph_engine.G.edges)
        }
    }


# --- TRANSACTION SCORING ENDPOINT (FRONTEND CONTRACT) ---
@app.post(
    "/api/transactions/score",
    response_model=TransactionScoreResponse,
    status_code=status.HTTP_200_OK,
    tags=["Scoring"]
)
def score_transaction(payload: TransactionScoreRequest):
    """
    Scores an incoming UPI transaction in real-time (< 200 ms target).
    
    1. Extracts behavioural & graph network features
    2. Runs inference using trained ML classifier (or deterministic fallback)
    3. Categorizes decision into ALLOW (<30), WARN (30-69), or HOLD (>=70)
    4. Automatically stores record in SQLite
    5. Returns stable transaction reference, risk score, decision, and reasons
    """
    tx_timestamp = payload.timestamp or datetime.utcnow().isoformat()
    # Generate stable unique transaction identifier
    tx_id = f"TX{int(time.time() * 1000) % 1000000:06d}"

    # Perform real-time scoring
    score_result = fraud_engine.score_transaction(
        sender_id=payload.sender_id,
        recipient_id=payload.recipient_id,
        amount=payload.amount,
        timestamp_str=tx_timestamp,
        device_changed=bool(payload.device_changed),
        simulated_overrides=payload.simulated_features
    )

    # Persist in SQLite
    record_to_save = {
        "transaction_id": tx_id,
        "sender_id": payload.sender_id,
        "recipient_id": payload.recipient_id,
        "amount": payload.amount,
        "timestamp": tx_timestamp,
        "device_changed": bool(payload.device_changed),
        "channel": payload.channel or "P2P",
        "risk_score": score_result["risk_score"],
        "decision": score_result["decision"],
        "reasons": score_result["reasons"],
        "latency_ms": score_result["latency_ms"]
    }
    database.save_transaction(record_to_save)

    # Update graph engine live with the new edge
    graph_engine.build_graph_from_transactions([{
        "sender_id": payload.sender_id,
        "recipient_id": payload.recipient_id,
        "amount": payload.amount,
        "timestamp": tx_timestamp,
        "risk_score": score_result["risk_score"]
    }])
    graph_engine.detect_mule_patterns()

    return TransactionScoreResponse(
        transaction_id=tx_id,
        risk_score=score_result["risk_score"],
        decision=score_result["decision"],
        reasons=score_result["reasons"],
        latency_ms=score_result["latency_ms"]
    )


# --- TRANSACTIONS LIST & FILTERING ---
@app.get(
    "/api/transactions",
    response_model=TransactionsListResponse,
    tags=["Transactions"]
)
def list_transactions(
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    decision: Optional[str] = Query(None, description="Filter by decision: ALLOW, WARN, HOLD"),
    sender_id: Optional[str] = Query(None, description="Filter by sender ID"),
    recipient_id: Optional[str] = Query(None, description="Filter by recipient ID")
):
    """
    Lists stored transactions from SQLite with optional filtering and pagination.
    """
    items, total = database.get_transactions(
        limit=limit,
        offset=offset,
        decision=decision,
        sender_id=sender_id,
        recipient_id=recipient_id
    )
    return TransactionsListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )


# --- DASHBOARD SUMMARY ENDPOINT ---
@app.get(
    "/api/dashboard/summary",
    response_model=DashboardSummary,
    tags=["Dashboard"]
)
def get_dashboard_summary():
    """
    Returns real-time dashboard aggregates derived directly from stored SQLite records.
    """
    summary = database.get_dashboard_summary()
    return DashboardSummary(**summary)


# --- ALERTS ENDPOINT ---
@app.get(
    "/api/alerts",
    response_model=List[AlertRecord],
    tags=["Alerts"]
)
def get_alerts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    Retrieves security alerts (all transactions flagged with WARN or HOLD).
    HOLD is treated as HIGH severity, WARN as MEDIUM severity.
    """
    alerts, _ = database.get_alerts(limit=limit, offset=offset)
    return [AlertRecord(**a) for a in alerts]


# --- NETWORK GRAPH & MULE DETECTION ENDPOINT ---
@app.get(
    "/api/network",
    response_model=NetworkGraphResponse,
    tags=["Network Intelligence"]
)
def get_network_graph():
    """
    Returns the directed transaction network graph with identified mule roles:
    - FAN_IN_AGGREGATOR: Mule pooling accounts
    - FAN_OUT_DISPERSER: Smurfing / dispersal accounts
    - CHAIN_MULE: Multi-hop rapid pass-through layering accounts
    - NORMAL: Verified standard user flow
    """
    # Re-read edges from database to ensure up-to-date visualization
    all_edges = database.get_all_edges_for_graph()
    graph_engine.build_graph_from_transactions(all_edges)
    nodes, edges = graph_engine.detect_mule_patterns()

    mule_count = sum(1 for n in nodes if n["is_mule"])

    return NetworkGraphResponse(
        nodes=nodes,
        edges=edges,
        mule_count=mule_count,
        total_nodes=len(nodes),
        total_edges=len(edges)
    )


# --- CASE MANAGEMENT ENDPOINTS ---
@app.get(
    "/api/cases",
    response_model=List[CaseRecord],
    tags=["Case Management"]
)
def list_cases(
    status: Optional[str] = Query(None, description="Filter by status: OPEN, INVESTIGATING, CLOSED"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    Lists fraud investigation cases opened from high-risk HOLD alerts.
    """
    cases, _ = database.get_cases(status=status, limit=limit, offset=offset)
    return [CaseRecord(**c) for c in cases]


@app.patch(
    "/api/cases/{case_id}",
    response_model=CaseRecord,
    tags=["Case Management"]
)
def update_case_status(
    case_id: str = FastPath(..., description="Unique Case ID"),
    payload: CaseUpdateRequest = ...
):
    """
    Updates the investigation status of a fraud case (OPEN, INVESTIGATING, CLOSED).
    Returns 404 if case does not exist. Never silently claims successful update.
    """
    try:
        updated = database.update_case(
            case_id=case_id,
            status=payload.status,
            notes=payload.notes
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID '{case_id}' was not found in the database."
        )

    return CaseRecord(**updated)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
