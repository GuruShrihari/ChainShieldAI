/**
 * TypeScript type definitions for ChainShieldAI.
 * Mirrors backend Pydantic models exactly.
 */

export interface RiskBreakdown {
    velocity: number;
    network_exposure: number;
    anomaly: number;
    channel_risk: number;
}

export interface GraphNode {
    id: string;
    risk_score: number;
    total_sent: number;
    total_received: number;
    tx_count: number;
    channels_used: string[];
    cluster_id: number;
    risk_breakdown: RiskBreakdown;
}

export interface GraphEdge {
    source: string;
    target: string;
    amount: number;
    channel: string;
    timestamp: string;
    tx_id: string;
}

export interface SuspiciousChain {
    path: string[];
    cumulative_risk: number;
    cashout_probability: number;
    channels: string[];
    is_mock_score: boolean;
}

export interface MLModelStatus {
    status: 'pending' | 'active' | 'error';
    version: string | null;
    accuracy: number | null;
    message: string;
}

export interface Stats {
    total_transactions: number;
    high_risk_accounts: number;
    chains_detected: number;
    alerts_fired: number;
    ml_model_status: MLModelStatus;
}

export interface GraphSnapshot {
    nodes: GraphNode[];
    edges: GraphEdge[];
    suspicious_chains: SuspiciousChain[];
    stats: Stats;
    timestamp: string;
}

export interface TransactionResponse {
    status: string;
    transaction: Transaction;
    transaction_number: number;
    total_transactions: number;
    snapshot: GraphSnapshot;
}

export interface Transaction {
    tx_id: string;
    from_account: string;
    to_account: string;
    amount: number;
    channel: string;
    timestamp: string;
    location: string;
}

export type AlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL';

export interface AlertItem {
    id: string;
    timestamp: string;
    severity: AlertSeverity;
    type: string;
    details: string;
    risk: number;
    createdAt: number;
}

export type ChannelFilter = 'ALL' | 'MOBILE' | 'WALLET' | 'ATM' | 'BANK';

/** ForceGraph node data shape for react-force-graph-2d */
export interface ForceGraphNode {
    id: string;
    risk_score: number;
    total_sent: number;
    total_received: number;
    tx_count: number;
    channels_used: string[];
    cluster_id: number;
    risk_breakdown: RiskBreakdown;
    x?: number;
    y?: number;
    vx?: number;
    vy?: number;
}

/** ForceGraph link data shape for react-force-graph-2d */
export interface ForceGraphLink {
    source: string | ForceGraphNode;
    target: string | ForceGraphNode;
    amount: number;
    channel: string;
    timestamp: string;
    tx_id: string;
}
