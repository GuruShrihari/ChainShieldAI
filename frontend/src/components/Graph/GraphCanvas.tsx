/**
 * GraphCanvas — Force-directed graph visualization using react-force-graph-2d.
 *
 * Renders the transaction network with risk-based node coloring,
 * channel-based edge coloring, glow rings on high-risk nodes,
 * and a scanning line overlay.
 */

import {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
} from 'react';
import ForceGraph2D, {
    type ForceGraphMethods,
    type NodeObject,
    type LinkObject,
} from 'react-force-graph-2d';
import type { ChannelFilter, ForceGraphLink, ForceGraphNode, GraphSnapshot } from '../../types';
import { getChannelColor, getRiskColor } from '../../utils/riskColors';
import { NodeTooltip } from './NodeTooltip';

interface GraphCanvasProps {
    graphData: GraphSnapshot | null;
    channelFilter: ChannelFilter;
    riskThreshold: number;
}

type FGNode = NodeObject<ForceGraphNode>;
type FGLink = LinkObject<ForceGraphNode, ForceGraphLink>;

export function GraphCanvas({ graphData, channelFilter, riskThreshold }: GraphCanvasProps) {
    const fgRef = useRef<ForceGraphMethods<FGNode, FGLink> | undefined>(undefined);
    const containerRef = useRef<HTMLDivElement>(null);
    const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
    const [selectedNode, setSelectedNode] = useState<ForceGraphNode | null>(null);
    const [showRedFlash, setShowRedFlash] = useState(false);
    const prevNodeCountRef = useRef(0);

    // Resize observer
    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        const observer = new ResizeObserver((entries) => {
            for (const entry of entries) {
                setDimensions({
                    width: entry.contentRect.width,
                    height: entry.contentRect.height,
                });
            }
        });
        observer.observe(container);
        return () => observer.disconnect();
    }, []);

    // Detect new high-risk nodes and flash
    useEffect(() => {
        if (!graphData) return;
        const highRiskNodes = graphData.nodes.filter((n) => n.risk_score >= 7);
        if (highRiskNodes.length > prevNodeCountRef.current) {
            setShowRedFlash(true);
            setTimeout(() => setShowRedFlash(false), 300);
        }
        prevNodeCountRef.current = highRiskNodes.length;
    }, [graphData]);

    // Filter graph data
    const filteredData = useMemo(() => {
        if (!graphData) return { nodes: [], links: [] };

        const filteredNodes = graphData.nodes
            .filter((n) => n.risk_score >= riskThreshold)
            .map((n) => ({ ...n }));

        const nodeIds = new Set(filteredNodes.map((n) => n.id));

        const filteredEdges = graphData.edges
            .filter((e) => {
                if (channelFilter !== 'ALL' && e.channel.toUpperCase() !== channelFilter) {
                    return false;
                }
                return nodeIds.has(e.source) && nodeIds.has(e.target);
            })
            .map((e) => ({
                source: e.source,
                target: e.target,
                amount: e.amount,
                channel: e.channel,
                timestamp: e.timestamp,
                tx_id: e.tx_id,
            }));

        return {
            nodes: filteredNodes as FGNode[],
            links: filteredEdges as FGLink[],
        };
    }, [graphData, channelFilter, riskThreshold]);

    // Suspicious chain edge set for dashed rendering
    const suspiciousEdges = useMemo(() => {
        if (!graphData) return new Set<string>();
        const edges = new Set<string>();
        for (const chain of graphData.suspicious_chains) {
            for (let i = 0; i < chain.path.length - 1; i++) {
                edges.add(`${chain.path[i]}->${chain.path[i + 1]}`);
            }
        }
        return edges;
    }, [graphData]);

    // Custom node rendering with glow
    const nodeCanvasObject = useCallback(
        (node: FGNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
            const risk = node.risk_score ?? 0;
            const totalFlow = (node.total_sent ?? 0) + (node.total_received ?? 0);
            const size = Math.max(4, Math.min(20, Math.sqrt(totalFlow) * 0.5));
            const x = node.x ?? 0;
            const y = node.y ?? 0;

            // Glow ring for high-risk nodes (risk > 7)
            if (risk > 7) {
                const time = Date.now() / 1000;
                const glowAlpha = 0.3 + Math.sin(time * 3) * 0.2;
                const glowSize = size + 6 + Math.sin(time * 2) * 2;

                ctx.beginPath();
                ctx.arc(x, y, glowSize, 0, Math.PI * 2);
                const color = getRiskColor(risk);
                const rgbMatch = color.match(/\d+/g);
                if (rgbMatch) {
                    ctx.fillStyle = `rgba(${rgbMatch[0]}, ${rgbMatch[1]}, ${rgbMatch[2]}, ${glowAlpha})`;
                }
                ctx.fill();
            }

            // Main node circle
            ctx.beginPath();
            ctx.arc(x, y, size, 0, Math.PI * 2);
            ctx.fillStyle = getRiskColor(risk);
            ctx.fill();

            // Border
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
            ctx.lineWidth = 0.5;
            ctx.stroke();

            // Label on hover (when zoomed in enough)
            if (globalScale > 1.2) {
                const label = node.id;
                ctx.font = `${Math.max(8, 10 / globalScale)}px 'Share Tech Mono', monospace`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'top';
                ctx.fillStyle = 'rgba(232, 232, 240, 0.8)';
                ctx.fillText(label, x, y + size + 3);
            }
        },
        []
    );

    // Custom link rendering
    const linkCanvasObject = useCallback(
        (link: FGLink, ctx: CanvasRenderingContext2D) => {
            const sourceNode = link.source as ForceGraphNode;
            const targetNode = link.target as ForceGraphNode;
            if (!sourceNode.x || !sourceNode.y || !targetNode.x || !targetNode.y) return;

            const sx = sourceNode.x;
            const sy = sourceNode.y;
            const tx = targetNode.x;
            const ty = targetNode.y;

            const edgeKey = `${sourceNode.id}->${targetNode.id}`;
            const isSuspicious = suspiciousEdges.has(edgeKey);
            const channel = link.channel ?? 'mobile';
            const width = Math.max(0.5, Math.log(link.amount ?? 1) * 0.5);

            ctx.beginPath();
            ctx.moveTo(sx, sy);
            ctx.lineTo(tx, ty);
            ctx.strokeStyle = getChannelColor(channel);
            ctx.lineWidth = width;

            if (isSuspicious) {
                ctx.setLineDash([4, 4]);
            } else {
                ctx.setLineDash([]);
            }

            ctx.globalAlpha = 0.6;
            ctx.stroke();
            ctx.globalAlpha = 1;
            ctx.setLineDash([]);

            // Arrowhead
            const angle = Math.atan2(ty - sy, tx - sx);
            const arrowLen = 5;
            const arrowX = tx - Math.cos(angle) * 10;
            const arrowY = ty - Math.sin(angle) * 10;

            ctx.beginPath();
            ctx.moveTo(arrowX, arrowY);
            ctx.lineTo(
                arrowX - arrowLen * Math.cos(angle - Math.PI / 6),
                arrowY - arrowLen * Math.sin(angle - Math.PI / 6)
            );
            ctx.lineTo(
                arrowX - arrowLen * Math.cos(angle + Math.PI / 6),
                arrowY - arrowLen * Math.sin(angle + Math.PI / 6)
            );
            ctx.fillStyle = getChannelColor(channel);
            ctx.globalAlpha = 0.6;
            ctx.fill();
            ctx.globalAlpha = 1;
        },
        [suspiciousEdges]
    );

    const handleNodeClick = useCallback((node: FGNode) => {
        setSelectedNode(node as ForceGraphNode);
    }, []);

    // Configure forces
    useEffect(() => {
        if (fgRef.current) {
            const fg = fgRef.current;
            fg.d3Force('charge')?.strength(-250);
            fg.d3Force('link')?.distance(90);
        }
    }, [filteredData]);

    return (
        <div
            ref={containerRef}
            style={{ width: '100%', height: '100%', position: 'relative' }}
        >
            {/* Scanning line */}
            <div className="scan-line-overlay" />

            {/* Red flash on high-risk detection */}
            {showRedFlash && <div className="red-flash-overlay" />}

            <ForceGraph2D
                ref={fgRef as React.MutableRefObject<ForceGraphMethods<FGNode, FGLink>>}
                width={dimensions.width}
                height={dimensions.height}
                graphData={filteredData}
                nodeCanvasObject={nodeCanvasObject}
                linkCanvasObject={linkCanvasObject}
                onNodeClick={handleNodeClick}
                nodeId="id"
                backgroundColor="#050508"
                enableNodeDrag={true}
                enableZoomInteraction={true}
                cooldownTicks={50}
                nodeRelSize={6}
            />

            {/* NodeTooltip */}
            {selectedNode && (
                <NodeTooltip
                    node={selectedNode}
                    onClose={() => setSelectedNode(null)}
                />
            )}
        </div>
    );
}
