# Requirements Traceability Matrix (RTM)

## HCLTech Future Ready AI Engineer Hackathon
**Project:** AI-Powered Daily Banking Assistant  
**Status:** 100% Implemented & Verified

---

## 1. Daily Banking Use Cases (All 10 Implemented)

| # | Use Case | Customer Question / Trigger | Expected Behavior | Implemented Python Function | Verified Status |
|---|---|---|---|---|---|
| **UC-1** | **Account & Balance Inquiry** | *"What is my current account balance?"* | Retrieve available balance, recent credits and debits, and account summary. | `banking.account.get_account_balance`, `get_recent_transactions`, `get_account_summary` | ✅ Tested & Passing |
| **UC-2** | **Daily Expense Tracking** | *"How much have I spent this month?"* | Analyze debit transactions, categorize spending (Food, Transport, Shopping, Bills) and present trends. | `banking.expenses.analyze_expenses`, `get_spending_trends` | ✅ Tested & Passing |
| **UC-3** | **Credit Card Assistance** | *"When is my credit card payment due?"* | Retrieve statement details, due date, amount due, and repayment options. | `banking.cards.get_credit_card_details`, `get_card_repayment_options` | ✅ Tested & Passing |
| **UC-4** | **UPI & Payment Assistance** | *"Did my UPI payment to Amazon go through?"* | Verify transaction status, show 12-digit UTR reference number, and explain failures. | `banking.payments.verify_upi_payment`, `get_upi_history` | ✅ Tested & Passing |
| **UC-5** | **EMI & Loan Tracking** | *"What is my next EMI amount?"* | Retrieve active loan details, amortized schedule breakdown, and outstanding balance. | `banking.loans.get_next_emi`, `get_loan_summary`, `get_emi_schedule` | ✅ Tested & Passing |
| **UC-6** | **Personal Finance Guidance** | *"Can I save more this month?"* | Analyze income, expenses, and recurring payments, then provide non-binding savings observations. | `banking.finance.analyze_personal_finance` | ✅ Tested & Passing |
| **UC-7** | **Smart Bill Reminder** | *"What payments are due this week?"* / *"How much money do I have available after paying all upcoming bills?"* | Identify upcoming card dues, EMIs, utility bills, and calculate remaining funds. | `banking.reminders.get_payments_due_this_week`, `calculate_remaining_funds_after_bills` | ✅ Tested & Passing |
| **UC-8** | **Card Services** | *"I lost my debit card"* | Authenticate customer, request explicit confirmation, block the card, and initiate replacement reference under bank controls. | `banking.cards.block_card`, `request_limit_change` | ✅ Tested & Passing |
| **UC-9** | **Fraud Support** | *"I do not recognize this transaction"* (e.g., `TXN123456`) | Retrieve details, perform heuristic fraud checks, protect account with card lock, and open dispute workflow. | `banking.fraud.fraud_verification`, `report_fraud_and_open_dispute` | ✅ Tested & Passing |
| **UC-10**| **Personalized Offers** | *"Am I eligible for a pre-approved loan?"* | Use approved underwriting eligibility tools and policy rules to retrieve personalized offers. | `banking.offers.get_personalized_offers`, `check_loan_eligibility` | ✅ Tested & Passing |

---

## 2. Functional Requirements (All 8 Implemented)

| Requirement | Name | Description | Implementation Details | Verification |
|---|---|---|---|---|
| **R1** | **Secure Authentication** | Validate customer identity and authorization before providing account-specific data or executing actions. | Implemented in `utils/authentication.py`. Validates Customer ID with SHA-256 hashed PIN. All banking queries strictly isolate customer records by `customer_id`. | Unit test `test_r1_secure_authentication` passes. |
| **R2** | **Real-Time Banking Data** | Retrieve live information from core banking, payments, loan, and card systems. | Clean integration-ready modular architecture with simulated core SQLite database (`accounts`, `transactions`, `credit_cards`, `loans`, `upi_payments`). | Unit test `test_uc1_account_and_balance_inquiry` passes. |
| **R3** | **Financial Insights** | Provide spending analysis, savings observations, budget alerts, and cash-flow insights. | Implemented in `banking/expenses.py` and `banking/finance.py`. Computes discretionary spend, debt-to-income ratios, and non-binding savings rate observations. | Unit tests `test_uc2_daily_expense_tracking` and `test_uc6_personal_finance_guidance` pass. |
| **R4** | **Card & Payment Actions** | Execute approved actions such as blocking a card, raising a dispute, requesting a limit change, or confirming a payment. | Confirmation state machine in `ai/assistant.py` and action methods in `banking/cards.py`, `banking/payments.py`, and `banking/fraud.py`. | Unit test `test_uc8_card_services_and_actions` passes. |
| **R5** | **Personalized Banking** | Present relevant deposits, investments, credit products, or savings plans using approved suitability rules. | Implemented in `banking/offers.py`. Policy-based underwriting evaluates credit score, FOIR, and income multiplier. | Unit test `test_uc10_personalized_offers` passes. |
| **R6** | **No Hallucinations** | If data is unavailable, return a clear not-found outcome instead of inventing figures. | AI orchestrator strictly queries deterministic Python tools. Zero figure estimation by LLM. Missing records return explicit `"NOT_FOUND"` outcomes with audit logs. | Unit test `test_r6_no_hallucinations_not_found` passes. |
| **R7** | **Human Oversight** | Route high-risk, regulated, or exceptional cases to an authorized bank employee. | Implemented in `banking/fraud.py` and `utils/audit_log.py`. All suspicious transactions and disputes are flagged with `escalated_to_human=1` and displayed in the Human Oversight Queue in the dashboard. | Unit test `test_uc9_fraud_support_and_human_oversight` passes. |
| **R8** | **Auditability** | Record trace ID, customer authorization, systems queried, tools invoked, decisions, and action outcomes. | Implemented in `utils/audit_log.py`. Every operation generates a unique `BANK-XXXXX` Trace ID and persists an immutable audit entry in SQLite. | Unit test `test_r8_auditability` passes. |

