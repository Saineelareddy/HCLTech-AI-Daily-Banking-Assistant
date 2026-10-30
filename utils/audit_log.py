"""
Auditability & Human Oversight Module (Requirements R7 & R8)
Records trace IDs, authorization context, systems queried, tools invoked, decisions, and outcomes.
Manages the human escalation queue for high-risk operations.
"""

import random
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from database.db import execute_query, fetch_all, fetch_one


def generate_trace_id() -> str:
    """
    Generates an enterprise-standard audit trace ID matching the format illustrated in the specification
    (e.g., 'BANK-50021' or 'BANK-202610-8492').
    """
    random_digits = random.randint(10000, 99999)
    return f"BANK-{random_digits}"


def log_audit_event(
    trace_id: str,
    customer_id: str,
    systems_queried: str,
    tools_invoked: str,
    action_type: str,
    input_params: Optional[Dict[str, Any]],
    decision_outcome: str,
    human_escalation: bool = False,
    error_details: Optional[str] = None
) -> Dict[str, Any]:
    """
    Persists an immutable audit log entry into the SQLite audit_logs table.
    Ensures complete compliance with Requirement R8 (Auditability).
    """
    query = """
        INSERT INTO audit_logs (
            trace_id, customer_id, systems_queried, tools_invoked,
            action_type, input_params, decision_outcome, human_escalation, error_details
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params_json = json.dumps(input_params or {}, default=str)
    execute_query(
        query,
        (
            trace_id,
            customer_id,
            systems_queried,
            tools_invoked,
            action_type,
            params_json,
            decision_outcome,
            1 if human_escalation else 0,
            error_details
        )
    )

    return {
        "trace_id": trace_id,
        "customer_id": customer_id,
        "timestamp": datetime.now().isoformat(),
        "systems_queried": systems_queried,
        "tools_invoked": tools_invoked,
        "action_type": action_type,
        "decision_outcome": decision_outcome,
        "human_escalation": human_escalation
    }


def get_audit_logs(customer_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves recent audit logs for compliance review or audit dashboard."""
    if customer_id:
        query = """
            SELECT log_id, trace_id, customer_id, timestamp, systems_queried,
                   tools_invoked, action_type, input_params, decision_outcome,
                   human_escalation, error_details
            FROM audit_logs
            WHERE customer_id = ?
            ORDER BY log_id DESC
            LIMIT ?
        """
        return fetch_all(query, (customer_id, limit))
    else:
        query = """
            SELECT log_id, trace_id, customer_id, timestamp, systems_queried,
                   tools_invoked, action_type, input_params, decision_outcome,
                   human_escalation, error_details
            FROM audit_logs
            ORDER BY log_id DESC
            LIMIT ?
        """
        return fetch_all(query, (limit,))


def get_escalated_cases() -> List[Dict[str, Any]]:
    """
    Retrieves all high-risk disputes or operations routed to human officers (Requirement R7).
    """
    query = """
        SELECT dispute_id, customer_id, transaction_id, reason, status,
               escalated_to_human, assigned_officer, created_at, investigation_notes
        FROM disputes
        ORDER BY created_at DESC
    """
    return fetch_all(query)


def update_escalated_case_status(
    dispute_id: str,
    status: str,
    assigned_officer: str,
    investigation_notes: str
) -> bool:
    """Updates the status and notes of a human oversight investigation ticket."""
    query = """
        UPDATE disputes
        SET status = ?, assigned_officer = ?, investigation_notes = ?, resolved_at = CURRENT_TIMESTAMP
        WHERE dispute_id = ?
    """
    rows = execute_query(query, (status, assigned_officer, investigation_notes, dispute_id))
    return rows > 0

