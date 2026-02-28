/**
 * App — Main application shell for ChainShieldAI.
 *
 * Layout: GraphCanvas (60% left) + Sidebar (40% right) with branding header.
 */

import { useState } from 'react';
import type { ChannelFilter, GraphNode } from './types';
import { useGraphData } from './hooks/useGraphData';
import { GraphCanvas } from './components/Graph/GraphCanvas';
import { Sidebar } from './components/Layout/Sidebar';

export default function App() {
    const {
        graphData,
        stats,
        alerts,
        isConnected,
        isLoading,
        nextTransaction,
        resetGraph,
        allProcessed,
    } = useGraphData();

    const [channelFilter, setChannelFilter] = useState<ChannelFilter>('ALL');
    const [riskThreshold, setRiskThreshold] = useState(0);
    const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

    // Sync selected node with live data
    const currentSelectedNode = selectedNode
        ? graphData?.nodes.find((n) => n.id === selectedNode.id) ?? selectedNode
        : null;

    return (
        <div className="app-layout">
            {/* Left: Graph Area */}
            <div className="graph-area">
                {/* Branding */}
                <div className="brand">
                    <div className="brand-title">
                        <span>⬡</span> ChainShieldAI
                    </div>
                    <div className="brand-subtitle">REAL-TIME THREAT INTELLIGENCE</div>
                </div>

                {/* Connection Status */}
                <div className="connection-status">
                    <div className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
                    <span>{isConnected ? 'LIVE' : 'OFFLINE'}</span>
                </div>

                <GraphCanvas
                    graphData={graphData}
                    channelFilter={channelFilter}
                    riskThreshold={riskThreshold}
                />
            </div>

            {/* Right: Sidebar */}
            <div className="sidebar-area">
                <Sidebar
                    stats={stats}
                    graphData={graphData}
                    alerts={alerts}
                    selectedNode={currentSelectedNode}
                    isLoading={isLoading}
                    allProcessed={allProcessed}
                    channelFilter={channelFilter}
                    riskThreshold={riskThreshold}
                    onNextTransaction={nextTransaction}
                    onReset={resetGraph}
                    onChannelFilterChange={setChannelFilter}
                    onRiskThresholdChange={setRiskThreshold}
                />
            </div>
        </div>
    );
}
