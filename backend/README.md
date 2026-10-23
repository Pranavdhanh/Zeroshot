# UPI Shield AI — Real-Time UPI Fraud Detection & Mule Account Intelligence
**Track 4: FinTech & GovTech Intelligence | VIT College Hackathon**

UPI Shield AI is a real-time, explainable fraud detection and mule account intelligence engine designed for Indian Unified Payments Interface (UPI) ecosystems. It combines behavioral baseline modeling, an ensemble machine learning classifier, and NetworkX directed graph analysis to detect account takeovers, velocity bursts, smurfing, and multi-hop mule layering in under 50 ms.

---

## 1. Architecture Overview

```
Frontend (React + Vite + Tailwind)
          |
          |  HTTP / JSON (CORS enabled on port 5173 / 3000)
          v
FastAPI Backend (backend/main.py)
   ├── Input Validation & Schemas (backend/schemas.py)
   ├── Real-Time Fraud Engine (backend/fraud_engine.py)
   │     ├── Behavioral Baseline (Historical SQLite aggregations)
   │     ├── Graph Feature Extraction (Recipient Network Risk)
   │     ├── ML Classifier (RandomForest / HistGradientBoosting)
   │     └── Explainable Reason Generator & Threshold Classification
   ├── Graph Intelligence Engine (backend/graph_engine.py)
   │     ├── Fan-In Mule Pooling Detection
   │     ├── Fan-Out Dispersal / Smurfing Detection
   │     └── Multi-Hop Rapid Layering Chain Detection
   └── SQLite Database Layer (backend/database.py)
         ├── Persistent Transactions Table
         └── Automatic Case Management (OPEN / INVESTIGATING / CLOSED)
```

---

## 2. API Contract for Frontend Teammate

Base URL: `http://127.0.0.1:8000`

### 2.1 Score Transaction: `POST /api/transactions/score`
**Request Payload:**
```json
{
  "sender_id": "U001",
  "recipient_id": "U009",
  "amount": 15000,
  "timestamp": "2026-10-23T22:30:00",
  "device_changed": true
}
```

**Response Payload:**
```json
{
  "transaction_id": "TX1001",
  "risk_score": 82.0,
  "decision": "HOLD",
  "reasons": [
    "New recipient (no prior payment history)",
    "Amount is unusually high (10.0x sender's historic average)",
    "Unfamiliar device detected",
    "Recipient associated with suspicious graph structure (mule hub or pass-through)"
  ],
  "latency_ms": 18.5
}
```

#### Decision Thresholds:
- **`ALLOW`**: `risk_score < 30` (Payment status: `COMPLETED`)
- **`WARN`**: `30 <= risk_score < 70` (Payment status: `PENDING_VERIFICATION`, flagged as alert)
- **`HOLD`**: `risk_score >= 70` (Payment status: `BLOCKED_ON_HOLD`, auto-opens investigation case)

---

### 2.2 System Health: `GET /health`
Returns server status, active ML model version, and graph intelligence status.

### 2.3 Transactions History: `GET /api/transactions`
- Query parameters: `limit` (default 50), `offset` (default 0), `decision` (ALLOW/WARN/HOLD), `sender_id`, `recipient_id`.
- Returns paginated transaction records.

### 2.4 Dashboard Summary: `GET /api/dashboard/summary`
Returns live metrics derived from SQLite:
```json
{
  "total_transactions": 142,
  "allow_count": 115,
  "warn_count": 18,
  "hold_count": 9,
  "total_volume": 482500.0,
  "flagged_volume": 128400.0,
  "avg_risk_score": 24.6,
  "total_alerts": 27,
  "open_cases_count": 9
}
```

### 2.5 Security Alerts: `GET /api/alerts`
Returns flagged transactions (WARN and HOLD) with severity levels:
- `HOLD` -> `HIGH` severity
- `WARN` -> `MEDIUM` severity

### 2.6 Mule Network Graph: `GET /api/network`
Returns nodes and directed edges formatted for visualization (e.g. Cytoscape.js, D3.js, React Flow):
- **`FAN_IN_AGGREGATOR`**: Accounts pooling funds from multiple senders with low outward flow.
- **`FAN_OUT_DISPERSER`**: Accounts rapidly dispersing funds to multiple new recipients.
- **`CHAIN_MULE`**: Accounts acting as rapid pass-through transit points in layering chains.
- **`NORMAL`**: Standard benign user flow.

### 2.7 Case Management: `GET /api/cases` & `PATCH /api/cases/{case_id}`
- Valid case status values: `OPEN`, `INVESTIGATING`, `CLOSED`.
- Updates case status and investigative notes.

---

## 3. Windows PowerShell Setup & Execution

### Step 1: Install Dependencies
Open Windows PowerShell in the repository root:
```powershell
pip install -r backend/requirements.txt
```

### Step 2: Train Machine Learning Model
Generates reproducible synthetic training data, trains the RandomForest classifier, and saves `backend/models/fraud_model.joblib`:
```powershell
python backend/train_model.py
```

### Step 3: Run Model Evaluation & Latency Benchmarks
Evaluates the model on an independent held-out dataset and computes precision, recall, false positive rate, confusion matrix, and p95 latency:
```powershell
python backend/evaluation.py
```
*Outputs evaluation results and saves `backend/evaluation_report.json`.*

### Step 4: Run Automated Tests
```powershell
pytest -v
```

### Step 5: Start the Backend API Server
```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger Documentation will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 4. How to Regenerate Ignored Artifacts

The repository `.gitignore` safely ignores virtual environments, databases, and model binaries. If cloning fresh:
1. **Regenerate Model Artifact**: Run `python backend/train_model.py`.
2. **Initialize SQLite Database & Demo Graph**: Start the server via `uvicorn backend.main:app --port 8000`. The server automatically creates `data/upi_shield.db` with necessary tables and seed graph nodes.
3. **Regenerate Benchmark Report**: Run `python backend/evaluation.py`.

---

## 5. Disclaimer & Ethics Notice
All account IDs, virtual payment addresses (VPAs), transaction amounts, and behavioral vectors used in this project are synthetically generated for academic demonstration in Track 4 (FinTech & GovTech Intelligence). No real personal, financial, banking, or UPI network data is included or accessed. High evaluation performance on synthetic benchmark data does not constitute proof of real-world operational efficacy.
