"""LangChain tools for deterministic customer data and semantic policy retrieval."""

from typing import Any
from langchain_core.tools import tool
from db.database import (
    get_customer as db_get_customer,
    get_customer_orders as db_get_customer_orders,
    get_customer_payments as db_get_customer_payments,
)


@tool
def get_customer(customer_id: str) -> dict[str, Any]:
    """Retrieve customer profile information by customer ID from the SQLite database.
    
    Args:
        customer_id: The unique customer identifier (e.g., 'CUST-001').
    """
    customer = db_get_customer(customer_id)
    if not customer:
        return {"error": f"Customer '{customer_id}' not found in database."}
    return customer


@tool
def get_customer_orders(customer_id: str) -> list[dict[str, Any]]:
    """Fetch all past and current orders for a given customer ID from the SQLite database.
    
    Args:
        customer_id: The unique customer identifier (e.g., 'CUST-001').
    """
    orders = db_get_customer_orders(customer_id)
    return orders


@tool
def get_recent_payments(customer_id: str) -> list[dict[str, Any]]:
    """Retrieve all payment transaction records for a given customer ID from the SQLite database.
    
    Args:
        customer_id: The unique customer identifier (e.g., 'CUST-001').
    """
    payments = db_get_customer_payments(customer_id)
    return payments


@tool
def search_company_policy(query: str) -> list[dict[str, Any]]:
    """Search company policy documentation in Chroma vector store using semantic similarity.
    
    Args:
        query: The search query describing the policy topic (e.g., 'duplicate charges refund', 'late shipping', 'cancellation').
    """
    # Lazy import to prevent circular dependency
    from ai.rag import query_knowledge_base
    return query_knowledge_base(query, top_k=3)
