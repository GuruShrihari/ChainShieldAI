"""FastAPI application for ChainShieldAI.

Provides REST endpoints and WebSocket support for real-time
fraud detection and graph visualization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.data_generator import generate_transactions
from app.graph_engine import GraphEngine
from app.ml_placeholder import get_model_status
from app.models import GraphSnapshot, Stats
from app.risk_model import RiskModel
from app.websocket_manager import WebSocketManager

# --------------------------------------------------------------------------
# App initialization
# --------------------------------------------------------------------------

app = FastAPI(
    title="ChainShieldAI",
    description="Real-Time Intelligent Propagation & Pattern Learning Engine for Fraud Detection",
    version="1.0.0",
)

# CORS for frontend at localhost:3000 and Vite default 5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# Global state
# --------------------------------------------------------------------------

graph_engine = GraphEngine()
ws_manager = WebSocketManager()
transactions: list[dict[str, Any]] = generate_transactions()
transaction_index: int = 0
processed_transactions: list[dict[str, Any]] = []
alerts_fired: int = 0


def _build_snapshot() -> GraphSnapshot:
    """Build a complete graph snapshot for API responses and WS broadcasts."""
    graph_engine.detect_communities()
    risk_model = RiskModel(graph_engine.graph)
    suspicious_chains = risk_model.detect_suspicious_chains()

    nodes = graph_engine.get_nodes()
    edges = graph_engine.get_edges()
    high_risk = graph_engine.get_high_risk_accounts(threshold=6.0)

    stats = Stats(
        total_transactions=len(processed_transactions),
        high_risk_accounts=len(high_risk),
        chains_detected=len(suspicious_chains),
        alerts_fired=alerts_fired,
        ml_model_status=get_model_status(),
    )

    return GraphSnapshot(
        nodes=nodes,
        edges=edges,
        suspicious_chains=suspicious_chains,
        stats=stats,
        timestamp=datetime.now().isoformat(),
    )


# --------------------------------------------------------------------------
# REST endpoints
# --------------------------------------------------------------------------


@app.post("/api/next-transaction")
async def next_transaction() -> dict[str, Any]:
    """Process the next synthetic transaction, propagate risk,
    broadcast via WebSocket, and return the graph snapshot.
    """
    global transaction_index, alerts_fired

    if transaction_index >= len(transactions):
        snapshot = _build_snapshot()
        return {
            "status": "complete",
            "message": "All transactions have been processed",
            "snapshot": snapshot.model_dump(),
        }

    tx = transactions[transaction_index]
    transaction_index += 1
    processed_transactions.append(tx)

    # Add to graph and propagate risk
    graph_engine.add_transaction(tx)
    graph_engine.propagate_risk()

    # Check if this triggered new high-risk accounts
    high_risk = graph_engine.get_high_risk_accounts(threshold=6.0)
    node_risk = graph_engine.graph.nodes.get(tx["to_account"], {}).get("risk_score", 0)
    if node_risk >= 6.0:
        alerts_fired += 1

    sender_risk = graph_engine.graph.nodes.get(tx["from_account"], {}).get("risk_score", 0)
    if sender_risk >= 6.0:
        alerts_fired += 1

    # Build snapshot and broadcast
    snapshot = _build_snapshot()
    await ws_manager.broadcast(snapshot.model_dump())

    return {
        "status": "ok",
        "transaction": tx,
        "transaction_number": transaction_index,
        "total_transactions": len(transactions),
        "snapshot": snapshot.model_dump(),
    }


@app.get("/api/graph")
async def get_graph() -> dict[str, Any]:
    """Return the full graph snapshot."""
    snapshot = _build_snapshot()
    return snapshot.model_dump()


@app.post("/api/reset")
async def reset_graph() -> dict[str, str]:
    """Reset the graph and transaction index to initial state."""
    global transaction_index, processed_transactions, alerts_fired

    graph_engine.reset()
    transaction_index = 0
    processed_transactions = []
    alerts_fired = 0

    # Broadcast empty state
    snapshot = _build_snapshot()
    await ws_manager.broadcast(snapshot.model_dump())

    return {"status": "ok", "message": "Graph and simulation reset"}


@app.get("/api/stats")
async def get_stats() -> dict[str, Any]:
    """Return current statistics."""
    high_risk = graph_engine.get_high_risk_accounts(threshold=6.0)
    risk_model = RiskModel(graph_engine.graph)
    chains = risk_model.detect_suspicious_chains()

    stats = Stats(
        total_transactions=len(processed_transactions),
        high_risk_accounts=len(high_risk),
        chains_detected=len(chains),
        alerts_fired=alerts_fired,
        ml_model_status=get_model_status(),
    )
    return stats.model_dump()


@app.get("/api/transactions")
async def get_transactions() -> list[dict[str, Any]]:
    """Return the processed transaction log."""
    return processed_transactions


# --------------------------------------------------------------------------
# WebSocket endpoint
# --------------------------------------------------------------------------


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time graph updates."""
    await ws_manager.connect(websocket)
    try:
        # Send current state on connect
        snapshot = _build_snapshot()
        await websocket.send_json(snapshot.model_dump())

        # Keep connection alive, waiting for client messages
        while True:
            # We don't process client messages, just keep the connection open
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
