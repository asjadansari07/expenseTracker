"""Shared fixtures for the Spendly test suite.

Database isolation
------------------
``database/db.py`` resolves its SQLite path from ``__file__``
(``Path(__file__).parent.parent / "expense_tracker.db"``) and exposes no
environment variable or config hook to redirect it. Importing ``app`` also
runs ``init_db()`` and ``seed_db()`` at module level, so importing the
application touches the real ``expense_tracker.db`` once, at collection time.
That is the application's own behaviour and cannot be avoided without editing
application code.

Per-test isolation is achieved by monkeypatching ``database.db.get_db``. Every
helper in ``database/db.py`` (``init_db``, ``seed_db``, ``create_user``,
``get_user_by_email``, ``get_user_by_id``) resolves ``get_db`` from that
module's globals at call time, so one patch covers all of them -- including
the helper objects that ``app.py`` imported into its own namespace. The
``isolated_db`` fixture is autouse, so no test in this suite can write to the
developer's real database.
"""

import sys
from pathlib import Path

# Make the project root importable regardless of how pytest is invoked, so
# `import app` and `import database.db` resolve without a pytest.ini.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import sqlite3

import pytest

import database.db as db_module
from app import app as flask_app

DEFAULT_PASSWORD = "password123"


@pytest.fixture
def app():
    """The Spendly application object (there is no factory)."""
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def db_path(tmp_path):
    """Path to a throwaway SQLite file for a single test."""
    return tmp_path / "test_expense_tracker.db"


@pytest.fixture(autouse=True)
def isolated_db(db_path, monkeypatch):
    """Redirect every ``database.db`` helper at a per-test temporary database."""
    def _get_db():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    monkeypatch.setattr(db_module, "get_db", _get_db)
    db_module.init_db()
    return db_path


@pytest.fixture
def client(app):
    """A Flask test client wired to the isolated database.

    Overrides pytest-flask's ``client`` so every client-using test is
    automatically isolated.
    """
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def make_user(isolated_db):
    """Factory that inserts a user through the app's own helper."""
    def _make_user(
        name="Test User",
        email="test@example.com",
        password=DEFAULT_PASSWORD,
    ):
        return db_module.create_user(name, email, password)

    return _make_user


@pytest.fixture
def user(make_user):
    """A persisted user plus its known plaintext credentials."""
    user_id = make_user()
    return {
        "id": user_id,
        "name": "Test User",
        "email": "test@example.com",
        "password": DEFAULT_PASSWORD,
    }


@pytest.fixture
def sign_in():
    """Populate the session the way ``login`` does."""
    def _sign_in(client, user_id, user_name="Test User"):
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["user_name"] = user_name

    return _sign_in


@pytest.fixture
def read_session():
    """Return the current session contents as a plain dict."""
    def _read_session(client):
        with client.session_transaction() as sess:
            return dict(sess)

    return _read_session
