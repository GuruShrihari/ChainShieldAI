/**
 * useGraphData hook for ChainShieldAI.
 *
 * Wraps useWebSocket + REST fallback. Provides graph data,
 * stats, alerts, and control functions.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import axios from 'axios';
import type {
    AlertItem,
    AlertSeverity,
    GraphSnapshot,
    Stats,
} from '../types';
import { useWebSocket } from './useWebSocket';
import { getRiskLabel } from '../utils/riskColors';

const API_BASE = 'http://localhost:8000';

interface UseGraphDataReturn {
    graphData: GraphSnapshot | null;
    stats: Stats | null;
    alerts: AlertItem[];
    isConnected: boolean;
    isLoading: boolean;
    nextTransaction: () => Promise<void>;
    resetGraph: () => Promise<void>;
    allProcessed: boolean;
}

let alertCounter = 0;

function generateAlertId(): string {
    alertCounter += 1;
    return `alert-${Date.now()}-${alertCounter}`;
}

export function useGraphData(): UseGraphDataReturn {
    const { graphData: wsData, isConnected } = useWebSocket();
    const [graphData, setGraphData] = useState<GraphSnapshot | null>(null);
    const [stats, setStats] = useState<Stats | null>(null);
    const [alerts, setAlerts] = useState<AlertItem[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [allProcessed, setAllProcessed] = useState(false);
    const prevHighRiskRef = useRef<Set<string>>(new Set());

    // Update from WebSocket data
    useEffect(() => {
        if (wsData) {
            setGraphData(wsData);
            setStats(wsData.stats);
            processNewAlerts(wsData);
        }
    }, [wsData]);

    const processNewAlerts = useCallback(
        (snapshot: GraphSnapshot) => {
            const currentHighRisk = new Set(
                snapshot.nodes
                    .filter((n) => n.risk_score >= 6.0)
                    .map((n) => n.id)
            );

            // Find newly high-risk nodes
            const newHighRisk = [...currentHighRisk].filter(
                (id) => !prevHighRiskRef.current.has(id)
            );
            prevHighRiskRef.current = currentHighRisk;

            const newAlerts: AlertItem[] = [];
            const now = Date.now();

            for (const nodeId of newHighRisk) {
                const node = snapshot.nodes.find((n) => n.id === nodeId);
                if (!node) continue;

                const severity: AlertSeverity =
                    node.risk_score >= 8 ? 'CRITICAL' : node.risk_score >= 6 ? 'WARNING' : 'INFO';

                const riskLabel = getRiskLabel(node.risk_score);

                newAlerts.push({
                    id: generateAlertId(),
                    timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
                    severity,
                    type: `${riskLabel}_RISK_DETECTED`,
                    details: `Account ${nodeId} risk elevated to ${node.risk_score.toFixed(1)}`,
                    risk: node.risk_score,
                    createdAt: now,
                });
            }

            // Add chain detection alerts
            for (const chain of snapshot.suspicious_chains) {
                if (chain.cumulative_risk > 15) {
                    newAlerts.push({
                        id: generateAlertId(),
                        timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
                        severity: 'CRITICAL',
                        type: 'MULE_CHAIN_DETECTED',
                        details: `Chain: ${chain.path.join(' → ')} | Cum. Risk: ${chain.cumulative_risk.toFixed(1)}`,
                        risk: chain.cumulative_risk,
                        createdAt: now,
                    });
                }
            }

            if (newAlerts.length > 0) {
                setAlerts((prev) => {
                    const combined = [...prev, ...newAlerts];
                    // Keep max 50 alerts
                    return combined.slice(-50);
                });
            }
        },
        []
    );

    const nextTransaction = useCallback(async () => {
        setIsLoading(true);
        try {
            const response = await axios.post<{
                status: string;
                snapshot: GraphSnapshot;
                transaction_number?: number;
                total_transactions?: number;
            }>(`${API_BASE}/api/next-transaction`);

            if (response.data.status === 'complete') {
                setAllProcessed(true);
            }

            if (response.data.snapshot) {
                setGraphData(response.data.snapshot);
                setStats(response.data.snapshot.stats);
                processNewAlerts(response.data.snapshot);
            }
        } catch {
            // Network error: will retry via WebSocket reconnect
        } finally {
            setIsLoading(false);
        }
    }, [processNewAlerts]);

    const resetGraph = useCallback(async () => {
        try {
            await axios.post(`${API_BASE}/api/reset`);
            setGraphData(null);
            setStats(null);
            setAlerts([]);
            setAllProcessed(false);
            prevHighRiskRef.current = new Set();
            alertCounter = 0;
        } catch {
            // Handle quietly
        }
    }, []);

    return {
        graphData,
        stats,
        alerts,
        isConnected,
        isLoading,
        nextTransaction,
        resetGraph,
        allProcessed,
    };
}
