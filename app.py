"""
AI-Powered Daily Banking Assistant - Streamlit Application
HCLTech Future Ready AI Engineer Hackathon
Covers all 10 banking use cases and all 8 functional requirements.
"""

import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.db import init_db
from utils.authentication import authenticate_customer, get_customer_profile, list_demo_customers
from utils.audit_log import get_audit_logs, get_escalated_cases, update_escalated_case_status
from banking.account import get_account_balance, get_recent_transactions, get_account_summary
from banking.expenses import analyze_expenses, get_spending_trends
from banking.cards import get_credit_card_details, get_card_repayment_options, block_card, request_limit_change
from banking.payments import verify_upi_payment, get_upi_history, execute_simulated_payment
from banking.loans import get_loan_summary, get_next_emi, get_emi_schedule
from banking.reminders import get_upcoming_payments, get_payments_due_this_week, calculate_remaining_funds_after_bills
from banking.finance import analyze_personal_finance
from banking.fraud import fraud_verification, report_fraud_and_open_dispute, get_customer_disputes
from banking.offers import get_personalized_offers, check_loan_eligibility
from ai.assistant import DailyBankingAssistant

# Page Configuration
st.set_page_config(
    page_title="HCLTech AI Daily Banking Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Corporate Banking Look
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #0f2b48 0%, #1a5276 100%);
        color: white;
        padding: 1.2rem 1.8rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .status-badge-success {
        background-color: #d1fae5;
        color: #065f46;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-badge-failed {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-badge-warning {
        background-color: #fef3c7;
        color: #92400e;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .chat-bubble-user {
        background-color: #eff6ff;
        border-left: 4px solid #2563eb;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.6rem;
    }
    .chat-bubble-assistant {
        background-color: #f8fafc;
        border-left: 4px solid #0f766e;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.6rem;
    }
    .trace-pill {
        font-family: monospace;
        background: #e2e8f0;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        color: #334155;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Database
@st.cache_resource
def ensure_db_initialized():
    init_db(force_reseed=False)
    return True

ensure_db_initialized()


# Session State Management
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "customer" not in st.session_state:
    st.session_state.customer = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_context" not in st.session_state:
    st.session_state.session_context = {}
if "assistant" not in st.session_state:
    st.session_state.assistant = DailyBankingAssistant()


# -----------------------------------------------------------------------------
# SIDEBAR: Authentication, Demo Controls, and System Diagnostics
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bank-building.png", width=64)
    st.title("HCLTech Banking")
    st.caption("AI-Powered Daily Banking Assistant MVP")

    st.markdown("---")

    if not st.session_state.authenticated:
        st.subheader("Customer Login (R1)")
        demo_users = list_demo_customers()
        demo_map = {f"{u['customer_id']} - {u['name']}": u['customer_id'] for u in demo_users}
        
        selected_demo = st.selectbox(
            "Quick Demo Account Switcher:",
            options=list(demo_map.keys()),
            help="Pre-configured profiles for hackathon evaluation."
        )
        selected_cid = demo_map[selected_demo]

        # Preset PINs: C1001: 1234, C1002: 2345, C1003: 3456
        default_pin = "1234" if selected_cid == "C1001" else ("2345" if selected_cid == "C1002" else "3456")
        pin_input = st.text_input("4-Digit Security PIN", value=default_pin, type="password")

        if st.button("🔐 Sign In Securely", use_container_width=True, type="primary"):
            user = authenticate_customer(selected_cid, pin_input)
            if user:
                st.session_state.authenticated = True
                st.session_state.customer = user
                st.session_state.chat_history = []
                st.session_state.session_context = {}
                st.rerun()
            else:
                st.error("Invalid Customer ID or PIN.")

    else:
        cust = st.session_state.customer
        st.success(f"Signed in as **{cust['name']}**")
        st.caption(f"ID: `{cust['customer_id']}` | KYC: `{cust['kyc_status']}` | Risk: `{cust['risk_tier']}`")

        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.customer = None
            st.session_state.chat_history = []
            st.session_state.session_context = {}
            st.rerun()

    st.markdown("---")
    st.markdown("### 🤖 AI Engine Settings")
    current_key = os.getenv("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "Google Gemini API Key (Optional)",
        value=current_key,
        type="password",
        help="Paste a free Gemini API key to activate live LLM intent parsing and natural conversational phrasing. If left blank, the deterministic rule-based fallback handles all queries."
    )
    if api_key_input:
        st.session_state.assistant.set_api_key(api_key_input)
        st.success("✨ Live LLM Mode Active")
    else:
        st.session_state.assistant.set_api_key("")
        st.info("🛡️ Offline Rule-Based Mode Active")

    st.markdown("---")
    st.markdown("### ⚙️ System Status")
    st.info("🟢 **Mode:** Fictional Demo Mode\n\n🛡️ **Storage:** SQLite Database\n\n⚡ **Calculations:** Deterministic Engine")

    with st.expander("Database Maintenance"):
        if st.button("🔄 Reset Sample Database", use_container_width=True):
            init_db(force_reseed=True)
            st.success("Database restored to default hackathon dataset.")
            st.rerun()


# -----------------------------------------------------------------------------
# MAIN VIEW: Header & Tabs
# -----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h2 style="margin:0; padding:0; color:#ffffff;">AI-Powered Daily Banking Assistant</h2>
    <p style="margin:0.2rem 0 0 0; color:#cbd5e1; font-size:0.95rem;">
        Single conversational interface for everyday servicing, payments, cards, loans, spending insights, and fraud support.
    </p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.authenticated:
    st.warning("👈 Please sign in using the demo account switcher in the sidebar to access your accounts.")
    st.stop()

cust_id = st.session_state.customer["customer_id"]

# Navigation Tabs covering all use cases and requirements
tab_chat, tab_account, tab_expenses, tab_cards, tab_payments, tab_loans, tab_reminders, tab_fraud, tab_offers, tab_audit = st.tabs([
    "💬 AI Assistant",
    "🏦 Accounts & Balance",
    "📊 Expense Tracking",
    "💳 Cards & Services",
    "⚡ UPI & Payments",
    "🏠 Loans & EMIs",
    "⏰ Bill Reminders",
    "🛡️ Fraud Support",
    "🎁 Personalized Offers",
    "👔 Human Oversight & Audit"
])


# =============================================================================
# TAB 1: CONVERSATIONAL AI CHATBOT (Single Interface for Everyday Banking)
# =============================================================================
with tab_chat:
    st.markdown("### 💬 Conversational Banking Interface")
    st.caption("Ask questions in natural language. Powered by deterministic banking tools with complete audit traceability.")

    # Suggested Questions Pills
    st.markdown("**Suggested Questions for Demo:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("What is my current balance?", key="sq1", use_container_width=True):
            st.session_state.prompt_input = "What is my current balance?"
        if st.button("How much did I spend this month?", key="sq2", use_container_width=True):
            st.session_state.prompt_input = "How much did I spend this month?"
        if st.button("When is my credit card payment due?", key="sq3", use_container_width=True):
            st.session_state.prompt_input = "When is my credit card payment due?"
    with col2:
        if st.button("Did my UPI payment to Amazon go through?", key="sq4", use_container_width=True):
            st.session_state.prompt_input = "Did my UPI payment to Amazon go through?"
        if st.button("What is my next EMI amount?", key="sq5", use_container_width=True):
            st.session_state.prompt_input = "What is my next EMI amount?"
        if st.button("What payments are due this week?", key="sq6", use_container_width=True):
            st.session_state.prompt_input = "What payments are due this week?"
    with col3:
        if st.button("How much money do I have available after paying all upcoming bills?", key="sq7", use_container_width=True):
            st.session_state.prompt_input = "How much money do I have available after paying all upcoming bills?"
        if st.button("I lost my debit card", key="sq8", use_container_width=True):
            st.session_state.prompt_input = "I lost my debit card"
        if st.button("I do not recognize transaction TXN123456", key="sq9", use_container_width=True):
            st.session_state.prompt_input = "I do not recognize transaction TXN123456"

    st.markdown("---")

    # Chat History Display
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.info("👋 Hello! Ask me anything about your balances, upcoming EMIs, credit cards, UPI payments, or expense insights.")
        else:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-bubble-user">
                        <strong>You:</strong><br>{message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    trace_html = f"<span class='trace-pill'>Trace ID: {message.get('trace_id', 'N/A')}</span>"
                    type_html = f"<span class='trace-pill'>Type: {message.get('answer_type', 'retrieved')}</span>"
                    tools_html = f"<span class='trace-pill'>Tools: {', '.join(message.get('tools_invoked', [])) or 'direct'}</span>"

                    st.markdown(f"""
                    <div class="chat-bubble-assistant">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <strong>AI Banking Assistant:</strong>
                            <div>{trace_html} {type_html} {tools_html}</div>
                        </div>
                        {message['content']}
                    </div>
                    """, unsafe_allow_html=True)

    # Input Box
    default_text = st.session_state.pop("prompt_input", "")
    with st.form("chat_form", clear_on_submit=True):
        col_in, col_btn = st.columns([5, 1])
        with col_in:
            user_text = st.text_input("Type your banking query or confirmation here:", value=default_text, placeholder="e.g., How much money do I have available after paying all upcoming bills?")
        with col_btn:
            submit_btn = st.form_submit_button("Send ➔", use_container_width=True, type="primary")

    if submit_btn and user_text.strip():
        # Record user message
        st.session_state.chat_history.append({"role": "user", "content": user_text})

        # Process through AI Assistant orchestrator
        response = st.session_state.assistant.process_query(
            customer_id=cust_id,
            user_message=user_text,
            session_context=st.session_state.session_context
        )

        # Update context if sensitive confirmation was requested or completed
        if "set_pending_action" in response:
            st.session_state.session_context["pending_action"] = response["set_pending_action"]
        elif response.get("clear_pending_action"):
            st.session_state.session_context.pop("pending_action", None)

        # Record assistant reply
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response["answer"],
            "trace_id": response.get("trace_id"),
            "answer_type": response.get("answer_type"),
            "tools_invoked": response.get("tools_invoked")
        })
        st.rerun()

    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.session_state.session_context = {}
        st.rerun()


# =============================================================================
# TAB 2: ACCOUNTS & BALANCE (Use Case 1 & Requirement R2)
# =============================================================================
with tab_account:
    st.markdown("### 🏦 Account and Balance Inquiry (Use Case 1)")
    bal_data = get_account_balance(cust_id)
    summary_data = get_account_summary(cust_id)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Liquid Balance", f"₹{bal_data['total_balance']:,.2f}")
    with col2:
        st.metric("Active Accounts", len(bal_data.get("accounts", [])))
    with col3:
        st.metric("Primary Account Type", bal_data.get("primary_account_type", "N/A"))

    st.markdown("#### Your Authorized Accounts")
    if bal_data.get("accounts"):
        acc_df = pd.DataFrame(bal_data["accounts"])
        acc_df["balance"] = acc_df["balance"].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(
            acc_df[["account_number", "account_type", "balance", "branch", "ifsc_code", "status"]],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("#### Recent Credits & Debits")
    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown("**Recent Credits (Income / Transfers In)**")
        credits = summary_data.get("recent_credits", [])
        if credits:
            for c in credits:
                st.success(f"➕ ₹{c['amount']:,.2f} on {c['transaction_date']} | **{c['merchant']}** ({c['category']})")
        else:
            st.write("No recent credits.")

    with c_right:
        st.markdown("**Recent Debits (Outflows / Spends)**")
        debits = summary_data.get("recent_debits", [])
        if debits:
            for d in debits:
                st.error(f"➖ ₹{d['amount']:,.2f} on {d['transaction_date']} | **{d['merchant']}** ({d['category']})")
        else:
            st.write("No recent debits.")


# =============================================================================
# TAB 3: EXPENSE TRACKING & TRENDS (Use Case 2 & Requirement R3)
# =============================================================================
with tab_expenses:
    st.markdown("### 📊 Daily Expense Tracking & Spending Trends (Use Case 2)")
    exp_res = analyze_expenses(cust_id)
    trends_res = get_spending_trends(cust_id)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.metric("Current Month Spend", f"₹{exp_res['total_spent']:,.2f}")
        if exp_res.get("category_breakdown"):
            cat_df = pd.DataFrame(exp_res["category_breakdown"])
            fig_pie = px.pie(
                cat_df,
                names="category",
                values="amount",
                title="Expense Categorization (Current Month)",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expense categorization data available.")

    with col2:
        st.markdown("**Category Breakdown**")
        if exp_res.get("category_breakdown"):
            cat_df = pd.DataFrame(exp_res["category_breakdown"])
            cat_df["amount"] = cat_df["amount"].apply(lambda x: f"₹{x:,.2f}")
            cat_df["percentage"] = cat_df["percentage"].apply(lambda x: f"{x}%")
            st.dataframe(cat_df, use_container_width=True, hide_index=True)

        if trends_res.get("trends"):
            t_df = pd.DataFrame(trends_res["trends"])
            fig_bar = px.bar(
                t_df,
                x="month_period",
                y="monthly_total",
                title="Monthly Spending Trends",
                labels={"month_period": "Month", "monthly_total": "Total Spent (₹)"},
                color_discrete_sequence=["#1f77b4"]
            )
            st.plotly_chart(fig_bar, use_container_width=True)


# =============================================================================
# TAB 4: CARDS & SERVICES (Use Case 3 & 8, Requirement R4)
# =============================================================================
with tab_cards:
    st.markdown("### 💳 Credit Card Assistance & Card Services (Use Cases 3 & 8)")
    card_info = get_credit_card_details(cust_id)
    repay_info = get_card_repayment_options(cust_id)

    if card_info["status"] == "SUCCESS":
        for card in card_info["cards"]:
            status_style = "status-badge-success" if card["status"] == "ACTIVE" else "status-badge-failed"
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom: 1rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="margin:0;">{card['card_type']} ({card['card_network']})</h4>
                    <span class="{status_style}">{card['status']}</span>
                </div>
                <p style="font-family:monospace; font-size:1.1rem; margin:0.4rem 0;">{card['card_number_masked']}</p>
                <div style="display:flex; gap:2rem; margin-top:0.6rem;">
                    <div><strong>Credit Limit:</strong> ₹{card['credit_limit']:,.2f}</div>
                    <div><strong>Available:</strong> ₹{card['available_limit']:,.2f}</div>
                    <div><strong>Outstanding:</strong> <span style="color:#b91c1c;">₹{card['current_outstanding']:,.2f}</span></div>
                    <div><strong>Due Date:</strong> {card['due_date']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if card.get("replacement_requested"):
                st.warning(f"ℹ️ Replacement card request is currently in transit. Reference: `{card['replacement_reference']}`")

        st.markdown("#### Repayment Options")
        if repay_info.get("repayment_options"):
            r_cols = st.columns(len(repay_info["repayment_options"]))
            for i, opt in enumerate(repay_info["repayment_options"]):
                with r_cols[i]:
                    amt_str = f"₹{opt['amount']:,.2f}" if isinstance(opt['amount'], (int, float)) else str(opt['amount'])
                    st.metric(opt["option"], amt_str)
                    st.caption(opt["benefit"])

        st.markdown("---")
        st.markdown("#### Card Actions (Customer Authentication & Confirmation - R4)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Block Card / Lost Card Service**")
            block_reason = st.selectbox("Reason for blocking:", ["Lost Card", "Stolen Card", "Suspicious Activity", "Damaged Card"])
            req_rep = st.checkbox("Automatically request a replacement card", value=True)
            if st.button("🚫 Block Card Immediately", type="primary"):
                res = block_card(cust_id, reason=block_reason, request_replacement=req_rep)
                st.success(res["message"])
                st.rerun()

        with c2:
            st.markdown("**Request Credit Limit Change**")
            new_lim = st.number_input("Requested New Limit (₹):", min_value=50000.0, max_value=1000000.0, step=25000.0, value=250000.0)
            if st.button("📈 Submit Limit Request"):
                res = request_limit_change(cust_id, new_limit=new_lim)
                if res["status"] == "SUCCESS":
                    st.success(res["message"])
                    st.rerun()
                else:
                    st.error(res["message"])
    else:
        st.info("No credit cards on file for your profile.")


# =============================================================================
# TAB 5: UPI & PAYMENTS (Use Case 4)
# =============================================================================
with tab_payments:
    st.markdown("### ⚡ UPI & Payment Assistance (Use Case 4)")
    st.caption("Verify status, reference numbers (UTR), and failure causes for digital payments.")

    # Verification Tool
    st.markdown("#### Verify Transaction Status")
    col_q, col_qb = st.columns([4, 1])
    with col_q:
        q_term = st.text_input("Search UPI payment by Merchant Name or 12-digit UTR:", placeholder="e.g. Amazon, Flipkart, Swiggy, 429381029481")
    with col_qb:
        q_search = st.button("🔍 Verify Payment", use_container_width=True)

    if q_search and q_term.strip():
        v_res = verify_upi_payment(cust_id, query_term=q_term)
        if v_res["status"] == "SUCCESS":
            m = v_res["latest_match"]
            if v_res["is_success"]:
                st.success(f"✅ **Payment Successful** | ₹{m['amount']:,.2f} to **{m['recipient_name']}** | UTR: `{m['upi_ref_no']}` on {m['payment_date']}")
            else:
                st.error(f"❌ **Payment Failed** | ₹{m['amount']:,.2f} to **{m['recipient_name']}**\n\n• **Failure Reason:** {v_res['failure_explanation']}\n• **UTR Reference:** `{m['upi_ref_no']}`")
        else:
            st.warning(v_res["message"])

    st.markdown("---")
    st.markdown("#### Recent UPI Payment History")
    upi_hist = get_upi_history(cust_id)
    if upi_hist.get("payments"):
        u_df = pd.DataFrame(upi_hist["payments"])
        u_df["amount"] = u_df["amount"].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(
            u_df[["payment_date", "recipient_name", "amount", "status", "upi_ref_no", "failure_reason"]],
            use_container_width=True,
            hide_index=True
        )

    # Simulated payment tester
    with st.expander("💸 Make a Quick Test UPI Transfer (Simulated)"):
        with st.form("sim_pay_form"):
            p_to = st.text_input("Beneficiary Name", value="Swiggy Delivery")
            p_vpa = st.text_input("UPI VPA", value="swiggy@icici")
            p_amt = st.number_input("Amount (₹)", min_value=1.0, value=250.0, step=50.0)
            pay_sub = st.form_submit_button("Confirm & Pay")
            if pay_sub:
                p_res = execute_simulated_payment(cust_id, p_to, p_vpa, p_amt)
                if p_res["status"] == "SUCCESS":
                    st.success(p_res["message"])
                    st.rerun()
                else:
                    st.error(p_res["message"])


# =============================================================================
# TAB 6: LOANS & EMIS (Use Case 5)
# =============================================================================
with tab_loans:
    st.markdown("### 🏠 EMI & Loan Tracking (Use Case 5)")
    loan_sum = get_loan_summary(cust_id)
    next_emi_info = get_next_emi(cust_id)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Outstanding Loans", f"₹{loan_sum['total_outstanding']:,.2f}")
    with col2:
        st.metric("Monthly EMI Commitment", f"₹{loan_sum['total_monthly_emi']:,.2f}")
    with col3:
        if next_emi_info["status"] == "SUCCESS":
            st.metric("Immediate Next EMI", f"₹{next_emi_info['emi_amount']:,.2f}", f"Due: {next_emi_info['due_date']}")
        else:
            st.metric("Immediate Next EMI", "None")

    if loan_sum.get("loans"):
        st.markdown("#### Active Loan Accounts")
        l_df = pd.DataFrame(loan_sum["loans"])
        l_df["principal_amount"] = l_df["principal_amount"].apply(lambda x: f"₹{x:,.2f}")
        l_df["outstanding_balance"] = l_df["outstanding_balance"].apply(lambda x: f"₹{x:,.2f}")
        l_df["emi_amount"] = l_df["emi_amount"].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(
            l_df[["loan_id", "loan_type", "principal_amount", "outstanding_balance", "interest_rate", "emi_amount", "next_emi_date", "status"]],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("#### Amortized EMI Schedule")
        sched_res = get_emi_schedule(cust_id)
        if sched_res.get("schedules"):
            s_df = pd.DataFrame(sched_res["schedules"])
            s_df["emi_amount"] = s_df["emi_amount"].apply(lambda x: f"₹{x:,.2f}")
            s_df["principal_component"] = s_df["principal_component"].apply(lambda x: f"₹{x:,.2f}")
            s_df["interest_component"] = s_df["interest_component"].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(
                s_df[["emi_number", "due_date", "emi_amount", "principal_component", "interest_component", "status", "paid_date"]],
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("No active loans or credit facilities found on file.")


# =============================================================================
# TAB 7: BILL REMINDERS & REMAINING FUNDS (Use Case 7 & Section 7 Workflow)
# =============================================================================
with tab_reminders:
    st.markdown("### ⏰ Smart Bill Reminders & Funds Planning (Use Case 7)")
    st.caption("Aggregates upcoming card dues, EMIs, utility bills, and computes remaining disposable funds.")

    # PDF Page 4 & 5 Calculation
    st.markdown("#### 💡 Remaining Funds Calculator (PDF Example Workflow)")
    funds_res = calculate_remaining_funds_after_bills(cust_id)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Available Balance", f"₹{funds_res['available_balance']:,.2f}")
    with c2:
        st.metric("Upcoming Obligations", f"₹{funds_res['upcoming_obligations']:,.2f}")
    with c3:
        st.metric("Estimated Remaining Funds", f"₹{funds_res['estimated_remaining_funds']:,.2f}")

    st.success(f"**Assistant Calculation:** {funds_res['answer']} *(Trace ID: `{funds_res['trace_id']}`)*")

    st.markdown("---")
    st.markdown("#### Upcoming Obligations Breakdown")
    due_week_res = get_payments_due_this_week(cust_id)
    st.info(f"📅 **Due This Week (Next 7 Days):** {due_week_res['count']} payments totaling **₹{due_week_res['total_upcoming_amount']:,.2f}**")

    if funds_res.get("breakdown"):
        b_df = pd.DataFrame(funds_res["breakdown"])
        b_df["amount"] = b_df["amount"].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(
            b_df[["due_date", "title", "type", "amount", "is_autopay"]],
            use_container_width=True,
            hide_index=True
        )


# =============================================================================
# TAB 8: FRAUD SUPPORT & DISPUTES (Use Case 9 & Requirement R7)
# =============================================================================
with tab_fraud:
    st.markdown("### 🛡️ Fraud Support & Account Protection (Use Case 9 & R7)")
    st.caption("Inspect suspicious transactions, place temporary holds, and escalate disputes to human fraud officers.")

    st.markdown("#### Verify Transaction for Fraud Signals")
    col_f1, col_f2 = st.columns([4, 1])
    with col_f1:
        tx_check_id = st.text_input("Enter Transaction ID to inspect:", value="TXN123456")
    with col_f2:
        btn_fraud = st.button("🚨 Run Fraud Check", use_container_width=True)

    if btn_fraud and tx_check_id:
        f_res = fraud_verification(cust_id, tx_check_id)
        if f_res["status"] == "SUCCESS":
            risk = f_res["risk_level"]
            box_fn = st.error if risk == "HIGH" else (st.warning if risk == "MEDIUM" else st.success)
            box_fn(f"**Risk Level: {risk}**\n\n• Signals: {'; '.join(f_res['risk_signals'])}\n• Recommended Action: {f_res['recommended_action']}")

            st.markdown("#### Protection & Dispute Action")
            with st.form("dispute_form"):
                d_reason = st.text_input("Dispute Reason", value="Unrecognized international merchant charge.")
                lock_card_chk = st.checkbox("Temporarily lock payment card to prevent further charges", value=True)
                d_sub = st.form_submit_button("🛡️ Open Dispute & Escalate to Human Officer", type="primary")

                if d_sub:
                    disp_res = report_fraud_and_open_dispute(cust_id, tx_check_id, d_reason, lock_linked_card=lock_card_chk)
                    st.success(disp_res["message"])
                    st.rerun()
        else:
            st.warning(f_res["message"])

    st.markdown("---")
    st.markdown("#### Your Active & Historical Disputes")
    my_disputes = get_customer_disputes(cust_id)
    if my_disputes.get("disputes"):
        d_df = pd.DataFrame(my_disputes["disputes"])
        st.dataframe(
            d_df[["dispute_id", "transaction_id", "reason", "status", "assigned_officer", "created_at", "investigation_notes"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No disputes currently logged.")


# =============================================================================
# TAB 9: PERSONALIZED OFFERS & FINANCE (Use Cases 6 & 10, Requirement R5)
# =============================================================================
with tab_offers:
    st.markdown("### 🎁 Personalized Banking & Offers (Use Cases 6 & 10 & R5)")
    offers_res = get_personalized_offers(cust_id)
    elig_res = check_loan_eligibility(cust_id, "PERSONAL_LOAN")
    finance_res = analyze_personal_finance(cust_id)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### 🎯 Pre-Approved Banking Offers")
        if offers_res.get("offers"):
            for o in offers_res["offers"]:
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom: 0.8rem; border-left: 4px solid #10b981;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0;">{o['title']}</h4>
                        <span class="status-badge-success">{o['offer_type']}</span>
                    </div>
                    <p style="margin:0.4rem 0; color:#475569;">{o['description']}</p>
                    <div style="font-size:0.85rem; color:#64748b;">
                        Valid until: <strong>{o['valid_until']}</strong> | Suitability Score: <strong>{round(o['suitability_score']*100)}%</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No promotional offers available at this moment.")

    with col2:
        st.markdown("#### 📋 Deterministic Loan Eligibility Check")
        st.metric("Credit Bureau Score", f"{elig_res['credit_score']} / 900")
        st.metric("Maximum Pre-Approved Loan", f"₹{elig_res['max_eligible_loan_amount']:,.2f}")
        st.caption(f"Status: **{elig_res['decision']}** — {elig_res['reason']}")

        st.markdown("#### 💡 Personal Finance Guidance (Use Case 6)")
        st.metric("Projected Savings Rate", f"{finance_res['savings_rate_percentage']}%", f"₹{finance_res['projected_monthly_savings']:,.2f} / month")
        for obs in finance_res["observations"]:
            st.info(f"💡 {obs}")


# =============================================================================
# TAB 10: HUMAN OVERSIGHT & AUDIT TRAIL (Requirements R7 & R8)
# =============================================================================
with tab_audit:
    st.markdown("### 👔 Human Oversight & Auditability (Requirements R7 & R8)")
    st.caption("Enterprise audit trail recording Trace IDs, systems queried, tools invoked, and human escalation queues.")

    st.markdown("#### 🛡️ Escalation Queue for Authorized Bank Officers (Requirement R7)")
    escalated = get_escalated_cases()
    if escalated:
        st.warning(f"⚠️ There are **{len(escalated)}** case(s) requiring human oversight or fraud officer review.")
        for e in escalated:
            with st.expander(f"Dispute {e['dispute_id']} — Status: {e['status']} (Officer: {e.get('assigned_officer', 'Unassigned')})"):
                st.write(f"• **Customer ID:** {e['customer_id']}")
                st.write(f"• **Transaction:** {e['transaction_id']}")
                st.write(f"• **Reason:** {e['reason']}")
                st.write(f"• **Investigation Notes:** {e.get('investigation_notes')}")

                # Officer resolution form
                with st.form(f"resolve_form_{e['dispute_id']}"):
                    new_status = st.selectbox("Update Status:", ["UNDER_INVESTIGATION", "RESOLVED", "REJECTED"], index=0)
                    officer_name = st.text_input("Investigating Officer Name:", value=e.get("assigned_officer") or "Officer Neha Gupta")
                    notes = st.text_area("Investigation Notes:", value=e.get("investigation_notes") or "")
                    if st.form_submit_button("Update Ticket Status"):
                        update_escalated_case_status(e["dispute_id"], new_status, officer_name, notes)
                        st.success("Case updated successfully.")
                        st.rerun()
    else:
        st.success("All escalated cases have been reviewed.")

    st.markdown("---")
    st.markdown("#### 🔍 Real-Time Audit Log Viewer (Requirement R8)")
    audit_data = get_audit_logs(limit=50)
    if audit_data:
        a_df = pd.DataFrame(audit_data)
        st.dataframe(
            a_df[["trace_id", "timestamp", "customer_id", "systems_queried", "tools_invoked", "action_type", "decision_outcome", "human_escalation"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No audit logs recorded yet.")

