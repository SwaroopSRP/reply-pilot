"""Seed database with realistic deterministic support data.

Populates customers, orders, and payments with deliberate scenarios:
1. Duplicate charge (Alex Johnson)
2. Refund within policy window (Sarah Miller)
3. Refund outside policy window (Marcus Vance)
4. Delayed physical shipment (Elena Rostova)
5. Cancellation inquiry (David Kim)
6. Product / upgrade question (Priya Patel)
7. Ambiguous / failed payment (Tom Henderson)
"""

from db.database import get_connection, init_db


CUSTOMERS = [
    {
        "id": "CUST-001",
        "name": "Alex Johnson",
        "email": "alex.johnson@example.com",
        "plan": "Pro",
        "status": "active",
        "joined_at": "2024-03-10 10:00:00",
    },
    {
        "id": "CUST-002",
        "name": "Sarah Miller",
        "email": "sarah.miller@example.com",
        "plan": "Pro",
        "status": "active",
        "joined_at": "2026-09-22 09:30:00",
    },
    {
        "id": "CUST-003",
        "name": "Marcus Vance",
        "email": "marcus.vance@example.com",
        "plan": "Pro",
        "status": "active",
        "joined_at": "2025-07-15 14:15:00",
    },
    {
        "id": "CUST-004",
        "name": "Elena Rostova",
        "email": "elena.rostova@enterprise-corp.com",
        "plan": "Enterprise",
        "status": "active",
        "joined_at": "2024-01-15 08:00:00",
    },
    {
        "id": "CUST-005",
        "name": "David Kim",
        "email": "david.kim@kimstudios.io",
        "plan": "Starter",
        "status": "active",
        "joined_at": "2025-11-01 12:45:00",
    },
    {
        "id": "CUST-006",
        "name": "Priya Patel",
        "email": "priya.patel@techfirm.co",
        "plan": "Starter",
        "status": "active",
        "joined_at": "2026-05-12 11:20:00",
    },
    {
        "id": "CUST-007",
        "name": "Tom Henderson",
        "email": "tom.h@freelancehub.net",
        "plan": "Pro",
        "status": "past_due",
        "joined_at": "2025-08-20 16:30:00",
    },
]

ORDERS = [
    # CUST-001: Alex Johnson (Duplicate charge scenario)
    {"id": "ORD-1001", "customer_id": "CUST-001", "product": "Pro Plan (Monthly)", "amount": 49.00, "status": "completed", "created_at": "2026-09-24 10:15:00"},
    {"id": "ORD-1002", "customer_id": "CUST-001", "product": "Pro Plan (Monthly)", "amount": 49.00, "status": "completed", "created_at": "2026-08-24 10:15:00"},

    # CUST-002: Sarah Miller (Refund within 14 days)
    {"id": "ORD-1003", "customer_id": "CUST-002", "product": "Pro Plan (Annual)", "amount": 490.00, "status": "completed", "created_at": "2026-09-23 14:20:00"},

    # CUST-003: Marcus Vance (Refund outside 14-day window - purchased > 30 days ago)
    {"id": "ORD-1004", "customer_id": "CUST-003", "product": "Pro Plan (Annual)", "amount": 490.00, "status": "completed", "created_at": "2026-08-10 09:00:00"},

    # CUST-004: Elena Rostova (Hardware delay)
    {"id": "ORD-1005", "customer_id": "CUST-004", "product": "Dedicated Security Key Hub (Express)", "amount": 149.00, "status": "shipped", "created_at": "2026-09-18 11:00:00"},
    {"id": "ORD-1006", "customer_id": "CUST-004", "product": "Enterprise Plan (Annual)", "amount": 1990.00, "status": "completed", "created_at": "2026-01-15 08:30:00"},

    # CUST-005: David Kim (Cancellation)
    {"id": "ORD-1007", "customer_id": "CUST-005", "product": "Starter Plan (Monthly)", "amount": 19.00, "status": "completed", "created_at": "2026-09-01 08:30:00"},
    {"id": "ORD-1008", "customer_id": "CUST-005", "product": "Starter Plan (Monthly)", "amount": 19.00, "status": "completed", "created_at": "2026-08-01 08:30:00"},

    # CUST-006: Priya Patel (Product inquiry)
    {"id": "ORD-1009", "customer_id": "CUST-006", "product": "Starter Plan (Monthly)", "amount": 19.00, "status": "completed", "created_at": "2026-09-12 16:45:00"},
    {"id": "ORD-1010", "customer_id": "CUST-006", "product": "Starter Plan (Monthly)", "amount": 19.00, "status": "completed", "created_at": "2026-08-12 16:45:00"},

    # CUST-007: Tom Henderson (Failed payment)
    {"id": "ORD-1011", "customer_id": "CUST-007", "product": "Pro Plan (Monthly)", "amount": 49.00, "status": "unpaid", "created_at": "2026-09-20 04:00:00"},
    {"id": "ORD-1012", "customer_id": "CUST-007", "product": "Pro Plan (Monthly)", "amount": 49.00, "status": "completed", "created_at": "2026-08-20 04:00:00"},
]

PAYMENTS = [
    # CUST-001 (Duplicate charge: PAY-2001 and PAY-2002 for ORD-1001)
    {"id": "PAY-2001", "customer_id": "CUST-001", "order_id": "ORD-1001", "amount": 49.00, "status": "successful", "created_at": "2026-09-24 10:15:02"},
    {"id": "PAY-2002", "customer_id": "CUST-001", "order_id": "ORD-1001", "amount": 49.00, "status": "successful", "created_at": "2026-09-24 10:15:05"},
    {"id": "PAY-2003", "customer_id": "CUST-001", "order_id": "ORD-1002", "amount": 49.00, "status": "successful", "created_at": "2026-08-24 10:15:02"},

    # CUST-002 (Sarah Miller - within 14 days)
    {"id": "PAY-2004", "customer_id": "CUST-002", "order_id": "ORD-1003", "amount": 490.00, "status": "successful", "created_at": "2026-09-23 14:20:05"},

    # CUST-003 (Marcus Vance - > 30 days ago)
    {"id": "PAY-2005", "customer_id": "CUST-003", "order_id": "ORD-1004", "amount": 490.00, "status": "successful", "created_at": "2026-08-10 09:00:05"},

    # CUST-004 (Elena Rostova - Hardware & Enterprise)
    {"id": "PAY-2006", "customer_id": "CUST-004", "order_id": "ORD-1005", "amount": 149.00, "status": "successful", "created_at": "2026-09-18 11:00:04"},
    {"id": "PAY-2007", "customer_id": "CUST-004", "order_id": "ORD-1006", "amount": 1990.00, "status": "successful", "created_at": "2026-01-15 08:30:05"},

    # CUST-005 (David Kim - Starter)
    {"id": "PAY-2008", "customer_id": "CUST-005", "order_id": "ORD-1007", "amount": 19.00, "status": "successful", "created_at": "2026-09-01 08:30:04"},
    {"id": "PAY-2009", "customer_id": "CUST-005", "order_id": "ORD-1008", "amount": 19.00, "status": "successful", "created_at": "2026-08-01 08:30:04"},

    # CUST-006 (Priya Patel - Starter)
    {"id": "PAY-2010", "customer_id": "CUST-006", "order_id": "ORD-1009", "amount": 19.00, "status": "successful", "created_at": "2026-09-12 16:45:04"},
    {"id": "PAY-2011", "customer_id": "CUST-006", "order_id": "ORD-1010", "amount": 19.00, "status": "successful", "created_at": "2026-08-12 16:45:04"},

    # CUST-007 (Tom Henderson - Failed attempts)
    {"id": "PAY-2012", "customer_id": "CUST-007", "order_id": "ORD-1011", "amount": 49.00, "status": "failed", "created_at": "2026-09-20 04:00:03"},
    {"id": "PAY-2013", "customer_id": "CUST-007", "order_id": "ORD-1011", "amount": 49.00, "status": "failed", "created_at": "2026-09-22 04:00:04"},
    {"id": "PAY-2014", "customer_id": "CUST-007", "order_id": "ORD-1011", "amount": 49.00, "status": "failed", "created_at": "2026-09-24 04:00:03"},
    {"id": "PAY-2015", "customer_id": "CUST-007", "order_id": "ORD-1012", "amount": 49.00, "status": "successful", "created_at": "2026-08-20 04:00:05"},
]


def seed_database(force: bool = False) -> None:
    """Seed SQLite database with initial records if empty or forced."""
    init_db()
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        if count > 0 and not force:
            return

        # Clear existing data if forced
        if force:
            conn.execute("DELETE FROM analyses")
            conn.execute("DELETE FROM conversations")
            conn.execute("DELETE FROM payments")
            conn.execute("DELETE FROM orders")
            conn.execute("DELETE FROM customers")

        # Insert customers
        conn.executemany(
            """
            INSERT OR REPLACE INTO customers (id, name, email, plan, status, joined_at)
            VALUES (:id, :name, :email, :plan, :status, :joined_at)
            """,
            CUSTOMERS,
        )

        # Insert orders
        conn.executemany(
            """
            INSERT OR REPLACE INTO orders (id, customer_id, product, amount, status, created_at)
            VALUES (:id, :customer_id, :product, :amount, :status, :created_at)
            """,
            ORDERS,
        )

        # Insert payments
        conn.executemany(
            """
            INSERT OR REPLACE INTO payments (id, customer_id, order_id, amount, status, created_at)
            VALUES (:id, :customer_id, :order_id, :amount, :status, :created_at)
            """,
            PAYMENTS,
        )


if __name__ == "__main__":
    seed_database(force=True)
    print("Database seeded successfully.")
