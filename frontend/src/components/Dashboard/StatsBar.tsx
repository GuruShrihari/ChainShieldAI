/**
 * StatsBar — 2x2 metric card grid with scramble-number animation.
 */

import { useEffect, useRef, useState } from 'react';
import type { Stats } from '../../types';

interface StatsBarProps {
    stats: Stats | null;
}

/**
 * Custom hook for digital scramble-then-resolve number effect.
 */
function useScrambleNumber(target: number, duration: number = 400): string {
    const [display, setDisplay] = useState(target.toString());
    const frameRef = useRef<number>(0);
    const startRef = useRef<number>(0);

    useEffect(() => {
        const digits = target.toString();
        startRef.current = Date.now();

        const animate = () => {
            const elapsed = Date.now() - startRef.current;
            const progress = Math.min(elapsed / duration, 1);

            if (progress < 1) {
                // Scramble: show random digits that progressively resolve
                const resolved = Math.floor(progress * digits.length);
                let result = '';
                for (let i = 0; i < digits.length; i++) {
                    if (i < resolved) {
                        result += digits[i];
                    } else {
                        result += Math.floor(Math.random() * 10).toString();
                    }
                }
                setDisplay(result);
                frameRef.current = requestAnimationFrame(animate);
            } else {
                setDisplay(digits);
            }
        };

        frameRef.current = requestAnimationFrame(animate);
        return () => cancelAnimationFrame(frameRef.current);
    }, [target, duration]);

    return display;
}

export function StatsBar({ stats }: StatsBarProps) {
    const totalTx = useScrambleNumber(stats?.total_transactions ?? 0);
    const highRisk = useScrambleNumber(stats?.high_risk_accounts ?? 0);
    const chains = useScrambleNumber(stats?.chains_detected ?? 0);
    const alertsFired = useScrambleNumber(stats?.alerts_fired ?? 0);

    return (
        <div className="stats-grid">
            <div className="stat-card cyan">
                <div className="stat-icon">📊</div>
                <div className="stat-label">Total Transactions</div>
                <div className="stat-value cyan">{totalTx}</div>
            </div>
            <div className="stat-card red">
                <div className="stat-icon">🔴</div>
                <div className="stat-label">High Risk Accounts</div>
                <div className="stat-value red">{highRisk}</div>
            </div>
            <div className="stat-card orange">
                <div className="stat-icon">🔗</div>
                <div className="stat-label">Chains Detected</div>
                <div className="stat-value orange">{chains}</div>
            </div>
            <div className="stat-card green">
                <div className="stat-icon">🚨</div>
                <div className="stat-label">Alerts Fired</div>
                <div className="stat-value green">{alertsFired}</div>
            </div>
        </div>
    );
}
