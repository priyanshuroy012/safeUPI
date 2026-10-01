"""
SafeUPI payment risk engine.

MVP strategy:
- Rule-based scoring first.
- Graph intelligence contributes recipient/network risk.
- Every score has human-readable reasons.
- The engine recommends an intervention rather than silently
  blocking a transaction.

Future ML layer:
- Train XGBoost/Random Forest on labeled historical/synthetic data.
- Use Isolation Forest as an unsupervised anomaly detector when labels
  are unavailable.
- Combine model probability with rule/graph signals.
"""

from typing import Dict, List

from backend.database.models import RiskDecision, RiskFeatures


def calculate_payment_risk(
    features: RiskFeatures,
    amount: float,
) -> RiskDecision:
    """
    Calculate an explainable payment risk score.

    Scoring:
    +20 new recipient
    +20 unusually large payment
    +15 unusual frequency
    +30 suspicious recipient/network
    +15 strong graph-flow warning

    Maximum = 100.
    """
    score = 0
    reasons: List[str] = []

    # Recipient novelty
    if features.is_new_recipient:
        score += 20
        reasons.append("New recipient")

    # Amount anomaly: >= 3x user's normal amount
    if features.amount_deviation >= 3.0:
        score += 20
        reasons.append(
            f"Amount is {features.amount_deviation:.1f}x the user's average"
        )

    # Frequency/velocity anomaly
    if features.unusual_frequency:
        score += 15
        reasons.append("Transaction frequency is unusual")

    # Existing recipient/network intelligence
    if features.recipient_risk_score >= 70:
        score += 30
        reasons.append("Recipient has high network risk")

    # Graph structure
    graph_warning = (
        features.recipient_in_degree >= 10
        or features.recipient_out_degree >= 5
        or features.recipient_flow_through_ratio >= 0.80
    )

    if graph_warning:
        score += 15
        reasons.append(
            "Recipient shows suspicious fund-flow characteristics"
        )

    score = min(score, 100)

    if score >= 70:
        level = "HIGH"
        action = "STRONG_WARNING"
    elif score >= 40:
        level = "MEDIUM"
        action = "CONFIRMATION_REQUIRED"
    else:
        level = "LOW"
        action = "ALLOW"

    if level == "HIGH":
        message = (
            f"₹{amount:,.2f} WILL LEAVE YOUR BANK ACCOUNT. "
            "Review the recipient before entering your UPI PIN."
        )
    elif level == "MEDIUM":
        message = (
            f"You are about to send ₹{amount:,.2f}. "
            "Review the recipient and payment details."
        )
    else:
        message = (
            f"Payment of ₹{amount:,.2f} appears low risk based on "
            "the available signals."
        )

    return RiskDecision(
        risk_score=score,
        risk_level=level,
        direction="OUTGOING",
        reasons=reasons or ["No major risk signals detected"],
        recommended_action=action,
        features=features,
    )


def risk_engine_health() -> Dict[str, str]:
    return {
        "status": "ok",
        "algorithm": "Explainable weighted rules + graph risk signals",
    }
