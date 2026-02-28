"""Pydantic models for ChainShieldAI API."""

from pydantic import BaseModel


class RiskBreakdown(BaseModel):
    velocity: float
    network_exposure: float
    anomaly: float
    channel_risk: float


class Node(BaseModel):
    id: str
    risk_score: float
    total_sent: float
    total_received: float
    tx_count: int
    channels_used: list[str]
    cluster_id: int
    risk_breakdown: RiskBreakdown


class Edge(BaseModel):
    source: str
    target: str
    amount: float
    channel: str
    timestamp: str
    tx_id: str


class SuspiciousChain(BaseModel):
    path: list[str]
    cumulative_risk: float
    cashout_probability: float  # sourced from ml_placeholder
    channels: list[str]
    is_mock_score: bool = True  # flag indicating ML score is placeholder


class Stats(BaseModel):
    total_transactions: int
    high_risk_accounts: int
    chains_detected: int
    alerts_fired: int
    ml_model_status: dict  # from ml_placeholder.get_model_status()


class GraphSnapshot(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
    suspicious_chains: list[SuspiciousChain]
    stats: Stats
    timestamp: str
