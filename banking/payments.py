"""
Banking Module: UPI and Payment Assistance (Use Case 4)
Handles payment status checks, UTR reference tracking, and failure explanations.
"""

import random
from database.db import fetch_all, fetch_one, execute_query
from utils.audit_log import log_audit_event, generate_trace_id


def verify_upi_payment(customer_id, query_term=None):
    """
    Checks status of a UPI payment by merchant name or reference number.
    Returns status, 12-digit UTR, and failure explanation if failed.
    """
    trace_id = generate_trace_id()

    if query_term:
        term = f"%{query_term.strip()}%"
        sql = """
            SELECT * FROM upi_payments
            WHERE customer_id = ? AND (recipient_name LIKE ? OR upi_ref_no LIKE ?)
            ORDER BY payment_date DESC LIMIT 5
        """
        payments = fetch_all(sql, (customer_id, term, term))
    else:
        sql = "SELECT * FROM upi_payments WHERE customer_id = ? ORDER BY payment_date DESC LIMIT 5"
        payments = fetch_all(sql, (customer_id,))

    if not payments:
        log_audit_event(trace_id, customer_id, "UPI Switch", "verify_upi_payment", "UPI_CHECK", {"query": query_term}, "NOT_FOUND")
        return {
            "status": "NOT_FOUND",
            "trace_id": trace_id,
            "message": f"No UPI payment records found matching '{query_term}'." if query_term else "No recent UPI payments found.",
            "payments": []
        }

    latest = payments[0]
    log_audit_event(trace_id, customer_id, "UPI Switch", "verify_upi_payment", "UPI_CHECK", {"query": query_term}, f"Status: {latest['status']}")

    return {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "latest_match": latest,
        "is_success": (latest["status"] == "SUCCESS"),
        "reference_number": latest["upi_ref_no"],
        "failure_explanation": latest["failure_reason"] if latest["status"] == "FAILED" else None,
        "payments": payments
    }


def get_upi_history(customer_id, limit=10):
    """Retrieves recent UPI payments for the customer."""
    trace_id = generate_trace_id()
    payments = fetch_all(
        "SELECT * FROM upi_payments WHERE customer_id = ? ORDER BY payment_date DESC LIMIT ?",
        (customer_id, limit)
    )
    return {"status": "SUCCESS", "trace_id": trace_id, "payments": payments}


def execute_simulated_payment(customer_id, recipient_name, recipient_vpa, amount):
    """Executes a simple payment debiting the customer's account (Requirement R4)."""
    trace_id = generate_trace_id()
    acc = fetch_one("SELECT account_number, balance FROM accounts WHERE customer_id = ? AND status = 'ACTIVE' LIMIT 1", (customer_id,))

    if not acc or acc["balance"] < amount:
        return {"status": "FAILED", "trace_id": trace_id, "message": "Insufficient balance for payment."}

    new_bal = acc["balance"] - amount
    execute_query("UPDATE accounts SET balance = ? WHERE account_number = ?", (new_bal, acc["account_number"]))

    ref_no = str(random.randint(100000000000, 999999999999))
    execute_query(
        """INSERT INTO upi_payments (upi_txn_id, customer_id, account_number, upi_ref_no, recipient_vpa, recipient_name, amount, payment_date, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'SUCCESS')""",
        (f"UPI{random.randint(1000, 9999)}", customer_id, acc["account_number"], ref_no, recipient_vpa, recipient_name, amount)
    )

    log_audit_event(trace_id, customer_id, "Core Banking", "execute_simulated_payment", "PAYMENT", {"amount": amount}, f"Success: UTR {ref_no}")
    return {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "amount": amount,
        "recipient": recipient_name,
        "upi_ref_no": ref_no,
        "new_balance": new_bal,
        "message": f"Payment of ₹{amount:,.2f} to {recipient_name} was successful. Reference UTR: {ref_no}."
    }
