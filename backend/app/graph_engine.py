"""NetworkX-based graph engine for ChainShieldAI.

Manages the transaction graph, risk propagation, and community detection.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

import networkx as nx
import numpy as np

from app.models import Edge, Node, RiskBreakdown

# Risk propagation constants
PROPAGATION_DECAY = 0.3
PROPAGATION_ITERATIONS = 3
MAX_RISK = 10.0

# Channel risk weights
CHANNEL_RISK_WEIGHTS: dict[str, float] = {
    "atm": 0.9,
    "wallet": 0.5,
    "mobile": 0.3,
    "bank": 0.1,
}

# Velocity window (transactions within this window count toward velocity)
VELOCITY_WINDOW = timedelta(minutes=30)


class GraphEngine:
    """Manages the transaction graph and risk propagation."""

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self._cluster_assignments: dict[str, int] = {}
        self._risk_breakdowns: dict[str, RiskBreakdown] = {}

    def reset(self) -> None:
        """Reset the graph to empty state."""
        self.graph = nx.DiGraph()
        self._cluster_assignments = {}
        self._risk_breakdowns = {}

    def add_transaction(self, tx: dict[str, Any]) -> None:
        """Add a transaction to the graph, updating node and edge attributes."""
        from_acc = tx["from_account"]
        to_acc = tx["to_account"]
        amount = float(tx["amount"])
        channel = tx["channel"]
        timestamp = tx["timestamp"]
        tx_id = tx["tx_id"]

        # Initialize or update sender node
        if not self.graph.has_node(from_acc):
            self.graph.add_node(
                from_acc,
                risk_score=0.0,
                total_sent=0.0,
                total_received=0.0,
                tx_count=0,
                channels_used=set(),
                last_seen=timestamp,
                tx_timestamps=[],
            )
        node_from = self.graph.nodes[from_acc]
        node_from["total_sent"] += amount
        node_from["tx_count"] += 1
        node_from["channels_used"].add(channel)
        node_from["last_seen"] = timestamp
        node_from["tx_timestamps"].append(timestamp)

        # Initialize or update receiver node
        if not self.graph.has_node(to_acc):
            self.graph.add_node(
                to_acc,
                risk_score=0.0,
                total_sent=0.0,
                total_received=0.0,
                tx_count=0,
                channels_used=set(),
                last_seen=timestamp,
                tx_timestamps=[],
            )
        node_to = self.graph.nodes[to_acc]
        node_to["total_received"] += amount
        node_to["tx_count"] += 1
        node_to["channels_used"].add(channel)
        node_to["last_seen"] = timestamp
        node_to["tx_timestamps"].append(timestamp)

        # Add edge (allow multigraph behavior via unique keys)
        self.graph.add_edge(
            from_acc,
            to_acc,
            key=tx_id,
            amount=amount,
            channel=channel,
            timestamp=timestamp,
            tx_id=tx_id,
        )

    def propagate_risk(self) -> None:
        """Run the full risk propagation algorithm.

        1. Compute base risk for each node
        2. Propagate risk from neighbors (3 iterations)
        3. Normalize and cap at MAX_RISK
        """
        if len(self.graph.nodes) == 0:
            return

        # Step 1: Compute base risk scores
        for node_id in self.graph.nodes:
            breakdown = self._compute_base_risk(node_id)
            self._risk_breakdowns[node_id] = breakdown
            base = (
                breakdown.velocity
                + breakdown.anomaly
                + breakdown.channel_risk
                + breakdown.network_exposure
            )
            self.graph.nodes[node_id]["risk_score"] = min(base, MAX_RISK)

        # Step 2: Propagate through network
        for _iteration in range(PROPAGATION_ITERATIONS):
            new_scores: dict[str, float] = {}
            for node_id in self.graph.nodes:
                current = self.graph.nodes[node_id]["risk_score"]

                # Get max risk from all neighbors (predecessors + successors)
                neighbor_risks: list[float] = []
                for pred in self.graph.predecessors(node_id):
                    neighbor_risks.append(self.graph.nodes[pred]["risk_score"])
                for succ in self.graph.successors(node_id):
                    neighbor_risks.append(self.graph.nodes[succ]["risk_score"])

                if neighbor_risks:
                    propagated = PROPAGATION_DECAY * max(neighbor_risks)
                    new_scores[node_id] = min(current + propagated, MAX_RISK)
                else:
                    new_scores[node_id] = current

            for node_id, score in new_scores.items():
                self.graph.nodes[node_id]["risk_score"] = score

        # Step 3: Update network_exposure in breakdowns after propagation
        for node_id in self.graph.nodes:
            if node_id in self._risk_breakdowns:
                # Update breakdown to reflect propagated values
                neighbor_risks = []
                for pred in self.graph.predecessors(node_id):
                    neighbor_risks.append(self.graph.nodes[pred]["risk_score"])
                for succ in self.graph.successors(node_id):
                    neighbor_risks.append(self.graph.nodes[succ]["risk_score"])

                if neighbor_risks:
                    self._risk_breakdowns[node_id].network_exposure = round(
                        PROPAGATION_DECAY * max(neighbor_risks), 2
                    )

    def _compute_base_risk(self, node_id: str) -> RiskBreakdown:
        """Compute the base risk breakdown for a node.

        Components:
        - velocity_score: how rapidly the account transacts
        - amount_anomaly: unusual transaction amounts
        - channel_risk: weighted by channel type (ATM = highest)
        - network_exposure: in/out degree ratio
        """
        node_data = self.graph.nodes[node_id]

        # 1. Velocity score: transactions per time window
        timestamps = node_data.get("tx_timestamps", [])
        velocity_score = 0.0
        if len(timestamps) >= 2:
            try:
                parsed = [
                    datetime.fromisoformat(t) if isinstance(t, str) else t
                    for t in timestamps
                ]
                parsed.sort()
                latest = parsed[-1]
                window_start = latest - VELOCITY_WINDOW
                recent_count = sum(1 for t in parsed if t >= window_start)
                velocity_score = min(recent_count * 0.5, 3.0)
            except (ValueError, TypeError):
                velocity_score = 0.0

        # 2. Amount anomaly: high amounts and unusual ratios
        total_sent = node_data.get("total_sent", 0.0)
        total_received = node_data.get("total_received", 0.0)
        tx_count = max(node_data.get("tx_count", 1), 1)

        avg_tx = (total_sent + total_received) / tx_count
        anomaly_score = 0.0
        if avg_tx > 3000:
            anomaly_score = 2.0
        elif avg_tx > 2000:
            anomaly_score = 1.0
        elif avg_tx > 1000:
            anomaly_score = 0.5

        # In/out ratio anomaly (high out vs in = potential mule)
        if total_received > 0 and total_sent > 0:
            ratio = total_sent / total_received
            if ratio > 3.0:
                anomaly_score += 1.5
            elif ratio > 1.5:
                anomaly_score += 0.7

        anomaly_score = min(anomaly_score, 3.0)

        # 3. Channel risk: ATM withdrawals are highest risk
        channels = node_data.get("channels_used", set())
        channel_scores = [CHANNEL_RISK_WEIGHTS.get(c, 0.3) for c in channels]
        channel_risk = 0.0
        if channel_scores:
            channel_risk = max(channel_scores) * 2.0
            if "atm" in channels and len(channels) >= 2:
                # Multi-channel with ATM = extra suspicious
                channel_risk += 0.5
        channel_risk = min(channel_risk, 3.0)

        # 4. Network exposure: based on degree
        in_deg = self.graph.in_degree(node_id)
        out_deg = self.graph.out_degree(node_id)
        exposure = min((in_deg + out_deg) * 0.3, 2.0)

        return RiskBreakdown(
            velocity=round(velocity_score, 2),
            network_exposure=round(exposure, 2),
            anomaly=round(anomaly_score, 2),
            channel_risk=round(channel_risk, 2),
        )

    def detect_communities(self) -> None:
        """Detect communities using greedy modularity optimization."""
        if len(self.graph.nodes) < 2:
            for node_id in self.graph.nodes:
                self._cluster_assignments[node_id] = 0
            return

        undirected = self.graph.to_undirected()
        try:
            communities = nx.community.greedy_modularity_communities(undirected)
            for cluster_id, community in enumerate(communities):
                for node_id in community:
                    self._cluster_assignments[node_id] = cluster_id
        except Exception:
            # Fallback: assign all to cluster 0
            for node_id in self.graph.nodes:
                self._cluster_assignments[node_id] = 0

    def get_nodes(self) -> list[Node]:
        """Return all nodes as Pydantic models."""
        nodes: list[Node] = []
        for node_id, data in self.graph.nodes(data=True):
            channels = data.get("channels_used", set())
            if isinstance(channels, set):
                channels_list = sorted(channels)
            else:
                channels_list = list(channels)

            breakdown = self._risk_breakdowns.get(
                node_id,
                RiskBreakdown(velocity=0, network_exposure=0, anomaly=0, channel_risk=0),
            )

            nodes.append(
                Node(
                    id=node_id,
                    risk_score=round(data.get("risk_score", 0.0), 2),
                    total_sent=round(data.get("total_sent", 0.0), 2),
                    total_received=round(data.get("total_received", 0.0), 2),
                    tx_count=data.get("tx_count", 0),
                    channels_used=channels_list,
                    cluster_id=self._cluster_assignments.get(node_id, 0),
                    risk_breakdown=breakdown,
                )
            )
        return nodes

    def get_edges(self) -> list[Edge]:
        """Return all edges as Pydantic models."""
        edges: list[Edge] = []
        for u, v, data in self.graph.edges(data=True):
            edges.append(
                Edge(
                    source=u,
                    target=v,
                    amount=float(data.get("amount", 0)),
                    channel=str(data.get("channel", "unknown")),
                    timestamp=str(data.get("timestamp", "")),
                    tx_id=str(data.get("tx_id", "")),
                )
            )
        return edges

    def get_high_risk_accounts(self, threshold: float = 6.0) -> list[str]:
        """Return account IDs with risk score above the threshold."""
        return [
            node_id
            for node_id, data in self.graph.nodes(data=True)
            if data.get("risk_score", 0.0) >= threshold
        ]

    def get_risk_breakdown(self, node_id: str) -> RiskBreakdown | None:
        """Get the risk breakdown for a specific node."""
        return self._risk_breakdowns.get(node_id)
