"""
Comprehensive Unit & Integration Tests for Daily Banking Assistant
Validates all 10 banking use cases and all 8 functional requirements.
"""

import unittest
import sys
import os

# Ensure package directory is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.db import init_db
from utils.authentication import authenticate_customer, get_customer_profile
from utils.audit_log import get_audit_logs, get_escalated_cases
from banking.account import get_account_balance, get_recent_transactions
from banking.expenses import analyze_expenses, get_spending_trends
from banking.cards import get_credit_card_details, get_card_repayment_options, block_card, request_limit_change
from banking.payments import verify_upi_payment, execute_simulated_payment
from banking.loans import get_loan_summary, get_next_emi, get_emi_schedule
from banking.reminders import get_upcoming_payments, get_payments_due_this_week, calculate_remaining_funds_after_bills
from banking.finance import analyze_personal_finance
from banking.fraud import fraud_verification, report_fraud_and_open_dispute
from banking.offers import get_personalized_offers, check_loan_eligibility
from ai.assistant import DailyBankingAssistant


class TestDailyBankingAssistant(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initializes test database with clean seeded data."""
        init_db(force_reseed=True)
        cls.assistant = DailyBankingAssistant()
        cls.test_cust = "C1001"

    # --- REQUIREMENT R1: SECURE AUTHENTICATION ---
    def test_r1_secure_authentication(self):
        # Valid login
        cust = authenticate_customer("C1001", "1234")
        self.assertIsNotNone(cust)
        self.assertEqual(cust["name"], "Rahul Sharma")
        self.assertEqual(cust["customer_id"], "C1001")

        # Invalid PIN
        bad_auth = authenticate_customer("C1001", "0000")
        self.assertIsNone(bad_auth)

        # Invalid Customer ID
        non_cust = authenticate_customer("C9999", "1234")
        self.assertIsNone(non_cust)

    # --- USE CASE 1 & R2: ACCOUNT & BALANCE INQUIRY ---
    def test_uc1_account_and_balance_inquiry(self):
        bal = get_account_balance(self.test_cust)
        self.assertEqual(bal["status"], "SUCCESS")
        self.assertIn("trace_id", bal)
        self.assertTrue(bal["trace_id"].startswith("BANK-"))
        self.assertGreaterEqual(bal["total_balance"], 125000.0)

        recent = get_recent_transactions(self.test_cust, limit=3)
        self.assertEqual(recent["status"], "SUCCESS")
        self.assertLessEqual(len(recent["transactions"]), 3)

    # --- USE CASE 2 & R3: DAILY EXPENSE TRACKING ---
    def test_uc2_daily_expense_tracking(self):
        exp = analyze_expenses(self.test_cust)
        self.assertEqual(exp["status"], "SUCCESS")
        self.assertGreater(exp["total_spent"], 0.0)
        self.assertTrue(len(exp["category_breakdown"]) > 0)

        # Verify trends
        trends = get_spending_trends(self.test_cust)
        self.assertEqual(trends["status"], "SUCCESS")

    # --- USE CASE 3: CREDIT CARD ASSISTANCE ---
    def test_uc3_credit_card_assistance(self):
        cards = get_credit_card_details(self.test_cust)
        self.assertEqual(cards["status"], "SUCCESS")
        self.assertEqual(len(cards["cards"]), 1)
        self.assertIn("due_date", cards["primary_card"])

        repay = get_card_repayment_options(self.test_cust)
        self.assertEqual(repay["status"], "SUCCESS")
        self.assertGreater(len(repay["repayment_options"]), 0)

    # --- USE CASE 4: UPI AND PAYMENT ASSISTANCE ---
    def test_uc4_upi_payment_assistance(self):
        # Successful payment check (Amazon)
        res_amazon = verify_upi_payment(self.test_cust, "Amazon")
        self.assertEqual(res_amazon["status"], "SUCCESS")
        self.assertTrue(res_amazon["is_success"])
        self.assertIsNotNone(res_amazon["reference_number"])

        # Failed payment check (Flipkart with failure explanation)
        res_flipkart = verify_upi_payment(self.test_cust, "Flipkart")
        self.assertEqual(res_flipkart["status"], "SUCCESS")
        self.assertFalse(res_flipkart["is_success"])
        self.assertIn("timeout", res_flipkart["failure_explanation"].lower())

    # --- USE CASE 5: EMI AND LOAN TRACKING ---
    def test_uc5_emi_and_loan_tracking(self):
        loan = get_loan_summary(self.test_cust)
        self.assertEqual(loan["status"], "SUCCESS")
        self.assertGreater(loan["total_active_loans"], 0)

        next_emi = get_next_emi(self.test_cust)
        self.assertEqual(next_emi["status"], "SUCCESS")
        self.assertEqual(next_emi["emi_amount"], 35000.0)

    # --- USE CASE 6: PERSONAL FINANCE GUIDANCE ---
    def test_uc6_personal_finance_guidance(self):
        fin = analyze_personal_finance(self.test_cust)
        self.assertEqual(fin["status"], "SUCCESS")
        self.assertIn("savings_rate_percentage", fin)
        self.assertTrue(len(fin["observations"]) > 0)

    # --- USE CASE 7 & SECTION 7 WORKFLOW: SMART BILL REMINDERS & REMAINING FUNDS ---
    def test_uc7_smart_bill_reminder_and_remaining_funds(self):
        # Due this week
        weekly = get_payments_due_this_week(self.test_cust)
        self.assertEqual(weekly["status"], "SUCCESS")

        # Exact multi-step calculation from PDF Page 4 & 5
        funds = calculate_remaining_funds_after_bills(self.test_cust)
        self.assertIn("BANK-", funds["trace_id"])
        self.assertIn("available balance is", funds["answer"].lower())
        self.assertEqual(funds["answer_type"], "calculated")
        self.assertIn("get_balance", funds["tools_invoked"])
        self.assertIn("get_upcoming_payments", funds["tools_invoked"])

    # --- USE CASE 8 & R4: CARD SERVICES (BLOCK CARD & LIMIT CHANGE) ---
    def test_uc8_card_services_and_actions(self):
        # Card limit change
        limit_res = request_limit_change(self.test_cust, 250000.0)
        self.assertEqual(limit_res["status"], "SUCCESS")
        self.assertEqual(limit_res["new_limit"], 250000.0)

        # Card blocking with replacement
        block_res = block_card(self.test_cust, reason="Lost card test", request_replacement=True)
        self.assertEqual(block_res["status"], "SUCCESS")
        self.assertEqual(block_res["new_status"], "BLOCKED")
        self.assertTrue(block_res["replacement_initiated"])
        self.assertIsNotNone(block_res["replacement_reference"])

    # --- USE CASE 9 & R7: FRAUD SUPPORT & HUMAN OVERSIGHT ---
    def test_uc9_fraud_support_and_human_oversight(self):
        # Verification of suspicious transaction
        fraud_check = fraud_verification(self.test_cust, "TXN123456")
        self.assertEqual(fraud_check["status"], "SUCCESS")
        self.assertEqual(fraud_check["risk_level"], "HIGH")

        # Open dispute with escalation to human officer
        dispute_res = report_fraud_and_open_dispute(self.test_cust, "TXN123456", "Suspicious charge")
        self.assertEqual(dispute_res["status"], "SUCCESS")
        self.assertTrue(dispute_res["escalated_to_human"])
        self.assertIn("DISP-", dispute_res["dispute_id"])
        self.assertIsNotNone(dispute_res["assigned_officer"])

        # Check human escalation queue
        escalated = get_escalated_cases()
        self.assertTrue(any(e["dispute_id"] == dispute_res["dispute_id"] for e in escalated))

    # --- USE CASE 10 & R5: PERSONALIZED OFFERS ---
    def test_uc10_personalized_offers(self):
        offers = get_personalized_offers(self.test_cust)
        self.assertEqual(offers["status"], "SUCCESS")
        self.assertGreater(offers["count"], 0)

        elig = check_loan_eligibility(self.test_cust, "PERSONAL_LOAN")
        self.assertEqual(elig["decision"], "ELIGIBLE")
        self.assertGreater(elig["max_eligible_loan_amount"], 0)

    # --- REQUIREMENT R6: NO HALLUCINATIONS (CLEAR NOT FOUND) ---
    def test_r6_no_hallucinations_not_found(self):
        # Querying a non-existent merchant
        not_found_upi = verify_upi_payment(self.test_cust, "NON_EXISTENT_MERCHANT_XYZ")
        self.assertEqual(not_found_upi["status"], "NOT_FOUND")

        # Querying an unknown transaction
        not_found_tx = fraud_verification(self.test_cust, "TXN9999999")
        self.assertEqual(not_found_tx["status"], "NOT_FOUND")

    # --- REQUIREMENT R8: AUDITABILITY ---
    def test_r8_auditability(self):
        logs = get_audit_logs(customer_id=self.test_cust, limit=10)
        self.assertTrue(len(logs) > 0)
        for log in logs:
            self.assertIn("trace_id", log)
            self.assertIn("systems_queried", log)
            self.assertIn("tools_invoked", log)
            self.assertIn("decision_outcome", log)

    # --- AI CONVERSATION ORCHESTRATION & CONFIRMATION ---
    def test_ai_conversation_flows(self):
        # Balance inquiry
        res1 = self.assistant.process_query(self.test_cust, "What is my current balance?")
        self.assertIn("balance", res1["answer"].lower())
        self.assertIn("get_balance", res1["tools_invoked"])

        # Section 7 example question
        res2 = self.assistant.process_query(self.test_cust, "How much money do I have available after paying all upcoming bills?")
        self.assertIn("available balance is", res2["answer"].lower())
        self.assertEqual(res2["answer_type"], "calculated")

        # Confirmation flow for card blocking
        res3 = self.assistant.process_query(self.test_cust, "I lost my debit card")
        self.assertEqual(res3["answer_type"], "confirmation_required")
        self.assertIn("set_pending_action", res3)

        # Confirming the pending action
        ctx = {"pending_action": res3["set_pending_action"]}
        res4 = self.assistant.process_query(self.test_cust, "CONFIRM", session_context=ctx)
        self.assertEqual(res4["answer_type"], "action_executed")
        self.assertTrue(res4.get("clear_pending_action"))


if __name__ == "__main__":
    unittest.main()

