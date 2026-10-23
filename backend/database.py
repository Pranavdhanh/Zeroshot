"""
UPI Shield AI — SQLite Persistence Layer
Built using Python's standard library sqlite3 module.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Default database file path
DB_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DB_PATH = str(DB_DIR / "upi_shield.db")


def get_db_path(custom_path: Optional[str] = None) -> str:
    path = custom_path or os.environ.get("UPI_SHIELD_DB_PATH", DEFAULT_DB_PATH)
    parent = Path(path).parent
    parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(db_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """
    Initializes database schema with proper indexes for rapid UPI scoring and retrieval.
    """
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            sender_id TEXT NOT NULL,
            recipient_id TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp TEXT NOT NULL,
            device_changed INTEGER NOT NULL DEFAULT 0,
            channel TEXT NOT NULL DEFAULT 'P2P',
            risk_score REAL NOT NULL,
            decision TEXT NOT NULL CHECK(decision IN ('ALLOW', 'WARN', 'HOLD')),
            reasons TEXT NOT NULL,
            latency_ms REAL NOT NULL,
            payment_status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cases (
            case_id TEXT PRIMARY KEY,
            transaction_id TEXT NOT NULL,
            sender_id TEXT NOT NULL,
            recipient_id TEXT NOT NULL,
            amount REAL NOT NULL,
            risk_score REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('OPEN', 'INVESTIGATING', 'CLOSED')),
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_tx_sender ON transactions(sender_id);
        CREATE INDEX IF NOT EXISTS idx_tx_recipient ON transactions(recipient_id);
        CREATE INDEX IF NOT EXISTS idx_tx_timestamp ON transactions(timestamp);
        CREATE INDEX IF NOT EXISTS idx_tx_decision ON transactions(decision);
        CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
        """)
    conn.close()


def save_transaction(
    tx_data: Dict[str, Any],
    db_path: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    """
    Persists scored transaction to SQLite.
    Rule: WARN and HOLD are not marked as completed payments.
    HOLD decisions automatically open a fraud investigation case.
    Returns: (transaction_id, created_case_id)
    """
    conn = get_connection(db_path)
    tx_id = tx_data["transaction_id"]
    decision = tx_data["decision"]

    # Map decision to payment status
    if decision == "ALLOW":
        payment_status = "COMPLETED"
    elif decision == "WARN":
        payment_status = "PENDING_VERIFICATION"
    else:  # HOLD
        payment_status = "BLOCKED_ON_HOLD"

    reasons_json = json.dumps(tx_data.get("reasons", []))
    now_iso = datetime.utcnow().isoformat()
    created_case_id: Optional[str] = None

    with conn:
        conn.execute(
            """
            INSERT INTO transactions (
                transaction_id, sender_id, recipient_id, amount,
                timestamp, device_changed, channel, risk_score,
                decision, reasons, latency_ms, payment_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tx_id,
                tx_data["sender_id"],
                tx_data["recipient_id"],
                float(tx_data["amount"]),
                tx_data["timestamp"],
                1 if tx_data.get("device_changed") else 0,
                tx_data.get("channel", "P2P"),
                float(tx_data["risk_score"]),
                decision,
                reasons_json,
                float(tx_data["latency_ms"]),
                payment_status,
                now_iso
            )
        )

        # Automatic Case Creation for HOLD (and high-risk WARN >= 50)
        if decision == "HOLD":
            created_case_id = f"CASE-{tx_id}"
            conn.execute(
                """
                INSERT OR IGNORE INTO cases (
                    case_id, transaction_id, sender_id, recipient_id,
                    amount, risk_score, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'OPEN', ?, ?, ?)
                """,
                (
                    created_case_id,
                    tx_id,
                    tx_data["sender_id"],
                    tx_data["recipient_id"],
                    float(tx_data["amount"]),
                    float(tx_data["risk_score"]),
                    f"Auto-generated case for transaction flagged with {decision}. High risk factors detected.",
                    now_iso,
                    now_iso
                )
            )

    conn.close()
    return tx_id, created_case_id


def get_sender_history_stats(
    sender_id: str,
    target_timestamp_str: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculates behavioral baseline features from past recorded transactions:
    - sender's historical average amount
    - known past recipients
    - transactions in the last 10 minutes prior to target_timestamp
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    try:
        if target_timestamp_str:
            target_dt = datetime.fromisoformat(target_timestamp_str)
        else:
            target_dt = datetime.utcnow()
    except Exception:
        target_dt = datetime.utcnow()

    ten_mins_prior = (target_dt - timedelta(minutes=10)).isoformat()
    target_dt_iso = target_dt.isoformat()

    # Past transactions by this sender before current timestamp
    cur.execute(
        """
        SELECT amount, recipient_id, timestamp
        FROM transactions
        WHERE sender_id = ? AND timestamp < ?
        ORDER BY timestamp DESC
        LIMIT 500
        """,
        (sender_id, target_dt_iso)
    )
    rows = cur.fetchall()

    if not rows:
        conn.close()
        return {
            "historical_avg_amount": None,
            "historical_tx_count": 0,
            "known_recipients": set(),
            "transactions_last_10min": 0
        }

    amounts = [r["amount"] for r in rows]
    known_recipients = {r["recipient_id"] for r in rows}
    historical_avg = sum(amounts) / len(amounts)

    # Count transactions in the 10-minute window prior to target_timestamp
    tx_last_10min = sum(1 for r in rows if r["timestamp"] >= ten_mins_prior)

    conn.close()
    return {
        "historical_avg_amount": historical_avg,
        "historical_tx_count": len(rows),
        "known_recipients": known_recipients,
        "transactions_last_10min": tx_last_10min
    }


def get_transactions(
    limit: int = 50,
    offset: int = 0,
    decision: Optional[str] = None,
    sender_id: Optional[str] = None,
    recipient_id: Optional[str] = None,
    db_path: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Retrieves transactions from SQLite with filtering and pagination.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    query = "SELECT * FROM transactions WHERE 1=1"
    count_query = "SELECT COUNT(*) as total FROM transactions WHERE 1=1"
    params: List[Any] = []

    if decision:
        query += " AND decision = ?"
        count_query += " AND decision = ?"
        params.append(decision.upper())
    if sender_id:
        query += " AND sender_id = ?"
        count_query += " AND sender_id = ?"
        params.append(sender_id)
    if recipient_id:
        query += " AND recipient_id = ?"
        count_query += " AND recipient_id = ?"
        params.append(recipient_id)

    cur.execute(count_query, params)
    total = cur.fetchone()["total"]

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cur.execute(query, params)
    rows = cur.fetchall()

    records = []
    for r in rows:
        d = dict(r)
        d["device_changed"] = bool(d["device_changed"])
        try:
            d["reasons"] = json.loads(d["reasons"])
        except Exception:
            d["reasons"] = []
        records.append(d)

    conn.close()
    return records, total


def get_dashboard_summary(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Derives live dashboard metrics from stored SQLite transactions and cases.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) as total_count,
            SUM(CASE WHEN decision = 'ALLOW' THEN 1 ELSE 0 END) as allow_count,
            SUM(CASE WHEN decision = 'WARN' THEN 1 ELSE 0 END) as warn_count,
            SUM(CASE WHEN decision = 'HOLD' THEN 1 ELSE 0 END) as hold_count,
            COALESCE(SUM(amount), 0) as total_volume,
            COALESCE(SUM(CASE WHEN decision IN ('WARN', 'HOLD') THEN amount ELSE 0 END), 0) as flagged_volume,
            COALESCE(AVG(risk_score), 0) as avg_risk_score
        FROM transactions
    """)
    tx_agg = cur.fetchone()

    cur.execute("SELECT COUNT(*) as open_cases FROM cases WHERE status IN ('OPEN', 'INVESTIGATING')")
    cases_agg = cur.fetchone()

    allow_count = tx_agg["allow_count"] or 0
    warn_count = tx_agg["warn_count"] or 0
    hold_count = tx_agg["hold_count"] or 0
    total_alerts = warn_count + hold_count

    summary = {
        "total_transactions": tx_agg["total_count"] or 0,
        "allow_count": allow_count,
        "warn_count": warn_count,
        "hold_count": hold_count,
        "total_volume": round(float(tx_agg["total_volume"] or 0), 2),
        "flagged_volume": round(float(tx_agg["flagged_volume"] or 0), 2),
        "avg_risk_score": round(float(tx_agg["avg_risk_score"] or 0), 1),
        "total_alerts": total_alerts,
        "open_cases_count": cases_agg["open_cases"] or 0
    }

    conn.close()
    return summary


def get_alerts(
    limit: int = 50,
    offset: int = 0,
    db_path: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Treats WARN and HOLD as security alerts with severity levels:
    - HOLD -> HIGH severity
    - WARN -> MEDIUM severity
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as total FROM transactions WHERE decision IN ('WARN', 'HOLD')")
    total = cur.fetchone()["total"]

    cur.execute("""
        SELECT t.*, c.case_id
        FROM transactions t
        LEFT JOIN cases c ON t.transaction_id = c.transaction_id
        WHERE t.decision IN ('WARN', 'HOLD')
        ORDER BY t.timestamp DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    rows = cur.fetchall()

    alerts = []
    for r in rows:
        d = dict(r)
        try:
            reasons = json.loads(d["reasons"])
        except Exception:
            reasons = []

        severity = "HIGH" if d["decision"] == "HOLD" else "MEDIUM"
        alerts.append({
            "alert_id": f"ALT-{d['transaction_id']}",
            "transaction_id": d["transaction_id"],
            "sender_id": d["sender_id"],
            "recipient_id": d["recipient_id"],
            "amount": d["amount"],
            "risk_score": d["risk_score"],
            "decision": d["decision"],
            "severity": severity,
            "reasons": reasons,
            "timestamp": d["timestamp"],
            "case_id": d.get("case_id")
        })

    conn.close()
    return alerts, total


def get_all_edges_for_graph(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extracts directed edges from stored transactions for graph intelligence.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("""
        SELECT sender_id, recipient_id, amount, timestamp, decision, risk_score
        FROM transactions
        ORDER BY timestamp ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_cases(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db_path: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Lists fraud cases with optional status filter.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    count_q = "SELECT COUNT(*) as total FROM cases WHERE 1=1"
    q = "SELECT * FROM cases WHERE 1=1"
    params: List[Any] = []

    if status:
        count_q += " AND status = ?"
        q += " AND status = ?"
        params.append(status.upper())

    cur.execute(count_q, params)
    total = cur.fetchone()["total"]

    q += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows], total


def update_case(
    case_id: str,
    status: str,
    notes: Optional[str] = None,
    db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Updates case status and notes.
    Validates status against permitted values ('OPEN', 'INVESTIGATING', 'CLOSED').
    Never silently claims an update succeeded if no rows were modified.
    """
    valid_statuses = {"OPEN", "INVESTIGATING", "CLOSED"}
    upper_status = status.upper()
    if upper_status not in valid_statuses:
        raise ValueError(f"Invalid status '{status}'. Must be one of {valid_statuses}")

    conn = get_connection(db_path)
    cur = conn.cursor()
    now_iso = datetime.utcnow().isoformat()
    rowcount = 0

    with conn:
        if notes is not None:
            cur.execute("""
                UPDATE cases
                SET status = ?, notes = ?, updated_at = ?
                WHERE case_id = ?
            """, (upper_status, notes, now_iso, case_id))
        else:
            cur.execute("""
                UPDATE cases
                SET status = ?, updated_at = ?
                WHERE case_id = ?
            """, (upper_status, now_iso, case_id))
        rowcount = cur.rowcount

    if rowcount == 0:
        conn.close()
        return None

    cur.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    updated_row = cur.fetchone()
    conn.close()
    return dict(updated_row) if updated_row else None
