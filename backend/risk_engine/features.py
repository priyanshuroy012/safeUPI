"""
SafeUPI feature engineering.

Goal:
Convert raw transactions into interpretable signals for the risk engine
and graph-based mule detector.

For the MVP we deliberately favor explainability over a complicated
black-box feature pipeline.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean
from typing import Dict, Iterable, List

from models import RiskFeatures, Transaction


def transaction_velocity(
    transactions: Iterable[Transaction],
    account_id: str,
    window_minutes: int = 10,
) -> float:
    """Count outgoing transactions from an account inside a time window."""
    txns = [
        t for t in transactions
        if t.sender == account_id
    ]

    if not txns:
        return 0.0

    txns.sort(key=lambda x: x.timestamp)

    max_count = 0
    left = 0

    for right in range(len(txns)):
        while (
            txns[right].timestamp - txns[left].timestamp
            > timedelta(minutes=window_minutes)
        ):
            left += 1

        max_count = max(max_count, right - left + 1)

    return float(max_count)


def account_graph_features(
    transactions: Iterable[Transaction],
    account_id: str,
) -> Dict[str, float]:
    """
    Calculate basic graph/flow features for an account.

    Features:
    - in_degree
    - out_degree
    - incoming/outgoing amount
    - flow-through ratio
    - velocity
    """
    txns = list(transactions)

    incoming = [t for t in txns if t.receiver == account_id]
    outgoing = [t for t in txns if t.sender == account_id]

    unique_senders = len({t.sender for t in incoming})
    unique_receivers = len({t.receiver for t in outgoing})

    incoming_amount = sum(t.amount for t in incoming)
    outgoing_amount = sum(t.amount for t in outgoing)

    flow_through_ratio = (
        outgoing_amount / incoming_amount
        if incoming_amount > 0
        else 0.0
    )

    velocity = transaction_velocity(txns, account_id)

    return {
        "in_degree": float(unique_senders),
        "out_degree": float(unique_receivers),
        "incoming_amount": incoming_amount,
        "outgoing_amount": outgoing_amount,
        "flow_through_ratio": flow_through_ratio,
        "velocity": velocity,
    }


def build_payment_features(
    payment_amount: float,
    user_average_amount: float,
    is_new_recipient: bool,
    unusual_frequency: bool,
    recipient_risk_score: float,
    recipient_in_degree: int,
    recipient_out_degree: int,
    recipient_flow_through_ratio: float,
    recipient_age_days: float = 0.0,
) -> RiskFeatures:
    """Build explainable features for one payment."""
    if user_average_amount <= 0:
        amount_deviation = 1.0
    else:
        amount_deviation = payment_amount / user_average_amount

    return RiskFeatures(
        amount_deviation=round(amount_deviation, 2),
        is_new_recipient=is_new_recipient,
        recipient_age_days=recipient_age_days,
        transaction_velocity=0.0,
        unusual_frequency=unusual_frequency,
        recipient_risk_score=recipient_risk_score,
        recipient_in_degree=recipient_in_degree,
        recipient_out_degree=recipient_out_degree,
        recipient_flow_through_ratio=round(
            recipient_flow_through_ratio, 3
        ),
        user_history_average=user_average_amount,
    )
