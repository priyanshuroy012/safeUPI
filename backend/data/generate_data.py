#!/usr/bin/env python3
"""
Generate a synthetic SafeUPI dataset.

The generated data is intentionally synthetic and must not be treated as
real financial information.
"""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


BANKS = ["DemoBank-A", "DemoBank-B", "DemoBank-C", "DemoBank-D"]
CITIES = [
    "Delhi", "Mumbai", "Bengaluru", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Jaipur", "Lucknow", "Ahmedabad"
]
CATEGORIES = [
    "Grocery", "Food", "Utilities", "Shopping", "Travel",
    "Education", "Healthcare", "Services", "P2P"
]
CHANNELS = ["UPI", "QR", "COLLECT"]


def make_accounts(n: int, rng: random.Random, np_rng: np.random.Generator) -> pd.DataFrame:
    rows = []

    # Keep a small synthetic mule population so graph/risk experiments have
    # a meaningful minority class.
    mule_count = max(1, int(n * 0.06))
    mule_ids = set(rng.sample(range(n), mule_count))

    for i in range(n):
        account_id = f"ACC{i + 1:05d}"
        name = f"Demo User {i + 1:04d}"
        upi_id = f"user{i + 1:05d}@safeupi"
        is_mule = i in mule_ids

        if is_mule:
            risk_level = "high"
        else:
            risk_level = rng.choices(
                ["low", "medium", "high"],
                weights=[0.76, 0.20, 0.04],
                k=1,
            )[0]

        created = datetime(2024, 1, 1) + timedelta(
            days=rng.randint(0, 900),
            hours=rng.randint(0, 23),
        )

        rows.append(
            {
                "account_id": account_id,
                "name": name,
                "upi_id": upi_id,
                "bank": rng.choice(BANKS),
                "city": rng.choice(CITIES),
                "account_type": rng.choices(
                    ["customer", "merchant"],
                    weights=[0.86, 0.14],
                    k=1,
                )[0],
                "risk_level": risk_level,
                "is_mule": int(is_mule),
                "created_at": created.isoformat(timespec="seconds"),
            }
        )

    return pd.DataFrame(rows)


def make_transactions(
    accounts: pd.DataFrame,
    n: int,
    rng: random.Random,
    np_rng: np.random.Generator,
) -> pd.DataFrame:
    account_ids = accounts["account_id"].tolist()
    mule_ids = accounts.loc[accounts["is_mule"] == 1, "account_id"].tolist()

    start = datetime(2026, 1, 1)
    rows = []

    for i in range(n):
        # Bias some transactions toward mule accounts to create a useful
        # synthetic network pattern.
        if mule_ids and rng.random() < 0.18:
            receiver = rng.choice(mule_ids)
            sender = rng.choice(account_ids)
            if sender == receiver:
                sender = rng.choice(account_ids)
        else:
            sender, receiver = rng.sample(account_ids, 2)

        timestamp = start + timedelta(
            minutes=rng.randint(0, 60 * 24 * 180)
        )

        # Log-normal amounts approximate the long-tail shape of payment sizes
        # without claiming to represent real UPI behavior.
        amount = round(float(np_rng.lognormal(mean=5.0, sigma=0.9)), 2)
        amount = min(max(amount, 10.0), 100000.0)

        receiver_is_mule = int(
            accounts.loc[
                accounts["account_id"] == receiver, "is_mule"
            ].iloc[0]
        )

        flagged_probability = 0.03 + (0.20 if receiver_is_mule else 0.0)
        is_flagged = int(rng.random() < flagged_probability)

        status = rng.choices(
            ["SUCCESS", "FAILED"],
            weights=[0.96, 0.04],
            k=1,
        )[0]

        rows.append(
            {
                "transaction_id": f"TXN{i + 1:08d}",
                "sender_id": sender,
                "receiver_id": receiver,
                "amount": amount,
                "timestamp": timestamp.isoformat(timespec="seconds"),
                "channel": rng.choice(CHANNELS),
                "status": status,
                "device_id": f"DEV{rng.randint(1, max(10, int(len(account_ids) * 0.75))):06d}",
                "ip_address": f"10.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}",
                "merchant_category": rng.choice(CATEGORIES),
                "is_flagged": is_flagged,
                "risk_score": round(
                    min(
                        0.99,
                        max(
                            0.01,
                            0.15
                            + 0.50 * is_flagged
                            + 0.25 * receiver_is_mule
                            + float(np_rng.normal(0, 0.08)),
                        ),
                    ),
                    4,
                ),
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic SafeUPI data")
    parser.add_argument("--accounts", type=int, default=200)
    parser.add_argument("--transactions", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()

    if args.accounts < 2:
        raise ValueError("--accounts must be at least 2")
    if args.transactions < 1:
        raise ValueError("--transactions must be positive")

    rng = random.Random(args.seed)
    np_rng = np.random.default_rng(args.seed)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    accounts = make_accounts(args.accounts, rng, np_rng)
    transactions = make_transactions(accounts, args.transactions, rng, np_rng)

    accounts.to_csv(args.output_dir / "accounts.csv", index=False)
    transactions.to_csv(args.output_dir / "transactions.csv", index=False)

    print(f"Generated {len(accounts):,} accounts")
    print(f"Generated {len(transactions):,} transactions")
    print(f"Output: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
