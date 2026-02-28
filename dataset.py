# synthetic_dataset.py
import random
from datetime import datetime, timedelta
import csv

ACCOUNTS = [f"A{i:03d}" for i in range(1, 21)]  # 20 accounts
CHANNELS = ["mobile_app", "wallet", "atm"]
OUTPUT_FILE = "synthetic_transactions.csv"

def generate_transaction(timestamp):
    from_account = random.choice(ACCOUNTS)
    # To ensure some chains, choose connected account 50% of time
    if random.random() < 0.5:
        to_account = random.choice([acc for acc in ACCOUNTS if acc != from_account])
    else:
        # occasionally create a high-risk chain
        to_account = random.choice([f"A{i:03d}" for i in range(21, 26)])
    channel = random.choices(CHANNELS, weights=[0.5,0.3,0.2])[0]
    amount = random.randint(100, 5000)
    return {
        "from_account": from_account,
        "to_account": to_account,
        "channel": channel,
        "amount": amount,
        "timestamp": timestamp
    }

def create_dataset(n_transactions=100):
    data = []
    current_time = datetime.now()
    for _ in range(n_transactions):
        tx = generate_transaction(current_time)
        data.append(tx)
        # Increment timestamp by 1-3 minutes to simulate realistic flow
        current_time += timedelta(seconds=random.randint(30,180))
    return data

def save_to_csv(data, file=OUTPUT_FILE):
    with open(file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["from_account","to_account","channel","amount","timestamp"])
        writer.writeheader()
        for row in data:
            writer.writerow({k: (v.isoformat() if k=="timestamp" else v) for k,v in row.items()})

if __name__ == "__main__":
    data = create_dataset(150)  # 150 transactions for prototype
    save_to_csv(data)
    print(f"✅ Synthetic dataset saved to {OUTPUT_FILE}")