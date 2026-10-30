"""
Database Manager for AI-Powered Daily Banking Assistant
Provides thread-safe connections, schema initialization, and parameterized queries.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "banking.db")
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with Row factory enabled for dictionary-like access."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(query: str, params: tuple = ()) -> int:
    """
    Executes an INSERT, UPDATE, or DELETE query using parameterized inputs to prevent SQL injection.
    Returns the number of affected rows.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def fetch_one(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """
    Executes a SELECT query and returns a single row as a standard Python dictionary.
    Returns None if no matching record is found.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """
    Executes a SELECT query and returns all matching rows as a list of Python dictionaries.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def init_db(force_reseed: bool = False) -> None:
    """
    Initializes the database schema and populates fictional sample data.
    If force_reseed is True, tables are dropped and re-created.
    """
    conn = get_connection()
    try:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    # Check if data already exists
    customer_count = fetch_one("SELECT COUNT(*) as cnt FROM customers")
    if force_reseed or not customer_count or customer_count["cnt"] == 0:
        # Import sample data loader
        from database.sample_data import seed_sample_data
        seed_sample_data()


if __name__ == "__main__":
    init_db(force_reseed=True)
    print("Database initialized successfully at:", DB_FILE)

