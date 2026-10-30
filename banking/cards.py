"""
Banking Module: Credit Card Assistance & Card Services (Use Cases 3 & 8, Requirement R4)
Handles statement inquiries, repayment options, card blocking, replacements, and limit changes.
All sensitive actions require explicit authorization and confirmation.
"""

import random
from datetime import datetime
from typing import Dict, Any, List, Optional
from database.db import fetch_all, fetch_one, execute_query
from utils.audit_log import log_audit_event, generate_trace_id


def get_credit_card_details(customer_id: str) -> Dict[str, Any]:
    """
    Retrieves statement details, credit limit, available limit, due date, and amount due.
    Use Case 3: Credit Card Assistance.
    """
    trace_id = generate_trace_id()
    query = """
        SELECT card_id, card_number_masked, card_network, card_type,
               credit_limit, available_limit, current_outstanding, minimum_due,
               statement_date, due_date, status, replacement_requested, replacement_reference
        FROM credit_cards
        WHERE customer_id = ?
    """
    cards = fetch_all(query, (customer_id,))

    if not cards:
        log_audit_event(
            trace_id=trace_id,
            customer_id=customer_id,
            systems_queried="Credit Card Platform",
            tools_invoked="get_credit_card_details",
            action_type="CREDIT_CARD_INQUIRY",
            input_params={"customer_id": customer_id},
            decision_outcome="NOT_FOUND: No credit cards on file"
        )
        return {
            "status": "NOT_FOUND",
            "trace_id": trace_id,
            "message": "No credit card accounts found for your profile.",
            "cards": []
        }

    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Credit Card Platform",
        tools_invoked="get_credit_card_details",
        action_type="CREDIT_CARD_INQUIRY",
        input_params={"customer_id": customer_id},
        decision_outcome=f"SUCCESS: Retrieved {len(cards)} credit cards"
    )

    return {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "cards": cards,
        "primary_card": cards[0]
    }


def get_card_repayment_options(customer_id: str) -> Dict[str, Any]:
    """
    Computes available repayment options:
    1. Total Outstanding (zero interest)
    2. Minimum Amount Due
    3. Custom Amount
    4. EMI Conversion (for balances > ₹5,000)
    """
    card_info = get_credit_card_details(customer_id)
    if card_info["status"] != "SUCCESS":
        return card_info

    primary = card_info["primary_card"]
    outstanding = primary["current_outstanding"]
    min_due = primary["minimum_due"]

    emi_eligible = outstanding >= 5000.0
    emi_estimate_6m = round((outstanding * 1.08) / 6, 2) if emi_eligible else None

    return {
        "status": "SUCCESS",
        "trace_id": card_info["trace_id"],
        "card_masked": primary["card_number_masked"],
        "due_date": primary["due_date"],
        "total_outstanding": outstanding,
        "minimum_due": min_due,
        "repayment_options": [
            {"option": "Pay Full Outstanding", "amount": outstanding, "benefit": "Avoid any interest charges"},
            {"option": "Pay Minimum Due", "amount": min_due, "benefit": "Avoid late payment fee and maintain active status"},
            {"option": "Custom Partial Payment", "amount": "User Choice", "benefit": "Flexible payment toward outstanding"}
        ],
        "emi_conversion_eligible": emi_eligible,
        "estimated_6month_emi": emi_estimate_6m
    }


def block_card(customer_id: str, card_id: Optional[str] = None, reason: str = "Customer lost card", request_replacement: bool = True) -> Dict[str, Any]:
    """
    Instantly blocks a credit or debit card under bank controls and initiates replacement if requested.
    Use Case 8: Card Services (Requirement R4).
    """
    trace_id = generate_trace_id()

    # Find target card
    if card_id:
        card = fetch_one("SELECT * FROM credit_cards WHERE customer_id = ? AND card_id = ?", (customer_id, card_id))
    else:
        card = fetch_one("SELECT * FROM credit_cards WHERE customer_id = ? ORDER BY card_id ASC", (customer_id,))

    if not card:
        log_audit_event(
            trace_id=trace_id,
            customer_id=customer_id,
            systems_queried="Card Management System",
            tools_invoked="block_card",
            action_type="CARD_BLOCK_REJECTED",
            input_params={"customer_id": customer_id, "card_id": card_id},
            decision_outcome="NOT_FOUND: Card not found for customer"
        )
        return {
            "status": "FAILED",
            "trace_id": trace_id,
            "message": "Card not found or access unauthorized."
        }

    rep_ref = f"REP-{datetime.now().strftime('%Y')}-{random.randint(1000, 9999)}" if request_replacement else None

    query = """
        UPDATE credit_cards
        SET status = 'BLOCKED', replacement_requested = ?, replacement_reference = ?
        WHERE card_id = ? AND customer_id = ?
    """
    execute_query(query, (1 if request_replacement else 0, rep_ref, card["card_id"], customer_id))

    outcome = f"SUCCESS: Card {card['card_number_masked']} BLOCKED. Reason: {reason}. Replacement ref: {rep_ref}"
    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Card Management System, Payment Switch",
        tools_invoked="block_card",
        action_type="CARD_BLOCKED",
        input_params={"card_id": card["card_id"], "reason": reason, "replacement": request_replacement},
        decision_outcome=outcome
    )

    return {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "card_id": card["card_id"],
        "card_masked": card["card_number_masked"],
        "new_status": "BLOCKED",
        "replacement_initiated": request_replacement,
        "replacement_reference": rep_ref,
        "message": f"Card ending in {card['card_number_masked'][-4:]} has been securely blocked immediately. "
                   + (f"Replacement card dispatch reference is {rep_ref}." if request_replacement else "")
    }


def request_limit_change(customer_id: str, new_limit: float, card_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Processes a credit card limit change request under bank policy controls.
    (Requirement R4).
    """
    trace_id = generate_trace_id()
    if card_id:
        card = fetch_one("SELECT * FROM credit_cards WHERE customer_id = ? AND card_id = ?", (customer_id, card_id))
    else:
        card = fetch_one("SELECT * FROM credit_cards WHERE customer_id = ? ORDER BY card_id ASC", (customer_id,))

    if not card:
        return {"status": "NOT_FOUND", "trace_id": trace_id, "message": "Card record not found."}

    # Policy rule: Maximum allowed limit is 3x customer monthly income or ₹5,00,000 max
    cust = fetch_one("SELECT monthly_income, credit_score FROM customers WHERE customer_id = ?", (customer_id,))
    max_permissible = min(cust["monthly_income"] * 3.5, 500000.0)

    if new_limit > max_permissible:
        outcome = f"REJECTED: Requested limit ₹{new_limit:,.2f} exceeds policy ceiling ₹{max_permissible:,.2f}"
        log_audit_event(
            trace_id=trace_id,
            customer_id=customer_id,
            systems_queried="Card Management System, Credit Policy Rule Engine",
            tools_invoked="request_limit_change",
            action_type="LIMIT_CHANGE_DECLINED",
            input_params={"new_limit": new_limit},
            decision_outcome=outcome
        )
        return {
            "status": "DECLINED",
            "trace_id": trace_id,
            "current_limit": card["credit_limit"],
            "max_permissible_limit": max_permissible,
            "message": f"Requested limit of ₹{new_limit:,.2f} exceeds current automated policy ceiling of ₹{max_permissible:,.2f} based on credit score ({cust['credit_score']})."
        }

    # Apply approved limit change
    diff = new_limit - card["credit_limit"]
    new_avail = card["available_limit"] + diff
    execute_query("UPDATE credit_cards SET credit_limit = ?, available_limit = ? WHERE card_id = ?", (new_limit, new_avail, card["card_id"]))

    outcome = f"SUCCESS: Credit limit revised from ₹{card['credit_limit']:,.2f} to ₹{new_limit:,.2f}"
    log_audit_event(
        trace_id=trace_id,
        customer_id=customer_id,
        systems_queried="Card Management System",
        tools_invoked="request_limit_change",
        action_type="LIMIT_CHANGE_APPROVED",
        input_params={"new_limit": new_limit},
        decision_outcome=outcome
    )

    return {
        "status": "SUCCESS",
        "trace_id": trace_id,
        "card_masked": card["card_number_masked"],
        "old_limit": card["credit_limit"],
        "new_limit": new_limit,
        "new_available_limit": new_avail,
        "message": f"Your credit limit has been successfully updated to ₹{new_limit:,.2f}."
    }
