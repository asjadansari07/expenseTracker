"""Tests for ``app.py``: routes, the ``login_required`` guard, the template
filters, and the registration validator.

All tests run against the temporary database wired up by ``conftest.py``.
"""

import sqlite3

import pytest
from flask import get_flashed_messages, session

import app as app_module
import database.db as db_module

NAME_ERROR = "Please enter your name."
EMAIL_ERROR = "Please enter a valid email address."
PASSWORD_ERROR = "Password must be at least 8 characters."
GENERIC_LOGIN_ERROR = "Invalid email or password."
DUPLICATE_EMAIL_ERROR = "An account with that email already exists."
SIGN_IN_PROMPT = "Please sign in to view your profile."

VALID_REGISTRATION = {
    "name": "Alice",
    "email": "alice@example.com",
    "password": "password123",
}


def _login_data(email, password):
    return {"email": email, "password": password}


def _count_users():
    """Number of rows in the isolated ``users`` table for the current test."""
    conn = db_module.get_db()
    try:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        conn.close()


# ------------------------------------------------------------------ #
# Template filters                                                    #
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("filter_name", ["date_display", "date_short", "inr"])
def test_template_filter_is_registered(filter_name):
    assert filter_name in app_module.app.jinja_env.filters


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-09-17 14:30:00", "17 September 2026"),
        ("2026-09-07 00:00:00", "7 September 2026"),
        ("2026-09-07 10:30:00", "7 September 2026"),
        ("2026-12-25 23:59:59", "25 December 2026"),
        ("2026-01-31 08:05:00", "31 January 2026"),
        ("2026-02-28 12:00:00", "28 February 2026"),
        ("2026-10-05 09:15:00", "5 October 2026"),
    ],
)
def test_date_display_formats_timestamp(value, expected):
    assert app_module.date_display(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        0,
        123,
        "not a date",
        "2026-09-17",
        "17/09/2026",
        "2026-09-17 14:30",
        "2026-13-01 00:00:00",
        "2026-02-30 00:00:00",
    ],
)
def test_date_display_falls_back_to_placeholder(value):
    assert app_module.date_display(value) == "—"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-09-07", "7 Sep 2026"),
        ("2026-09-17", "17 Sep 2026"),
        ("2026-12-25", "25 Dec 2026"),
        ("2026-01-31", "31 Jan 2026"),
        ("2026-02-28", "28 Feb 2026"),
        ("2026-10-05", "5 Oct 2026"),
    ],
)
def test_date_short_formats_date(value, expected):
    assert app_module.date_short(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        0,
        20260917,
        "not a date",
        "2026-09-17 12:00:00",
        "2026-13-01",
        "2026-02-30",
        "17/09/2026",
    ],
)
def test_date_short_falls_back_to_placeholder(value):
    assert app_module.date_short(value) == "—"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1200.0, "₹1,200.00"),
        (1200, "₹1,200.00"),
        ("1200.5", "₹1,200.50"),
        (350.5, "₹350.50"),
        (425.75, "₹425.75"),
        (0, "₹0.00"),
        ("0", "₹0.00"),
        (1234567.89, "₹1,234,567.89"),
        (-350.5, "-₹350.50"),
        (-1200, "-₹1,200.00"),
    ],
)
def test_inr_formats_amount(value, expected):
    assert app_module.inr(value) == expected


@pytest.mark.parametrize("value", [None, "", "abc", "12,00"])
def test_inr_falls_back_to_placeholder(value):
    assert app_module.inr(value) == "—"


# ------------------------------------------------------------------ #
# login_required                                                      #
# ------------------------------------------------------------------ #

def test_login_required_redirects_signed_out_visitor_to_login(app):
    @app_module.login_required
    def view():
        return "secret"

    with app.test_request_context():
        response = view()

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_login_required_flashes_prompt_for_signed_out_visitor(app):
    @app_module.login_required
    def view():
        return "secret"

    with app.test_request_context():
        view()
        messages = get_flashed_messages(with_categories=True)

    assert ("error", SIGN_IN_PROMPT) in messages


def test_login_required_lets_signed_in_visitor_reach_the_view(app):
    @app_module.login_required
    def view():
        return "secret"

    with app.test_request_context():
        session["user_id"] = 1
        result = view()

    assert result == "secret"


def test_login_required_preserves_wrapped_view_name(app):
    @app_module.login_required
    def my_view():
        return "ok"

    assert my_view.__name__ == "my_view"


# ------------------------------------------------------------------ #
# _validate_registration                                              #
# ------------------------------------------------------------------ #

@pytest.mark.parametrize(
    ("name", "email", "password", "expected"),
    [
        ("Alice", "alice@example.com", "password123", None),
        ("Alice", "alice@example.com", "12345678", None),
        ("", "alice@example.com", "password123", NAME_ERROR),
        ("Alice", "", "password123", EMAIL_ERROR),
        ("Alice", "aliceexample.com", "password123", EMAIL_ERROR),
        ("Alice", "alice.example.com", "password123", EMAIL_ERROR),
        ("Alice", "alice@example", "password123", EMAIL_ERROR),
        ("Alice", "alice@", "password123", EMAIL_ERROR),
        ("Alice", "user@localhost", "password123", EMAIL_ERROR),
        ("Alice", "@example.com", "password123", EMAIL_ERROR),
        ("Alice", "alice@.com", "password123", EMAIL_ERROR),
        ("Alice", "alice@example.", "password123", EMAIL_ERROR),
        ("Alice", "ali@ce@example.com", "password123", EMAIL_ERROR),
        ("Alice", "a@b@c.com", "password123", EMAIL_ERROR),
        ("Alice", "alice@example.com", "1234567", PASSWORD_ERROR),
        ("Alice", "alice@mail.example.co.in", "password123", None),
    ],
)
def test_validate_registration_returns_expected_message(
    name, email, password, expected
):
    assert app_module._validate_registration(name, email, password) == expected


def test_validate_registration_whitespace_only_name_is_valid_for_a_stripped_caller():
    # The helper documents that it expects name to already be stripped; the
    # route strips it before calling, so this is the documented contract
    # rather than a user-facing hole (see test_register_rejects_invalid_input).
    result = app_module._validate_registration(
        "   ", "alice@example.com", "password123"
    )

    assert result is None


# ------------------------------------------------------------------ #
# Landing, legal pages                                                #
# ------------------------------------------------------------------ #

def test_landing_page_renders(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Track every rupee." in response.get_data(as_text=True)


def test_terms_and_conditions_page_renders(client):
    response = client.get("/terms-and-conditions")

    assert response.status_code == 200
    assert "Terms & Conditions" in response.get_data(as_text=True)


def test_privacy_policy_page_renders(client):
    response = client.get("/privacy-policy")

    assert response.status_code == 200
    assert "Privacy Policy" in response.get_data(as_text=True)


# ------------------------------------------------------------------ #
# /register                                                           #
# ------------------------------------------------------------------ #

def test_register_page_renders(client):
    response = client.get("/register")

    assert response.status_code == 200
    assert "Create your account" in response.get_data(as_text=True)


def test_register_with_valid_details_redirects_to_login(client):
    response = client.post("/register", data=VALID_REGISTRATION)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_register_with_valid_details_creates_the_user(client):
    client.post("/register", data=VALID_REGISTRATION)

    row = db_module.get_user_by_email("alice@example.com")
    assert row is not None
    assert row["name"] == "Alice"


def test_register_flashes_a_success_message(client):
    response = client.post(
        "/register", data=VALID_REGISTRATION, follow_redirects=True
    )

    assert "Account created successfully." in response.get_data(as_text=True)


def test_register_accepts_password_of_exactly_eight_characters(client):
    response = client.post(
        "/register", data={**VALID_REGISTRATION, "password": "12345678"}
    )

    assert response.status_code == 302


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({**VALID_REGISTRATION, "name": "   "}, NAME_ERROR),
        ({**VALID_REGISTRATION, "email": ""}, EMAIL_ERROR),
        ({**VALID_REGISTRATION, "email": "aliceexample.com"}, EMAIL_ERROR),
        ({**VALID_REGISTRATION, "email": "alice@example"}, EMAIL_ERROR),
        ({**VALID_REGISTRATION, "email": "alice@.com"}, EMAIL_ERROR),
        ({**VALID_REGISTRATION, "email": "alice@example."}, EMAIL_ERROR),
        ({**VALID_REGISTRATION, "email": "ali@ce@example.com"}, EMAIL_ERROR),
        ({**VALID_REGISTRATION, "password": "short"}, PASSWORD_ERROR),
    ],
)
def test_register_rejects_invalid_input(client, data, message):
    response = client.post("/register", data=data)

    assert response.status_code == 400
    assert message in response.get_data(as_text=True)


def test_register_invalid_input_does_not_create_user(client):
    client.post("/register", data={**VALID_REGISTRATION, "password": "short"})

    assert db_module.get_user_by_email("alice@example.com") is None


def test_register_duplicate_email_returns_an_error(client, make_user):
    make_user(name="Alice", email="alice@example.com")

    response = client.post("/register", data=VALID_REGISTRATION)

    assert response.status_code == 400
    assert DUPLICATE_EMAIL_ERROR in response.get_data(as_text=True)


@pytest.mark.parametrize(
    "email", ["ALICE@EXAMPLE.COM", "  Alice@Example.com  "]
)
def test_register_duplicate_email_check_ignores_casing(
    client, make_user, email
):
    make_user(name="Alice", email="alice@example.com")

    response = client.post(
        "/register", data={**VALID_REGISTRATION, "email": email}
    )

    assert response.status_code == 400
    assert DUPLICATE_EMAIL_ERROR in response.get_data(as_text=True)


def test_register_invalid_input_echoes_back_supplied_values(client):
    response = client.post(
        "/register", data={**VALID_REGISTRATION, "password": "short"}
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 400
    assert f'value="{VALID_REGISTRATION["name"]}"' in html
    assert f'value="{VALID_REGISTRATION["email"]}"' in html


def test_register_duplicate_email_echoes_back_supplied_values(
    client, make_user
):
    make_user(name="Alice", email="alice@example.com")

    response = client.post("/register", data=VALID_REGISTRATION)
    html = response.get_data(as_text=True)

    assert response.status_code == 400
    assert f'value="{VALID_REGISTRATION["name"]}"' in html
    assert f'value="{VALID_REGISTRATION["email"]}"' in html


def test_register_invalid_input_leaves_users_table_empty(client):
    client.post("/register", data={**VALID_REGISTRATION, "password": "short"})

    assert _count_users() == 0


def test_register_duplicate_email_does_not_insert_second_row(
    client, make_user
):
    make_user(name="Alice", email="alice@example.com")

    client.post("/register", data=VALID_REGISTRATION)

    assert _count_users() == 1


def test_register_success_does_not_sign_the_user_in(client, read_session):
    client.post("/register", data=VALID_REGISTRATION)

    assert "user_id" not in read_session(client)


# ------------------------------------------------------------------ #
# /login                                                              #
# ------------------------------------------------------------------ #

def test_login_page_renders(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert "Welcome back" in response.get_data(as_text=True)


def test_login_redirects_an_already_signed_in_visitor(client, user, sign_in):
    sign_in(client, user["id"], user["name"])

    response = client.get("/login")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


@pytest.mark.parametrize(
    "data",
    [
        {"email": "", "password": ""},
        {"email": "alice@example.com", "password": ""},
        {"email": "", "password": "password123"},
    ],
)
def test_login_rejects_missing_fields(client, data):
    response = client.post("/login", data=data)

    assert response.status_code == 400
    assert GENERIC_LOGIN_ERROR in response.get_data(as_text=True)


def test_login_rejects_unknown_email(client):
    response = client.post(
        "/login", data=_login_data("nobody@example.com", "password123")
    )

    assert response.status_code == 400
    assert GENERIC_LOGIN_ERROR in response.get_data(as_text=True)


def test_login_rejects_wrong_password(client, user):
    response = client.post(
        "/login", data=_login_data(user["email"], "wrong-password")
    )

    assert response.status_code == 400
    assert GENERIC_LOGIN_ERROR in response.get_data(as_text=True)


def test_login_with_valid_credentials_redirects_to_profile(client, user):
    response = client.post(
        "/login", data=_login_data(user["email"], user["password"])
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/profile"


def test_login_with_valid_credentials_sets_the_session(
    client, user, read_session
):
    client.post(
        "/login", data=_login_data(user["email"], user["password"])
    )

    sess = read_session(client)
    assert sess["user_id"] == user["id"]
    assert sess["user_name"] == user["name"]


def test_login_email_is_case_insensitive(client, user):
    response = client.post(
        "/login", data=_login_data("TEST@EXAMPLE.COM", user["password"])
    )

    assert response.status_code == 302


def test_login_clears_pre_existing_session_keys(client, user, read_session):
    with client.session_transaction() as sess:
        sess["leftover"] = "value"

    client.post(
        "/login", data=_login_data(user["email"], user["password"])
    )

    assert "leftover" not in read_session(client)


def test_login_response_does_not_expose_password_hash(client, user):
    response = client.post(
        "/login",
        data=_login_data(user["email"], user["password"]),
        follow_redirects=True,
    )
    html = response.get_data(as_text=True)
    stored_hash = db_module.get_user_by_id(user["id"])["password_hash"]

    assert stored_hash not in html
    assert "password_hash" not in html


def test_login_wrong_password_echoes_back_email(client, user):
    response = client.post(
        "/login", data=_login_data(user["email"], "wrong-password")
    )

    assert response.status_code == 400
    assert f'value="{user["email"]}"' in response.get_data(as_text=True)


def test_login_unknown_email_echoes_back_email(client):
    response = client.post(
        "/login", data=_login_data("nobody@example.com", "password123")
    )

    assert response.status_code == 400
    assert 'value="nobody@example.com"' in response.get_data(as_text=True)


def test_login_failure_does_not_set_a_session(client, user, read_session):
    client.post("/login", data=_login_data(user["email"], "wrong-password"))

    assert "user_id" not in read_session(client)


# ------------------------------------------------------------------ #
# /logout                                                             #
# ------------------------------------------------------------------ #

def test_logout_redirects_to_login(client, user, sign_in):
    sign_in(client, user["id"], user["name"])

    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_logout_clears_the_session(client, user, sign_in, read_session):
    sign_in(client, user["id"], user["name"])

    client.get("/logout")

    assert "user_id" not in read_session(client)


def test_logout_flashes_a_signed_out_message(client, user, sign_in):
    sign_in(client, user["id"], user["name"])

    response = client.get("/logout", follow_redirects=True)

    assert "You have been signed out." in response.get_data(as_text=True)


def test_logout_without_a_session_redirects_to_login(client):
    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_logout_without_a_session_leaves_session_empty(client, read_session):
    client.get("/logout")

    assert "user_id" not in read_session(client)


# ------------------------------------------------------------------ #
# /profile                                                            #
# ------------------------------------------------------------------ #

def test_profile_redirects_signed_out_visitor_to_login(client):
    response = client.get("/profile")

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_profile_flashes_prompt_for_signed_out_visitor(client):
    response = client.get("/profile", follow_redirects=True)

    assert SIGN_IN_PROMPT in response.get_data(as_text=True)


def test_profile_renders_for_signed_in_visitor(client, user, sign_in):
    sign_in(client, user["id"], user["name"])

    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert user["name"] in html
    assert user["email"] in html


def test_profile_does_not_expose_password_hash(client, user, sign_in):
    sign_in(client, user["id"], user["name"])

    html = client.get("/profile").get_data(as_text=True)
    stored_hash = db_module.get_user_by_id(user["id"])["password_hash"]

    assert stored_hash not in html
    assert "password_hash" not in html


def test_profile_renders_placeholder_expenses(client, user, sign_in):
    sign_in(client, user["id"], user["name"])

    html = client.get("/profile").get_data(as_text=True)

    assert "Grocery shopping" in html
    assert "Restaurant dinner" in html
    assert "Food" in html
    assert "Transport" in html


def test_profile_renders_placeholder_expense_total_as_inr(
    client, user, sign_in
):
    sign_in(client, user["id"], user["name"])

    html = client.get("/profile").get_data(as_text=True)

    assert "₹3,855.25" in html


def test_profile_renders_member_since_with_date_display(
    client, user, sign_in, isolated_db
):
    conn = sqlite3.connect(str(isolated_db))
    try:
        conn.execute(
            "UPDATE users SET created_at = ? WHERE id = ?",
            ("2026-09-17 10:00:00", user["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    sign_in(client, user["id"], user["name"])
    html = client.get("/profile").get_data(as_text=True)

    assert "17 September 2026" in html


def test_profile_clears_session_when_user_row_is_gone(
    client, sign_in, read_session
):
    sign_in(client, 987654, "Gone User")

    response = client.get("/profile")

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    assert "user_id" not in read_session(client)


def test_profile_flashes_when_user_row_is_gone(client, sign_in):
    sign_in(client, 987654, "Gone User")

    response = client.get("/profile", follow_redirects=True)

    assert SIGN_IN_PROMPT in response.get_data(as_text=True)


# ------------------------------------------------------------------ #
# Unknown paths                                                       #
# ------------------------------------------------------------------ #

def test_unknown_path_returns_404(client):
    response = client.get("/no-such-page")

    assert response.status_code == 404
