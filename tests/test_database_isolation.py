
import os
from pathlib import Path

from database.db import (
    BASE_DIR,
    DB_PATH,
    get_connection,
)


def test_database_isolation():
    """Verify pytest uses a separate SQLite database."""

    production_db = (
        BASE_DIR / "data" / "support_tickets.db"
    ).resolve()

    test_db = DB_PATH.resolve()

    print("\n========== DATABASE ISOLATION TEST ==========")
    print("Production database:", production_db)
    print("Test database:", test_db)

    # Verify environment configuration.
    assert "SUPPORT_DB_PATH" in os.environ

    assert test_db == Path(
        os.environ["SUPPORT_DB_PATH"]
    ).resolve()

    # Ensure the production database is not selected.
    assert test_db != production_db

    # Confirm the test database was initialized.
    with get_connection() as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

    assert {
        "tickets",
        "ticket_audit_logs",
        "delivery_history",
    }.issubset(tables)

    print("PASS: Temporary database configured")
    print("PASS: Production database path excluded")
    print("PASS: All required tables initialized")
    print("PASS: Database isolation verified")
