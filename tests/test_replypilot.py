"""Unit tests for ReplyPilot core functionality:
- SQLite customer and payment lookups
- Semantic RAG retrieval
- Pydantic structured output validation
- Edge case handling (empty message validation)
"""

import pytest
from pydantic import ValidationError

from core.schemas import SupportAnalysis
from db.database import (
    init_db,
    get_customer,
    get_customer_orders,
    get_customer_payments,
)
from db.seed import seed_database
from ai.rag import query_knowledge_base
from ai.chains import run_support_analysis


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Ensure database is initialized and seeded before tests run."""
    init_db()
    seed_database(force=True)


def test_customer_lookup_success():
    """Verify deterministic customer retrieval by ID."""
    cust = get_customer("CUST-001")
    assert cust is not None
    assert cust["name"] == "Alex Johnson"
    assert cust["plan"] == "Pro"
    assert cust["status"] == "active"


def test_customer_lookup_nonexistent():
    """Verify None is returned when customer ID is invalid."""
    cust = get_customer("CUST-999")
    assert cust is None


def test_payment_lookup_duplicate_scenario():
    """Verify Alex Johnson has duplicate payments for the same order."""
    payments = get_customer_payments("CUST-001")
    assert len(payments) >= 2
    
    # Check duplicate charges for ORD-1001
    ord_1001_payments = [p for p in payments if p["order_id"] == "ORD-1001"]
    assert len(ord_1001_payments) == 2
    assert ord_1001_payments[0]["amount"] == 49.00
    assert ord_1001_payments[1]["amount"] == 49.00


def test_rag_semantic_retrieval():
    """Verify RAG correctly retrieves relevant sections for duplicate billing."""
    results = query_knowledge_base("duplicate charges refund policy", top_k=2)
    assert len(results) > 0
    top_result = results[0]
    assert "Duplicate Charges" in top_result["section"] or "Billing Policy" in top_result["source"]
    assert 0.0 <= top_result["similarity"] <= 1.0


def test_rag_refund_policy_retrieval():
    """Verify RAG retrieves 14-day refund policy for refund queries."""
    results = query_knowledge_base("14 days money back guarantee refund", top_k=2)
    assert len(results) > 0
    sources_text = " ".join([r["section"] for r in results])
    assert "Refund" in sources_text or "14-Day" in sources_text


def test_structured_output_validation():
    """Verify SupportAnalysis Pydantic schema enforces types and confidence bounds."""
    valid_data = {
        "intent": "Duplicate Charge",
        "sentiment": "Frustrated",
        "priority": "high",
        "summary": "Customer charged twice for Pro plan.",
        "recommended_action": "Verify records and refund $49.00 duplicate.",
        "requires_human_review": True,
        "confidence": 0.95,
        "sources": ["Billing Policy > Duplicate Charges"],
        "draft_response": "Hi Alex, we will refund your duplicate charge.",
    }
    analysis = SupportAnalysis(**valid_data)
    assert analysis.priority == "high"
    assert analysis.confidence == 0.95

    # Test invalid confidence bounds (> 1.0) raises ValidationError
    invalid_data = dict(valid_data, confidence=1.5)
    with pytest.raises(ValidationError):
        SupportAnalysis(**invalid_data)

    invalid_negative = dict(valid_data, confidence=-0.2)
    with pytest.raises(ValidationError):
        SupportAnalysis(**invalid_negative)


def test_empty_message_validation():
    """Verify empty customer message raises ValueError."""
    with pytest.raises(ValueError, match="Customer message cannot be empty"):
        run_support_analysis(customer_id="CUST-001", customer_message="   ")


def test_end_to_end_analysis_duplicate_scenario():
    """Verify full analysis workflow correctly identifies duplicate charge."""
    analysis, chunks, customer = run_support_analysis(
        customer_id="CUST-001",
        customer_message="I was charged twice for my Pro subscription. Can you refund the extra charge?",
    )
    assert analysis.intent == "Duplicate Charge"
    assert analysis.priority == "high"
    assert analysis.requires_human_review is True
    assert "refund" in analysis.recommended_action.lower()
    assert customer["name"] == "Alex Johnson"
