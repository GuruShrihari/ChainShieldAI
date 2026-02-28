"""
⚠️ PLACEHOLDER — ML model integration pending. Do not implement training logic here.

Future: This module will load a trained LightGBM/XGBoost model and score chains.
For now, all functions return realistic mock values.
"""


def get_cashout_probability(chain: list, features: dict) -> float:
    """
    ⚠️ PLACEHOLDER — ML model integration pending. Do not implement training logic here.

    Mock: returns a deterministic pseudo-random value based on chain length + risk.
    Replace with model.predict() when ML module is ready.
    """
    chain_len = len(chain)
    total_risk = features.get("cumulative_risk", 0.0)

    # Deterministic mock formula: longer chains + higher risk = higher probability
    base = 0.25 + chain_len * 0.1
    risk_factor = min(total_risk / 30.0, 0.4)
    hash_jitter = (sum(ord(c) for c in "".join(chain)) % 17) * 0.01

    return min(round(base + risk_factor + hash_jitter, 3), 0.95)


def get_model_risk_contribution(account_id: str) -> float:
    """
    ⚠️ PLACEHOLDER — ML model integration pending. Do not implement training logic here.

    Mock: returns a fixed placeholder score derived from the account ID.
    Replace with model feature importance when ML module is ready.
    """
    # Deterministic mock based on account ID characters
    hash_val = sum(ord(c) for c in account_id) % 100
    return round(hash_val / 100.0 * 3.0, 2)


def get_model_status() -> dict:
    """
    ⚠️ PLACEHOLDER — ML model integration pending. Do not implement training logic here.

    Returns model readiness info for the /api/stats endpoint.
    """
    return {
        "status": "pending",
        "version": None,
        "accuracy": None,
        "message": "ML model not yet integrated",
    }
