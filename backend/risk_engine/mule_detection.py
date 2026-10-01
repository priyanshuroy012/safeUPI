"""
SafeUPI graph-based mule-account detection.

MVP algorithm:
1. Build a directed transaction graph with NetworkX.
2. Calculate interpretable structural/temporal features.
3. Apply weighted rules to produce a mule-like risk score.
4. Return reasons so investigators can understand the flag.

This is NOT a criminal classifier. A high score means "suspicious
fund-flow pattern" and should trigger investigation, not guilt.
"""

from collections import defaultdict
from typing import Any, Dict, Iterable, List

import networkx as nx

from backend.database.models import MuleScore, Transaction


def build_transaction_graph(
    transactions: Iterable[Transaction],
) -> nx.DiGraph:
    """Create a directed weighted transaction graph."""
    graph = nx.DiGraph()

    for tx in transactions:
        graph.add_node(tx.sender)
        graph.add_node(tx.receiver)

        if graph.has_edge(tx.sender, tx.receiver):
            graph[tx.sender][tx.receiver]["amount"] += tx.amount
            graph[tx.sender][tx.receiver]["count"] += 1
        else:
            graph.add_edge(
                tx.sender,
                tx.receiver,
                amount=tx.amount,
                count=1,
            )

    return graph


def calculate_account_features(
    transactions: Iterable[Transaction],
    account_id: str,
) -> Dict[str, float]:
    """Calculate graph and money-flow features for one account."""
    txns = list(transactions)

    incoming = [t for t in txns if t.receiver == account_id]
    outgoing = [t for t in txns if t.sender == account_id]

    incoming_amount = sum(t.amount for t in incoming)
    outgoing_amount = sum(t.amount for t in outgoing)

    unique_senders = len({t.sender for t in incoming})
    unique_receivers = len({t.receiver for t in outgoing})

    flow_through_ratio = (
        outgoing_amount / incoming_amount
        if incoming_amount
        else 0.0
    )

    # In the MVP we use a simple "rapid movement" approximation:
    # count outgoing transactions that occur after incoming transactions
    # for the same account. A production system should calculate exact
    # holding times by matching funds/transaction windows.
    rapid_outgoing_count = 0
    for out_tx in outgoing:
        prior_incoming = [
            in_tx for in_tx in incoming
            if in_tx.timestamp <= out_tx.timestamp
        ]
        if prior_incoming:
            latest_in = max(prior_incoming, key=lambda x: x.timestamp)
            holding_minutes = (
                out_tx.timestamp - latest_in.timestamp
            ).total_seconds() / 60

            if holding_minutes <= 10:
                rapid_outgoing_count += 1

    rapid_flow_ratio = (
        rapid_outgoing_count / len(outgoing)
        if outgoing
        else 0.0
    )

    return {
        "in_degree": float(unique_senders),
        "out_degree": float(unique_receivers),
        "incoming_count": float(len(incoming)),
        "outgoing_count": float(len(outgoing)),
        "incoming_amount": float(incoming_amount),
        "outgoing_amount": float(outgoing_amount),
        "flow_through_ratio": round(flow_through_ratio, 3),
        "rapid_flow_ratio": round(rapid_flow_ratio, 3),
    }


def score_account(
    account_id: str,
    features: Dict[str, float],
) -> MuleScore:
    """
    Weighted rule-based mule score.

    Maximum contribution:
    +20 high in-degree
    +15 high out-degree
    +25 high flow-through
    +25 rapid movement
    +15 many transactions

    Thresholds:
    0-39   LOW
    40-69  MEDIUM
    70-100 HIGH
    """
    score = 0
    reasons: List[str] = []

    if features["in_degree"] >= 10:
        score += 20
        reasons.append("High number of unique incoming counterparties")

    if features["out_degree"] >= 5:
        score += 15
        reasons.append("High number of unique outgoing counterparties")

    if features["flow_through_ratio"] >= 0.80:
        score += 25
        reasons.append("High flow-through ratio")

    if features["rapid_flow_ratio"] >= 0.50:
        score += 25
        reasons.append("Rapid movement of incoming funds")

    if (
        features["incoming_count"] + features["outgoing_count"]
        >= 30
    ):
        score += 15
        reasons.append("High transaction activity")

    score = min(score, 100)

    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    return MuleScore(
        account_id=account_id,
        score=score,
        risk_level=level,
        reasons=reasons or ["No major mule-like pattern detected"],
        features=features,
    )


def detect_mule_accounts(
    transactions: Iterable[Transaction],
) -> List[MuleScore]:
    """Score every account appearing in the transaction graph."""
    txns = list(transactions)

    accounts = {
        account
        for tx in txns
        for account in (tx.sender, tx.receiver)
    }

    results = [
        score_account(
            account_id,
            calculate_account_features(txns, account_id),
        )
        for account_id in accounts
    ]

    return sorted(results, key=lambda x: x.score, reverse=True)


def mule_engine_health() -> Dict[str, str]:
    return {
        "status": "ok",
        "algorithm": "NetworkX graph + weighted explainable rules",
    }
