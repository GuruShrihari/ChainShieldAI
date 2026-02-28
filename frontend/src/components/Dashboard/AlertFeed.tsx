/**
 * AlertFeed — Real-time alert feed with framer-motion slide-in animations.
 *
 * Max 50 items, auto-scrolls to latest, stale items dim after 30 seconds.
 */

import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { AlertItem } from '../../types';

interface AlertFeedProps {
    alerts: AlertItem[];
}

const STALE_THRESHOLD_MS = 30_000; // 30 seconds

export function AlertFeed({ alerts }: AlertFeedProps) {
    const feedRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom on new alerts
    useEffect(() => {
        if (feedRef.current) {
            feedRef.current.scrollTo({
                top: feedRef.current.scrollHeight,
                behavior: 'smooth',
            });
        }
    }, [alerts.length]);

    const now = Date.now();

    return (
        <div className="panel">
            <div className="panel-header">⚡ ALERT FEED</div>
            <div className="alert-feed" ref={feedRef}>
                <AnimatePresence>
                    {alerts.length === 0 ? (
                        <div style={{
                            color: 'var(--text-muted)',
                            fontFamily: 'var(--font-header)',
                            fontSize: '10px',
                            letterSpacing: '0.1em',
                            padding: '16px 0',
                            textAlign: 'center',
                        }}>
                            NO ALERTS — WAITING FOR DATA
                        </div>
                    ) : (
                        alerts.map((alert, idx) => {
                            const isStale = now - alert.createdAt > STALE_THRESHOLD_MS;
                            return (
                                <motion.div
                                    key={alert.id}
                                    className={`alert-item ${alert.severity} ${isStale ? 'stale' : ''}`}
                                    initial={{ x: 30, opacity: 0 }}
                                    animate={{ x: 0, opacity: isStale ? 0.4 : 1 }}
                                    exit={{ x: -30, opacity: 0 }}
                                    transition={{ delay: (idx % 5) * 0.05, duration: 0.3 }}
                                >
                                    <span className="alert-time">[{alert.timestamp}]</span>
                                    <span>⚠ {alert.type}: {alert.details}</span>
                                    <span className="alert-risk">Risk: {alert.risk.toFixed(1)}</span>
                                </motion.div>
                            );
                        })
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
