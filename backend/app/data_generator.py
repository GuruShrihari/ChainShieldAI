"""Synthetic transaction data generator for ChainShieldAI.

Generates 200 transactions in-memory at startup with injected suspicious
mule chain patterns. No CSV files or disk I/O.
"""

import random
from datetime import datetime, timedelta
from typing import Any

# Fixed seed for reproducible demo data
_RNG = random.Random(42)

ACCOUNTS = [f"ACC_{i:03d}" for i in range(1, 51)]  # ACC_001 to ACC_050
CHANNELS = ["mobile", "wallet", "atm", "bank"]
CHANNEL_WEIGHTS = [0.60, 0.20, 0.15, 0.05]
LOCATIONS = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin",
    "Mumbai", "Delhi", "London", "Singapore", "Dubai",
]

NUM_TRANSACTIONS = 200
NUM_SUSPICIOUS_CHAINS = 17  # 15-20 range


def _generate_mule_chains() -> list[list[dict[str, Any]]]:
    """Generate 15-20 suspicious mule chain transaction sequences.

    Each chain is 3-6 accounts long following patterns like:
    account A → B → C → ATM_withdrawal
    """
    chains: list[list[dict[str, Any]]] = []
    used_accounts: set[str] = set()

    for i in range(NUM_SUSPICIOUS_CHAINS):
        chain_length = _RNG.randint(3, 6)
        # Pick accounts for this chain, preferring unused ones
        available = [a for a in ACCOUNTS if a not in used_accounts]
        if len(available) < chain_length:
            available = ACCOUNTS.copy()

        chain_accounts = _RNG.sample(available, min(chain_length, len(available)))
        used_accounts.update(chain_accounts)

        # Generate transactions along the chain
        # Pattern: Mobile → Wallet → ... → ATM (last hop is always ATM withdrawal)
        chain_channels = ["mobile"] + \
            [_RNG.choice(["mobile", "wallet"]) for _ in range(chain_length - 2)] + \
            ["atm"]

        base_time = datetime(2026, 2, 28, 10, 0, 0) + timedelta(minutes=i * 15)
        base_amount = _RNG.uniform(1500, 4500)

        chain_txs: list[dict[str, Any]] = []
        for j in range(len(chain_accounts) - 1):
            # Amount slightly decreases along chain (mule fee skimming)
            amount = round(base_amount * (1 - j * 0.05) + _RNG.uniform(-100, 100), 2)
            amount = max(amount, 100)

            tx = {
                "tx_id": f"TX_CHAIN_{i:02d}_{j:02d}",
                "from_account": chain_accounts[j],
                "to_account": chain_accounts[j + 1],
                "amount": amount,
                "channel": chain_channels[j],
                "timestamp": (base_time + timedelta(minutes=j * _RNG.randint(5, 25))).isoformat(),
                "location": _RNG.choice(LOCATIONS),
            }
            chain_txs.append(tx)

        chains.append(chain_txs)

    return chains


def _generate_normal_transactions(
    count: int,
    start_time: datetime,
) -> list[dict[str, Any]]:
    """Generate normal (non-suspicious) transactions."""
    transactions: list[dict[str, Any]] = []
    current_time = start_time

    for i in range(count):
        from_acc = _RNG.choice(ACCOUNTS)
        to_acc = _RNG.choice([a for a in ACCOUNTS if a != from_acc])
        channel = _RNG.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]
        amount = round(_RNG.uniform(50, 5000), 2)

        tx = {
            "tx_id": f"TX_NORM_{i:04d}",
            "from_account": from_acc,
            "to_account": to_acc,
            "amount": amount,
            "channel": channel,
            "timestamp": current_time.isoformat(),
            "location": _RNG.choice(LOCATIONS),
        }
        transactions.append(tx)
        current_time += timedelta(seconds=_RNG.randint(30, 180))

    return transactions


def generate_transactions() -> list[dict[str, Any]]:
    """Generate all 200 synthetic transactions.

    Mixes normal transactions with injected suspicious mule chains,
    then sorts by timestamp to simulate a realistic stream.
    """
    # Generate suspicious chains first
    chains = _generate_mule_chains()
    chain_txs: list[dict[str, Any]] = []
    for chain in chains:
        chain_txs.extend(chain)

    # Fill remaining slots with normal transactions
    normal_count = NUM_TRANSACTIONS - len(chain_txs)
    normal_count = max(normal_count, 0)
    normal_txs = _generate_normal_transactions(
        normal_count,
        datetime(2026, 2, 28, 9, 0, 0),
    )

    # Combine and sort by timestamp
    all_txs = chain_txs + normal_txs
    all_txs.sort(key=lambda tx: tx["timestamp"])

    # Re-assign sequential tx_ids for clean ordering
    for idx, tx in enumerate(all_txs):
        if not tx["tx_id"].startswith("TX_CHAIN"):
            tx["tx_id"] = f"TX_{idx:04d}"

    return all_txs


def load_real_transactions(batch_size: int = 500) -> list[dict[str, Any]]:
    """Load transactions from the real CSV dataset.

    Reads data/transactions.csv, maps columns to the format expected by
    the graph engine, and returns up to `batch_size` transactions sorted
    by timestamp.

    Falls back to generate_transactions() if the CSV is not found.
    """
    from pathlib import Path

    import pandas as pd

    project_root = Path(__file__).resolve().parent.parent.parent
    tx_csv = project_root / "data" / "transactions.csv"

    if not tx_csv.exists():
        print(f"[WARNING] {tx_csv} not found — falling back to synthetic data")
        return generate_transactions()

    # Channel mapping from TX_TYPE to our channel names
    channel_map: dict[str, str] = {
        "TRANSFER": "bank",
        "CASH-IN": "atm",
        "CASH-OUT": "atm",
        "DEBIT": "mobile",
        "PAYMENT": "wallet",
    }

    df = pd.read_csv(tx_csv, nrows=batch_size)

    transactions: list[dict[str, Any]] = []
    base_time = datetime(2026, 2, 28, 9, 0, 0)

    for _, row in df.iterrows():
        tx_type = str(row.get("TX_TYPE", "TRANSFER"))
        channel = channel_map.get(tx_type, "bank")

        # Map TIMESTAMP (integer step) to ISO datetime
        step = int(row.get("TIMESTAMP", 0))
        tx_time = base_time + timedelta(minutes=step * 5)

        tx: dict[str, Any] = {
            "tx_id": f"TX_{int(row['TX_ID']):06d}",
            "from_account": f"ACC_{int(row['SENDER_ACCOUNT_ID']):05d}",
            "to_account": f"ACC_{int(row['RECEIVER_ACCOUNT_ID']):05d}",
            "amount": round(float(row["TX_AMOUNT"]), 2),
            "channel": channel,
            "timestamp": tx_time.isoformat(),
            "location": "Unknown",
        }
        transactions.append(tx)

    transactions.sort(key=lambda t: t["timestamp"])
    return transactions

