/**
 * Sidebar — Right panel (40% width) containing all dashboard components
 * stacked vertically with internal scroll.
 */

import type { AlertItem, ChannelFilter, GraphNode, GraphSnapshot, Stats } from '../../types';
import { StatsBar } from '../Dashboard/StatsBar';
import { ControlPanel } from '../Dashboard/ControlPanel';
import { AlertFeed } from '../Dashboard/AlertFeed';
import { SuspiciousChains } from '../Dashboard/SuspiciousChains';
import { RiskBreakdown } from '../Dashboard/RiskBreakdown';

interface SidebarProps {
    stats: Stats | null;
    graphData: GraphSnapshot | null;
    alerts: AlertItem[];
    selectedNode: GraphNode | null;
    isLoading: boolean;
    allProcessed: boolean;
    channelFilter: ChannelFilter;
    riskThreshold: number;
    onNextTransaction: () => void;
    onReset: () => void;
    onChannelFilterChange: (filter: ChannelFilter) => void;
    onRiskThresholdChange: (value: number) => void;
}

export function Sidebar({
    stats,
    graphData,
    alerts,
    selectedNode,
    isLoading,
    allProcessed,
    channelFilter,
    riskThreshold,
    onNextTransaction,
    onReset,
    onChannelFilterChange,
    onRiskThresholdChange,
}: SidebarProps) {
    return (
        <>
            <StatsBar stats={stats} />

            <ControlPanel
                onNextTransaction={onNextTransaction}
                onReset={onReset}
                isLoading={isLoading}
                allProcessed={allProcessed}
                channelFilter={channelFilter}
                onChannelFilterChange={onChannelFilterChange}
                riskThreshold={riskThreshold}
                onRiskThresholdChange={onRiskThresholdChange}
            />

            <AlertFeed alerts={alerts} />

            <SuspiciousChains chains={graphData?.suspicious_chains ?? []} />

            <RiskBreakdown selectedNode={selectedNode} />
        </>
    );
}
