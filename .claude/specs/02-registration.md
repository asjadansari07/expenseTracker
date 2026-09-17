# Spec: Registration

## Overview

Implement account creation for Spendly. Step 1 delivered the data layer — a
`users` table with a `UNIQUE` email column and a `password_hash` column — but
nothing writes to it. Today `GET /register` renders a form that posts to
`/register`, and no view accepts that POST, so every submission 405s.

This step wires the form to a working `POST /register` handler: it validates
input, hashes the password with werkzeug, inserts the user through a
`database/db.py` helper, and display message registration successfull and then redirects to the sign-in page. It also introduces
`app.secret_key`, the session infrastructure that Step 3 (login/logout) and
Step 4 (profile) will build on.

Registration creates the account only. It does **not** log the user in —
establishing a session on signup is Step 3's job.

## Depends on

- **Step 1 — Database setup** (complete). Requires the existing `users` table
  (`id`, `name`, `email` UNIQUE, `password_hash`, `created_at`) and the
  existing `get_db()` helper with `row_factory` and `PRAGMA foreign_keys = ON`.
- No dependency on any other step.

## Routes

- `POST /register` — accepts the signup form, validates input, creates the user,
  redirects to `/login` on success — **public**

Added to the existing `register()` view rather than as a second function:
`@app.route("/register", methods=["GET", "POST"])`. `GET` behaviour is unchanged
(still renders `register.html`). This keeps one URL per resource, matching what
`register.html` already posts to.

## Database changes

**No database changes.**

Verified against `database/db.py`: the `users` table already has every column
this feature needs — `name TEXT NOT NULL`, `email TEXT UNIQUE NOT NULL`,
`password_hash TEXT NOT NULL`, `created_at TEXT DEFAULT (datetime('now'))`.

One important property to respect, not change: SQLite's `UNIQUE` is
**case-sensitive**, so `Foo@x.com` and `foo@x.com` would both insert. The spec
requires normalising email to lowercase at the boundary (see Rules) rather than
adding a `COLLATE NOCASE` constraint, to avoid a schema migration in this step.

## Templates

- **Create:** none.
- **Modify:**
  - `templates/register.html`
    - Replace the hardcoded `action="/register"` with
      `action="{{ url_for('register') }}"` (CLAUDE.md forbids hardcoded URLs;
      this file is being edited anyway).
    - Repopulate `name` and `email` from context on validation failure:
      `value="{{ name or '' }}"`, `value="{{ email or '' }}"`. Never repopulate
      the password field.
    - Keep the existing `{% if error %}` block as the error-display mechanism.
  - `templates/base.html`
    - Add a flash-message block inside `<main>`, above `{% block content %}`, so
      the post-redirect success message actually renders. Without this, anything
      passed to `flash()` is silently discarded. Loop over
      `get_flashed_messages(with_categories=true)` and render each with the
      existing `.auth-error` class, wrapped in a `.flash-container` div.
    - This is a shared template, so the block must render nothing when there are
      no messages — no layout change for pages that never flash.
  - `static/css/style.css`
    - Add a `.flash-container` rule (`max-width: var(--auth-width)`, centred,
      2rem side padding). `.auth-error` is styled to sit inside `.auth-card`,
      and `<main>` has no padding of its own, so without this the success banner
      would render edge-to-edge across the viewport.

## Files to change

- `app.py` — add `secret_key`, extend the `register()` view to accept POST, add
  the validation and error-handling logic, import `request`, `redirect`,
  `url_for`, `flash`, and the new db helper.
- `database/db.py` — add a `create_user()` helper.
- `templates/register.html` — url_for + field repopulation.
- `templates/base.html` — flash-message rendering block.
- `static/css/style.css` — `.flash-container` wrapper rule.

## Files to create

None.

## New dependencies

**No new dependencies.**

`werkzeug==3.1.6` is already pinned in `requirements.txt` and provides
`generate_password_hash` / `check_password_hash`; `database/db.py` already
imports the former. No new pip packages.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only — `?` placeholders, never f-strings in SQL
- Passwords hashed with werkzeug (`generate_password_hash`) — plaintext must
  never reach the database or a log line
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- **No DB logic in routes.** The insert lives in `database/db.py`; `app.py`
  only calls it. Do not open a connection or write SQL in the view.
- **Add `create_user(name, email, password)` to `database/db.py`.** It hashes
  the password internally, strips and lowercases the email, inserts with a
  parameterised query, and returns the new row id. On a duplicate email it
  catches `sqlite3.IntegrityError` and returns `None` — check-then-insert would
  be racy, so rely on the `UNIQUE` constraint and handle the failure.
- **Normalise email** with `.strip().lower()` in `create_user()` before insert,
  so the case-sensitive `UNIQUE` constraint behaves the way users expect.
- **Validate server-side in the route**, since the HTML `required` attributes are
  trivially bypassed: name and email non-empty after stripping, email contains a
  single `@` with a dot after it, password at least 8 characters (matching the
  form's "Min. 8 characters" placeholder). On failure re-render `register.html`
  with an `error` string and a **400** status.
- **Duplicate email** re-renders `register.html` with a non-leaky message
  ("An account with that email already exists.") and a 400 — do not surface the
  raw `IntegrityError`.
- **`app.secret_key`** must be set before any `flash()`/`session` call, sourced
  as `os.environ.get("SECRET_KEY", <dev fallback>)`. Import `os` (stdlib). Note
  the fallback is for local development only.
- **Success path:** `flash(...)` then `redirect(url_for("login"))` — POST →
  redirect → GET, so a refresh doesn't resubmit the form. Do not render a
  template directly from a successful POST.
- Do not implement `/login` POST, `/logout`, `/profile`, or any expense route —
  those are Steps 3, 4, 7, 8, 9.
- Do not modify `seed_db()`. The demo user (`demo@spendly.com` / `demo123`) must
  keep working; note that registering that email will correctly 400 as a
  duplicate.

## Definition of done

Each item is verifiable by running the app on port 5001.

- [ ] `GET /register` returns 200 and renders the form exactly as before
- [ ] Submitting a valid new name/email/password redirects to `/login` (302) and
      shows the success message there — proving `secret_key` is wired
- [ ] The new row exists in `users` with the submitted name and lowercased email
- [ ] The stored `password_hash` is a werkzeug hash (begins `pbkdf2:sha256` or
      `scrypt:`), never the plaintext password
- [ ] Submitting an email that already exists re-renders the form with an error,
      returns 400, and adds no second row (`SELECT COUNT(*)` unchanged)
- [ ] Submitting `demo@spendly.com` returns 400 as a duplicate
- [ ] Submitting `DEMO@SPENDLY.COM` also returns 400 — case-insensitive duplicate
- [ ] A password of 7 characters re-renders the form with an error and 400
- [ ] Blank/whitespace-only name or email re-renders the form with an error and
      400
- [ ] A malformed email (e.g. `nope`, `a@b`) re-renders the form with an error
      and 400
- [ ] After a validation error, the name and email fields still show what was
      typed and the password field is empty
- [ ] No `IntegrityError` text, SQL, or password value appears in the rendered
      error message
- [ ] Submitting the form with JS disabled still works (no client-side-only
      validation)
- [ ] `grep` of `app.py` finds no `sqlite3`, no `INSERT`, and no `SELECT` — all
      DB access goes through `database/db.py`
- [ ] `grep` of `templates/` finds no hardcoded `/register` or `/login` URLs
- [ ] `/`, `/login`, `/terms-and-conditions`, and `/privacy-policy` still return
      200 with no new flash output when no messages are queued
- [ ] App starts cleanly on port 5001 with no errors or warnings
