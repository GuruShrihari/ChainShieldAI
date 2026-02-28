/**
 * NodeTooltip — Slide-in panel showing detailed account information
 * when a node is clicked in the graph.
 */

import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import type { ForceGraphNode } from '../../types';
import { getRiskColor, getRiskLabel } from '../../utils/riskColors';

interface NodeTooltipProps {
    node: ForceGraphNode;
    onClose: () => void;
}

const BREAKDOWN_COLORS: Record<string, string> = {
    velocity: '#00f5ff',
    network_exposure: '#ff6b00',
    anomaly: '#ff2d55',
    channel_risk: '#aa00ff',
};

export function NodeTooltip({ node, onClose }: NodeTooltipProps) {
    const riskColor = getRiskColor(node.risk_score);
    const riskLabel = getRiskLabel(node.risk_score);

    const breakdownData = [
        { name: 'Velocity', value: node.risk_breakdown.velocity, color: BREAKDOWN_COLORS.velocity },
        { name: 'Network', value: node.risk_breakdown.network_exposure, color: BREAKDOWN_COLORS.network_exposure },
        { name: 'Anomaly', value: node.risk_breakdown.anomaly, color: BREAKDOWN_COLORS.anomaly },
        { name: 'Channel', value: node.risk_breakdown.channel_risk, color: BREAKDOWN_COLORS.channel_risk },
    ].filter((d) => d.value > 0);

    // If all values are 0, show a placeholder
    const hasBreakdownData = breakdownData.length > 0;

    return (
        <motion.div
            className="tooltip-panel"
            initial={{ x: 320, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 320, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
            <button className="tooltip-close" onClick={onClose} aria-label="Close tooltip">
                ✕
            </button>

            <div className="tooltip-node-id">{node.id}</div>
            <div style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-header)', letterSpacing: '0.1em' }}>
                CLUSTER {node.cluster_id} • {riskLabel}
            </div>

            <div className="tooltip-risk-score" style={{ color: riskColor }}>
                {node.risk_score.toFixed(1)}
            </div>

            {/* Stats */}
            <div className="tooltip-stat-row">
                <span className="tooltip-stat-label">Transactions</span>
                <span className="tooltip-stat-value">{node.tx_count}</span>
            </div>
            <div className="tooltip-stat-row">
                <span className="tooltip-stat-label">Total Sent</span>
                <span className="tooltip-stat-value">${node.total_sent.toLocaleString()}</span>
            </div>
            <div className="tooltip-stat-row">
                <span className="tooltip-stat-label">Total Received</span>
                <span className="tooltip-stat-value">${node.total_received.toLocaleString()}</span>
            </div>
            <div className="tooltip-stat-row">
                <span className="tooltip-stat-label">In/Out Ratio</span>
                <span className="tooltip-stat-value">
                    {node.total_sent > 0
                        ? (node.total_received / node.total_sent).toFixed(2)
                        : '∞'}
                </span>
            </div>

            {/* Channel badges */}
            <div className="channel-badges">
                {node.channels_used.map((channel) => (
                    <span key={channel} className={`channel-badge ${channel}`}>
                        {channel}
                    </span>
                ))}
            </div>

            {/* Model Risk Contribution — MOCK */}
            <div style={{ marginTop: '16px' }}>
                <div className="tooltip-stat-row">
                    <span className="tooltip-stat-label">
                        ML Risk Contrib. <span className="mock-badge">⚠ MOCK</span>
                    </span>
                    {/* MOCK — ml_placeholder.get_model_risk_contribution() */}
                    <span className="tooltip-stat-value">
                        {((node.id.split('').reduce((a, c) => a + c.charCodeAt(0), 0) % 100) / 100 * 3).toFixed(2)}
                    </span>
                </div>
            </div>

            {/* Risk Breakdown Donut */}
            <div style={{ marginTop: '16px' }}>
                <div style={{
                    fontFamily: 'var(--font-header)',
                    fontSize: '9px',
                    color: 'var(--text-muted)',
                    letterSpacing: '0.12em',
                    textTransform: 'uppercase' as const,
                    marginBottom: '8px',
                }}>
                    Risk Breakdown
                </div>
                {hasBreakdownData ? (
                    <ResponsiveContainer width="100%" height={140}>
                        <PieChart>
                            <Pie
                                data={breakdownData}
                                dataKey="value"
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                innerRadius={35}
                                outerRadius={55}
                                paddingAngle={3}
                                isAnimationActive={true}
                            >
                                {breakdownData.map((entry) => (
                                    <Cell key={entry.name} fill={entry.color} stroke="none" />
                                ))}
                            </Pie>
                        </PieChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="breakdown-placeholder">No risk data available</div>
                )}

                {/* Breakdown bars */}
                <div className="breakdown-bars">
                    {Object.entries(BREAKDOWN_COLORS).map(([key, color]) => {
                        const value = node.risk_breakdown[key as keyof typeof node.risk_breakdown];
                        const maxVal = 3;
                        const pct = Math.min((value / maxVal) * 100, 100);
                        return (
                            <div key={key} className="breakdown-bar-row">
                                <span className="breakdown-bar-label">
                                    {key.replace('_', ' ')}
                                </span>
                                <div className="breakdown-bar-track">
                                    <div
                                        className="breakdown-bar-value"
                                        style={{ width: `${pct}%`, background: color }}
                                    />
                                </div>
                                <span className="breakdown-bar-number">{value.toFixed(1)}</span>
                            </div>
                        );
                    })}
                </div>
            </div>
        </motion.div>
    );
}
