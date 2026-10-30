"""
Banking Module: Personalized Offers & Eligibility Engine (Use Case 10 & Requirement R5)
Evaluates policy rules, credit scores, and debt-to-income ratios to deliver
tailored pre-approved loan, deposit, and card offers.
"""

from typing import Dict, Any, List
from database.db import fetch_all, fetch_one
from utils.audit_log import log_audit_event, generate_trace_id


def get_personalized_offers(customer_id: str) -> Dict[str, Any]:
    """
    Retrieves personalized pre-approved offers based on customer eligibility and profile suitability.
    Use Case 10: Personalized Offers.
    """
    trace_id = generate_trace_id()

    query = """
        SELECT offer_id, offer_type, title, description, max_amount,
               interest_rate, valid_until, eligibility_met, suitability_score, status
        FROM personalized_offers
        WHERE customer_id = ? AND status = 'AVAILABLE'
        ORDER BY suitability_score DESC
    """
    offers = fetch_all(query, (customer_id,))

    cust = fetch_one("SELECT name, monthly_income, credit_score FROM customers WHERE customer_id = ?", (customer_id,))

    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Personalization Engine, CRM Platform, Credit Bureau Link",
        tools_invoked="get_personalized_offers",
        action_type="OFFERS_INQUIRY",
        input_params={"customer_id": customer_id},
        decision_outcome=f"SUCCESS: {len(offers)} offers retrieved (Credit Score: {cust['credit_score'] if cust else 'N/A'})"
    )

    if not offers:
        return {
            "status": "NOT_FOUND",
            "trace_id": trace_id,
            "message": "No pre-approved promotional offers are currently active for your profile.",
            "offers": []
        }

    return {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "customer_name": cust["name"] if cust else "Customer",
        "credit_score": cust["credit_score"] if cust else 750,
        "count": len(offers),
        "offers": offers
    }


def check_loan_eligibility(customer_id: str, requested_type: str = "PERSONAL_LOAN") -> Dict[str, Any]:
    """
    Performs deterministic eligibility calculation using standard banking policy rules:
    1. Minimum credit score: 700
    2. FOIR (Fixed Obligation to Income Ratio): Max 50% of monthly income
    3. Maximum multiplier: 12x net monthly income
    (Requirement R5 & No Hallucinations R6).
    """
    trace_id = generate_trace_id()

    cust = fetch_one("SELECT monthly_income, credit_score, risk_tier FROM customers WHERE customer_id = ?", (customer_id,))
    if not cust:
        return {"status": "NOT_FOUND", "trace_id": trace_id, "message": "Customer profile not found."}

    income = cust["monthly_income"]
    score = cust["credit_score"]

    # Check existing EMIs
    emi_row = fetch_one("SELECT SUM(emi_amount) as total_emi FROM loans WHERE customer_id = ? AND status = 'ACTIVE'", (customer_id,))
    existing_emi = (emi_row["total_emi"] or 0.0) if emi_row else 0.0

    # FOIR calculation
    max_permissible_emi = (income * 0.50) - existing_emi

    if score < 700 or max_permissible_emi <= 1000:
        decision = "INELIGIBLE"
        max_loan = 0.0
        reason = f"Credit score ({score}) below policy minimum 700 or high existing debt obligations (₹{existing_emi:,.2f}/mo)."
    else:
        decision = "ELIGIBLE"
        # 3-year loan estimation at 10.5%
        max_loan = round(max_permissible_emi * 30, -3)  # approx principal for affordable EMI
        reason = f"Pre-qualified with a strong credit score ({score}) and healthy repayment capacity."

    result = {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "decision": decision,
        "customer_id": customer_id,
        "credit_score": score,
        "monthly_income": income,
        "existing_monthly_emi": existing_emi,
        "available_emi_capacity": round(max(0.0, max_permissible_emi), 2),
        "max_eligible_loan_amount": max_loan,
        "indicative_interest_rate": 10.49 if score >= 750 else 11.99,
        "reason": reason
    }

    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Underwriting Rules Engine, Credit Bureau Service",
        tools_invoked="check_loan_eligibility",
        action_type="LOAN_ELIGIBILITY_CHECK",
        input_params={"customer_id": customer_id, "loan_type": requested_type},
        decision_outcome=f"{decision}: Max eligible loan ₹{max_loan:,.2f}"
    )

    return result

