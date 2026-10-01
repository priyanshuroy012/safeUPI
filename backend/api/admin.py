"""
SafeUPI Admin API
-----------------
Provides dashboard-level analytics for the prototype.

The values below are demo/synthetic values. They should be replaced by
database queries when connecting the project to a real data source.
"""

from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter(prefix="/api/admin", tags=["Admin"])


DEMO_STATS = {
    "total_transactions": 24821,
    "high_risk_transactions": 183,
    "suspicious_accounts": 47,
    "suspicious_networks": 12,
    "total_amount_monitored": 124800000,
}


DEMO_ALERTS = [
    {
        "time": "11:42 AM",
        "type": "Rapid Flow",
        "description": "Funds moved out within 3 minutes",
        "account_id": "MULE_A",
        "risk_score": 94,
    },
    {
        "time": "11:15 AM",
        "type": "High In-Degree",
        "description": "Received funds from 28 accounts",
        "account_id": "MULE_C",
        "risk_score": 87,
    },
    {
        "time": "10:47 AM",
        "type": "Layering",
        "description": "Funds moved through 4 hops",
        "account_id": "MULE_D",
        "risk_score": 82,
    },
    {
        "time": "10:22 AM",
        "type": "Unusual Amount",
        "description": "Amount 6.5x above history",
        "account_id": "A11234",
        "risk_score": 76,
    },
]


@router.get("/analytics")
def get_analytics() -> Dict[str, Any]:
    """Return dashboard KPI data for the admin frontend."""
    return {
        "stats": DEMO_STATS,
        "risk_distribution": {
            "low": 68,
            "medium": 20,
            "high": 12,
        },
        "alerts": DEMO_ALERTS,
        "quick_insights": [
            "MULE_A shows rapid fund movement and high in-degree.",
            "12 suspicious networks exhibit layering-like patterns.",
            "High-risk transactions increased compared with the previous period.",
            "Rapid flow-through is a frequent suspicious pattern.",
        ],
    }


@router.get("/alerts")
def get_alerts() -> List[Dict[str, Any]]:
    """Return recent high-risk alerts."""
    return DEMO_ALERTS


@router.get("/health")
def admin_health() -> Dict[str, str]:
    return {"service": "admin-api", "status": "ok"}
