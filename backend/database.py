import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "expenses.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrent read performance
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id            TEXT PRIMARY KEY,
                idempotency_key TEXT UNIQUE,          -- prevents duplicate POSTs on retry
                amount        INTEGER NOT NULL,        -- stored in paise (1 INR = 100 paise) to avoid float errors
                category      TEXT NOT NULL,
                description   TEXT NOT NULL,
                date          TEXT NOT NULL,           -- ISO-8601 date string YYYY-MM-DD
                created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date DESC)
        """)