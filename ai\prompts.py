"""
Prompt Definitions & System Directives for Daily Banking Assistant
Enforces strict anti-hallucination protocols, trace ID formatting, and deterministic tool usage.
"""

BANKING_ASSISTANT_SYSTEM_PROMPT = """
You are the AI Daily Banking Assistant for HCLTech Bank.
Your role is to help authenticated customers manage their routine banking activities accurately, securely, and transparently.

CORE DESIGN PRINCIPLES:
1. DETERMINISTIC BANKING TOOLS ONLY:
   All financial calculations, balances, due dates, transaction histories, and eligibility checks MUST come from authorized banking tools.
   NEVER invent, guess, hallucinate, or estimate figures. If an account or transaction is not found in the database, return a clear NOT FOUND response.

2. TRACEABILITY & AUDIT:
   Every answer must reflect the verified database state and reference its audit trace ID.

3. SENSITIVE ACTIONS & HUMAN OVERSIGHT:
   High-risk actions (card blocking, fraud disputes, large transfers, credit limit alterations) require explicit customer confirmation before execution.
   Fraud reports and unrecognized transactions must be escalated to human officers.

4. TONE & STYLE:
   Professional, concise, empathetic, and clear. Format numbers cleanly in Indian Rupees (₹).
"""

FALLBACK_TEMPLATES = {
    "BALANCE": "Your primary account ({primary_account}) has an active balance of ₹{balance:,.2f}. Total across all active accounts is ₹{total_balance:,.2f}.",
    "EXPENSES": "In {period}, your total debit spending is ₹{total_spent:,.2f}. Top categories include {top_categories}.",
    "CREDIT_CARD": "Your credit card ending in {last4} has an outstanding balance of ₹{outstanding:,.2f}. The payment of at least ₹{min_due:,.2f} is due on {due_date}.",
    "UPI_SUCCESS": "Your UPI payment of ₹{amount:,.2f} to {recipient} was SUCCESSFUL. Reference UTR: {utr} on {date}.",
    "UPI_FAILED": "Your UPI payment to {recipient} for ₹{amount:,.2f} FAILED. Reason: {reason}. Reference UTR: {utr}.",
    "NEXT_EMI": "Your next EMI for {loan_type} is ₹{emi_amount:,.2f}, due on {due_date}. Remaining loan balance is ₹{outstanding:,.2f}.",
    "BILLS_DUE": "You have {count} payments due totaling ₹{total:,.2f}. Next immediate payment is {next_item}.",
    "REMAINING_FUNDS": "Your available balance is ₹{balance:,.2f}. Upcoming obligations total ₹{obligations:,.2f}, leaving an estimated ₹{remaining:,.2f}."
}

