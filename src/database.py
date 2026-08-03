"""
Sprint 2 — SQLite schema and access layer.

Two tables, both designed now so they're ready before the app starts
writing to them for real (leads in Sprint 4, corrections in Sprint 4/5):

- leads: the live intake log for the Lead Priority Scorer. One row per
  inquiry, scored at intake time using the rule-based rubric in
  docs/lead_scoring_rubric.md.
- expense_corrections: an audit trail of every time a staff member
  overrides the expense classifier's predicted category. Doubles as the
  future training-data source if the classifier is ever retrained on
  corrected labels.

WAL mode is enabled on every connection — see docs/decision_log.md
("SQLite backup plan") for why: WAL lets backup_db.py copy the database
safely without blocking concurrent reads/writes from the app.

The database file itself (leads.db, per config.toml) is git-ignored and
only ever populated in BUSINESS_MODE — the public demo never touches it.
"""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("leads.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    lead_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    date_received       TEXT NOT NULL,
    source              TEXT NOT NULL,
    service_interest    TEXT,
    message_type        TEXT NOT NULL,
    discount_requested  INTEGER NOT NULL DEFAULT 0,  -- 0/1
    priority_score      INTEGER NOT NULL,
    priority_label       TEXT NOT NULL,
    contact_name        TEXT,
    contact_phone       TEXT,
    status              TEXT NOT NULL DEFAULT 'New',
    notes               TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS expense_corrections (
    correction_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id          INTEGER,          -- references cleaned_expenses.csv's expense_id
    vendor_name         TEXT,
    description         TEXT,
    amount              REAL,
    predicted_category  TEXT NOT NULL,
    corrected_category  TEXT NOT NULL,
    corrected_by        TEXT,
    corrected_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_date ON leads(date_received);
CREATE INDEX IF NOT EXISTS idx_corrections_expense_id ON expense_corrections(expense_id);
"""


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a connection with WAL mode enabled and dict-like row access."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Create both tables (and indexes) if they don't already exist. Safe
    to call every time the app starts."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

def insert_lead(
    conn: sqlite3.Connection,
    date_received: str,
    source: str,
    message_type: str,
    priority_score: int,
    priority_label: str,
    service_interest: str = None,
    discount_requested: bool = False,
    contact_name: str = None,
    contact_phone: str = None,
    status: str = "New",
    notes: str = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO leads (
            date_received, source, service_interest, message_type,
            discount_requested, priority_score, priority_label,
            contact_name, contact_phone, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            date_received,
            source,
            service_interest,
            message_type,
            int(discount_requested),
            priority_score,
            priority_label,
            contact_name,
            contact_phone,
            status,
            notes,
        ),
    )
    conn.commit()
    return cur.lastrowid


def list_leads(conn: sqlite3.Connection, status: str = None) -> list[dict]:
    if status:
        rows = conn.execute(
            "SELECT * FROM leads WHERE status = ? ORDER BY date_received DESC", (status,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM leads ORDER BY date_received DESC").fetchall()
    return [dict(r) for r in rows]


def update_lead_status(conn: sqlite3.Connection, lead_id: int, status: str) -> None:
    conn.execute(
        "UPDATE leads SET status = ?, updated_at = datetime('now') WHERE lead_id = ?",
        (status, lead_id),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Expense corrections
# ---------------------------------------------------------------------------

def insert_correction(
    conn: sqlite3.Connection,
    predicted_category: str,
    corrected_category: str,
    expense_id: int = None,
    vendor_name: str = None,
    description: str = None,
    amount: float = None,
    corrected_by: str = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO expense_corrections (
            expense_id, vendor_name, description, amount,
            predicted_category, corrected_category, corrected_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (expense_id, vendor_name, description, amount, predicted_category, corrected_category, corrected_by),
    )
    conn.commit()
    return cur.lastrowid


def list_corrections(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM expense_corrections ORDER BY corrected_at DESC").fetchall()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    print(f"Initialized {DEFAULT_DB_PATH.resolve()} with WAL mode and both tables.")
