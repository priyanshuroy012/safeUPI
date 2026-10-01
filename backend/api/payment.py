"""
SafeUPI Payment API
-------------------
Handles payment-risk analysis before a simulated payment is confirmed.

This prototype does NOT execute real UPI transactions.
"""

from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/payment", tags=["Payment"])


class PaymentRequest(BaseModel):
    user_id: str = Field(..., examples=["USER_001"])
    recipient: str = Field(..., examples=["randomaccount@upi"])
    recipient_name: str = Field(..., examples=["Cashback Rewards"])
    amount: float = Field(..., gt=0, examples=[5000])
    transaction_type: str = Field(default="PAY", examples=["PAY"])

    # Prototype risk signals
    is_new_recipient: bool = False
    unusual_amount: bool = False
    unusual_frequency: bool = False
    recipient_suspicious: bool = False


class RiskResponse(BaseModel):
    risk_score: int
    risk_level: str
    direction: str
    reasons: List[str]
    recommended_action: str
    message: str


def calculate_risk(payment: PaymentRequest) -> RiskResponse:
    """
    Simple explainable rule-based risk engine for the MVP.

    Scoring:
    +20 new recipient
    +20 unusual amount
    +15 unusual frequency
    +30 suspicious recipient
    """
    score = 0
    reasons: List[str] = []

    if payment.is_new_recipient:
        score += 20
        reasons.append("New recipient")

    if payment.unusual_amount:
        score += 20
        reasons.append("Transaction amount is unusual")

    if payment.unusual_frequency:
        score += 15
        reasons.append("Transaction frequency is unusual")

    if payment.recipient_suspicious:
        score += 30
        reasons.append("Recipient has suspicious activity")

    # Cap at 100 so the UI always receives a valid percentage-like score.
    score = min(score, 100)

    if score >= 70:
        level = "HIGH"
        action = "STRONG_WARNING"
        message = f"₹{payment.amount:,.2f} WILL LEAVE YOUR BANK ACCOUNT."
    elif score >= 40:
        level = "MEDIUM"
        action = "CONFIRMATION_REQUIRED"
        message = f"You are about to send ₹{payment.amount:,.2f} to {payment.recipient}."
    else:
        level = "LOW"
        action = "ALLOW"
        message = f"Payment of ₹{payment.amount:,.2f} to {payment.recipient}."

    return RiskResponse(
        risk_score=score,
        risk_level=level,
        direction="OUTGOING",
        reasons=reasons or ["No major risk signals detected"],
        recommended_action=action,
        message=message,
    )


@router.post("/analyze", response_model=RiskResponse)
def analyze_payment(payment: PaymentRequest) -> RiskResponse:
    """Analyze a payment and return an explainable risk decision."""
    return calculate_risk(payment)


@router.get("/health")
def payment_health() -> Dict[str, str]:
    return {"service": "payment-risk-engine", "status": "ok"}
