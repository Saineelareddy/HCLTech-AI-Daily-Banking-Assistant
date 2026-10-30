"""
Sample Data Loader for AI-Powered Daily Banking Assistant
Provides realistic banking data for multiple customers to test all 10 use cases.
"""

import hashlib
from datetime import datetime, timedelta
from database.db import get_connection


def hash_pin(pin: str) -> str:
    """Generates a secure SHA-256 hash of a 4-digit PIN."""
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


def seed_sample_data() -> None:
    """Populates the SQLite database with comprehensive fictional banking records."""
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing data to avoid primary key collisions on re-seed
    tables = [
        "audit_logs", "personalized_offers", "disputes", "bills_subscriptions",
        "emi_schedules", "loans", "upi_payments", "credit_cards",
        "transactions", "accounts", "customers"
    ]
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")

    # Today's reference date
    today = datetime.now()
    cur_month_str = today.strftime("%Y-%m")

    # 1. CUSTOMERS
    customers = [
        ("C1001", "Rahul Sharma", "rahul.sharma@example.com", "+91 98765 43210", hash_pin("1234"), "VERIFIED", "LOW", 95000.0, 785),
        ("C1002", "Priya Patel", "priya.patel@example.com", "+91 98123 45678", hash_pin("2345"), "VERIFIED", "LOW", 65000.0, 740),
        ("C1003", "Amit Verma", "amit.verma@example.com", "+91 97654 32109", hash_pin("3456"), "VERIFIED", "MEDIUM", 130000.0, 810)
    ]
    cursor.executemany("""
        INSERT INTO customers (customer_id, name, email, phone, pin_hash, kyc_status, risk_tier, monthly_income, credit_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, customers)

    # 2. ACCOUNTS
    accounts = [
        ("ACC100101", "C1001", "SALARY", 125000.0, "INR", "Connaught Place, New Delhi", "HCLB0001001", "ACTIVE"),
        ("ACC100102", "C1001", "SAVINGS", 35000.0, "INR", "Connaught Place, New Delhi", "HCLB0001001", "ACTIVE"),
        ("ACC100201", "C1002", "SAVINGS", 64500.0, "INR", "MG Road, Bengaluru", "HCLB0002005", "ACTIVE"),
        ("ACC100301", "C1003", "CURRENT", 210000.0, "INR", "Bandra Kurla Complex, Mumbai", "HCLB0003010", "ACTIVE")
    ]
    cursor.executemany("""
        INSERT INTO accounts (account_number, customer_id, account_type, balance, currency, branch, ifsc_code, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, accounts)

    # 3. TRANSACTIONS
    # Note: Includes illustrative figures from PDF page 3 (Food ₹8,500, Transport ₹3,200, Shopping ₹12,000, Bills ₹4,500)
    transactions = [
        # Customer C1001 - Current Month
        ("TXN1001", "ACC100101", "C1001", (today - timedelta(days=2)).strftime("%Y-%m-%d"), 8500.0, "DEBIT", "Food", "Zomato & Nature Basket", "UPI", "Groceries and weekend dining", "SUCCESS", 0),
        ("TXN1002", "ACC100101", "C1001", (today - timedelta(days=4)).strftime("%Y-%m-%d"), 3200.0, "DEBIT", "Transport", "Uber & Metro Rail", "DEBIT_CARD", "Commute and cab fares", "SUCCESS", 0),
        ("TXN1003", "ACC100101", "C1001", (today - timedelta(days=6)).strftime("%Y-%m-%d"), 12000.0, "DEBIT", "Shopping", "Amazon Retail India", "UPI", "Electronics & home essentials", "SUCCESS", 0),
        ("TXN1004", "ACC100101", "C1001", (today - timedelta(days=8)).strftime("%Y-%m-%d"), 4500.0, "DEBIT", "Bills", "Tata Power DDL", "NET_BANKING", "Monthly Electricity Bill", "SUCCESS", 0),
        ("TXN1005", "ACC100101", "C1001", (today - timedelta(days=1)).strftime("%Y-%m-%d"), 95000.0, "CREDIT", "Salary", "HCLTech Payroll", "NEFT", "Monthly Salary Credit", "SUCCESS", 0),
        ("TXN1006", "ACC100101", "C1001", (today - timedelta(days=10)).strftime("%Y-%m-%d"), 2400.0, "DEBIT", "Food", "Swiggy Dineout", "UPI", "Family dinner", "SUCCESS", 0),
        ("TXN1007", "ACC100101", "C1001", (today - timedelta(days=12)).strftime("%Y-%m-%d"), 1800.0, "DEBIT", "Entertainment", "PVR Cinemas", "DEBIT_CARD", "Movie tickets and snacks", "SUCCESS", 0),
        ("TXN1008", "ACC100101", "C1001", (today - timedelta(days=15)).strftime("%Y-%m-%d"), 5000.0, "CREDIT", "Investment", "Groww Mutual Fund Dividend", "NEFT", "Dividend payout", "SUCCESS", 0),
        # Suspicious transaction for C1001 to test Fraud Support (Use Case 9)
        ("TXN123456", "ACC100101", "C1001", (today - timedelta(hours=8)).strftime("%Y-%m-%d"), 8450.0, "DEBIT", "Shopping", "GLOBAL_GAMING_PORTAL_CY", "CREDIT_CARD", "Unrecognized international gaming purchase", "SUCCESS", 1),

        # Customer C1002
        ("TXN2001", "ACC100201", "C1002", (today - timedelta(days=3)).strftime("%Y-%m-%d"), 4200.0, "DEBIT", "Food", "Blinkit", "UPI", "Grocery quick delivery", "SUCCESS", 0),
        ("TXN2002", "ACC100201", "C1002", (today - timedelta(days=5)).strftime("%Y-%m-%d"), 65000.0, "CREDIT", "Salary", "Infosys Technologies", "NEFT", "Salary Credit", "SUCCESS", 0),
        ("TXN2003", "ACC100201", "C1002", (today - timedelta(days=7)).strftime("%Y-%m-%d"), 15000.0, "DEBIT", "Shopping", "Myntra Fashion", "DEBIT_CARD", "Festive clothing", "SUCCESS", 0),

        # Customer C1003
        ("TXN3001", "ACC100301", "C1003", (today - timedelta(days=2)).strftime("%Y-%m-%d"), 130000.0, "CREDIT", "Salary", "Consulting Retainer", "NEFT", "Monthly Client Retainer", "SUCCESS", 0),
        ("TXN3002", "ACC100301", "C1003", (today - timedelta(days=4)).strftime("%Y-%m-%d"), 18500.0, "DEBIT", "Travel", "MakeMyTrip Flights", "NET_BANKING", "Flight booking to Mumbai", "SUCCESS", 0)
    ]
    cursor.executemany("""
        INSERT INTO transactions (transaction_id, account_number, customer_id, transaction_date, amount, transaction_type, category, merchant, payment_method, description, status, is_suspicious)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, transactions)

    # 4. CREDIT CARDS
    statement_date_c1 = (today - timedelta(days=20)).strftime("%Y-%m-%d")
    due_date_c1 = (today + timedelta(days=8)).strftime("%Y-%m-%d")

    credit_cards = [
        ("CC1001", "C1001", "•••• •••• •••• 4589", "VISA", "HCL Platinum Rewards", 200000.0, 168000.0, 32000.0, 3200.0, statement_date_c1, due_date_c1, "ACTIVE", 0, None),
        ("CC1002", "C1002", "•••• •••• •••• 8912", "MASTERCARD", "Smart Cashback Credit Card", 150000.0, 135800.0, 14200.0, 1500.0, statement_date_c1, (today + timedelta(days=12)).strftime("%Y-%m-%d"), "ACTIVE", 0, None),
        ("CC1003", "C1003", "•••• •••• •••• 1104", "RUPAY", "Regalia Elite RuPay", 300000.0, 275000.0, 25000.0, 2500.0, statement_date_c1, (today + timedelta(days=4)).strftime("%Y-%m-%d"), "BLOCKED", 1, "REP-2026-8819")
    ]
    cursor.executemany("""
        INSERT INTO credit_cards (card_id, customer_id, card_number_masked, card_network, card_type, credit_limit, available_limit, current_outstanding, minimum_due, statement_date, due_date, status, replacement_requested, replacement_reference)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, credit_cards)

    # 5. UPI PAYMENTS (Covers Use Case 4: UPI status, ref numbers, failures)
    upi_payments = [
        ("UPI1001", "C1001", "ACC100101", "429381029481", "amazonpay@apl", "Amazon India", 1499.0, (today - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS", None),
        ("UPI1002", "C1001", "ACC100101", "429381029482", "swiggy@icici", "Swiggy Delivery", 640.0, (today - timedelta(hours=14)).strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS", None),
        ("UPI1003", "C1001", "ACC100101", "429381029483", "flipkart@axisbank", "Flipkart Internet Pvt Ltd", 4999.0, (today - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), "FAILED", "Beneficiary Bank server timeout (Error Code: NPCI-U30)"),
        ("UPI1004", "C1001", "ACC100101", "429381029484", "tatapower@yesbank", "Tata Power Delhi", 4500.0, (today - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS", None),
        ("UPI2001", "C1002", "ACC100201", "429381029485", "amazonpay@apl", "Amazon India", 2899.0, (today - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), "FAILED", "Insufficient account balance at the time of debit (Error Code: NPCI-ZM)"),
        ("UPI3001", "C1003", "ACC100301", "429381029486", "uber@hdfcbank", "Uber Rides", 450.0, (today - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS", None)
    ]
    cursor.executemany("""
        INSERT INTO upi_payments (upi_txn_id, customer_id, account_number, upi_ref_no, recipient_vpa, recipient_name, amount, payment_date, status, failure_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, upi_payments)

    # 6. LOANS (Covers Use Case 5: EMI and Loan Tracking)
    next_emi_date_c1 = (today + timedelta(days=5)).strftime("%Y-%m-%d")
    loans = [
        ("LN100101", "C1001", "HOME_LOAN", 4500000.0, 3840000.0, 8.4, 240, 35000.0, (today - timedelta(days=730)).strftime("%Y-%m-%d"), (today + timedelta(days=6570)).strftime("%Y-%m-%d"), next_emi_date_c1, "ACTIVE"),
        ("LN100201", "C1002", "AUTO_LOAN", 800000.0, 420000.0, 9.1, 60, 12500.0, (today - timedelta(days=365)).strftime("%Y-%m-%d"), (today + timedelta(days=1460)).strftime("%Y-%m-%d"), (today + timedelta(days=10)).strftime("%Y-%m-%d"), "ACTIVE")
    ]
    cursor.executemany("""
        INSERT INTO loans (loan_id, customer_id, loan_type, principal_amount, outstanding_balance, interest_rate, tenure_months, emi_amount, start_date, end_date, next_emi_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, loans)

    # 7. EMI SCHEDULES
    emi_schedules = [
        ("SCH1001-23", "LN100101", "C1001", 23, (today - timedelta(days=25)).strftime("%Y-%m-%d"), 35000.0, 8120.0, 26880.0, "PAID", (today - timedelta(days=25)).strftime("%Y-%m-%d")),
        ("SCH1001-24", "LN100101", "C1001", 24, next_emi_date_c1, 35000.0, 8180.0, 26820.0, "UPCOMING", None),
        ("SCH1001-25", "LN100101", "C1001", 25, (today + timedelta(days=35)).strftime("%Y-%m-%d"), 35000.0, 8240.0, 26760.0, "UPCOMING", None),
        ("SCH2001-12", "LN100201", "C1002", 12, (today + timedelta(days=10)).strftime("%Y-%m-%d"), 12500.0, 9300.0, 3200.0, "UPCOMING", None)
    ]
    cursor.executemany("""
        INSERT INTO emi_schedules (schedule_id, loan_id, customer_id, emi_number, due_date, emi_amount, principal_component, interest_component, status, paid_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, emi_schedules)

    # 8. BILLS & SUBSCRIPTIONS (Covers Use Case 7: Smart Bill Reminder)
    bills = [
        ("BILL1001", "C1001", "Airtel Xstream Fiber", "Broadband", 999.0, (today + timedelta(days=3)).strftime("%Y-%m-%d"), 1, "SCHEDULED"),
        ("BILL1002", "C1001", "Tata Power DDL", "Utility - Electricity", 4500.0, (today + timedelta(days=6)).strftime("%Y-%m-%d"), 0, "UNPAID"),
        ("BILL1003", "C1001", "Netflix Premium 4K", "OTT Subscription", 649.0, (today + timedelta(days=14)).strftime("%Y-%m-%d"), 1, "SCHEDULED"),
        ("BILL1004", "C1001", "Indraprastha Gas Limited", "Utility - Piped Gas", 850.0, (today + timedelta(days=18)).strftime("%Y-%m-%d"), 0, "UNPAID"),
        ("BILL2001", "C1002", "Jio Fiber Gigabit", "Broadband", 1199.0, (today + timedelta(days=2)).strftime("%Y-%m-%d"), 1, "SCHEDULED"),
        ("BILL3001", "C1003", "Tata Sky Binge+", "DTH & Cable", 750.0, (today + timedelta(days=5)).strftime("%Y-%m-%d"), 0, "UNPAID")
    ]
    cursor.executemany("""
        INSERT INTO bills_subscriptions (bill_id, customer_id, biller_name, biller_category, amount, due_date, auto_pay, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, bills)

    # 9. DISPUTES (Use Case 9 & R7: Fraud Support & Human Oversight)
    disputes = [
        ("DISP-9001", "C1001", "TXN123456", "Customer did not recognize transaction at GLOBAL_GAMING_PORTAL_CY. Card security locked.", "UNDER_INVESTIGATION", 1, "Officer Neha Gupta (Fraud Risk Unit)", (today - timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S"), None, "Temporary transaction hold placed. Customer confirmed card remains in possession.")
    ]
    cursor.executemany("""
        INSERT INTO disputes (dispute_id, customer_id, transaction_id, reason, status, escalated_to_human, assigned_officer, created_at, resolved_at, investigation_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, disputes)

    # 10. PERSONALIZED OFFERS (Use Case 10 & R5: Personalized Banking)
    offers = [
        ("OFFER-PL-101", "C1001", "PRE_APPROVED_LOAN", "Pre-Approved Personal Loan", "Instant disbursal with zero documentation based on clean salary track record.", 500000.0, 10.49, (today + timedelta(days=30)).strftime("%Y-%m-%d"), 1, 0.98, "AVAILABLE"),
        ("OFFER-CC-102", "C1001", "CREDIT_CARD_UPGRADE", "Lifetime Free Metal Infi-Card", "Upgrade from Platinum Rewards with 5X reward points on travel and dining.", 350000.0, None, (today + timedelta(days=45)).strftime("%Y-%m-%d"), 1, 0.92, "AVAILABLE"),
        ("OFFER-FD-103", "C1001", "FD_SPECIAL_RATE", "High-Yield 444-Day Green Deposit", "Special deposit rate of 7.75% p.a. for premium banking customers.", 1000000.0, 7.75, (today + timedelta(days=15)).strftime("%Y-%m-%d"), 1, 0.88, "AVAILABLE"),
        ("OFFER-AUTO-201", "C1002", "PRE_APPROVED_LOAN", "Pre-Approved Two-Wheeler / EV Loan", "Attractive interest rate for green mobility vehicle upgrades.", 150000.0, 8.99, (today + timedelta(days=20)).strftime("%Y-%m-%d"), 1, 0.90, "AVAILABLE"),
        ("OFFER-HL-301", "C1003", "PRE_APPROVED_LOAN", "Pre-Approved Luxury Home Loan", "Pre-qualified for customized home loan sanction based on high consulting cash flows.", 7500000.0, 8.35, (today + timedelta(days=60)).strftime("%Y-%m-%d"), 1, 0.95, "AVAILABLE")
    ]
    cursor.executemany("""
        INSERT INTO personalized_offers (offer_id, customer_id, offer_type, title, description, max_amount, interest_rate, valid_until, eligibility_met, suitability_score, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, offers)

    # 11. AUDIT LOGS (R8: Trace ID, tools, queries)
    sample_audit = [
        ("BANK-50021", "C1001", today.strftime("%Y-%m-%d %H:%M:%S"), "Core Banking, Card Management", "get_balance, get_upcoming_payments", "BALANCE_INQUIRY", '{"customer_id": "C1001"}', "SUCCESS: Balance ₹1,25,000, obligations ₹35,000", 0, None)
    ]
    cursor.executemany("""
        INSERT INTO audit_logs (trace_id, customer_id, timestamp, systems_queried, tools_invoked, action_type, input_params, decision_outcome, human_escalation, error_details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_audit)

    conn.commit()
    conn.close()
    print("Sample banking data seeded successfully.")


if __name__ == "__main__":
    seed_sample_data()

