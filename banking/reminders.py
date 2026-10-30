"""
Banking Module: Smart Bill Reminders & Funds Planning (Use Case 7 & Section 7 Workflow)
Aggregates upcoming credit card dues, active EMIs, utility bills, and subscription renewals.
Computes deterministic remaining funds available after covering upcoming obligations.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from database.db import fetch_all, fetch_one
from utils.audit_log import log_audit_event, generate_trace_id


def get_upcoming_payments(customer_id: str, days_ahead: int = 30) -> Dict[str, Any]:
    """
    Identifies all upcoming obligations within the specified lookahead window (default 30 days).
    Aggregates:
    - Credit card total dues / minimum dues
    - Active loan EMI installments
    - Utility bills and subscriptions
    """
    trace_id = generate_trace_id()
    today = datetime.now().date()
    end_date = today + timedelta(days=days_ahead)

    today_str = today.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    obligations = []

    # 1. Credit Card Dues
    cards = fetch_all("""
        SELECT card_id, card_number_masked, card_type, current_outstanding, minimum_due, due_date
        FROM credit_cards
        WHERE customer_id = ? AND status != 'BLOCKED' AND due_date BETWEEN ? AND ?
    """, (customer_id, today_str, end_date_str))

    for c in cards:
        if c["current_outstanding"] > 0:
            obligations.append({
                "type": "Credit Card Payment",
                "title": f"{c['card_type']} ({c['card_number_masked'][-4:]})",
                "amount": c["current_outstanding"],
                "minimum_due": c["minimum_due"],
                "due_date": c["due_date"],
                "is_autopay": False
            })

    # 2. Upcoming Loan EMIs
    loans = fetch_all("""
        SELECT loan_id, loan_type, emi_amount, next_emi_date
        FROM loans
        WHERE customer_id = ? AND status = 'ACTIVE' AND next_emi_date BETWEEN ? AND ?
    """, (customer_id, today_str, end_date_str))

    for l in loans:
        obligations.append({
            "type": "Loan EMI",
            "title": f"{l['loan_type'].replace('_', ' ').title()} EMI",
            "amount": l["emi_amount"],
            "due_date": l["next_emi_date"],
            "is_autopay": True
        })

    # 3. Utility Bills & Subscriptions
    bills = fetch_all("""
        SELECT bill_id, biller_name, biller_category, amount, due_date, auto_pay, status
        FROM bills_subscriptions
        WHERE customer_id = ? AND status != 'PAID' AND due_date BETWEEN ? AND ?
    """, (customer_id, today_str, end_date_str))

    for b in bills:
        obligations.append({
            "type": b["biller_category"],
            "title": b["biller_name"],
            "amount": b["amount"],
            "due_date": b["due_date"],
            "is_autopay": bool(b["auto_pay"])
        })

    # Sort obligations chronologically by due date
    obligations.sort(key=lambda x: x["due_date"])
    total_due = sum(item["amount"] for item in obligations)

    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Core Banking, Card Management, Loan Management, Bill Payment Switch",
        tools_invoked="get_upcoming_payments",
        action_type="UPCOMING_PAYMENTS_INQUIRY",
        input_params={"customer_id": customer_id, "days_ahead": days_ahead},
        decision_outcome=f"SUCCESS: {len(obligations)} upcoming obligations totaling ₹{total_due:,.2f}"
    )

    return {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "window_days": days_ahead,
        "total_upcoming_amount": round(total_due, 2),
        "count": len(obligations),
        "obligations": obligations
    }


def get_payments_due_this_week(customer_id: str) -> Dict[str, Any]:
    """
    Specifically identifies obligations due within the next 7 days.
    Directly answers: 'What payments are due this week?'
    """
    return get_upcoming_payments(customer_id, days_ahead=7)


def calculate_remaining_funds_after_bills(customer_id: str) -> Dict[str, Any]:
    """
    Implements the exact multi-step calculation illustrated on PDF Page 4 & 5:
    1. Retrieve account balance
    2. Check upcoming EMIs, credit card dues, and scheduled bills
    3. Calculate estimated remaining funds using deterministic tools
    """
    trace_id = generate_trace_id()

    # 1. Available balance
    acc = fetch_one("SELECT SUM(balance) as total_bal FROM accounts WHERE customer_id = ? AND status = 'ACTIVE'", (customer_id,))
    available_balance = (acc["total_bal"] or 0.0) if acc else 0.0

    # 2. Upcoming obligations (next 30 days)
    upcoming_data = get_upcoming_payments(customer_id, days_ahead=30)
    upcoming_obligations = upcoming_data["total_upcoming_amount"]

    # 3. Deterministic calculation of remaining funds
    remaining_funds = max(0.0, available_balance - upcoming_obligations)

    answer_text = (
        f"Your available balance is ₹{available_balance:,.2f}. "
        f"Upcoming obligations total ₹{upcoming_obligations:,.2f}, leaving an estimated ₹{remaining_funds:,.2f}."
    )

    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Core Banking System, Payment Gateway, Loan Management, Card Platform",
        tools_invoked="get_balance, get_upcoming_payments",
        action_type="FUNDS_REMAINING_CALCULATION",
        input_params={"customer_id": customer_id},
        decision_outcome=f"SUCCESS: {answer_text}"
    )

    return {
        "trace_id": trace_id,
        "available_balance": available_balance,
        "upcoming_obligations": upcoming_obligations,
        "estimated_remaining_funds": round(remaining_funds, 2),
        "answer": answer_text,
        "answer_type": "calculated",
        "tools_invoked": ["get_balance", "get_upcoming_payments"],
        "breakdown": upcoming_data["obligations"]
    }

