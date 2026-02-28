/**
 * useWebSocket hook for ChainShieldAI.
 *
 * Connects to ws://localhost:8000/ws and provides real-time
 * graph snapshot updates with auto-reconnect.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type { GraphSnapshot } from '../types';

const WS_URL = 'ws://localhost:8000/ws';
const MAX_RETRIES = 5;
const BASE_DELAY = 1000;

interface UseWebSocketReturn {
    graphData: GraphSnapshot | null;
    isConnected: boolean;
    lastUpdate: string | null;
}

export function useWebSocket(): UseWebSocketReturn {
    const [graphData, setGraphData] = useState<GraphSnapshot | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [lastUpdate, setLastUpdate] = useState<string | null>(null);

    const wsRef = useRef<WebSocket | null>(null);
    const retriesRef = useRef(0);
    const mountedRef = useRef(true);

    const connect = useCallback(() => {
        if (!mountedRef.current) return;

        try {
            const ws = new WebSocket(WS_URL);
            wsRef.current = ws;

            ws.onopen = () => {
                if (!mountedRef.current) return;
                setIsConnected(true);
                retriesRef.current = 0;
            };

            ws.onmessage = (event: MessageEvent) => {
                if (!mountedRef.current) return;
                try {
                    const snapshot = JSON.parse(event.data as string) as GraphSnapshot;
                    setGraphData(snapshot);
                    setLastUpdate(snapshot.timestamp);
                } catch {
                    // Ignore malformed messages
                }
            };

            ws.onclose = () => {
                if (!mountedRef.current) return;
                setIsConnected(false);

                // Auto-reconnect with exponential backoff
                if (retriesRef.current < MAX_RETRIES) {
                    const delay = BASE_DELAY * Math.pow(2, retriesRef.current);
                    retriesRef.current += 1;
                    setTimeout(connect, delay);
                }
            };

            ws.onerror = () => {
                // onclose will handle reconnection
                ws.close();
            };
        } catch {
            // Connection failed, will retry via onclose
        }
    }, []);

    useEffect(() => {
        mountedRef.current = true;
        connect();

        return () => {
            mountedRef.current = false;
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
        };
    }, [connect]);

    return { graphData, isConnected, lastUpdate };
}
