/**
 * RiskBreakdown — Recharts PieChart (donut) and progress bars
 * for the selected node's risk breakdown.
 */

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import type { GraphNode } from '../../types';

interface RiskBreakdownProps {
    selectedNode: GraphNode | null;
}

const SEGMENTS = [
    { key: 'velocity' as const, label: 'Velocity', color: '#00f5ff' },
    { key: 'network_exposure' as const, label: 'Network Exposure', color: '#ff6b00' },
    { key: 'anomaly' as const, label: 'Anomaly', color: '#ff2d55' },
    { key: 'channel_risk' as const, label: 'Channel Risk', color: '#aa00ff' },
];

export function RiskBreakdown({ selectedNode }: RiskBreakdownProps) {
    if (!selectedNode) {
        return (
            <div className="panel">
                <div className="panel-header">📊 RISK BREAKDOWN</div>
                <div className="breakdown-placeholder">
                    SELECT A NODE TO VIEW BREAKDOWN
                </div>
            </div>
        );
    }

    const breakdown = selectedNode.risk_breakdown;
    const data = SEGMENTS.map((seg) => ({
        name: seg.label,
        value: breakdown[seg.key],
        color: seg.color,
    })).filter((d) => d.value > 0);

    const maxVal = 3;

    return (
        <div className="panel">
            <div className="panel-header">
                📊 RISK BREAKDOWN — {selectedNode.id}
            </div>

            {data.length > 0 ? (
                <ResponsiveContainer width="100%" height={160}>
                    <PieChart>
                        <Pie
                            data={data}
                            dataKey="value"
                            nameKey="name"
                            cx="50%"
                            cy="50%"
                            innerRadius={40}
                            outerRadius={60}
                            paddingAngle={3}
                            isAnimationActive={true}
                            animationDuration={600}
                        >
                            {data.map((entry) => (
                                <Cell key={entry.name} fill={entry.color} stroke="none" />
                            ))}
                        </Pie>
                        <Tooltip
                            contentStyle={{
                                background: 'var(--bg-panel)',
                                border: '1px solid var(--border)',
                                borderRadius: '4px',
                                fontFamily: 'var(--font-body)',
                                fontSize: '11px',
                                color: 'var(--text-primary)',
                            }}
                        />
                    </PieChart>
                </ResponsiveContainer>
            ) : (
                <div className="breakdown-placeholder">
                    No risk factors detected
                </div>
            )}

            {/* Progress bars for each breakdown value */}
            <div className="breakdown-bars">
                {SEGMENTS.map((seg) => {
                    const value = breakdown[seg.key];
                    const pct = Math.min((value / maxVal) * 100, 100);
                    return (
                        <div key={seg.key} className="breakdown-bar-row">
                            <span className="breakdown-bar-label">{seg.label}</span>
                            <div className="breakdown-bar-track">
                                <div
                                    className="breakdown-bar-value"
                                    style={{ width: `${pct}%`, background: seg.color }}
                                />
                            </div>
                            <span className="breakdown-bar-number">{value.toFixed(1)}</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
