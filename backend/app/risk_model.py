"""Rule-based risk scoring and chain fingerprinting for ChainShieldAI.

All logic is deterministic rules — zero ML calls.
For cash-out probability, calls ml_placeholder.get_cashout_probability().
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from typing import Any

import networkx as nx

from app.ml_placeholder import get_cashout_probability
from app.models import SuspiciousChain


# Chain detection constants
TEMPORAL_WINDOW = timedelta(hours=2)
SUSPICIOUS_RISK_THRESHOLD = 5.0
MAX_CHAIN_LENGTH = 6
MIN_CHAIN_LENGTH = 3

# Fingerprint pattern: Mobile → Wallet → ATM
MULE_CHANNEL_PATTERN = ["mobile", "wallet", "atm"]


class RiskModel:
    """Rule-based risk model for suspicious chain detection."""

    def __init__(self, graph: nx.DiGraph) -> None:
        self.graph = graph

    def detect_temporal_chains(self) -> list[SuspiciousChain]:
        """Detect sequences matching Mobile→Wallet→ATM within 2-hour windows.

        Uses temporal chain fingerprinting to find transaction sequences
        that follow typical mule cash-out patterns.
        """
        chains: list[SuspiciousChain] = []
        seen_chains: set[str] = set()

        for node in self.graph.nodes:
            # Start BFS-like exploration from each node
            found = self._find_pattern_chains(
                node, MULE_CHANNEL_PATTERN, TEMPORAL_WINDOW
            )
            for chain_info in found:
                chain_key = "->".join(chain_info["path"])
                if chain_key not in seen_chains:
                    seen_chains.add(chain_key)
                    cum_risk = sum(
                        self.graph.nodes[n].get("risk_score", 0.0)
                        for n in chain_info["path"]
                    )
                    cashout_prob = get_cashout_probability(
                        chain_info["path"],
                        {"cumulative_risk": cum_risk},
                    )
                    chains.append(
                        SuspiciousChain(
                            path=chain_info["path"],
                            cumulative_risk=round(cum_risk, 2),
                            cashout_probability=cashout_prob,
                            channels=chain_info["channels"],
                            is_mock_score=True,
                        )
                    )

        return chains

    def _find_pattern_chains(
        self,
        start_node: str,
        channel_pattern: list[str],
        window: timedelta,
    ) -> list[dict[str, Any]]:
        """Find chains starting from start_node that match the channel pattern
        within the given time window.
        """
        results: list[dict[str, Any]] = []
        pattern_len = len(channel_pattern)

        # DFS with path tracking
        stack: list[tuple[str, list[str], list[str], str | None]] = [
            (start_node, [start_node], [], None)
        ]

        while stack:
            current, path, channels, first_timestamp = stack.pop()

            if len(channels) == pattern_len:
                # We matched the full pattern
                results.append({"path": list(path), "channels": list(channels)})
                continue

            if len(path) > pattern_len + 1:
                continue

            expected_channel = channel_pattern[len(channels)]

            for _, successor, edge_data in self.graph.out_edges(current, data=True):
                if successor in path:
                    continue  # No cycles

                edge_channel = edge_data.get("channel", "")
                edge_timestamp = edge_data.get("timestamp", "")

                if edge_channel != expected_channel:
                    continue

                # Check temporal window
                if first_timestamp is not None:
                    try:
                        t_first = datetime.fromisoformat(first_timestamp)
                        t_current = datetime.fromisoformat(edge_timestamp)
                        if abs(t_current - t_first) > window:
                            continue
                    except (ValueError, TypeError):
                        pass

                new_first = first_timestamp if first_timestamp else edge_timestamp
                stack.append(
                    (
                        successor,
                        path + [successor],
                        channels + [edge_channel],
                        new_first,
                    )
                )

        return results

    def detect_suspicious_chains(self) -> list[SuspiciousChain]:
        """BFS from high-risk nodes to find chains with cumulative risk > threshold.

        Combines temporal chain fingerprinting with general BFS exploration.
        """
        all_chains: list[SuspiciousChain] = []
        seen_chain_keys: set[str] = set()

        # Get chains from temporal fingerprinting
        temporal = self.detect_temporal_chains()
        for chain in temporal:
            key = "->".join(chain.path)
            if key not in seen_chain_keys:
                seen_chain_keys.add(key)
                all_chains.append(chain)

        # BFS from high-risk nodes
        high_risk_nodes = [
            n for n, d in self.graph.nodes(data=True)
            if d.get("risk_score", 0.0) >= SUSPICIOUS_RISK_THRESHOLD
        ]

        for start in high_risk_nodes:
            bfs_chains = self._bfs_chain_search(start)
            for chain_info in bfs_chains:
                key = "->".join(chain_info["path"])
                if key not in seen_chain_keys:
                    seen_chain_keys.add(key)
                    cum_risk = chain_info["cumulative_risk"]
                    if cum_risk > SUSPICIOUS_RISK_THRESHOLD * 2:
                        cashout_prob = get_cashout_probability(
                            chain_info["path"],
                            {"cumulative_risk": cum_risk},
                        )
                        all_chains.append(
                            SuspiciousChain(
                                path=chain_info["path"],
                                cumulative_risk=round(cum_risk, 2),
                                cashout_probability=cashout_prob,
                                channels=chain_info["channels"],
                                is_mock_score=True,
                            )
                        )

        return all_chains

    def _bfs_chain_search(self, start: str) -> list[dict[str, Any]]:
        """BFS from a starting node to discover chains."""
        results: list[dict[str, Any]] = []
        queue: deque[tuple[str, list[str], list[str], float]] = deque()

        start_risk = self.graph.nodes[start].get("risk_score", 0.0)
        queue.append((start, [start], [], start_risk))

        while queue:
            current, path, channels, cum_risk = queue.popleft()

            if len(path) >= MIN_CHAIN_LENGTH:
                results.append({
                    "path": list(path),
                    "channels": list(channels),
                    "cumulative_risk": round(cum_risk, 2),
                })

            if len(path) >= MAX_CHAIN_LENGTH:
                continue

            for _, successor, edge_data in self.graph.out_edges(current, data=True):
                if successor in path:
                    continue  # No cycles

                succ_risk = self.graph.nodes[successor].get("risk_score", 0.0)
                edge_channel = edge_data.get("channel", "unknown")

                queue.append((
                    successor,
                    path + [successor],
                    channels + [edge_channel],
                    cum_risk + succ_risk,
                ))

        return results

    def get_risk_contribution_breakdown(
        self, node_id: str
    ) -> dict[str, float] | None:
        """Return percentage contributions from velocity, network_exposure,
        anomaly, and channel_risk for a specific node.
        """
        if node_id not in self.graph.nodes:
            return None

        node_data = self.graph.nodes[node_id]
        risk = node_data.get("risk_score", 0.0)

        if risk <= 0:
            return {
                "velocity": 0.0,
                "network_exposure": 0.0,
                "anomaly": 0.0,
                "channel_risk": 0.0,
            }

        # These are approximate percentages based on the breakdown
        # The actual breakdowns are stored in the graph engine
        in_deg = self.graph.in_degree(node_id)
        out_deg = self.graph.out_degree(node_id)
        total_sent = node_data.get("total_sent", 0.0)
        total_received = node_data.get("total_received", 0.0)
        channels = node_data.get("channels_used", set())

        velocity_pct = min(len(node_data.get("tx_timestamps", [])) * 5, 30)
        channel_pct = 20 if "atm" in channels else 10
        anomaly_pct = min(
            (total_sent + total_received) / max(node_data.get("tx_count", 1), 1) / 100,
            25,
        )
        network_pct = 100 - velocity_pct - channel_pct - anomaly_pct

        return {
            "velocity": round(velocity_pct, 1),
            "network_exposure": round(max(network_pct, 5), 1),
            "anomaly": round(anomaly_pct, 1),
            "channel_risk": round(channel_pct, 1),
        }
