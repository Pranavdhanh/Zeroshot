"""
UPI Shield AI — Data Schemas and Validation Contracts
Track 4: FinTech & GovTech Intelligence
"""

from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


# --- Configuration & Thresholds ---
# Single source of truth for decision thresholds
THRESHOLD_ALLOW_MAX = 30.0  # < 30 is ALLOW
THRESHOLD_WARN_MAX = 70.0   # 30 to < 70 is WARN, >= 70 is HOLD


DecisionType = Literal["ALLOW", "WARN", "HOLD"]
CaseStatusType = Literal["OPEN", "INVESTIGATING", "CLOSED"]
SeverityType = Literal["LOW", "MEDIUM", "HIGH"]


class TransactionScoreRequest(BaseModel):
    """
    Frontend contract for POST /api/transactions/score
    """
    sender_id: str = Field(..., min_length=1, description="Unique identifier for the sender account / UPI ID")
    recipient_id: str = Field(..., min_length=1, description="Unique identifier for the recipient account / VPA")
    amount: float = Field(..., gt=0, description="Transaction amount in INR, must be strictly greater than 0")
    timestamp: Optional[str] = Field(None, description="ISO format timestamp (e.g. 2026-10-23T22:30:00). Defaults to current time")
    device_changed: Optional[bool] = Field(False, description="Flag indicating if transaction originates from a new or unfamiliar device")
    channel: Optional[str] = Field("P2P", description="UPI Channel / context: P2P, P2M, QR_SCAN, COLLECT")
    note: Optional[str] = Field(None, description="Optional user note / remark")
    simulated_features: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional simulation feature overrides for testing specific attack vectors"
    )

    @field_validator("sender_id", "recipient_id")
    @classmethod
    def strip_and_validate_ids(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Account ID cannot be empty or blank")
        return cleaned

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be strictly positive (> 0)")
        if v > 10_000_000:
            raise ValueError("Amount exceeds maximum permitted single UPI limit of 10,000,000")
        return round(float(v), 2)

    @model_validator(mode="after")
    def check_distinct_parties(self):
        if self.sender_id == self.recipient_id:
            raise ValueError("Sender and recipient cannot be the same account")
        return self


class TransactionScoreResponse(BaseModel):
    """
    Frontend contract returned by POST /api/transactions/score
    """
    transaction_id: str = Field(..., description="Stable unique transaction reference ID (e.g. TX1001)")
    risk_score: float = Field(..., ge=0, le=100, description="Fraud probability score from 0 to 100")
    decision: DecisionType = Field(..., description="Actionable decision: ALLOW, WARN, or HOLD")
    reasons: List[str] = Field(default_factory=list, description="Human-readable explainability factor list")
    latency_ms: float = Field(..., description="Actual server-side scoring duration in milliseconds")


class TransactionRecord(BaseModel):
    """
    Full transaction record stored in database and returned in GET /api/transactions
    """
    transaction_id: str
    sender_id: str
    recipient_id: str
    amount: float
    timestamp: str
    device_changed: bool
    channel: str
    risk_score: float
    decision: DecisionType
    reasons: List[str]
    latency_ms: float
    payment_status: str  # COMPLETED for ALLOW, PENDING_VERIFICATION for WARN, BLOCKED_ON_HOLD for HOLD
    created_at: str


class TransactionsListResponse(BaseModel):
    items: List[TransactionRecord]
    total: int
    limit: int
    offset: int


class DashboardSummary(BaseModel):
    total_transactions: int
    allow_count: int
    warn_count: int
    hold_count: int
    total_volume: float
    flagged_volume: float
    avg_risk_score: float
    total_alerts: int
    open_cases_count: int


class AlertRecord(BaseModel):
    alert_id: str
    transaction_id: str
    sender_id: str
    recipient_id: str
    amount: float
    risk_score: float
    decision: DecisionType
    severity: SeverityType
    reasons: List[str]
    timestamp: str
    case_id: Optional[str] = None


class NetworkNode(BaseModel):
    id: str
    label: str
    role: str  # NORMAL, FAN_IN_AGGREGATOR, FAN_OUT_DISPERSER, CHAIN_MULE, HIGH_RISK
    risk_score: float
    in_degree: int
    out_degree: int
    total_in: float
    total_out: float
    is_mule: bool
    reasons: List[str]


class NetworkEdge(BaseModel):
    source: str
    target: str
    amount: float
    count: int
    last_timestamp: str


class NetworkGraphResponse(BaseModel):
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    mule_count: int
    total_nodes: int
    total_edges: int


class CaseRecord(BaseModel):
    case_id: str
    transaction_id: str
    sender_id: str
    recipient_id: str
    amount: float
    risk_score: float
    status: CaseStatusType
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class CaseUpdateRequest(BaseModel):
    status: CaseStatusType
    notes: Optional[str] = None
