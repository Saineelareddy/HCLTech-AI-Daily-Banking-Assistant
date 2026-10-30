"""
Banking Module: Daily Expense Tracking & Analytics (Use Case 2 & Requirement R3)
Analyzes debit transactions, categorizes monthly spending, and computes trends.
"""

from datetime import datetime
from typing import Dict, Any, List
from database.db import fetch_all
from utils.audit_log import log_audit_event, generate_trace_id


def analyze_expenses(customer_id: str, period: str = "current_month") -> Dict[str, Any]:
    """
    Analyzes debits for the authorized customer, categorizing spending by Food, Transport,
    Shopping, Bills, etc., as highlighted in Section 3 of the problem statement.
    """
    trace_id = generate_trace_id()
    now = datetime.now()
    cur_year_month = now.strftime("%Y-%m")

    query = """
        SELECT category, SUM(amount) as total_amount, COUNT(*) as txn_count
        FROM transactions
        WHERE customer_id = ?
          AND transaction_type = 'DEBIT'
          AND status = 'SUCCESS'
          AND strftime('%Y-%m', transaction_date) = ?
        GROUP BY category
        ORDER BY total_amount DESC
    """
    categories = fetch_all(query, (customer_id, cur_year_month))

    total_spent = sum(c["total_amount"] for c in categories) if categories else 0.0

    # Retrieve all debit transactions this month for detailed line items
    item_query = """
        SELECT transaction_id, transaction_date, amount, category, merchant, description
        FROM transactions
        WHERE customer_id = ?
          AND transaction_type = 'DEBIT'
          AND status = 'SUCCESS'
          AND strftime('%Y-%m', transaction_date) = ?
        ORDER BY transaction_date DESC
    """
    all_debits = fetch_all(item_query, (customer_id, cur_year_month))

    # Calculate category percentages
    category_breakdown = []
    for c in categories:
        pct = (c["total_amount"] / total_spent * 100) if total_spent > 0 else 0.0
        category_breakdown.append({
            "category": c["category"],
            "amount": round(c["total_amount"], 2),
            "percentage": round(pct, 1),
            "transaction_count": c["txn_count"]
        })

    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Core Banking System, Analytics Engine",
        tools_invoked="analyze_expenses",
        action_type="EXPENSE_ANALYSIS",
        input_params={"customer_id": customer_id, "period": period},
        decision_outcome=f"SUCCESS: Total spend ₹{total_spent:,.2f} across {len(category_breakdown)} categories"
    )

    return {
        "status": "SUCCESS" if categories else "NO_EXPENSES",
        "trace_id": trace_id,
        "period": cur_year_month,
        "total_spent": round(total_spent, 2),
        "category_breakdown": category_breakdown,
        "recent_expenses": all_debits[:10]
    }


def get_spending_trends(customer_id: str) -> Dict[str, Any]:
    """
    Computes monthly historical spending trends for visualization in Plotly.
    """
    trace_id = generate_trace_id()
    query = """
        SELECT strftime('%Y-%m', transaction_date) as month_period,
               SUM(amount) as monthly_total,
               COUNT(*) as tx_count
        FROM transactions
        WHERE customer_id = ?
          AND transaction_type = 'DEBIT'
          AND status = 'SUCCESS'
        GROUP BY month_period
        ORDER BY month_period ASC
    """
    trends = fetch_all(query, (customer_id,))

    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Analytics Platform",
        tools_invoked="get_spending_trends",
        action_type="TREND_ANALYSIS",
        input_params={"customer_id": customer_id},
        decision_outcome=f"SUCCESS: Retrieved {len(trends)} monthly data points"
    )

    return {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "trends": trends
    }

