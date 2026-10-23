"""
FastAPI application for Real-Time UPI Fraud Alert System.

Provides:
  - REST API: /api/score, /api/metrics, /api/cases, /api/config, /api/network
  - WebSocket: /ws/alerts (live transaction alert streaming)
  - Static Web UI: Analyst Dashboard & Phone Warning Simulator
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from service.scorer import RealTimeScorer
from decision.config import DecisionConfig
from decision.engine import CostDecisionEngine

app = FastAPI(title="Real-Time UPI Fraud Alert System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core scoring engine
scorer = RealTimeScorer()

# In-memory case management store
cases_db: List[Dict[str, Any]] = []

# Live metrics tracking
stats = {
    "total_scored": 0,
    "total_alerts": 0,
    "fraud_prevented_inr": 0.0,
    "genuine_friction_count": 0,
    "start_time": time.time(),
}

# WebSocket connections registry
active_connections: List[WebSocket] = []

# Background stream control
stream_task: Optional[asyncio.Task] = None
is_streaming: bool = False
stream_speed_tps: int = 10


class TransactionPayload(BaseModel):
    txn_id: Optional[str] = "TXN_LIVE"
    timestamp: Optional[str] = None
    sender_id: str = "U000001"
    sender_vpa: str = "user000001@upi"
    receiver_vpa: str = "mule0001@upi"
    amount: float = 25000.0
    is_collect_request: bool = False
    is_merchant_txn: bool = False
    call_active_flag: bool = False
    screen_share_active: bool = False
    new_device_flag: bool = False
    new_city_flag: bool = False
    sim_swap_flag: bool = False
    sender_city: str = "Chennai"
    sender_device: str = "Android"
    is_senior: bool = False


class CaseUpdate(BaseModel):
    status: str  # OPEN, IN_INVESTIGATION, CONFIRMED_FRAUD, FALSE_POSITIVE
    analyst_notes: Optional[str] = ""
    assigned_to: Optional[str] = "Analyst-1"


class ConfigUpdate(BaseModel):
    cost_warn_friction: float
    cost_hold_friction: float
    warn_effectiveness: float
    min_prob_warn: float
    min_prob_hold: float
    senior_protection_multiplier: float


@app.post("/api/score")
async def score_transaction(payload: TransactionPayload):
    """Score a single incoming UPI payment in real time."""
    txn_dict = payload.model_dump()
    if not txn_dict.get("timestamp"):
        txn_dict["timestamp"] = datetime.now().isoformat()

    result = scorer.score_transaction(txn_dict)

    # Update global metrics
    stats["total_scored"] += 1
    if result["action"] in ["WARN", "HOLD"]:
        stats["total_alerts"] += 1
        stats["fraud_prevented_inr"] += result["amount"]

        # Automatically open a case if not already exists
        case_id = f"CASE-{len(cases_db) + 1:04d}"
        case_record = {
            "case_id": case_id,
            "txn_id": result["txn_id"],
            "timestamp": result["timestamp"],
            "sender_vpa": result["sender_vpa"],
            "receiver_vpa": result["receiver_vpa"],
            "amount": result["amount"],
            "action": result["action"],
            "risk_score": result["risk_score"],
            "status": "OPEN",
            "typology_guess": result["fraud_typology_guess"],
            "analyst_notes": "",
            "assigned_to": "Unassigned",
        }
        cases_db.insert(0, case_record)
        if len(cases_db) > 200:
            cases_db.pop()

        # Broadcast alert to all connected analyst dashboards
        await broadcast_alert(result)

    return result


async def broadcast_alert(alert_data: Dict[str, Any]):
    """Send alert JSON over WebSocket to connected dashboard clients."""
    disconnected = []
    for ws in active_connections:
        try:
            await ws.send_json(alert_data)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in active_connections:
            active_connections.remove(ws)


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for live analyst alert feed."""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keepalive listener
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.get("/api/metrics")
async def get_metrics():
    """Return live latency percentiles, throughput, and financial metrics."""
    latency = scorer.get_latency_stats()
    uptime_sec = max(1.0, time.time() - stats["start_time"])
    alerts_per_min = (stats["total_alerts"] / uptime_sec) * 60.0

    return {
        "p50_latency_ms": round(latency["p50"], 2),
        "p95_latency_ms": round(latency["p95"], 2),
        "p99_latency_ms": round(latency["p99"], 2),
        "total_scored": stats["total_scored"],
        "total_alerts": stats["total_alerts"],
        "alerts_per_minute": round(alerts_per_min, 1),
        "fraud_prevented_inr": round(stats["fraud_prevented_inr"], 0),
        "genuine_friction_count": stats["genuine_friction_count"],
        "is_streaming": is_streaming,
        "stream_speed_tps": stream_speed_tps,
    }


@app.get("/api/cases")
async def list_cases():
    """Return all analyst cases."""
    return cases_db


@app.post("/api/cases/{case_id}")
async def update_case(case_id: str, update: CaseUpdate):
    """Update case status, notes, or assignment."""
    for case in cases_db:
        if case["case_id"] == case_id:
            case["status"] = update.status
            if update.analyst_notes:
                case["analyst_notes"] = update.analyst_notes
            if update.assigned_to:
                case["assigned_to"] = update.assigned_to

            # If confirmed fraud, flag receiver in graph engine live!
            if update.status == "CONFIRMED_FRAUD":
                scorer.graph_engine.flag_account(case["receiver_vpa"], datetime.now())

            return {"success": True, "case": case}
    raise HTTPException(status_code=404, detail="Case not found")


@app.get("/api/config")
async def get_config():
    """Get active decision configuration."""
    return scorer.decision_config.__dict__


@app.post("/api/config")
async def update_config(update: ConfigUpdate):
    """Live update decision thresholds and friction penalties from dashboard slider."""
    cfg = scorer.decision_config
    cfg.cost_warn_friction = update.cost_warn_friction
    cfg.cost_hold_friction = update.cost_hold_friction
    cfg.warn_effectiveness = update.warn_effectiveness
    cfg.min_prob_warn = update.min_prob_warn
    cfg.min_prob_hold = update.min_prob_hold
    cfg.senior_protection_multiplier = update.senior_protection_multiplier
    scorer.decision_engine.config = cfg
    return {"success": True, "config": cfg.__dict__}


@app.get("/api/network/subgraph")
async def get_subgraph(vpa: Optional[str] = None):
    """
    Return nodes and edges around flagged accounts or a specific VPA
    formatted for Cytoscape.js network visualization.
    """
    target_nodes = set()
    if vpa and vpa in scorer.graph_engine.accounts:
        target_nodes.add(vpa)
        # Add 1-hop and 2-hop neighbors
        for n1 in scorer.graph_engine.adjacency.get(vpa, set()):
            target_nodes.add(n1)
    else:
        # Default: all flagged accounts + their direct neighbors
        flagged = scorer.graph_engine.flagged_accounts
        target_nodes.update(flagged)
        for f in list(flagged)[:20]:
            target_nodes.update(list(scorer.graph_engine.adjacency.get(f, set()))[:5])

    # If empty, seed from active accounts
    if len(target_nodes) == 0:
        for acc in list(scorer.graph_engine.accounts.keys())[:30]:
            target_nodes.add(acc)

    elements = []
    nodes_included = set()

    for node in target_nodes:
        if node in scorer.graph_engine.accounts:
            acc = scorer.graph_engine.accounts[node]
            is_flagged = node in scorer.graph_engine.flagged_accounts
            is_mule = "mule" in node.lower()

            if is_flagged:
                node_type = "flagged"
            elif is_mule:
                node_type = "mule"
            elif "merchant" in node.lower():
                node_type = "merchant"
            else:
                node_type = "user"

            elements.append({
                "data": {
                    "id": node,
                    "label": node.split("@")[0],
                    "type": node_type,
                    "in_degree": acc.in_degree,
                    "out_degree": acc.out_degree,
                    "community": acc.community_id,
                }
            })
            nodes_included.add(node)

    # Edges between included nodes
    for src in nodes_included:
        for dst in scorer.graph_engine.adjacency.get(src, set()):
            if dst in nodes_included and src < dst:
                elements.append({
                    "data": {
                        "id": f"{src}->{dst}",
                        "source": src,
                        "target": dst,
                    }
                })

    return {"elements": elements}


async def _stream_worker():
    """Background task reading test parquet transactions and scoring them."""
    global is_streaming
    try:
        df = pd.read_parquet("data/transactions.parquet")
        # Filter to fraud + genuine mix from test portion
        test_txns = df.tail(10000).to_dict("records")
        idx = 0

        while is_streaming:
            txn = test_txns[idx % len(test_txns)]
            idx += 1

            # Score and broadcast if alert
            score_res = scorer.score_transaction(txn)
            stats["total_scored"] += 1

            if score_res["action"] in ["WARN", "HOLD"]:
                stats["total_alerts"] += 1
                stats["fraud_prevented_inr"] += score_res["amount"]

                case_id = f"CASE-{len(cases_db) + 1:04d}"
                case_record = {
                    "case_id": case_id,
                    "txn_id": score_res["txn_id"],
                    "timestamp": score_res["timestamp"],
                    "sender_vpa": score_res["sender_vpa"],
                    "receiver_vpa": score_res["receiver_vpa"],
                    "amount": score_res["amount"],
                    "action": score_res["action"],
                    "risk_score": score_res["risk_score"],
                    "status": "OPEN",
                    "typology_guess": score_res["fraud_typology_guess"],
                    "analyst_notes": "",
                    "assigned_to": "Unassigned",
                }
                cases_db.insert(0, case_record)
                if len(cases_db) > 200:
                    cases_db.pop()

                await broadcast_alert(score_res)

            sleep_duration = 1.0 / max(1, stream_speed_tps)
            await asyncio.sleep(sleep_duration)

    except asyncio.CancelledError:
        pass
    finally:
        is_streaming = False


@app.post("/api/stream/start")
async def start_stream(speed_tps: int = 15):
    """Start live transaction streaming."""
    global is_streaming, stream_task, stream_speed_tps
    if not is_streaming:
        is_streaming = True
        stream_speed_tps = speed_tps
        stream_task = asyncio.create_task(_stream_worker())
    return {"status": "started", "tps": stream_speed_tps}


@app.post("/api/stream/stop")
async def stop_stream():
    """Stop transaction streaming."""
    global is_streaming, stream_task
    if is_streaming and stream_task:
        is_streaming = False
        stream_task.cancel()
        stream_task = None
    return {"status": "stopped"}


# Serve static web frontend
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """Redirect to analyst dashboard."""
    dashboard_html = os.path.join(static_dir, "index.html")
    if os.path.exists(dashboard_html):
        with open(dashboard_html, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return {"message": "Analyst Dashboard running. Static assets in /frontend."}


@app.get("/phone")
async def phone_view():
    """Render simulated mobile payment app screen."""
    phone_html = os.path.join(static_dir, "phone.html")
    if os.path.exists(phone_html):
        with open(phone_html, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return {"message": "Phone simulator in /frontend/phone.html"}
