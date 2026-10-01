#!/usr/bin/env python3
"""
SafeUPI transaction graph utilities.

Accounts are represented as nodes. Successful transactions are represented
as directed edges from sender -> receiver. Multiple transactions between the
same pair are aggregated while preserving count and total amount.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import networkx as nx
import pandas as pd


class TransactionGraph:
    """Build and analyze a directed account-transaction graph."""

    def __init__(self, graph: nx.DiGraph | None = None) -> None:
        self.graph = graph if graph is not None else nx.DiGraph()

    @classmethod
    def from_dataframes(
        cls,
        transactions: pd.DataFrame,
        accounts: pd.DataFrame | None = None,
        successful_only: bool = True,
    ) -> "TransactionGraph":
        required = {"sender_id", "receiver_id", "amount"}
        missing = required - set(transactions.columns)
        if missing:
            raise ValueError(
                f"transactions is missing required columns: {sorted(missing)}"
            )

        tx = transactions.copy()

        if successful_only and "status" in tx.columns:
            tx = tx[tx["status"].astype(str).str.upper() == "SUCCESS"]

        tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0.0)

        graph = nx.DiGraph()

        if accounts is not None and "account_id" in accounts.columns:
            for _, row in accounts.iterrows():
                node_id = str(row["account_id"])
                attrs = {
                    key: value
                    for key, value in row.to_dict().items()
                    if key != "account_id"
                }
                graph.add_node(node_id, **attrs)

        grouped = (
            tx.groupby(["sender_id", "receiver_id"], as_index=False)
            .agg(
                transaction_count=("amount", "size"),
                total_amount=("amount", "sum"),
                average_amount=("amount", "mean"),
            )
        )

        for _, row in grouped.iterrows():
            sender = str(row["sender_id"])
            receiver = str(row["receiver_id"])

            graph.add_edge(
                sender,
                receiver,
                transaction_count=int(row["transaction_count"]),
                total_amount=float(row["total_amount"]),
                average_amount=float(row["average_amount"]),
            )

        return cls(graph)

    @classmethod
    def from_csv(
        cls,
        transactions_path: str | Path,
        accounts_path: str | Path | None = None,
        successful_only: bool = True,
    ) -> "TransactionGraph":
        transactions = pd.read_csv(transactions_path)
        accounts = (
            pd.read_csv(accounts_path)
            if accounts_path is not None
            else None
        )
        return cls.from_dataframes(
            transactions,
            accounts,
            successful_only=successful_only,
        )

    def summary(self) -> dict:
        total_value = sum(
            data.get("total_amount", 0.0)
            for _, _, data in self.graph.edges(data=True)
        )

        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "total_transferred": round(total_value, 2),
            "density": round(nx.density(self.graph), 6),
        }

    def top_accounts_by_degree(self, n: int = 10) -> pd.DataFrame:
        rows = []

        for node in self.graph.nodes:
            rows.append(
                {
                    "account_id": node,
                    "in_degree": self.graph.in_degree(node),
                    "out_degree": self.graph.out_degree(node),
                    "total_degree": self.graph.degree(node),
                }
            )

        return (
            pd.DataFrame(rows)
            .sort_values(
                ["total_degree", "in_degree"],
                ascending=False,
            )
            .head(n)
            .reset_index(drop=True)
        )

    def account_flow_features(self) -> pd.DataFrame:
        rows = []

        for node in self.graph.nodes:
            incoming = list(self.graph.in_edges(node, data=True))
            outgoing = list(self.graph.out_edges(node, data=True))

            incoming_amount = sum(
                float(data.get("total_amount", 0.0))
                for _, _, data in incoming
            )
            outgoing_amount = sum(
                float(data.get("total_amount", 0.0))
                for _, _, data in outgoing
            )

            rows.append(
                {
                    "account_id": node,
                    "incoming_transactions": sum(
                        int(data.get("transaction_count", 0))
                        for _, _, data in incoming
                    ),
                    "outgoing_transactions": sum(
                        int(data.get("transaction_count", 0))
                        for _, _, data in outgoing
                    ),
                    "unique_senders": len(incoming),
                    "unique_receivers": len(outgoing),
                    "incoming_amount": round(incoming_amount, 2),
                    "outgoing_amount": round(outgoing_amount, 2),
                    "flow_ratio": round(
                        incoming_amount / max(outgoing_amount, 1e-9),
                        4,
                    ),
                }
            )

        return pd.DataFrame(rows)

    def centrality_features(self) -> pd.DataFrame:
        if not self.graph:
            return pd.DataFrame(
                columns=["account_id", "degree_centrality", "pagerank"]
            )

        degree = nx.degree_centrality(self.graph)
        pagerank = nx.pagerank(self.graph)

        return pd.DataFrame(
            [
                {
                    "account_id": node,
                    "degree_centrality": round(degree.get(node, 0.0), 6),
                    "pagerank": round(pagerank.get(node, 0.0), 8),
                }
                for node in self.graph.nodes
            ]
        )

    def get_account_neighbors(self, account_id: str) -> dict:
        account_id = str(account_id)

        if account_id not in self.graph:
            return {
                "account_id": account_id,
                "incoming": [],
                "outgoing": [],
            }

        incoming = [
            {
                "account_id": neighbor,
                **dict(self.graph.edges[neighbor, account_id]),
            }
            for neighbor in self.graph.predecessors(account_id)
        ]

        outgoing = [
            {
                "account_id": neighbor,
                **dict(self.graph.edges[account_id, neighbor]),
            }
            for neighbor in self.graph.successors(account_id)
        ]

        return {
            "account_id": account_id,
            "incoming": incoming,
            "outgoing": outgoing,
        }

    def detect_communities(self) -> list[set]:
        """
        Detect communities using an undirected projection.

        Community detection is useful for identifying dense transaction
        clusters, but a community is not automatically fraudulent.
        """
        undirected = self.graph.to_undirected()

        if undirected.number_of_nodes() == 0:
            return []

        communities = nx.community.greedy_modularity_communities(undirected)
        return [set(group) for group in communities]

    def export_graphml(self, path: str | Path) -> None:
        """
        Export a GraphML representation.

        Complex/non-serializable node attributes are converted to strings.
        """
        export_graph = nx.DiGraph()

        for node, attrs in self.graph.nodes(data=True):
            export_graph.add_node(
                node,
                **{key: str(value) for key, value in attrs.items()}
            )

        for source, target, attrs in self.graph.edges(data=True):
            export_graph.add_edge(
                source,
                target,
                **{
                    key: float(value) if isinstance(value, float) else int(value)
                    if isinstance(value, int)
                    else str(value)
                    for key, value in attrs.items()
                },
            )

        nx.write_graphml(export_graph, path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze SafeUPI transaction graph")
    parser.add_argument(
        "--transactions",
        default="data/transactions.csv",
        help="Path to transactions.csv",
    )
    parser.add_argument(
        "--accounts",
        default="data/accounts.csv",
        help="Path to accounts.csv",
    )
    args = parser.parse_args()

    graph = TransactionGraph.from_csv(args.transactions, args.accounts)

    print("\nGraph summary")
    print("-------------")
    for key, value in graph.summary().items():
        print(f"{key}: {value}")

    print("\nTop accounts by degree")
    print("----------------------")
    print(graph.top_accounts_by_degree(10).to_string(index=False))

    print("\nCommunity count")
    print("---------------")
    print(len(graph.detect_communities()))


if __name__ == "__main__":
    main()
