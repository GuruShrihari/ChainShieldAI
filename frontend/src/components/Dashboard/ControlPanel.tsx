/**
 * ControlPanel — Transaction controls, channel filter pills, risk threshold slider.
 */

import type { ChannelFilter } from '../../types';

interface ControlPanelProps {
    onNextTransaction: () => void;
    onReset: () => void;
    isLoading: boolean;
    allProcessed: boolean;
    channelFilter: ChannelFilter;
    onChannelFilterChange: (filter: ChannelFilter) => void;
    riskThreshold: number;
    onRiskThresholdChange: (value: number) => void;
}

const CHANNEL_OPTIONS: ChannelFilter[] = ['ALL', 'MOBILE', 'WALLET', 'ATM', 'BANK'];

export function ControlPanel({
    onNextTransaction,
    onReset,
    isLoading,
    allProcessed,
    channelFilter,
    onChannelFilterChange,
    riskThreshold,
    onRiskThresholdChange,
}: ControlPanelProps) {
    return (
        <div className="controls">
            <div className="panel" style={{ margin: 0 }}>
                <button
                    className="btn-primary"
                    onClick={onNextTransaction}
                    disabled={isLoading || allProcessed}
                >
                    {allProcessed ? '✓ ALL 200 TRANSACTIONS PROCESSED' : '▶ NEXT TRANSACTION'}
                </button>

                <button
                    className="btn-secondary"
                    onClick={onReset}
                >
                    ↺ RESET SIMULATION
                </button>

                {/* Channel filter pills */}
                <div className="filter-pills">
                    {CHANNEL_OPTIONS.map((ch) => (
                        <button
                            key={ch}
                            className={`pill ${channelFilter === ch ? 'active' : ''}`}
                            onClick={() => onChannelFilterChange(ch)}
                        >
                            {ch}
                        </button>
                    ))}
                </div>

                {/* Risk threshold slider */}
                <div className="slider-container">
                    <div className="slider-label">
                        <span>RISK THRESHOLD</span>
                        <span className="slider-value">{riskThreshold.toFixed(1)}</span>
                    </div>
                    <input
                        type="range"
                        min={0}
                        max={10}
                        step={0.1}
                        value={riskThreshold}
                        onChange={(e) => onRiskThresholdChange(parseFloat(e.target.value))}
                    />
                </div>
            </div>
        </div>
    );
}
