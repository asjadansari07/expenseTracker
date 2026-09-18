import functools
import os
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session
)
from werkzeug.security import check_password_hash

from database.db import (
    get_db, init_db, seed_db, create_user, get_user_by_email, get_user_by_id
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-not-for-production")

# Initialize database
with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Validation helpers                                                  #
# ------------------------------------------------------------------ #

def _validate_registration(name, email, password):
    """Returns an error string, or None if the input is valid.

    Expects name and email to already be stripped.
    """
    if not name:
        return "Please enter your name."

    local, _, domain = email.partition("@")
    if not local or not domain or "@" in domain:
        return "Please enter a valid email address."
    if "." not in domain or domain.startswith(".") or domain.endswith("."):
        return "Please enter a valid email address."

    if len(password) < 8:
        return "Password must be at least 8 characters."

    return None


# ------------------------------------------------------------------ #
# Access control                                                      #
# ------------------------------------------------------------------ #

def login_required(view):
    """Redirects signed-out visitors to the sign-in page.

    Apply below the route so the wrapped view keeps its endpoint name:

        @app.route("/profile")
        @login_required
        def profile():
            ...
    """
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to view your profile.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


# ------------------------------------------------------------------ #
# Template filters                                                    #
# ------------------------------------------------------------------ #

@app.template_filter("date_display")
def date_display(value):
    """Renders the stored UTC timestamp as a readable date, e.g. 17 September 2026.

    Returns a placeholder rather than raising, because created_at is
    defaulted but not NOT NULL, so a missing or malformed value is possible.
    """
    if not value:
        return "—"

    try:
        parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return "—"

    # %-d is not portable to Windows, so drop the leading zero by hand.
    return f"{parsed.day} {parsed.strftime('%B %Y')}"


@app.template_filter("date_short")
def date_short(value):
    """Renders an expense date (YYYY-MM-DD) as e.g. 7 Sep 2026.

    Separate from date_display because the expenses table stores a plain
    date where users.created_at stores a full timestamp.
    """
    if not value:
        return "—"

    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        return "—"

    return f"{parsed.day} {parsed.strftime('%b %Y')}"


@app.template_filter("inr")
def inr(value):
    """Formats an amount as rupees, e.g. 1200.0 -> ₹1,200.00."""
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


# ------------------------------------------------------------------ #
# Placeholder data                                                    #
# ------------------------------------------------------------------ #

# Hardcoded sample expenses for the profile page. These are deliberately
# NOT read from the database: the profile spec keeps this page off the
# expenses table, and the real list arrives in Step 7. Every signed-in
# user sees the same rows, so the template labels them as samples.
# Only the fields the page renders — no ids, no user_id.
PLACEHOLDER_EXPENSES = [
    {
        "amount": 350.50,
        "category": "Food",
        "date": "2026-09-07",
        "description": "Grocery shopping",
    },
    {
        "amount": 80.00,
        "category": "Transport",
        "date": "2026-09-08",
        "description": "Bus fare",
    },
    {
        "amount": 1200.00,
        "category": "Bills",
        "date": "2026-09-10",
        "description": "Electricity bill",
    },
    {
        "amount": 500.00,
        "category": "Health",
        "date": "2026-09-12",
        "description": "Pharmacy",
    },
    {
        "amount": 250.00,
        "category": "Entertainment",
        "date": "2026-09-14",
        "description": "Movie tickets",
    },
    {
        "amount": 899.00,
        "category": "Shopping",
        "date": "2026-09-15",
        "description": "Clothing",
    },
    {
        "amount": 150.00,
        "category": "Other",
        "date": "2026-09-16",
        "description": "Miscellaneous",
    },
    {
        "amount": 425.75,
        "category": "Food",
        "date": "2026-09-17",
        "description": "Restaurant dinner",
    },
]


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method != "POST":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    error = _validate_registration(name, email, password)
    if error:
        return render_template(
            "register.html", error=error, name=name, email=email
        ), 400

    if create_user(name, email, password) is None:
        return render_template(
            "register.html",
            error="An account with that email already exists.",
            name=name,
            email=email
        ), 400

    flash("Account created successfully. Please sign in.", "success")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method != "POST":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    # One generic message for every failure below, so the form cannot be
    # used to find out which emails have accounts.
    error = "Invalid email or password."

    if not email or not password:
        return render_template("login.html", error=error, email=email), 400

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error=error, email=email), 400

    # Clear first so a pre-existing anonymous session is never promoted.
    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]

    return redirect(url_for("profile"))


@app.route("/terms-and-conditions")
def terms_and_conditions():
    return render_template("terms-and-conditions.html")


@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy-policy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():
    user = get_user_by_id(session["user_id"])

    # The row can be deleted while a browser still holds a valid session.
    if user is None:
        session.clear()
        flash("Please sign in to view your profile.", "error")
        return redirect(url_for("login"))

    # Only the fields the page renders — never the whole row, so
    # password_hash cannot leak into the response.
    return render_template(
        "profile.html",
        user={
            "name": user["name"],
            "email": user["email"],
            "created_at": user["created_at"],
        },
        expenses=PLACEHOLDER_EXPENSES,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
