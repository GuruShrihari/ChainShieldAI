"""ML Trainer — Train an XGBoost mule-detection model from the real dataset.

Usage:
    cd backend
    python -m app.ml_trainer

Reads data/accounts.csv and data/transactions.csv, engineers per-account
features, trains an XGBoost classifier, and saves the model artifact to
backend/app/model/mule_detector.joblib.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # ChainShieldAI/
DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = Path(__file__).resolve().parent / "model"

ACCOUNTS_CSV = DATA_DIR / "accounts.csv"
TRANSACTIONS_CSV = DATA_DIR / "transactions.csv"
MODEL_PATH = MODEL_DIR / "mule_detector.joblib"
META_PATH = MODEL_DIR / "model_meta.json"


# ---------------------------------------------------------------------------
# Feature Engineering
# ---------------------------------------------------------------------------
def build_features(accounts_df: pd.DataFrame, tx_df: pd.DataFrame) -> pd.DataFrame:
    """Engineer per-account features from raw transactions and account data."""

    # --- Sender-side aggregates ---
    sender_agg = (
        tx_df.groupby("SENDER_ACCOUNT_ID")
        .agg(
            tx_count_sent=("TX_ID", "count"),
            total_sent=("TX_AMOUNT", "sum"),
            avg_sent=("TX_AMOUNT", "mean"),
            max_sent=("TX_AMOUNT", "max"),
            unique_receivers=("RECEIVER_ACCOUNT_ID", "nunique"),
        )
        .rename_axis("ACCOUNT_ID")
    )

    # --- Receiver-side aggregates ---
    receiver_agg = (
        tx_df.groupby("RECEIVER_ACCOUNT_ID")
        .agg(
            tx_count_received=("TX_ID", "count"),
            total_received=("TX_AMOUNT", "sum"),
            avg_received=("TX_AMOUNT", "mean"),
            max_received=("TX_AMOUNT", "max"),
            unique_senders=("SENDER_ACCOUNT_ID", "nunique"),
        )
        .rename_axis("ACCOUNT_ID")
    )

    # --- Fraud-transaction counts per account (as sender) ---
    fraud_sent = (
        tx_df[tx_df["IS_FRAUD"] == True]
        .groupby("SENDER_ACCOUNT_ID")
        .agg(fraud_tx_sent=("TX_ID", "count"))
        .rename_axis("ACCOUNT_ID")
    )

    fraud_received = (
        tx_df[tx_df["IS_FRAUD"] == True]
        .groupby("RECEIVER_ACCOUNT_ID")
        .agg(fraud_tx_received=("TX_ID", "count"))
        .rename_axis("ACCOUNT_ID")
    )

    # --- Merge everything onto accounts ---
    features = accounts_df[["ACCOUNT_ID", "INIT_BALANCE", "ACCOUNT_TYPE", "COUNTRY"]].copy()
    features = features.set_index("ACCOUNT_ID")

    features = features.join(sender_agg, how="left")
    features = features.join(receiver_agg, how="left")
    features = features.join(fraud_sent, how="left")
    features = features.join(fraud_received, how="left")
    features = features.fillna(0)

    # --- Derived features ---
    features["total_tx"] = features["tx_count_sent"] + features["tx_count_received"]
    features["total_volume"] = features["total_sent"] + features["total_received"]

    # Fan-in ratio (mules tend to have high fan-in)
    features["fan_in_ratio"] = features["unique_senders"] / (
        features["unique_senders"] + features["unique_receivers"] + 1e-6
    )

    # Fan-out ratio
    features["fan_out_ratio"] = features["unique_receivers"] / (
        features["unique_senders"] + features["unique_receivers"] + 1e-6
    )

    # Send/receive ratio (mules receive more than they send, then cash out)
    features["send_receive_ratio"] = features["total_sent"] / (
        features["total_received"] + 1e-6
    )

    # Average transaction size overall
    features["avg_tx_amount"] = features["total_volume"] / (
        features["total_tx"] + 1e-6
    )

    # Is individual account
    features["is_individual"] = (features["ACCOUNT_TYPE"] == "I").astype(int)

    # Country encoding (one-hot would be large, use frequency encoding)
    country_freq = features["COUNTRY"].value_counts(normalize=True)
    features["country_freq"] = features["COUNTRY"].map(country_freq)

    # Drop non-numeric columns
    features = features.drop(columns=["ACCOUNT_TYPE", "COUNTRY"])

    return features


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def train_model() -> None:
    """Load data, engineer features, train XGBoost, and save the model."""
    print("=" * 60)
    print("ChainShieldAI — ML Mule Detector Training")
    print("=" * 60)

    # Load CSVs
    print("\n[1/5] Loading datasets...")
    accounts_df = pd.read_csv(ACCOUNTS_CSV)
    tx_df = pd.read_csv(TRANSACTIONS_CSV)

    # Normalize IS_FRAUD in transactions (could be string or bool)
    tx_df["IS_FRAUD"] = tx_df["IS_FRAUD"].astype(str).str.strip().str.lower() == "true"

    print(f"  Accounts: {len(accounts_df):,}")
    print(f"  Transactions: {len(tx_df):,}")

    # Build features
    print("\n[2/5] Engineering features...")
    features = build_features(accounts_df, tx_df)
    print(f"  Feature columns: {list(features.columns)}")
    print(f"  Shape: {features.shape}")

    # Labels
    label_map = accounts_df.set_index("ACCOUNT_ID")["IS_FRAUD"]
    label_map = label_map.astype(str).str.strip().str.lower() == "true"
    y = label_map.reindex(features.index).astype(int)

    print(f"\n  Class distribution:")
    print(f"    Legitimate: {(y == 0).sum():,}")
    print(f"    Mule/Fraud: {(y == 1).sum():,}")
    print(f"    Fraud ratio: {y.mean():.4f}")

    X = features.values.astype(np.float32)
    feature_names = list(features.columns)

    # Train/test split
    print("\n[3/5] Splitting data (80/20 stratified)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    # Handle class imbalance
    n_negative = (y_train == 0).sum()
    n_positive = (y_train == 1).sum()
    scale_pos = n_negative / max(n_positive, 1)

    # Train XGBoost
    print("\n[4/5] Training XGBoost classifier...")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=scale_pos,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    roc_auc = roc_auc_score(y_test, y_proba)

    print("\n  Classification Report:")
    report = classification_report(y_test, y_pred, target_names=["Legitimate", "Mule"])
    print(report)
    print(f"  ROC-AUC: {roc_auc:.4f}")

    # Feature importance
    importances = model.feature_importances_
    importance_pairs = sorted(
        zip(feature_names, importances), key=lambda x: x[1], reverse=True
    )
    print("\n  Top Feature Importances:")
    for name, imp in importance_pairs[:10]:
        print(f"    {name:25s} {imp:.4f}")

    # Save model
    print(f"\n[5/5] Saving model to {MODEL_PATH}...")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    artifact = {
        "model": model,
        "feature_names": feature_names,
    }
    joblib.dump(artifact, MODEL_PATH)

    # Save metadata
    report_dict = classification_report(y_test, y_pred, target_names=["Legitimate", "Mule"], output_dict=True)
    mule_key = "Mule"
    meta = {
        "version": "1.0.0",
        "roc_auc": round(roc_auc, 4),
        "accuracy": round(report_dict["accuracy"], 4),
        "precision_mule": round(report_dict[mule_key]["precision"], 4),
        "recall_mule": round(report_dict[mule_key]["recall"], 4),
        "f1_mule": round(report_dict[mule_key]["f1-score"], 4),
        "feature_names": feature_names,
        "n_train": len(X_train),
        "n_test": len(X_test),
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"  Model saved: {MODEL_PATH}")
    print(f"  Metadata saved: {META_PATH}")
    print("\n✅ Training complete!")


if __name__ == "__main__":
    train_model()
