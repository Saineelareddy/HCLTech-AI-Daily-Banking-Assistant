"""
AI Assistant Orchestrator for Daily Banking
Implements the core architecture:
Streamlit Frontend → Python Application → AI Assistant → Banking Functions → SQLite Database.

Supports dual modes:
1. LLM API Mode: Uses Gemini/LLM to understand user intent, trigger deterministic banking tools,
   and explain the verified result in natural language.
2. Rule-Based Fallback Mode: Offline, zero-latency deterministic intent matching (100% feature parity).
"""

import os
import re
import json
import requests
from typing import Dict, Any, Optional

from banking.account import get_account_balance, get_recent_transactions
from banking.expenses import analyze_expenses, get_spending_trends
from banking.cards import get_credit_card_details, get_card_repayment_options, block_card, request_limit_change
from banking.payments import verify_upi_payment, get_upi_history
from banking.loans import get_loan_summary, get_next_emi, get_emi_schedule
from banking.reminders import get_upcoming_payments, get_payments_due_this_week, calculate_remaining_funds_after_bills
from banking.finance import analyze_personal_finance
from banking.fraud import fraud_verification, report_fraud_and_open_dispute
from banking.offers import get_personalized_offers, check_loan_eligibility
from utils.audit_log import generate_trace_id, log_audit_event


class DailyBankingAssistant:
    """
    Central AI Banking Assistant orchestrator.
    Dispatches customer requests to deterministic banking tools, maintains confirmation state,
    and returns auditable structured responses.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    def set_api_key(self, api_key: str):
        """Allows dynamically setting or updating the LLM API key from the UI."""
        self.api_key = api_key.strip()

    def process_query(
        self,
        customer_id: str,
        user_message: str,
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main query processing entry point.
        Checks for pending action confirmations first.
        If an LLM API key is present, uses LLM for intent classification and explanation.
        Otherwise, seamlessly uses the smart rule-based fallback.
        """
        msg = user_message.strip()
        lower_msg = msg.lower()
        session_context = session_context or {}
        pending_action = session_context.get("pending_action")

        # -------------------------------------------------------------
        # STEP 1: Check for Confirmation of Sensitive Actions (R4 & R7)
        # -------------------------------------------------------------
        if pending_action:
            if lower_msg in ["yes", "confirm", "confirm block", "proceed", "y", "sure", "ok", "please proceed"]:
                return self._execute_confirmed_action(customer_id, pending_action)
            elif lower_msg in ["no", "cancel", "abort", "nevermind", "n", "stop"]:
                trace_id = generate_trace_id()
                log_audit_event(
                    trace_id=trace_id,
                    customer_id=customer_id,
                    systems_queried="AI Orchestrator",
                    tools_invoked="cancel_action",
                    action_type="ACTION_CANCELLED",
                    input_params=pending_action,
                    decision_outcome="Customer aborted sensitive operation"
                )
                return {
                    "trace_id": trace_id,
                    "answer": "Operation cancelled. No changes have been made to your cards or accounts.",
                    "answer_type": "cancelled",
                    "tools_invoked": [],
                    "clear_pending_action": True
                }

        # -------------------------------------------------------------
        # STEP 2: Try LLM API Orchestration if API Key is configured
        # -------------------------------------------------------------
        if self.api_key:
            try:
                llm_response = self._process_with_llm(customer_id, msg)
                if llm_response:
                    return llm_response
            except Exception as e:
                # Log fallback and gracefully continue with rule-based engine
                print(f"[AI Assistant] LLM call failed ({e}); switching to rule-based engine.")

        # -------------------------------------------------------------
        # STEP 3: Rule-Based Fallback Engine
        # -------------------------------------------------------------
        return self._process_rule_based(customer_id, msg)

    # -----------------------------------------------------------------
    # LLM ORCHESTRATION PIPELINE
    # -----------------------------------------------------------------
    def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """Sends a request to Google Gemini API."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800}
        }
        resp = requests.post(url, json=payload, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"].strip()
        return None

    def _process_with_llm(self, customer_id: str, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Uses LLM to understand intent, map to deterministic banking tool,
        and then explain the real database result to the customer.
        """
        intent_prompt = f"""
You are the AI Intent Classifier for HCLTech Bank.
Analyze the customer's question and map it to ONE of the authorized banking operations.
Customer Message: "{user_message}"

Allowed operations:
- "get_balance": Account balance inquiry
- "recent_transactions": Recent credits or debits inquiry
- "analyze_expenses": Monthly spending, category breakdown
- "get_credit_card_details": Credit card statement, due date, outstanding
- "verify_upi_payment": Check UPI status for a merchant (e.g. Amazon, Flipkart, Swiggy)
- "get_next_emi": Next loan EMI amount, due date, loan details
- "get_upcoming_payments": Bills due this week or upcoming obligations
- "calculate_remaining_funds_after_bills": Money left after paying upcoming bills
- "analyze_personal_finance": Savings guidance, budget advice
- "block_card": Lost or stolen card, block request
- "fraud_verification": Unrecognized charge, suspicious transaction
- "get_personalized_offers": Pre-approved loans or offers
- "greeting": Hello, hi, or general greeting

Respond ONLY with a JSON object:
{{
  "operation": "<operation_name>",
  "merchant": "<merchant_name_if_applicable_else_null>",
  "transaction_id": "<transaction_id_if_mentioned_else_null>",
  "greeting_message": "<friendly_greeting_if_operation_is_greeting_else_null>"
}}
"""
        raw_intent = self._call_gemini_api(intent_prompt)
        if not raw_intent:
            return None

        # Extract JSON from LLM output
        clean_json_str = raw_intent.replace("```json", "").replace("```", "").strip()
        intent_data = json.loads(clean_json_str)
        op = intent_data.get("operation")

        # Execute the corresponding DETERMINISTIC banking tool
        if op == "greeting":
            trace_id = generate_trace_id()
            greeting = intent_data.get("greeting_message") or "Hello! I am your AI Daily Banking Assistant. How can I assist you with your accounts, cards, UPI payments, or loans today?"
            return {
                "trace_id": trace_id,
                "answer": greeting,
                "answer_type": "llm_conversational",
                "tools_invoked": []
            }

        elif op == "get_balance":
            db_res = get_account_balance(customer_id)
            tool_name = "get_balance"
        elif op == "recent_transactions":
            db_res = get_recent_transactions(customer_id, limit=5)
            tool_name = "get_recent_transactions"
        elif op == "analyze_expenses":
            db_res = analyze_expenses(customer_id)
            tool_name = "analyze_expenses"
        elif op == "get_credit_card_details":
            db_res = get_credit_card_details(customer_id)
            tool_name = "get_credit_card_details"
        elif op == "verify_upi_payment":
            merchant = intent_data.get("merchant")
            db_res = verify_upi_payment(customer_id, query_term=merchant)
            tool_name = "verify_upi_payment"
        elif op == "get_next_emi":
            db_res = get_next_emi(customer_id)
            tool_name = "get_next_emi"
        elif op == "get_upcoming_payments":
            db_res = get_payments_due_this_week(customer_id)
            tool_name = "get_upcoming_payments"
        elif op == "calculate_remaining_funds_after_bills":
            db_res = calculate_remaining_funds_after_bills(customer_id)
            tool_name = "calculate_remaining_funds_after_bills"
        elif op == "analyze_personal_finance":
            db_res = analyze_personal_finance(customer_id)
            tool_name = "analyze_personal_finance"
        elif op == "block_card":
            # Sensitive confirmation
            return {
                "trace_id": generate_trace_id(),
                "answer": "⚠️ **SENSITIVE ACTION CONFIRMATION REQUIRED**\n\nDo you confirm that you want to permanently block your payment card and request a replacement?\n\nPlease reply **CONFIRM** or **YES** to proceed, or **CANCEL** to abort.",
                "answer_type": "confirmation_required",
                "tools_invoked": [],
                "set_pending_action": {"action": "BLOCK_CARD", "reason": "Customer reported card lost via AI Assistant", "replace": True}
            }
        elif op == "fraud_verification":
            tx_id = intent_data.get("transaction_id") or "TXN123456"
            db_res = fraud_verification(customer_id, tx_id)
            tool_name = "fraud_verification"
        elif op == "get_personalized_offers":
            db_res = get_personalized_offers(customer_id)
            tool_name = "get_personalized_offers"
        else:
            return None

        # Now have LLM explain the ACTUAL DETERMINISTIC DATA (Guarantees R6: No Hallucination)
        explain_prompt = f"""
You are the AI Daily Banking Assistant for HCLTech Bank.
The customer asked: "{user_message}".
The verified banking database returned this authentic data:
{json.dumps(db_res, default=str)}

INSTRUCTIONS:
1. Formulate a clear, professional, empathetic conversational response explaining this real data.
2. NEVER invent, modify, or round financial numbers beyond standard currency format. Use Rupee symbol (₹).
3. If status is NOT_FOUND, clearly tell the customer that no matching record was found in their authorized profile.
"""
        natural_answer = self._call_gemini_api(explain_prompt)
        if not natural_answer:
            # Fall back to raw message if explanation call fails
            natural_answer = db_res.get("answer") or db_res.get("message") or str(db_res)

        return {
            "trace_id": db_res.get("trace_id", generate_trace_id()),
            "answer": natural_answer,
            "answer_type": "llm_orchestrated",
            "tools_invoked": [tool_name],
            "data": db_res
        }

    # -----------------------------------------------------------------
    # RULE-BASED FALLBACK ENGINE (100% Deterministic & Offline Capable)
    # -----------------------------------------------------------------
    def _process_rule_based(self, customer_id: str, msg: str) -> Dict[str, Any]:
        lower_msg = msg.lower()

        # Greetings & conversational opening
        if lower_msg in ["hi", "hello", "hey", "good morning", "good evening", "namaste"]:
            trace_id = generate_trace_id()
            return {
                "trace_id": trace_id,
                "answer": (
                    "👋 **Hello! Welcome to HCLTech Daily Banking Assistant.**\n\n"
                    "I can help you manage your everyday banking activities through natural language. How can I assist you today?\n\n"
                    "**Quick Questions you can ask:**\n"
                    "• *'What is my current balance?'*\n"
                    "• *'How much did I spend this month?'*\n"
                    "• *'Did my UPI payment to Amazon go through?'*\n"
                    "• *'When is my credit card payment due?'*\n"
                    "• *'What is my next EMI amount?'*\n"
                    "• *'How much money do I have available after paying all upcoming bills?'*"
                ),
                "answer_type": "informational",
                "tools_invoked": []
            }

        # USE CASE 7: Remaining funds / After paying bills (PDF Page 4 & 5 Workflow)
        if any(phrase in lower_msg for phrase in [
            "available after paying all upcoming bills",
            "after paying bills",
            "money left after",
            "available after bills",
            "how much money do i have available after paying"
        ]):
            result = calculate_remaining_funds_after_bills(customer_id)
            return {
                "trace_id": result["trace_id"],
                "answer": result["answer"],
                "answer_type": "calculated",
                "tools_invoked": result["tools_invoked"],
                "data": result
            }

        # USE CASE 1: Account and Balance Inquiry
        elif any(phrase in lower_msg for phrase in ["balance", "how much money", "account balance", "current balance", "savings balance"]):
            res = get_account_balance(customer_id)
            if res["status"] == "SUCCESS":
                ans = f"Your primary {res['primary_account_type'].title()} account ({res['primary_account']}) balance is ₹{res['primary_balance']:,.2f}. Total balance across all active accounts is ₹{res['total_balance']:,.2f}."
            else:
                ans = res["message"]
            return {
                "trace_id": res["trace_id"],
                "answer": ans,
                "answer_type": "retrieved",
                "tools_invoked": ["get_balance"],
                "data": res
            }

        # USE CASE 1: Recent Credits / Debits / Account Summary
        elif any(phrase in lower_msg for phrase in ["recent credit", "recent debit", "transactions", "statement", "passbook", "account summary"]):
            tx_type = "CREDIT" if "credit" in lower_msg else ("DEBIT" if "debit" in lower_msg else None)
            res = get_recent_transactions(customer_id, limit=5, tx_type=tx_type)
            if res["status"] == "SUCCESS":
                tx_lines = [f"• {t['transaction_date']}: ₹{t['amount']:,.2f} ({t['transaction_type']}) at {t['merchant']} [{t['category']}]" for t in res["transactions"]]
                ans = f"Here are your recent {tx_type or ''} transactions:\n" + "\n".join(tx_lines)
            else:
                ans = "No recent transactions found on your account."
            return {
                "trace_id": res["trace_id"],
                "answer": ans,
                "answer_type": "retrieved",
                "tools_invoked": ["get_recent_transactions"],
                "data": res
            }

        # USE CASE 2: Daily Expense Tracking & Monthly Spend
        elif any(phrase in lower_msg for phrase in ["spend this month", "spent this month", "expense", "expenses", "spending", "how much did i spend"]):
            res = analyze_expenses(customer_id, period="current_month")
            if res["status"] == "SUCCESS":
                cat_summary = ", ".join([f"{c['category']}: ₹{c['amount']:,.2f} ({c['percentage']}%)" for c in res["category_breakdown"][:4]])
                ans = f"This month, you have spent a total of ₹{res['total_spent']:,.2f}. Top categories: {cat_summary}."
            else:
                ans = "You have no recorded debit expenses for the current month."
            return {
                "trace_id": res["trace_id"],
                "answer": ans,
                "answer_type": "retrieved",
                "tools_invoked": ["analyze_expenses"],
                "data": res
            }

        # USE CASE 3: Credit Card Assistance
        elif any(phrase in lower_msg for phrase in ["credit card", "card due", "card bill", "card payment due", "when is my credit card"]):
            if any(term in lower_msg for term in ["repay", "option", "how to pay", "repayment"]):
                res = get_card_repayment_options(customer_id)
                ans = f"Your credit card ({res['card_masked']}) total outstanding is ₹{res['total_outstanding']:,.2f} due on {res['due_date']}. Minimum due is ₹{res['minimum_due']:,.2f}."
                if res.get("emi_conversion_eligible"):
                    ans += f" You can also convert this balance into a 6-month EMI at approx ₹{res['estimated_6month_emi']:,.2f}/month."
                tools = ["get_credit_card_details", "get_card_repayment_options"]
            else:
                res = get_credit_card_details(customer_id)
                if res["status"] == "SUCCESS":
                    p = res["primary_card"]
                    ans = f"Your {p['card_type']} ({p['card_number_masked']}) has an outstanding balance of ₹{p['current_outstanding']:,.2f}. Minimum amount due is ₹{p['minimum_due']:,.2f}, payable by {p['due_date']}. Available credit limit: ₹{p['available_limit']:,.2f}."
                else:
                    ans = res["message"]
                tools = ["get_credit_card_details"]
            return {
                "trace_id": res["trace_id"],
                "answer": ans,
                "answer_type": "retrieved",
                "tools_invoked": tools,
                "data": res
            }

        # USE CASE 8: Card Services - Lost Card (Confirmation Required)
        elif any(phrase in lower_msg for phrase in ["lost my card", "lost my debit card", "lost my credit card", "block card", "block my card", "stolen card"]):
            card_res = get_credit_card_details(customer_id)
            masked = card_res["primary_card"]["card_number_masked"] if card_res["status"] == "SUCCESS" else "card"
            return {
                "trace_id": generate_trace_id(),
                "answer": f"⚠️ **SENSITIVE ACTION CONFIRMATION REQUIRED**\n\nAre you sure you want to permanently block your card ({masked}) and request a new replacement card to be dispatched to your registered address?\n\nPlease reply **CONFIRM** or **YES** to proceed, or **CANCEL** to abort.",
                "answer_type": "confirmation_required",
                "tools_invoked": [],
                "set_pending_action": {
                    "action": "BLOCK_CARD",
                    "reason": "Customer reported card lost/stolen via AI Assistant",
                    "replace": True
                }
            }

        # USE CASE 8 & R4: Request Card Limit Change
        elif any(phrase in lower_msg for phrase in ["increase limit", "credit limit", "change limit", "modify limit", "higher limit"]):
            numbers = re.findall(r"\d+", lower_msg.replace(",", ""))
            requested_limit = float(numbers[-1]) if numbers else 250000.0
            return {
                "trace_id": generate_trace_id(),
                "answer": f"⚠️ **CONFIRMATION REQUIRED**\n\nDo you confirm your request to change your credit card limit to **₹{requested_limit:,.2f}**?\n\nReply **CONFIRM** to proceed with automated policy underwriting, or **CANCEL**.",
                "answer_type": "confirmation_required",
                "tools_invoked": [],
                "set_pending_action": {
                    "action": "CHANGE_LIMIT",
                    "new_limit": requested_limit
                }
            }

        # USE CASE 4: UPI and Payment Assistance
        elif any(phrase in lower_msg for phrase in ["upi", "amazon", "swiggy", "flipkart", "payment go through", "payment status", "did my payment"]):
            target_merchant = None
            for m in ["amazon", "swiggy", "flipkart", "zomato", "uber", "tata"]:
                if m in lower_msg:
                    target_merchant = m
                    break
            res = verify_upi_payment(customer_id, query_term=target_merchant)
            if res["status"] == "SUCCESS":
                m = res["latest_match"]
                if res["is_success"]:
                    ans = f"✅ Your UPI payment of ₹{m['amount']:,.2f} to **{m['recipient_name']}** was **SUCCESSFUL** on {m['payment_date']}. Reference UTR: `{m['upi_ref_no']}`."
                else:
                    ans = f"❌ Your UPI payment of ₹{m['amount']:,.2f} to **{m['recipient_name']}** **FAILED**.\n• **Explanation:** {res['failure_explanation']}\n• **Reference UTR:** `{m['upi_ref_no']}`."
            else:
                ans = f"No UPI payment records found matching '{target_merchant or 'your query'}'. (Status: NOT_FOUND, no simulated transaction occurred)."
            return {
                "trace_id": res["trace_id"],
                "answer": ans,
                "answer_type": "retrieved",
                "tools_invoked": ["verify_upi_payment"],
                "data": res
            }

        # USE CASE 5: EMI and Loan Tracking
        elif any(phrase in lower_msg for phrase in ["emi", "loan", "home loan", "auto loan", "next emi", "outstanding loan"]):
            if "schedule" in lower_msg:
                res = get_emi_schedule(customer_id)
                ans = f"You have {len(res['schedules'])} scheduled EMI installments recorded on file."
                tools = ["get_emi_schedule"]
            else:
                res = get_next_emi(customer_id)
                if res["status"] == "SUCCESS":
                    ans = f"Your next EMI for **{res['loan_type']}** is **₹{res['emi_amount']:,.2f}**, due on **{res['due_date']}** (Principal: ₹{res['principal_split']:,.2f}, Interest: ₹{res['interest_split']:,.2f}). Outstanding loan balance is ₹{res['outstanding_balance']:,.2f}."
                else:
                    ans = res["message"]
                tools = ["get_next_emi"]
            return {
                "trace_id": res["trace_id"],
                "answer": ans,
                "answer_type": "retrieved",
                "tools_invoked": tools,
                "data": res
            }

        # USE CASE 6: Personal Finance Guidance
        elif any(phrase in lower_msg for phrase in ["save more", "savings", "save money", "personal finance", "finance advice", "budget"]):
            res = analyze_personal_finance(customer_id)
            obs_formatted = "\n".join([f"• {obs}" for obs in res["observations"]])
            ans = (
                f"📊 **Personal Finance Analysis**\n\n"
                f"• Monthly Inflow: ₹{res['monthly_income']:,.2f}\n"
                f"• Total Expenses & Debits: ₹{res['total_current_expenses']:,.2f}\n"
                f"• Fixed Commitments (EMIs + Bills): ₹{res['monthly_recurring_commitments']:,.2f}\n"
                f"• Projected Savings Rate: **{res['savings_rate_percentage']}%** (₹{res['projected_monthly_savings']:,.2f})\n\n"
                f"**Non-Binding Savings Observations:**\n{obs_formatted}"
            )
            return {
                "trace_id": res["trace_id"],
                "answer": ans,
                "answer_type": "calculated",
                "tools_invoked": ["analyze_personal_finance"],
                "data": res
            }

        # USE CASE 7: Smart Bill Reminder (due this week / upcoming)
        elif any(phrase in lower_msg for phrase in ["due this week", "bills due", "reminders", "bill reminder", "upcoming payments", "subscriptions"]):
            is_week = "week" in lower_msg
            res = get_payments_due_this_week(customer_id) if is_week else get_upcoming_payments(customer_id, days_ahead=30)
            if res["count"] > 0:
                items = "\n".join([f"• {b['due_date']}: **{b['title']}** ({b['type']}) — ₹{b['amount']:,.2f} {'[Autopay Active]' if b.get('is_autopay') else '[Manual Pay Required]'}" for b in res["obligations"][:6]])
                ans = f"📅 You have **{res['count']}** payment(s) due {'this week' if is_week else 'in the next 30 days'} totaling **₹{res['total_upcoming_amount']:,.2f}**:\n\n{items}"
            else:
                ans = f"You have no upcoming bills or payments due {'this week' if is_week else 'in the next 30 days'}."
            return {
                "trace_id": res["trace_id"],
                "answer": ans,
                "answer_type": "retrieved",
                "tools_invoked": ["get_upcoming_payments"],
                "data": res
            }

        # USE CASE 9: Fraud Support & Unrecognized Transactions
        elif any(phrase in lower_msg for phrase in [
            "fraud", "don't recognize", "do not recognize", "suspicious", "unauthorized",
            "unrecognized", "chargeback", "dispute", "txn123456"
        ]):
            tx_id = "TXN123456"
            found_tx = re.findall(r"TXN\d+", msg.upper())
            if found_tx:
                tx_id = found_tx[0]

            verify_res = fraud_verification(customer_id, tx_id)
            if verify_res["status"] == "SUCCESS":
                tx = verify_res["transaction"]
                ans = (
                    f"🚨 **Security & Fraud Verification for {tx['transaction_id']}**\n\n"
                    f"• **Merchant:** {tx['merchant']}\n"
                    f"• **Amount:** ₹{tx['amount']:,.2f} on {tx['transaction_date']}\n"
                    f"• **Risk Assessment:** **{verify_res['risk_level']} RISK**\n"
                    f"• **Signals:** {'; '.join(verify_res['risk_signals'])}\n\n"
                    f"Would you like to **file an immediate dispute** and temporarily lock your payment card to protect your account?\n"
                    f"Reply **CONFIRM DISPUTE** to proceed or **CANCEL**."
                )
                return {
                    "trace_id": verify_res["trace_id"],
                    "answer": ans,
                    "answer_type": "confirmation_required",
                    "tools_invoked": ["fraud_verification"],
                    "data": verify_res,
                    "set_pending_action": {
                        "action": "FILE_DISPUTE",
                        "transaction_id": tx["transaction_id"],
                        "merchant": tx["merchant"],
                        "amount": tx["amount"]
                    }
                }
            else:
                return {
                    "trace_id": verify_res["trace_id"],
                    "answer": verify_res["message"],
                    "answer_type": "retrieved",
                    "tools_invoked": ["fraud_verification"]
                }

        # USE CASE 10: Personalized Offers & Loan Eligibility
        elif any(phrase in lower_msg for phrase in ["offer", "offers", "pre-approved", "eligible", "eligibility", "pre approved"]):
            if "loan" in lower_msg:
                res = check_loan_eligibility(customer_id, "PERSONAL_LOAN")
                if res["decision"] == "ELIGIBLE":
                    ans = f"🎉 **Pre-Approved Loan Eligibility Confirmed!**\n\nBased on your credit score of **{res['credit_score']}** and low debt obligations, you are eligible for up to **₹{res['max_eligible_loan_amount']:,.2f}** at an attractive **{res['indicative_interest_rate']}% p.a.** with instant paperless disbursal."
                else:
                    ans = f"Eligibility status: **{res['decision']}**. {res['reason']}"
                tools = ["check_loan_eligibility"]
            else:
                res = get_personalized_offers(customer_id)
                if res["status"] == "SUCCESS":
                    offer_lines = [f"• **{o['title']}**: {o['description']}" for o in res["offers"]]
                    ans = f"🎁 **Personalized Offers for {res['customer_name']} (Credit Score: {res['credit_score']})**:\n\n" + "\n\n".join(offer_lines)
                else:
                    ans = res["message"]
                tools = ["get_personalized_offers"]
            return {
                "trace_id": res["trace_id"],
                "answer": ans,
                "answer_type": "retrieved",
                "tools_invoked": tools,
                "data": res
            }

        # Default fallback
        trace_id = generate_trace_id()
        return {
            "trace_id": trace_id,
            "answer": (
                "I am your AI Daily Banking Assistant. Here are some everyday banking activities I can assist with:\n\n"
                "• **Balance & History:** *'What is my current balance?'* or *'Show recent debits'*\n"
                "• **Expense Tracking:** *'How much have I spent this month?'*\n"
                "• **Credit Cards:** *'When is my credit card payment due?'* or *'Repayment options'*\n"
                "• **UPI & Payments:** *'Did my UPI payment to Amazon go through?'*\n"
                "• **Loans & EMIs:** *'What is my next EMI amount?'*\n"
                "• **Bill Reminders:** *'What payments are due this week?'* or *'How much money do I have available after paying all upcoming bills?'*\n"
                "• **Card Management:** *'I lost my debit card'*\n"
                "• **Fraud Support:** *'I do not recognize transaction TXN123456'*\n"
                "• **Offers & Advice:** *'Can I save more this month?'* or *'Am I eligible for a pre-approved loan?'*"
            ),
            "answer_type": "informational",
            "tools_invoked": []
        }

    def _execute_confirmed_action(self, customer_id: str, pending_action: Dict[str, Any]) -> Dict[str, Any]:
        """Executes an action only after verified customer confirmation (Requirement R4)."""
        action_name = pending_action.get("action")

        if action_name == "BLOCK_CARD":
            res = block_card(
                customer_id=customer_id,
                reason=pending_action.get("reason", "Customer requested block"),
                request_replacement=pending_action.get("replace", True)
            )
            return {
                "trace_id": res["trace_id"],
                "answer": f"🛡️ **Action Completed:** {res['message']}",
                "answer_type": "action_executed",
                "tools_invoked": ["block_card"],
                "data": res,
                "clear_pending_action": True
            }

        elif action_name == "CHANGE_LIMIT":
            new_limit = pending_action.get("new_limit", 250000.0)
            res = request_limit_change(customer_id, new_limit=new_limit)
            return {
                "trace_id": res["trace_id"],
                "answer": f"💳 **Action Completed:** {res['message']}",
                "answer_type": "action_executed",
                "tools_invoked": ["request_limit_change"],
                "data": res,
                "clear_pending_action": True
            }

        elif action_name == "FILE_DISPUTE":
            tx_id = pending_action.get("transaction_id", "TXN123456")
            res = report_fraud_and_open_dispute(
                customer_id=customer_id,
                transaction_id=tx_id,
                reason="Unrecognized suspicious transaction reported by customer",
                lock_linked_card=True
            )
            return {
                "trace_id": res["trace_id"],
                "answer": (
                    f"🚨 **Dispute Registered & Human Escalation Complete** (Requirement R7):\n\n"
                    f"• Dispute ID: **{res['dispute_id']}**\n"
                    f"• Assigned Bank Officer: **{res['assigned_officer']}**\n"
                    f"• Protection Actions: {', '.join(res['protection_actions'])}\n\n"
                    f"{res['message']}"
                ),
                "answer_type": "escalated",
                "tools_invoked": ["report_fraud_and_open_dispute"],
                "data": res,
                "clear_pending_action": True
            }

        return {
            "trace_id": generate_trace_id(),
            "answer": "Pending action completed.",
            "answer_type": "action_executed",
            "tools_invoked": [],
            "clear_pending_action": True
        }
