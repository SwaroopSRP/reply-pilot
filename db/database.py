"""SQLite database access layer for ReplyPilot.

Handles connections, table creation, and deterministic queries for customers,
orders, payments, conversations, and analysis history.
"""

import sqlite3
from typing import Any, Optional
from core.config import settings


def get_connection() -> sqlite3.Connection:
    """Create and return a SQLite connection configured with Row factory."""
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Initialize SQLite tables according to specification."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                plan TEXT NOT NULL,
                status TEXT NOT NULL,
                joined_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                product TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                order_id TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (order_id) REFERENCES orders(id)
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                intent TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                priority TEXT NOT NULL,
                summary TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                requires_human_review INTEGER NOT NULL,
                confidence REAL NOT NULL,
                draft_response TEXT NOT NULL,
                sources TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
            """
        )


def get_all_customers() -> list[dict[str, Any]]:
    """Retrieve all customers sorted by name."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM customers ORDER BY name ASC").fetchall()
        return [dict(r) for r in rows]


def get_customer(customer_id: str) -> Optional[dict[str, Any]]:
    """Look up a single customer by deterministic ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
        return dict(row) if row else None


def get_customer_orders(customer_id: str) -> list[dict[str, Any]]:
    """Fetch all orders for a customer sorted newest first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC",
            (customer_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_customer_payments(customer_id: str) -> list[dict[str, Any]]:
    """Fetch all payment records for a customer sorted newest first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM payments WHERE customer_id = ? ORDER BY created_at DESC",
            (customer_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def save_conversation(conversation_id: str, customer_id: str, message: str, created_at: str) -> None:
    """Save customer inquiry message."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversations (id, customer_id, message, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (conversation_id, customer_id, message, created_at),
        )


def save_analysis(
    analysis_id: str,
    conversation_id: str,
    intent: str,
    sentiment: str,
    priority: str,
    summary: str,
    recommended_action: str,
    requires_human_review: bool,
    confidence: float,
    draft_response: str,
    sources_json: str,
    created_at: str,
) -> None:
    """Persist structured analysis to SQLite."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO analyses (
                id, conversation_id, intent, sentiment, priority,
                summary, recommended_action, requires_human_review,
                confidence, draft_response, sources, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis_id,
                conversation_id,
                intent,
                sentiment,
                priority,
                summary,
                recommended_action,
                1 if requires_human_review else 0,
                confidence,
                draft_response,
                sources_json,
                created_at,
            ),
        )


def get_analyses_history(limit: int = 30) -> list[dict[str, Any]]:
    """Retrieve historical analyses joined with conversation and customer details."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT 
                a.id AS analysis_id,
                a.conversation_id,
                a.intent,
                a.sentiment,
                a.priority,
                a.summary,
                a.recommended_action,
                a.requires_human_review,
                a.confidence,
                a.draft_response,
                a.sources,
                a.created_at AS analysis_time,
                c.id AS customer_id,
                c.name AS customer_name,
                c.email AS customer_email,
                c.plan AS customer_plan,
                conv.message AS customer_message
            FROM analyses a
            JOIN conversations conv ON a.conversation_id = conv.id
            JOIN customers c ON conv.customer_id = c.id
            ORDER BY a.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_analysis_by_id(analysis_id: str) -> Optional[dict[str, Any]]:
    """Retrieve full analysis record by ID."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT 
                a.*,
                c.id AS customer_id,
                c.name AS customer_name,
                c.email AS customer_email,
                c.plan AS customer_plan,
                c.status AS customer_status,
                conv.message AS customer_message
            FROM analyses a
            JOIN conversations conv ON a.conversation_id = conv.id
            JOIN customers c ON conv.customer_id = c.id
            WHERE a.id = ?
            """,
            (analysis_id,),
        ).fetchone()
        return dict(row) if row else None
