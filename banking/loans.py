"""
Banking Module: EMI & Loan Tracking (Use Case 5)
Retrieves loan details, active liabilities, outstanding balances, and amortized EMI schedules.
"""

from typing import Dict, Any, List, Optional
from database.db import fetch_all, fetch_one
from utils.audit_log import log_audit_event, generate_trace_id


def get_loan_summary(customer_id: str) -> Dict[str, Any]:
    """
    Retrieves summary of all active loans for the customer.
    Includes loan type, sanctioned principal, outstanding balance, interest rate, and next EMI.
    """
    trace_id = generate_trace_id()
    query = """
        SELECT loan_id, loan_type, principal_amount, outstanding_balance,
               interest_rate, tenure_months, emi_amount, start_date, end_date,
               next_emi_date, status
        FROM loans
        WHERE customer_id = ? AND status = 'ACTIVE'
    """
    loans = fetch_all(query, (customer_id,))

    if not loans:
        log_audit_event(
            trace_id=trace_id,
            customer_id=customer_id,
            systems_queried="Loan Management System",
            tools_invoked="get_loan_summary",
            action_type="LOAN_INQUIRY",
            input_params={"customer_id": customer_id},
            decision_outcome="NOT_FOUND: No active loans"
        )
        return {
            "status": "NOT_FOUND",
            "trace_id": trace_id,
            "message": "You currently do not have any active loans or credit facilities.",
            "loans": [],
            "total_outstanding": 0.0,
            "total_monthly_emi": 0.0
        }

    total_outstanding = sum(l["outstanding_balance"] for l in loans)
    total_monthly_emi = sum(l["emi_amount"] for l in loans)

    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Loan Management System",
        tools_invoked="get_loan_summary",
        action_type="LOAN_INQUIRY",
        input_params={"customer_id": customer_id},
        decision_outcome=f"SUCCESS: {len(loans)} active loans, total outstanding ₹{total_outstanding:,.2f}"
    )

    return {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "total_active_loans": len(loans),
        "total_outstanding": total_outstanding,
        "total_monthly_emi": total_monthly_emi,
        "loans": loans
    }


def get_next_emi(customer_id: str) -> Dict[str, Any]:
    """
    Retrieves specific details about the immediate next upcoming EMI obligation.
    Directly answers: 'What is my next EMI amount?'
    """
    trace_id = generate_trace_id()
    query = """
        SELECT l.loan_id, l.loan_type, l.emi_amount, l.next_emi_date, l.outstanding_balance,
               s.emi_number, s.principal_component, s.interest_component
        FROM loans l
        LEFT JOIN emi_schedules s ON l.loan_id = s.loan_id AND s.due_date = l.next_emi_date
        WHERE l.customer_id = ? AND l.status = 'ACTIVE'
        ORDER BY l.next_emi_date ASC
        LIMIT 1
    """
    next_emi = fetch_one(query, (customer_id,))

    if not next_emi:
        log_audit_event(
            trace_id=trace_id,
            customer_id=customer_id,
            systems_queried="Loan Management System",
            tools_invoked="get_next_emi",
            action_type="NEXT_EMI_CHECK",
            input_params={"customer_id": customer_id},
            decision_outcome="NOT_FOUND: No upcoming EMIs scheduled"
        )
        return {
            "status": "NOT_FOUND",
            "trace_id": trace_id,
            "message": "No scheduled EMI payments found."
        }

    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Loan Management System",
        tools_invoked="get_next_emi",
        action_type="NEXT_EMI_CHECK",
        input_params={"customer_id": customer_id},
        decision_outcome=f"SUCCESS: Next EMI ₹{next_emi['emi_amount']:,.2f} due on {next_emi['next_emi_date']}"
    )

    return {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "loan_id": next_emi["loan_id"],
        "loan_type": next_emi["loan_type"].replace("_", " ").title(),
        "emi_amount": next_emi["emi_amount"],
        "due_date": next_emi["next_emi_date"],
        "principal_split": next_emi.get("principal_component"),
        "interest_split": next_emi.get("interest_component"),
        "outstanding_balance": next_emi["outstanding_balance"]
    }


def get_emi_schedule(customer_id: str, loan_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves full amortized EMI schedule for the specified or primary active loan."""
    trace_id = generate_trace_id()
    if loan_id:
        query = """
            SELECT schedule_id, loan_id, emi_number, due_date, emi_amount,
                   principal_component, interest_component, status, paid_date
            FROM emi_schedules
            WHERE customer_id = ? AND loan_id = ?
            ORDER BY emi_number ASC
        """
        schedules = fetch_all(query, (customer_id, loan_id))
    else:
        query = """
            SELECT schedule_id, loan_id, emi_number, due_date, emi_amount,
                   principal_component, interest_component, status, paid_date
            FROM emi_schedules
            WHERE customer_id = ?
            ORDER BY due_date ASC
        """
        schedules = fetch_all(query, (customer_id,))

    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Loan Management System",
        tools_invoked="get_emi_schedule",
        action_type="SCHEDULE_INQUIRY",
        input_params={"customer_id": customer_id, "loan_id": loan_id},
        decision_outcome=f"SUCCESS: Returned {len(schedules)} schedule rows"
    )

    return {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "schedules": schedules
    }

