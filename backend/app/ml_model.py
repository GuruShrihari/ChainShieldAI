"""ML Model — Real XGBoost mule detection integration.

Loads the trained mule-detection model and provides scoring functions
used throughout the application. Falls back to mock behavior if the
model file is not found.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------
MODEL_DIR = Path(__file__).resolve().parent / "model"
MODEL_PATH = MODEL_DIR / "mule_detector.joblib"
META_PATH = MODEL_DIR / "model_meta.json"

_model = None
_feature_names: list[str] = []
_meta: dict[str, Any] = {}
_model_loaded = False


def _load_model() -> None:
    """Load the trained model and metadata. Called once at import time."""
    global _model, _feature_names, _meta, _model_loaded

    if not MODEL_PATH.exists():
        logger.warning(
            "ML model not found at %s — falling back to mock scoring.", MODEL_PATH
        )
        return

    try:
        import joblib

        artifact = joblib.load(MODEL_PATH)
        _model = artifact["model"]
        _feature_names = artifact["feature_names"]

        if META_PATH.exists():
            with open(META_PATH) as f:
                _meta = json.load(f)

        _model_loaded = True
        logger.info("ML model loaded: version=%s, roc_auc=%s",
                     _meta.get("version", "?"), _meta.get("roc_auc", "?"))
    except Exception as e:
        logger.error("Failed to load ML model: %s", e)


# Load on import
_load_model()


# ---------------------------------------------------------------------------
# Feature extraction helper
# ---------------------------------------------------------------------------
def _extract_features_from_node(node_data: dict[str, Any]) -> np.ndarray:
    """Build the feature vector for a single account from graph node data.

    Maps the graph-engine node attributes to the same features used during
    training. Some training-time features (like fraud_tx_sent) are not
    available at runtime, so we set them to 0.
    """
    total_sent = float(node_data.get("total_sent", 0))
    total_received = float(node_data.get("total_received", 0))
    tx_count = int(node_data.get("tx_count", 0))
    channels = node_data.get("channels_used", set())
    if isinstance(channels, (set, frozenset)):
        channels = list(channels)

    # Approximate the training features from available runtime data
    # in-degree / out-degree aren't directly on the node, use tx_count as proxy
    tx_count_sent = tx_count // 2 + 1  # rough split
    tx_count_received = tx_count - tx_count_sent

    unique_counterparties = max(1, tx_count // 3)  # rough estimate

    features = {
        "INIT_BALANCE": 0.0,  # not available at runtime
        "tx_count_sent": tx_count_sent,
        "total_sent": total_sent,
        "avg_sent": total_sent / max(tx_count_sent, 1),
        "max_sent": total_sent / max(tx_count_sent, 1) * 1.5,  # estimate
        "unique_receivers": unique_counterparties,
        "tx_count_received": tx_count_received,
        "total_received": total_received,
        "avg_received": total_received / max(tx_count_received, 1),
        "max_received": total_received / max(tx_count_received, 1) * 1.5,
        "unique_senders": unique_counterparties,
        "fraud_tx_sent": 0,  # unknown at runtime
        "fraud_tx_received": 0,  # unknown at runtime
        "total_tx": tx_count,
        "total_volume": total_sent + total_received,
        "fan_in_ratio": unique_counterparties / (2 * unique_counterparties + 1e-6),
        "fan_out_ratio": unique_counterparties / (2 * unique_counterparties + 1e-6),
        "send_receive_ratio": total_sent / (total_received + 1e-6),
        "avg_tx_amount": (total_sent + total_received) / max(tx_count, 1),
        "is_individual": 1,  # default assumption
        "country_freq": 0.5,  # default assumption
    }

    # Order features to match training feature order
    return np.array(
        [features.get(name, 0.0) for name in _feature_names], dtype=np.float32
    ).reshape(1, -1)


def _extract_features_from_dict(features: dict[str, Any]) -> np.ndarray:
    """Build feature vector from a pre-computed feature dict (e.g. from graph_engine)."""
    return np.array(
        [features.get(name, 0.0) for name in _feature_names], dtype=np.float32
    ).reshape(1, -1)


# ---------------------------------------------------------------------------
# Public API (replaces ml_placeholder functions)
# ---------------------------------------------------------------------------
def get_cashout_probability(chain: list[str], features: dict[str, Any]) -> float:
    """Return the ML-predicted cash-out probability for a chain.

    Uses the aggregate features from the chain's nodes to predict
    the likelihood of this chain being a mule cash-out pattern.
    """
    if not _model_loaded:
        # Mock fallback
        chain_len = len(chain)
        total_risk = features.get("cumulative_risk", 0.0)
        base = 0.25 + chain_len * 0.1
        risk_factor = min(total_risk / 30.0, 0.4)
        hash_jitter = (sum(ord(c) for c in "".join(chain)) % 17) * 0.01
        return min(round(base + risk_factor + hash_jitter, 3), 0.95)

    try:
        # Build an aggregate feature vector from the chain features
        X = _extract_features_from_dict(features)
        proba = float(_model.predict_proba(X)[0, 1])
        return round(proba, 3)
    except Exception as e:
        logger.error("ML prediction failed for chain: %s", e)
        return 0.5


def get_model_risk_contribution(account_id: str, node_data: dict[str, Any] | None = None) -> float:
    """Return ML-predicted mule probability for a specific account.

    If node_data is provided (from the graph engine), uses it for prediction.
    Otherwise returns a default score.
    """
    if not _model_loaded or node_data is None:
        # Mock fallback
        hash_val = sum(ord(c) for c in str(account_id)) % 100
        return round(hash_val / 100.0 * 3.0, 2)

    try:
        X = _extract_features_from_node(node_data)
        proba = float(_model.predict_proba(X)[0, 1])
        return round(proba * 3.0, 2)  # Scale to 0-3 range for UI consistency
    except Exception as e:
        logger.error("ML risk contribution failed for %s: %s", account_id, e)
        return 0.0


def get_mule_probability(node_data: dict[str, Any]) -> float:
    """Return the raw ML-predicted mule probability (0-1) for an account."""
    if not _model_loaded:
        return 0.0

    try:
        X = _extract_features_from_node(node_data)
        proba = float(_model.predict_proba(X)[0, 1])
        return round(proba, 4)
    except Exception as e:
        logger.error("ML mule probability prediction failed: %s", e)
        return 0.0


def get_model_status() -> dict[str, Any]:
    """Return model status info for the /api/stats endpoint."""
    if not _model_loaded:
        return {
            "status": "pending",
            "version": None,
            "accuracy": None,
            "message": "ML model not yet integrated",
        }

    return {
        "status": "active",
        "version": _meta.get("version", "1.0.0"),
        "accuracy": _meta.get("accuracy"),
        "roc_auc": _meta.get("roc_auc"),
        "f1_mule": _meta.get("f1_mule"),
        "message": "XGBoost mule detector loaded",
    }


def is_model_loaded() -> bool:
    """Return whether the ML model is successfully loaded."""
    return _model_loaded
