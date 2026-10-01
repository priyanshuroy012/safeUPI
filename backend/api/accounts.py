"""
SafeUPI Account Investigation API
---------------------------------
Returns account-level risk information and a synthetic transaction network.

Important:
A suspicious risk score is NOT proof that an account is fraudulent.
The dashboard should describe such accounts as "flagged for investigation"
or "showing suspicious/mule-like patterns".
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/admin/accounts", tags=["Accounts"])


DEMO_ACCOUNTS: Dict[str, Dict[str, Any]] = {
    "MULE_A": {
        "account_id": "MULE_A",
        "risk_score": 94,
        "risk_level": "HIGH",
        "account_type": "Flagged account",
        "incoming_transactions": 47,
        "outgoing_transactions": 39,
        "unique_senders": 31,
        "unique_receivers": 28,
        "average_holding_time_minutes": 3.7,
        "total_in_amount": 1248000,
        "total_out_amount": 1192000,
        "flow_through_ratio": 0.95,
        "patterns": [
            "High in-degree",
            "High out-degree",
            "Rapid fund movement",
            "High flow-through",
        ],
    },
    "MULE_B": {
        "account_id": "MULE_B",
        "risk_score": 91,
        "risk_level": "HIGH",
        "account_type": "Flagged account",
        "incoming_transactions": 23,
        "outgoing_transactions": 8,
        "unique_senders": 18,
        "unique_receivers": 8,
        "average_holding_time_minutes": 3.1,
        "total_in_amount": 1192000,
        "total_out_amount": 1192000,
        "flow_through_ratio": 1.00,
        "patterns": [
            "Multiple counterparties",
            "Rapid movement",
            "Layering-like flow",
        ],
    },
}


DEMO_NETWORKS = {
    "MULE_A": [
        {"source": "VICTIM_001", "target": "MULE_A", "amount": 5000},
        {"source": "VICTIM_002", "target": "MULE_A", "amount": 12000},
        {"source": "VICTIM_003", "target": "MULE_A", "amount": 8000},
        {"source": "MULE_A", "target": "MULE_B", "amount": 24000},
        {"source": "MULE_B", "target": "MULE_C", "amount": 18000},
        {"source": "MULE_B", "target": "MULE_D", "amount": 6000},
        {"source": "MULE_C", "target": "FRAUDSTER", "amount": 14000},
        {"source": "MULE_D", "target": "FRAUDSTER", "amount": 5000},
    ]
}


@router.get("")
def list_accounts() -> List[Dict[str, Any]]:
    """Return accounts currently flagged for investigation."""
    return list(DEMO_ACCOUNTS.values())


@router.get("/{account_id}")
def get_account(account_id: str) -> Dict[str, Any]:
    """Return account-level risk features and investigation signals."""
    account = DEMO_ACCOUNTS.get(account_id)

    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    return account


@router.get("/{account_id}/network")
def get_account_network(account_id: str) -> Dict[str, Any]:
    """Return graph edges around an investigated account."""
    if account_id not in DEMO_ACCOUNTS:
        raise HTTPException(status_code=404, detail="Account not found")

    return {
        "account_id": account_id,
        "nodes": [
            {"id": "VICTIM_001", "type": "victim"},
            {"id": "VICTIM_002", "type": "victim"},
            {"id": "VICTIM_003", "type": "victim"},
            {"id": "MULE_A", "type": "flagged"},
            {"id": "MULE_B", "type": "intermediary"},
            {"id": "MULE_C", "type": "intermediary"},
            {"id": "MULE_D", "type": "intermediary"},
            {"id": "FRAUDSTER", "type": "destination"},
        ],
        "edges": DEMO_NETWORKS.get(account_id, []),
    }


@router.get("/health")
def accounts_health() -> Dict[str, str]:
    return {"service": "account-investigation-api", "status": "ok"}
