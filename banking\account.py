"""
Banking Module: Account & Balance Inquiry (Use Case 1)
Retrieves real-time balances, recent credits and debits, and comprehensive account summaries.
"""

from typing import Dict, Any, List, Optional
from database.db import fetch_all, fetch_one
from utils.audit_log import log_audit_event, generate_trace_id


def get_account_balance(customer_id: str) -> Dict[str, Any]:
    """
    Retrieves the customer's available balance across accounts.
    Returns primary account balance, breakdown by account, and total available liquid funds.
    """
    trace_id = generate_trace_id()
    query = """
        SELECT account_number, account_type, balance, currency, branch, ifsc_code, status
        FROM accounts
        WHERE customer_id = ? AND status = 'ACTIVE'
    """
    accounts = fetch_all(query, (customer_id,))

    if not accounts:
        log_audit_event(
            trace_id=trace_id,
            customer_id=customer_id,
            systems_queried="Core Banking System",
            tools_invoked="get_account_balance",
            action_type="BALANCE_INQUIRY",
            input_params={"customer_id": customer_id},
            decision_outcome="NOT_FOUND: No active accounts found for customer"
        )
        return {
            "status": "NOT_FOUND",
            "trace_id": trace_id,
            "message": f"No active bank accounts found for customer ID {customer_id}.",
            "total_balance": 0.0,
            "accounts": []
        }

    total_balance = sum(acc["balance"] for acc in accounts)
    primary_account = accounts[0]

    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Core Banking System",
        tools_invoked="get_account_balance",
        action_type="BALANCE_INQUIRY",
        input_params={"customer_id": customer_id},
        decision_outcome=f"SUCCESS: Total balance ₹{total_balance:,.2f} across {len(accounts)} accounts"
    )

    return {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "primary_account": primary_account["account_number"],
        "primary_account_type": primary_account["account_type"],
        "primary_balance": primary_account["balance"],
        "total_balance": total_balance,
        "currency": primary_account["currency"],
        "accounts": accounts
    }


def get_recent_transactions(customer_id: str, limit: int = 5, tx_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves recent credits and debits for the authorized customer.
    Filters by transaction type ('CREDIT' or 'DEBIT') if provided.
    """
    trace_id = generate_trace_id()
    if tx_type:
        query = """
            SELECT transaction_id, account_number, transaction_date, amount,
                   transaction_type, category, merchant, payment_method, description, status
            FROM transactions
            WHERE customer_id = ? AND transaction_type = ?
            ORDER BY transaction_date DESC, transaction_id DESC
            LIMIT ?
        """
        records = fetch_all(query, (customer_id, tx_type.upper(), limit))
    else:
        query = """
            SELECT transaction_id, account_number, transaction_date, amount,
                   transaction_type, category, merchant, payment_method, description, status
            FROM transactions
            WHERE customer_id = ?
            ORDER BY transaction_date DESC, transaction_id DESC
            LIMIT ?
        """
        records = fetch_all(query, (customer_id, limit))

    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Core Banking System",
        tools_invoked="get_recent_transactions",
        action_type="TRANSACTION_HISTORY",
        input_params={"customer_id": customer_id, "limit": limit, "tx_type": tx_type},
        decision_outcome=f"SUCCESS: Retrieved {len(records)} transactions"
    )

    return {
        "status": "SUCCESS" if records else "EMPTY",
        "trace_id": trace_id,
        "count": len(records),
        "transactions": records
    }


def get_account_summary(customer_id: str) -> Dict[str, Any]:
    """
    Provides a comprehensive snapshot of customer accounts, recent transactions,
    and aggregate inflows and outflows.
    """
    balance_info = get_account_balance(customer_id)
    recent_credits = get_recent_transactions(customer_id, limit=3, tx_type="CREDIT")
    recent_debits = get_recent_transactions(customer_id, limit=3, tx_type="DEBIT")

    return {
        "status": balance_info["status"],
        "trace_id": balance_info["trace_id"],
        "total_balance": balance_info.get("total_balance", 0.0),
        "accounts": balance_info.get("accounts", []),
        "recent_credits": recent_credits["transactions"],
        "recent_debits": recent_debits["transactions"]
    }

