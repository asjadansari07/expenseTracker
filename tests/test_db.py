"""Tests for the helpers in ``database/db.py``.

Every test runs against a temporary database supplied by the ``isolated_db``
fixture in ``conftest.py``; nothing here touches the real
``expense_tracker.db``.
"""

import sqlite3

import pytest
from werkzeug.security import check_password_hash

import database.db as db_module


# ------------------------------------------------------------------ #
# Query helpers                                                       #
# ------------------------------------------------------------------ #

def _table_names(db_path):
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    finally:
        conn.close()
    return {row[0] for row in rows}


def _count_rows(db_path, query):
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute(query).fetchone()[0]
    finally:
        conn.close()


def _count_users(db_path):
    return _count_rows(db_path, "SELECT COUNT(*) FROM users")


def _count_expenses(db_path):
    return _count_rows(db_path, "SELECT COUNT(*) FROM expenses")


# ------------------------------------------------------------------ #
# init_db                                                             #
# ------------------------------------------------------------------ #

def test_init_db_creates_users_table(isolated_db):
    assert "users" in _table_names(isolated_db)


def test_init_db_creates_expenses_table(isolated_db):
    assert "expenses" in _table_names(isolated_db)


def test_init_db_is_idempotent(isolated_db):
    db_module.init_db()
    db_module.init_db()

    count = _count_rows(
        isolated_db,
        "SELECT COUNT(*) FROM sqlite_master "
        "WHERE type = 'table' AND name = 'users'",
    )

    assert count == 1


# ------------------------------------------------------------------ #
# create_user                                                         #
# ------------------------------------------------------------------ #

def test_create_user_returns_new_row_id(isolated_db):
    user_id = db_module.create_user(
        "Alice", "alice@example.com", "password123"
    )

    assert isinstance(user_id, int)
    assert user_id > 0


def test_create_user_hashes_password(isolated_db):
    user_id = db_module.create_user(
        "Alice", "alice@example.com", "password123"
    )
    row = db_module.get_user_by_id(user_id)

    assert row["password_hash"] != "password123"
    assert check_password_hash(row["password_hash"], "password123")


def test_create_user_lowercases_email(isolated_db):
    user_id = db_module.create_user(
        "Alice", "Alice@Example.COM", "password123"
    )

    assert db_module.get_user_by_id(user_id)["email"] == "alice@example.com"


def test_create_user_strips_surrounding_whitespace(isolated_db):
    user_id = db_module.create_user(
        "  Alice  ", "  alice@example.com  ", "password123"
    )
    row = db_module.get_user_by_id(user_id)

    assert row["name"] == "Alice"
    assert row["email"] == "alice@example.com"


def test_create_user_defaults_created_at_to_a_timestamp(isolated_db):
    user_id = db_module.create_user(
        "Alice", "alice@example.com", "password123"
    )
    row = db_module.get_user_by_id(user_id)

    # SQLite's datetime('now') yields 'YYYY-MM-DD HH:MM:SS' (19 chars).
    assert row["created_at"] is not None
    assert len(row["created_at"]) == 19


def test_create_user_returns_none_for_duplicate_email(isolated_db):
    db_module.create_user("Alice", "alice@example.com", "password123")

    result = db_module.create_user(
        "Alice Again", "alice@example.com", "other-pass"
    )

    assert result is None


@pytest.mark.parametrize(
    "duplicate_email",
    ["alice@example.com", "ALICE@EXAMPLE.COM", "  Alice@Example.com  "],
)
def test_create_user_duplicate_check_ignores_email_casing(
    isolated_db, duplicate_email
):
    db_module.create_user("Alice", "alice@example.com", "password123")

    result = db_module.create_user(
        "Alice Again", duplicate_email, "password123"
    )

    assert result is None


def test_create_user_duplicate_email_does_not_insert_second_row(isolated_db):
    db_module.create_user("Alice", "alice@example.com", "password123")
    db_module.create_user("Alice Again", "alice@example.com", "password123")

    assert _count_users(isolated_db) == 1


# ------------------------------------------------------------------ #
# get_user_by_email                                                   #
# ------------------------------------------------------------------ #

def test_get_user_by_email_returns_matching_row(user):
    row = db_module.get_user_by_email("test@example.com")

    assert row["id"] == user["id"]
    assert row["name"] == "Test User"


@pytest.mark.parametrize(
    "email",
    ["test@example.com", "TEST@EXAMPLE.COM", "  Test@Example.com  "],
)
def test_get_user_by_email_normalises_input(isolated_db, email):
    db_module.create_user("Test User", "test@example.com", "password123")

    assert db_module.get_user_by_email(email) is not None


def test_get_user_by_email_returns_none_for_unknown_email(isolated_db):
    assert db_module.get_user_by_email("nobody@example.com") is None


def test_get_user_by_email_returns_row_as_is_including_password_hash(user):
    row = db_module.get_user_by_email("test@example.com")

    assert row["password_hash"] is not None


# ------------------------------------------------------------------ #
# get_user_by_id                                                      #
# ------------------------------------------------------------------ #

def test_get_user_by_id_returns_matching_row(user):
    row = db_module.get_user_by_id(user["id"])

    assert row["email"] == "test@example.com"


def test_get_user_by_id_returns_none_for_unknown_id(isolated_db):
    assert db_module.get_user_by_id(999999) is None


def test_get_user_by_id_returns_row_as_is_including_password_hash(user):
    row = db_module.get_user_by_id(user["id"])

    assert row["password_hash"] is not None


# ------------------------------------------------------------------ #
# seed_db                                                             #
# ------------------------------------------------------------------ #

def test_seed_db_inserts_demo_user(isolated_db):
    db_module.seed_db()
    row = db_module.get_user_by_email("demo@spendly.com")

    assert row is not None
    assert row["name"] == "Demo User"


def test_seed_db_hashes_the_demo_password(isolated_db):
    db_module.seed_db()
    row = db_module.get_user_by_email("demo@spendly.com")

    assert row["password_hash"] != "demo123"
    assert check_password_hash(row["password_hash"], "demo123")


def test_seed_db_inserts_eight_expenses(isolated_db):
    db_module.seed_db()

    assert _count_expenses(isolated_db) == 8


def test_seed_db_covers_all_seven_categories(isolated_db):
    db_module.seed_db()
    conn = sqlite3.connect(str(isolated_db))
    try:
        categories = {
            row[0]
            for row in conn.execute("SELECT DISTINCT category FROM expenses")
        }
    finally:
        conn.close()

    assert categories == {
        "Food",
        "Transport",
        "Bills",
        "Health",
        "Entertainment",
        "Shopping",
        "Other",
    }


def test_seed_db_pins_sample_dates(isolated_db):
    db_module.seed_db()
    conn = sqlite3.connect(str(isolated_db))
    try:
        dates = [
            row[0]
            for row in conn.execute("SELECT date FROM expenses ORDER BY date")
        ]
    finally:
        conn.close()

    assert dates[0] == "2026-09-07"
    assert dates[-1] == "2026-09-17"


def test_seed_db_is_idempotent(isolated_db):
    db_module.seed_db()
    db_module.seed_db()

    assert _count_users(isolated_db) == 1
    assert _count_expenses(isolated_db) == 8


def test_seed_db_skips_insert_when_a_user_already_exists(isolated_db):
    db_module.create_user("Existing", "existing@example.com", "password123")

    db_module.seed_db()

    assert db_module.get_user_by_email("demo@spendly.com") is None
    assert _count_expenses(isolated_db) == 0
