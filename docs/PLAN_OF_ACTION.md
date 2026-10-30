# Project Development Plan of Action (POA)

## AI-Powered Daily Banking Assistant
**HCLTech Future Ready AI Engineer Hackathon**

---

## 1. Project Objective & Vision

To develop a complete, functional, production-ready MVP for an AI-Powered Daily Banking Assistant that allows retail banking customers to manage their routine banking activities through a single conversational interface. The solution complies 100% with all 10 daily banking use cases and all 8 functional requirements specified by HCLTech.

---

## 2. Development Milestones & Task Breakdown

### Milestone 1: Requirements Analysis & Schema Design
- [x] Analyze `Daily_Banking_Assistant_Use_Case.pdf` thoroughly across all 6 pages.
- [x] Design normalized SQLite relational schema covering 11 tables: `customers`, `accounts`, `transactions`, `credit_cards`, `upi_payments`, `loans`, `emi_schedules`, `bills_subscriptions`, `disputes`, `personalized_offers`, and `audit_logs`.
- [x] Seed rich, realistic fictional banking records for multiple customer personas (Rahul Sharma C1001, Priya Patel C1002, Amit Verma C1003) reflecting the exact figures from the PDF specification (e.g. ₹1,25,000 balance, ₹8,500 food, ₹35,000 EMI).

### Milestone 2: Deterministic Banking Logic Implementation
- [x] `banking/account.py`: Account balances, recent credits/debits, account summary.
- [x] `banking/expenses.py`: Categorization (Food, Transport, Shopping, Bills) and monthly spending trends.
- [x] `banking/cards.py`: Statement details, due dates, repayment options, card blocking, limit changes.
- [x] `banking/payments.py`: UPI status check, 12-digit UTR tracking, NPCI failure explanations, test payments.
- [x] `banking/loans.py`: Loan summary, next EMI countdown, amortized schedule breakdown.
- [x] `banking/reminders.py`: Upcoming card dues, EMIs, utility bills, and remaining funds calculator.
- [x] `banking/finance.py`: Monthly cash flow, debt-to-income ratio, non-binding savings observations.
- [x] `banking/fraud.py`: Heuristic fraud verification, suspicious transaction flagging, dispute escalation.
- [x] `banking/offers.py`: Policy-based loan and deposit pre-approval engine.

### Milestone 3: Security, Auditability, and Human Oversight
- [x] `utils/authentication.py`: Secure PIN verification via SHA-256 and customer data isolation.
- [x] `utils/audit_log.py`: Unique `BANK-XXXXX` Trace ID generation, immutable event logging, and escalation queue.
- [x] Implement human officer review workflow for high-risk fraud cases (Requirement R7).

### Milestone 4: AI Assistant Orchestrator & State Machine
- [x] `ai/assistant.py`: Natural language intent routing to deterministic Python tools.
- [x] Confirmation state machine for sensitive operations (card block, limit change, dispute filing).
- [x] Anti-hallucination protocols returning explicit `NOT_FOUND` outcomes for missing records.
- [x] Standardized output formatting matching PDF Page 5 (`trace_id`, `answer`, `answer_type`, `tools_invoked`).

### Milestone 5: Streamlit Frontend & Visual Analytics
- [x] Build multi-tab corporate banking portal with HCLTech blue theme.
- [x] Interactive conversational AI chatbot with Suggested Prompts and trace badges.
- [x] Plotly visualizations: expense categorization donut chart and monthly spending trend bar chart.
- [x] Dedicated cards for accounts, credit cards, UPI history, loan schedules, and reminders.
- [x] Human Oversight & Audit Log viewer table.

### Milestone 6: Automated Testing & Documentation
- [x] Write and run 14 automated unit tests in `tests/test_banking.py`.
- [x] Produce comprehensive `README.md`, `docs/ARCHITECTURE.md`, `docs/REQUIREMENTS.md`, and `docs/PLAN_OF_ACTION.md`.
- [x] Provide one-click launch scripts (`run_app.bat` and `run_app.ps1`).

---

## 3. Expected Outcomes & Deliverables

1. **Fully Functional MVP:** Customer can ask everyday questions in natural language and receive instant, verified answers derived directly from the database.
2. **Zero Financial Hallucinations:** All monetary calculations and policy checks are performed deterministically by Python functions.
3. **Enterprise Compliance:** Sensitive actions require customer confirmation, high-risk cases are escalated to authorized staff, and all actions generate immutable audit logs with Trace IDs.

