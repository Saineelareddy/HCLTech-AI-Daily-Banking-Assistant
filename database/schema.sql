-- HCLTech Future Ready AI Engineer Hackathon - Daily Banking Assistant
-- SQLite Schema Definition

-- 1. Customers Table (R1: Secure Authentication & Authorization)
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT NOT NULL,
    pin_hash TEXT NOT NULL,
    kyc_status TEXT DEFAULT 'VERIFIED',
    risk_tier TEXT DEFAULT 'LOW',
    monthly_income REAL DEFAULT 75000.0,
    credit_score INTEGER DEFAULT 760,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Accounts Table (Use Case 1: Account and Balance Inquiry, R2: Real-time Data)
CREATE TABLE IF NOT EXISTS accounts (
    account_number TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    account_type TEXT NOT NULL, -- 'SAVINGS', 'CURRENT', 'SALARY'
    balance REAL NOT NULL,
    currency TEXT DEFAULT 'INR',
    branch TEXT NOT NULL,
    ifsc_code TEXT NOT NULL,
    status TEXT DEFAULT 'ACTIVE', -- 'ACTIVE', 'FROZEN', 'DORMANT'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 3. Transactions Table (Use Case 1 & 2: Recent Credits/Debits, Daily Expense Tracking)
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    account_number TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    amount REAL NOT NULL,
    transaction_type TEXT NOT NULL, -- 'DEBIT', 'CREDIT'
    category TEXT NOT NULL, -- 'Food', 'Transport', 'Shopping', 'Bills', 'Salary', 'Entertainment', 'Healthcare', 'Investment'
    merchant TEXT NOT NULL,
    payment_method TEXT NOT NULL, -- 'UPI', 'DEBIT_CARD', 'CREDIT_CARD', 'NET_BANKING', 'NEFT'
    description TEXT,
    status TEXT DEFAULT 'SUCCESS', -- 'SUCCESS', 'PENDING', 'FAILED'
    is_suspicious INTEGER DEFAULT 0,
    FOREIGN KEY (account_number) REFERENCES accounts(account_number),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 4. Credit Cards Table (Use Case 3 & 8: Statement, Due Date, Repayment, Card Services)
CREATE TABLE IF NOT EXISTS credit_cards (
    card_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    card_number_masked TEXT NOT NULL,
    card_network TEXT NOT NULL, -- 'VISA', 'MASTERCARD', 'RUPAY'
    card_type TEXT DEFAULT 'Platinum Rewards',
    credit_limit REAL NOT NULL,
    available_limit REAL NOT NULL,
    current_outstanding REAL NOT NULL,
    minimum_due REAL NOT NULL,
    statement_date DATE NOT NULL,
    due_date DATE NOT NULL,
    status TEXT DEFAULT 'ACTIVE', -- 'ACTIVE', 'BLOCKED', 'TEMPORARILY_LOCKED', 'REPLACED'
    replacement_requested INTEGER DEFAULT 0,
    replacement_reference TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 5. UPI Payments Table (Use Case 4: UPI and Payment Assistance)
CREATE TABLE IF NOT EXISTS upi_payments (
    upi_txn_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    account_number TEXT NOT NULL,
    upi_ref_no TEXT UNIQUE NOT NULL, -- 12-digit UTR
    recipient_vpa TEXT NOT NULL,
    recipient_name TEXT NOT NULL,
    amount REAL NOT NULL,
    payment_date TIMESTAMP NOT NULL,
    status TEXT NOT NULL, -- 'SUCCESS', 'FAILED', 'PENDING'
    failure_reason TEXT, -- e.g., 'Bank server timeout', 'Insufficient balance', 'Bank decline'
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (account_number) REFERENCES accounts(account_number)
);

-- 6. Loans Table (Use Case 5: EMI and Loan Tracking)
CREATE TABLE IF NOT EXISTS loans (
    loan_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    loan_type TEXT NOT NULL, -- 'HOME_LOAN', 'PERSONAL_LOAN', 'AUTO_LOAN', 'EDUCATION_LOAN'
    principal_amount REAL NOT NULL,
    outstanding_balance REAL NOT NULL,
    interest_rate REAL NOT NULL,
    tenure_months INTEGER NOT NULL,
    emi_amount REAL NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    next_emi_date DATE NOT NULL,
    status TEXT DEFAULT 'ACTIVE', -- 'ACTIVE', 'CLOSED', 'DEFAULTED'
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 7. EMI Schedules Table (Use Case 5: Detailed EMI Schedule Breakdown)
CREATE TABLE IF NOT EXISTS emi_schedules (
    schedule_id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    emi_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    emi_amount REAL NOT NULL,
    principal_component REAL NOT NULL,
    interest_component REAL NOT NULL,
    status TEXT DEFAULT 'UPCOMING', -- 'PAID', 'UPCOMING', 'OVERDUE'
    paid_date DATE,
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 8. Bills & Subscriptions Table (Use Case 7: Smart Bill Reminder)
CREATE TABLE IF NOT EXISTS bills_subscriptions (
    bill_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    biller_name TEXT NOT NULL,
    biller_category TEXT NOT NULL, -- 'Utility - Electricity', 'Broadband', 'Mobile Postpaid', 'OTT Subscription', 'Insurance'
    amount REAL NOT NULL,
    due_date DATE NOT NULL,
    auto_pay INTEGER DEFAULT 0,
    status TEXT DEFAULT 'UNPAID', -- 'PAID', 'UNPAID', 'SCHEDULED'
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 9. Disputes & Fraud Reports Table (Use Case 9 & R7: Fraud Support & Human Oversight)
CREATE TABLE IF NOT EXISTS disputes (
    dispute_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    transaction_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT DEFAULT 'UNDER_INVESTIGATION', -- 'OPEN', 'UNDER_INVESTIGATION', 'RESOLVED', 'REJECTED'
    escalated_to_human INTEGER DEFAULT 1,
    assigned_officer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    investigation_notes TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 10. Personalized Offers Table (Use Case 10 & R5: Personalized Banking)
CREATE TABLE IF NOT EXISTS personalized_offers (
    offer_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    offer_type TEXT NOT NULL, -- 'PRE_APPROVED_LOAN', 'CREDIT_CARD_UPGRADE', 'FD_SPECIAL_RATE', 'CASHBACK_OFFER', 'SIP_BOOST'
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    max_amount REAL,
    interest_rate REAL,
    valid_until DATE NOT NULL,
    eligibility_met INTEGER DEFAULT 1,
    suitability_score REAL DEFAULT 0.95,
    status TEXT DEFAULT 'AVAILABLE', -- 'AVAILABLE', 'ACCEPTED', 'EXPIRED'
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 11. Audit Logs Table (R8: Auditability & Traceability)
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    systems_queried TEXT NOT NULL,
    tools_invoked TEXT NOT NULL,
    action_type TEXT NOT NULL,
    input_params TEXT,
    decision_outcome TEXT NOT NULL,
    human_escalation INTEGER DEFAULT 0,
    error_details TEXT
);

