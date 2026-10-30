"""
Banking Module: Personal Finance Guidance (Use Case 6 & Requirement R3)
Analyzes income, variable expenses, and recurring commitments to provide
simple, non-binding financial observations and savings recommendations.
"""

from datetime import datetime
from database.db import fetch_one, fetch_all
from utils.audit_log import log_audit_event, generate_trace_id


def analyze_personal_finance(customer_id):
    """
    Calculates monthly cash flow and returns actionable, non-binding savings tips.
    Formula: Projected Savings = Income - Monthly Expenses - Fixed Bills
    """
    trace_id = generate_trace_id()
    cur_month = datetime.now().strftime("%Y-%m")

    # 1. Customer Income
    cust = fetch_one("SELECT monthly_income FROM customers WHERE customer_id = ?", (customer_id,))
    income = cust["monthly_income"] if cust else 75000.0

    # 2. Total Debit Expenses This Month
    cat_rows = fetch_all(
        "SELECT category, SUM(amount) as total FROM transactions WHERE customer_id = ? AND transaction_type = 'DEBIT' AND status = 'SUCCESS' AND strftime('%Y-%m', transaction_date) = ? GROUP BY category",
        (customer_id, cur_month)
    )
    total_expenses = sum(r["total"] for r in cat_rows) if cat_rows else 0.0

    # Discretionary vs Essential spend
    discretionary_categories = {"Shopping", "Food", "Entertainment", "Travel"}
    discretionary_spend = sum(r["total"] for r in cat_rows if r["category"] in discretionary_categories)
    essential_spend = total_expenses - discretionary_spend

    # 3. Monthly Commitments (Loan EMIs + Recurring Bills)
    emi_row = fetch_one("SELECT SUM(emi_amount) as total FROM loans WHERE customer_id = ? AND status = 'ACTIVE'", (customer_id,))
    total_emi = (emi_row["total"] or 0.0) if emi_row else 0.0

    bill_row = fetch_one("SELECT SUM(amount) as total FROM bills_subscriptions WHERE customer_id = ?", (customer_id,))
    total_bills = (bill_row["total"] or 0.0) if bill_row else 0.0

    commitments = total_emi + total_bills

    # 4. Net Savings & Savings Rate
    projected_savings = max(0.0, income - total_expenses - commitments)
    savings_rate = round((projected_savings / income) * 100, 1) if income > 0 else 0.0

    # 5. Non-binding observations
    observations = [
        f"Your current monthly savings rate is {savings_rate}% (approx ₹{projected_savings:,.2f}).",
        f"Discretionary spending (Food, Shopping) is ₹{discretionary_spend:,.2f}. Cutting 15% here could save an extra ₹{round(discretionary_spend * 0.15):,.2f}.",
        f"Fixed obligations (EMIs ₹{total_emi:,.2f} + Bills ₹{total_bills:,.2f}) equal {round((commitments/income)*100, 1)}% of your income."
    ]

    log_audit_event(trace_id, customer_id, "Finance Engine", "analyze_personal_finance", "INSIGHTS", {}, f"Savings Rate: {savings_rate}%")

    return {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "monthly_income": income,
        "total_current_expenses": round(total_expenses, 2),
        "discretionary_spending": round(discretionary_spend, 2),
        "essential_spending": round(essential_spend, 2),
        "monthly_recurring_commitments": round(commitments, 2),
        "projected_monthly_savings": round(projected_savings, 2),
        "savings_rate_percentage": savings_rate,
        "observations": observations
    }
