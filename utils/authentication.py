"""
Authentication & Authorization Module (Requirement R1)
Validates customer identity and enforces customer-specific data isolation.
"""

import hashlib
from typing import Optional, Dict, Any, List
from database.db import fetch_one, fetch_all


def hash_pin(pin: str) -> str:
    """Computes SHA-256 hash of a 4-digit PIN."""
    return hashlib.sha256(pin.strip().encode("utf-8")).hexdigest()


def authenticate_customer(customer_id: str, pin: str) -> Optional[Dict[str, Any]]:
    """
    Validates customer credentials against the database.
    Returns the customer record (excluding pin_hash) if valid, otherwise None.
    Enforces Requirement R1: Secure Authentication.
    """
    if not customer_id or not pin:
        return None

    clean_cid = customer_id.strip().upper()
    pin_hash_val = hash_pin(pin)

    query = """
        SELECT customer_id, name, email, phone, kyc_status, risk_tier, monthly_income, credit_score, created_at
        FROM customers
        WHERE customer_id = ? AND pin_hash = ?
    """
    customer = fetch_one(query, (clean_cid, pin_hash_val))
    return customer


def get_customer_profile(customer_id: str) -> Optional[Dict[str, Any]]:
    """Fetches non-sensitive customer profile information for authorized sessions."""
    query = """
        SELECT customer_id, name, email, phone, kyc_status, risk_tier, monthly_income, credit_score, created_at
        FROM customers
        WHERE customer_id = ?
    """
    return fetch_one(query, (customer_id.strip().upper(),))


def list_demo_customers() -> List[Dict[str, Any]]:
    """Lists available demo customers for rapid hackathon review and testing."""
    query = """
        SELECT customer_id, name, email, phone, risk_tier
        FROM customers
        ORDER BY customer_id ASC
    """
    return fetch_all(query)

