import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta


def get_db():
    """Returns a SQLite connection with row_factory and foreign keys enabled."""
    db_path = Path(__file__).parent.parent / "expense_tracker.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Creates all tables using CREATE TABLE IF NOT EXISTS."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def seed_db():
    """Inserts sample data for development. Prevents duplicate inserts."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count > 0:
        conn.close()
        return

    # Insert demo user
    password_hash = generate_password_hash("demo123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash)
    )
    demo_user_id = cursor.lastrowid

    # Generate dates for current month (September 2026)
    today = datetime(2026, 9, 17)

    # Insert 8 sample expenses across 7 categories (INR amounts)
    expenses = [
        (demo_user_id, 350.50, "Food", (today - timedelta(days=10)).strftime("%Y-%m-%d"), "Grocery shopping"),
        (demo_user_id, 80.00, "Transport", (today - timedelta(days=9)).strftime("%Y-%m-%d"), "Bus fare"),
        (demo_user_id, 1200.00, "Bills", (today - timedelta(days=7)).strftime("%Y-%m-%d"), "Electricity bill"),
        (demo_user_id, 500.00, "Health", (today - timedelta(days=5)).strftime("%Y-%m-%d"), "Pharmacy"),
        (demo_user_id, 250.00, "Entertainment", (today - timedelta(days=3)).strftime("%Y-%m-%d"), "Movie tickets"),
        (demo_user_id, 899.00, "Shopping", (today - timedelta(days=2)).strftime("%Y-%m-%d"), "Clothing"),
        (demo_user_id, 150.00, "Other", (today - timedelta(days=1)).strftime("%Y-%m-%d"), "Miscellaneous"),
        (demo_user_id, 425.75, "Food", today.strftime("%Y-%m-%d"), "Restaurant dinner"),
    ]

    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses
    )

    conn.commit()
    conn.close()


def create_user(name, email, password):
    """Creates a user with a hashed password.

    Returns the new row id, or None if the email is already taken.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name.strip(), email.strip().lower(), generate_password_hash(password))
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()
