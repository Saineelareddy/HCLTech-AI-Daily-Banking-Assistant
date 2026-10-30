# AI-Powered Daily Banking Assistant
### HCLTech Future Ready AI Engineer Hackathon — Functional MVP

An enterprise-grade, conversational AI banking assistant allowing retail customers to manage all everyday banking activities through a single interface. Built with **Streamlit**, **Python**, **SQLite**, and **Plotly**, adhering strictly to the HCLTech Hackathon problem statement.

---

## 🌟 Key Highlights

- **100% Coverage of All 10 Banking Use Cases:** Account inquiry, daily expense tracking, credit card assistance, UPI tracking, loan/EMI management, financial guidance, smart reminders, card services, fraud protection, and personalized offers.
- **100% Compliance with All 8 Functional Requirements (R1 - R8):** Secure PIN authentication, real-time banking data simulation, financial insights, confirmation before sensitive actions, policy-based personalized offers, zero hallucinations, human oversight escalation queue, and auditability with enterprise Trace IDs.
- **Deterministic Core Principle:** All financial math, balances, due dates, and underwriting rules are computed by pure, deterministic Python functions. The AI language model is used solely for orchestration, natural language understanding, and conversational explanation.

---

## 🛠️ Technology Stack

- **Frontend & Dashboard:** [Streamlit](https://streamlit.io/) (1.66+)
- **Backend & Business Logic:** Python (3.11+)
- **Database:** SQLite (Embedded Relational Database with 11 normalized tables)
- **Data Analytics:** [Pandas](https://pandas.pydata.org/)
- **Visualizations:** [Plotly](https://plotly.com/python/) (Interactive category pie/donut & spending trend bar charts)
- **AI Orchestrator:** Conversational Assistant with intent routing, entity extraction, and confirmation state machine. Supports optional Gemini / LLM API integration with full deterministic rule-based fallback.

---

## 📂 Project Structure

```text
daily_banking_assistant/
│
├── app.py                      # Main Streamlit Banking Dashboard Application
├── requirements.txt            # Python dependencies
├── README.md                   # Complete project documentation and guide
│
├── database/
│   ├── db.py                   # Thread-safe SQLite connector and query utilities
│   ├── schema.sql              # SQL DDL for all 11 banking tables
│   └── sample_data.py          # Seed script with realistic fictional banking records
│
├── banking/                    # Deterministic Banking Operations
│   ├── account.py              # UC-1: Account and balance inquiries, recent credits/debits
│   ├── expenses.py             # UC-2: Monthly spend categorization and trends
│   ├── cards.py                # UC-3 & UC-8: Credit card dues, repayments, limit changes, card block
│   ├── payments.py             # UC-4: UPI status lookup, UTR reference tracking, failure causes
│   ├── loans.py                # UC-5: Active loans, next EMI countdown, amortized schedule
│   ├── reminders.py            # UC-7: Upcoming bill reminders and remaining funds calculator
│   ├── finance.py              # UC-6: Personal finance observations and debt-to-income analysis
│   ├── fraud.py                # UC-9: Transaction risk verification, dispute filing, card freeze
│   └── offers.py               # UC-10: Policy-based pre-approved loan & deposit eligibility
│
├── ai/                         # Conversational Orchestration Layer
│   ├── assistant.py            # AI Assistant orchestrator & confirmation state machine
│   └── prompts.py              # System directives and response templates
│
├── utils/                      # Security & Governance
│   ├── authentication.py       # R1: SHA-256 PIN authentication and profile retrieval
│   └── audit_log.py            # R7 & R8: Trace ID generation, audit logging, human escalation queue
│
├── docs/                       # Technical Documentation
│   ├── ARCHITECTURE.md         # System design, data flow, and Mermaid diagrams
│   ├── REQUIREMENTS.md         # Traceability matrix mapping all 10 UCs and 8 Requirements
│   └── PLAN_OF_ACTION.md       # Development plan, milestones, and deliverables
│
└── tests/
    └── test_banking.py         # Automated unit test suite (14 test cases, 100% passing)
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
Ensure you have Python 3.10+ installed on your system.

### 2. Navigate to Project Directory
```powershell
cd daily_banking_assistant
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Initialize Database
```powershell
python -c "from database.db import init_db; init_db(force_reseed=True)"
```

### 5. Run Streamlit Application
```powershell
streamlit run app.py
```
The application will launch automatically in your browser at `http://localhost:8501`.

---

## 👥 Demo Personas & Credentials

For rapid hackathon demonstration, 3 customer profiles are pre-configured:

| Customer ID | Name | Role / Profile | Demo PIN | Active Products |
|---|---|---|---|---|
| **C1001** *(Default)* | **Rahul Sharma** | Salaried Executive (₹95,000/mo, Credit Score 785) | `1234` | Primary Salary Account (₹1,25,000), Platinum VISA Card, Active Home Loan (EMI ₹35,000), Suspicious Transaction `TXN123456` |
| **C1002** | **Priya Patel** | IT Professional (₹65,000/mo, Credit Score 740) | `2345` | Savings Account (₹64,500), Auto Loan (EMI ₹12,500), Failed Amazon UPI Payment |
| **C1003** | **Amit Verma** | Senior Consultant (₹1,30,000/mo, Credit Score 810) | `3456` | Current Account (₹2,10,000), Blocked RuPay Card with Replacement Reference, Eligible for ₹75L Home Loan |

---

## 💬 Example Natural Language Queries to Try

You can type any of these in the **AI Assistant** chat tab or click the suggested buttons:

1. **Balance Inquiry (UC-1):**
   > *"What is my current balance?"*
2. **Expense Tracking (UC-2):**
   > *"How much have I spent this month?"*
3. **Credit Card Assistance (UC-3):**
   > *"When is my credit card payment due?"* or *"What are my repayment options?"*
4. **UPI Status (UC-4):**
   > *"Did my UPI payment to Amazon go through?"* or *"Why did my Flipkart payment fail?"*
5. **Loan / EMI (UC-5):**
   > *"What is my next EMI amount?"* or *"Show my loan schedule"*
6. **Financial Guidance (UC-6):**
   > *"Can I save more this month?"*
7. **Upcoming Obligations & Remaining Funds (UC-7 & Section 7 Workflow):**
   > *"What payments are due this week?"*  
   > *"How much money do I have available after paying all upcoming bills?"*
8. **Lost Card Service (UC-8 & R4):**
   > *"I lost my debit card"* → Assistant prompts for confirmation → Reply *"CONFIRM"* to block card and order replacement.
9. **Fraud & Dispute (UC-9 & R7):**
   > *"I do not recognize transaction TXN123456"* → Assistant flags high risk → Confirms dispute → Escalates to human fraud officer.
10. **Personalized Offers (UC-10 & R5):**
    > *"Am I eligible for a pre-approved loan?"* or *"Show my personalized offers"*

---

## 🧪 Automated Testing

To run the automated test suite verifying all 10 use cases and 8 functional requirements:
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```
**Result:** 14 tests run, 0 failures, 0 errors (`OK`).

---

## 🛡️ Enterprise Security & Human Oversight

- **Customer Data Isolation:** Every query enforces customer authorization via parameterization (`WHERE customer_id = ?`).
- **Confirmation Guardrails (R4):** Sensitive operations (card blocking, limit revisions, dispute registrations) cannot execute without affirmative customer consent.
- **Human Escalation Queue (R7):** All suspicious transactions and disputes are automatically routed to a simulated authorized bank officer queue where staff can review, update notes, and resolve tickets.
- **Auditability (R8):** Every operation generates an enterprise Trace ID (e.g., `BANK-50021`) logged with exact tools invoked, systems queried, timestamps, and decision outcomes.

---

## 🔮 Limitations & Future Enhancements

- **Limitations:** Currently operating in Demo Mode using a simulated relational SQLite database. Live bank connectivity requires RBI-approved Open Banking / Account Aggregator APIs.
- **Future Enhancements:**
  - Integration with RBI Account Aggregator (AA) framework for multi-bank statement analysis.
  - Multilingual voice banking interface with speech-to-text for regional Indian languages.
  - Biometric authentication (WebAuthn / Passkeys) in production mobile wrappers.

