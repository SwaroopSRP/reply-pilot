"""Data models and type definitions for SQLite records."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Customer:
    """Customer entity representing account profile."""
    id: str
    name: str
    email: str
    plan: str
    status: str
    joined_at: str


@dataclass
class Order:
    """Order entity representing product purchase."""
    id: str
    customer_id: str
    product: str
    amount: float
    status: str
    created_at: str


@dataclass
class Payment:
    """Payment transaction record."""
    id: str
    customer_id: str
    order_id: str
    amount: float
    status: str
    created_at: str


@dataclass
class Conversation:
    """Inbound customer support ticket/inquiry."""
    id: str
    customer_id: str
    message: str
    created_at: str


@dataclass
class Analysis:
    """Grounded AI copilot analysis record."""
    id: str
    conversation_id: str
    intent: str
    sentiment: str
    priority: str
    summary: str
    recommended_action: str
    requires_human_review: bool
    confidence: float
    draft_response: str
    sources: str
    created_at: str
