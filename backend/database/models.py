"""
SafeUPI data models.

These are Pydantic models for the prototype API and risk engine.
They describe the data flowing through the system without tying the
MVP to a specific database.
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
TransactionDirection = Literal["INCOMING", "OUTGOING"]
TransactionType = Literal["PAY", "COLLECT", "REFUND"]


class Transaction(BaseModel):
    transaction_id: str
    sender: str
    receiver: str
    amount: float = Field(gt=0)
    timestamp: datetime
    transaction_type: TransactionType = "PAY"


class AccountProfile(BaseModel):
    account_id: str
    account_type: str = "USER"

    transaction_count: int = 0
    incoming_count: int = 0
    outgoing_count: int = 0

    incoming_amount: float = 0.0
    outgoing_amount: float = 0.0

    unique_senders: int = 0
    unique_receivers: int = 0

    average_holding_time_minutes: float = 0.0
    flow_through_ratio: float = 0.0


class RiskFeatures(BaseModel):
    """
    Features used by the payment-risk engine.

    Most values are normalized or interpretable signals rather than
    opaque model features, which makes the demo easier to explain.
    """

    amount_deviation: float = 0.0
    is_new_recipient: bool = False
    recipient_age_days: float = 0.0
    transaction_velocity: float = 0.0
    unusual_frequency: bool = False

    recipient_risk_score: float = 0.0
    recipient_in_degree: int = 0
    recipient_out_degree: int = 0
    recipient_flow_through_ratio: float = 0.0

    user_history_average: float = 0.0


class RiskDecision(BaseModel):
    risk_score: int
    risk_level: RiskLevel
    direction: TransactionDirection
    reasons: List[str]
    recommended_action: str
    features: Optional[RiskFeatures] = None


class MuleScore(BaseModel):
    account_id: str
    score: int
    risk_level: RiskLevel
    reasons: List[str]
    features: Dict[str, float]
