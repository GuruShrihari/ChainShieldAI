/**
 * SuspiciousChains — Table displaying detected suspicious chains
 * with risk badges, cash-out probability bars, and mock ML indicators.
 */

import { motion, AnimatePresence } from 'framer-motion';
import type { SuspiciousChain } from '../../types';
import { getRiskLabel } from '../../utils/riskColors';
import { getMockCashoutProbability } from '../../utils/mockMLData'; // MOCK

interface SuspiciousChainsProps {
    chains: SuspiciousChain[];
}

function getRiskBadgeClass(risk: number): string {
    if (risk >= 20) return 'critical';
    if (risk >= 12) return 'high';
    if (risk >= 6) return 'medium';
    return 'low';
}

function getRowRiskClass(risk: number): string {
    if (risk >= 20) return 'high-risk';
    if (risk >= 12) return 'mid-risk';
    return '';
}

function getCashoutBarColor(prob: number): string {
    if (prob >= 0.7) return 'var(--accent-red)';
    if (prob >= 0.4) return 'var(--accent-orange)';
    return 'var(--accent-green)';
}

export function SuspiciousChains({ chains }: SuspiciousChainsProps) {
    return (
        <div className="panel">
            <div className="panel-header">🔗 SUSPICIOUS CHAINS</div>
            {chains.length === 0 ? (
                <div style={{
                    color: 'var(--text-muted)',
                    fontFamily: 'var(--font-header)',
                    fontSize: '10px',
                    letterSpacing: '0.1em',
                    padding: '16px 0',
                    textAlign: 'center',
                }}>
                    NO CHAINS DETECTED YET
                </div>
            ) : (
                <div style={{ overflowX: 'auto' }}>
                    <table className="chains-table">
                        <thead>
                            <tr>
                                <th>Chain Path</th>
                                <th>Risk</th>
                                <th>Cash-Out Prob</th>
                                <th>Channels</th>
                                <th>ML Score</th>
                            </tr>
                        </thead>
                        <tbody>
                            <AnimatePresence>
                                {chains.map((chain, idx) => {
                                    const badgeClass = getRiskBadgeClass(chain.cumulative_risk);
                                    const rowClass = getRowRiskClass(chain.cumulative_risk);
                                    // MOCK — Using mock cashout probability from mockMLData
                                    const cashoutProb = chain.cashout_probability || getMockCashoutProbability(chain.path);
                                    const barColor = getCashoutBarColor(cashoutProb);

                                    return (
                                        <motion.tr
                                            key={chain.path.join('->')}
                                            className={rowClass}
                                            initial={{ y: 20, opacity: 0 }}
                                            animate={{ y: 0, opacity: 1 }}
                                            exit={{ opacity: 0 }}
                                            transition={{ delay: idx * 0.05 }}
                                        >
                                            <td>
                                                <div className="chain-path">
                                                    {chain.path.map((acc, i) => (
                                                        <span key={acc}>
                                                            {acc}
                                                            {i < chain.path.length - 1 && (
                                                                <span className="chain-arrow"> → </span>
                                                            )}
                                                        </span>
                                                    ))}
                                                </div>
                                            </td>
                                            <td>
                                                <span className={`risk-badge ${badgeClass}`}>
                                                    {chain.cumulative_risk.toFixed(1)}
                                                </span>
                                            </td>
                                            <td>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                    <div className="cashout-bar-bg">
                                                        <div
                                                            className="cashout-bar-fill"
                                                            style={{
                                                                width: `${cashoutProb * 100}%`,
                                                                background: barColor,
                                                            }}
                                                        />
                                                    </div>
                                                    <span style={{ fontSize: '10px', fontFamily: 'var(--font-body)' }}>
                                                        {/* MOCK — cashout probability from ml_placeholder */}
                                                        {(cashoutProb * 100).toFixed(0)}%
                                                    </span>
                                                    {chain.is_mock_score && (
                                                        <span className="mock-badge">⚠ MOCK</span>
                                                    )}
                                                </div>
                                            </td>
                                            <td>
                                                <div className="channel-badges" style={{ marginTop: 0 }}>
                                                    {chain.channels.map((ch, i) => (
                                                        <span key={`${ch}-${i}`} className={`channel-badge ${ch}`}>
                                                            {ch}
                                                        </span>
                                                    ))}
                                                </div>
                                            </td>
                                            <td>
                                                {/* MOCK — ML Score always pending */}
                                                <span className="mock-badge">⚠ MOCK — Pending</span>
                                            </td>
                                        </motion.tr>
                                    );
                                })}
                            </AnimatePresence>
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
