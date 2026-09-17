import os

from flask import Flask, render_template, request, redirect, url_for, flash
from database.db import get_db, init_db, seed_db, create_user

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


@app.route("/login")
def login():
    return render_template("login.html")


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
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


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
