
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_DB_PATH = BASE_DIR / "data" / "support_tickets.db"

DB_PATH = Path(
    os.environ.get(
        "SUPPORT_DB_PATH",
        str(DEFAULT_DB_PATH)
    )
).resolve()



def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DB_PATH,
        timeout=30
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():
    """
    Create persistent support ticket and audit tables.
    """

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT UNIQUE,
                original_complaint TEXT NOT NULL,
                category TEXT NOT NULL,
                urgency TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                language TEXT NOT NULL,
                summary TEXT NOT NULL,
                escalation_signals TEXT NOT NULL DEFAULT '[]',
                evidence_found INTEGER NOT NULL DEFAULT 0,
                policy_sources TEXT NOT NULL DEFAULT '[]',
                proposed_response TEXT NOT NULL,
                escalation_decision TEXT NOT NULL DEFAULT 'Pending',
                escalation_reason TEXT,
                ticket_status TEXT NOT NULL DEFAULT 'Pending',
                review_status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS ticket_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL,
                action TEXT NOT NULL,
                previous_value TEXT,
                new_value TEXT,
                performed_by TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id)
                    REFERENCES tickets(ticket_id)
            )
        """)
        
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS delivery_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                delivery_id TEXT NOT NULL UNIQUE,
                ticket_id TEXT NOT NULL,
                delivery_mode TEXT NOT NULL,
                delivery_status TEXT NOT NULL,
                channel TEXT NOT NULL,
                response TEXT NOT NULL,
                delivered_at TEXT NOT NULL,
                actual_message_sent INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
            )
            """
        )


    print("SQLite database initialized successfully.")
    print(f"Database location: {DB_PATH}")


if __name__ == "__main__":
    initialize_database()
