# Spec: Login and Logout

## Overview

Establish authenticated sessions for Spendly. Step 2 delivered working account
creation: `POST /register` validates input, hashes the password with werkzeug and
inserts the user through `create_user()`, then flashes a success message and
redirects to `/login`. But `/login` is still `GET`-only, so the form in
`login.html` (which posts to `/login`) currently 405s, and `/logout` is still a
raw-string stub. There is no way for a user to actually sign in.

This step wires the sign-in half of authentication: `POST /login` looks the user
up by email, verifies the password against the stored `password_hash`, and
establishes the session; `GET /logout` tears that session down. It also makes the
navbar session-aware so a signed-in user can reach the sign-out link — without
that, `logout` is only reachable by typing the URL.

It deliberately stops at the session boundary: `/profile` and every expense
route stay stubs (Steps 4, 7, 8, 9). The session keys introduced here
(`session["user_id"]`) are the contract those later steps will read.

## Depends on

- **Step 1 — Database setup** (complete). Requires the `users` table
  (`id`, `name`, `email UNIQUE`, `password_hash`, `created_at`), `get_db()` with
  `row_factory` + `PRAGMA foreign_keys = ON`, and `seed_db()`'s demo user
  (`demo@spendly.com` / `demo123`) as a ready-made account to test against.
- **Step 2 — Registration** (complete). Requires `create_user()` to exist (it
  defines email normalisation, which login must mirror), `app.secret_key` to be
  set, and the flash-message block in `base.html` to render queued messages.
  Login cannot be tested end-to-end without a way to create an account.

## Routes

- `POST /login` — accepts the sign-in form, verifies the password, establishes
  the session, redirects to `/` — **public**
- `GET /logout` — clears the session, flashes a confirmation, redirects to
  `/login` — **logged-in** (harmless if already signed out)

Both extend existing functions rather than adding new ones:

- `login()` becomes `@app.route("/login", methods=["GET", "POST"])`. The existing
  `GET` branch already renders `login.html`, and `login.html` already posts to
  `/login`, so no new URL is introduced. This mirrors exactly how Step 2 extended
  `register()`.
- `logout()` replaces the `return "Logout — coming in Step 3"` stub in place.
  CLAUDE.md forbids raw-string returns for implemented stub routes, so it must
  redirect (there is no logout page to render).

`GET /login` while already signed in returns a `302` to `landing` instead of
re-rendering the form. `landing` is a real implemented page; redirecting to
`/profile` would land the user on a Step 4 stub, so it is not used.

**Why `GET` for logout:** the roadmap table in CLAUDE.md specifies
`GET /logout`, matching the `GET /expenses/<id>/delete` convention already used
in this project. A GET logout can be triggered by any third-party link or image
tag, which is a real (if low-impact, self-inflicted) CSRF vector — it logs the
victim out and nothing more. Because the roadmap fixes the method, this spec
keeps `GET` and does not re-litigate it; out of scope here.

## Database changes

**No database changes.**

Verified against `database/db.py`: the `users` table already stores everything
login needs — `id INTEGER PRIMARY KEY AUTOINCREMENT`,
`email TEXT UNIQUE NOT NULL`, `password_hash TEXT NOT NULL`. All columns are
read through existing helpers; no new table, column, index or constraint is
required, so there is no schema migration in this step.

One property to respect, not change: `create_user()` normalises with
`email.strip().lower()` before inserting, while SQLite's `UNIQUE` is
**case-sensitive**. Login must therefore apply the identical
`.strip().lower()` normalisation to the submitted email, or a user who registered
as `Nitish@Example.com` would be unable to sign in. The fix is normalisation at
the lookup, not a `COLLATE NOCASE` migration.

## Templates

- **Create:** none.
- **Modify:**
  - `templates/login.html`
    - Replace the hardcoded `action="/login"` with
      `action="{{ url_for('login') }}"` (CLAUDE.md forbids hardcoded URLs; this
      file is being edited anyway).
    - Repopulate the email field from context on failure:
      `value="{{ email or '' }}"`. Never repopulate the password field.
    - Keep the existing `{% if error %}` block as the error-display mechanism.
  - `templates/base.html`
    - Make the navbar session-aware. Currently it always renders
      `Sign in` + `Get started` (`base.html:21-24`), so a signed-in user has no
      route to `/logout`. Wrap the links in
      `{% if session.get('user_id') %}`: render a `Sign out` link
      (`url_for('logout')`) when signed in, and the existing two links when not.
      The `else` branch must be the current markup, unchanged.
    - Make the flash block category-aware: render each message with
      `flash-{{ category }}` (plus the existing `auth-error` base class) instead
      of hardcoding `auth-error`. Step 2's block styles *every* message as an
      error, so the sign-out confirmation and the "Account created" notice both
      currently render in danger red. Keep the loop and the
      `{% if messages %}` guard exactly as they are.

## Files to change

- `app.py` — add `session` and `check_password_hash` to the imports; extend
  `login()` to accept `POST` with the credential-verification logic; replace the
  `logout()` stub body.
- `database/db.py` — add a `get_user_by_email()` helper; import
  `check_password_hash` only if the helper is chosen to verify (it is not — see
  Rules).
- `templates/login.html` — `url_for` action + email repopulation.
- `templates/base.html` — session-aware navbar, category-aware flash classes.
- `static/css/style.css` — add a `.flash-success` rule so success messages are
  not styled as errors.

## Files to create

None.

No test files are created: the repository has no `tests/` directory (verified),
and Step 2 established manual verification against a running app as this
project's convention. `pytest` and `pytest-flask` are pinned in
`requirements.txt` but nothing uses them yet. Introducing a test suite is a
separate decision and out of scope here.

## New dependencies

**No new dependencies.**

`werkzeug==3.1.6` is already pinned and provides `check_password_hash` alongside
the `generate_password_hash` that `database/db.py` already imports. Flask's
`session` is part of `flask==3.1.3`. No new pip packages, so `requirements.txt`
is unchanged.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only — `?` placeholders, never f-strings in SQL
- Passwords hashed with werkzeug — verification must use `check_password_hash`,
  never a manual hash comparison or `==` against the stored hash
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- **No DB logic in routes.** The lookup lives in `database/db.py`; `app.py` only
  calls it. Do not open a connection or write SQL in the view.
- **Add `get_user_by_email(email)` to `database/db.py`.** It applies
  `.strip().lower()` to the argument, runs a parameterised
  `SELECT * FROM users WHERE email = ?`, and returns the `sqlite3.Row` or `None`.
  Reuse `get_db()` and close the connection in a `finally` block, matching
  `create_user()`. The helper returns the row (including `password_hash`) and
  makes **no** authentication decision — `db.py` stays a data layer with no auth
  policy, and the view owns the credential check and the session.
- **Verify in the route** with
  `check_password_hash(user["password_hash"], password)`. Import
  `check_password_hash` in `app.py` — do not import it in `db.py` for this
  purpose.
- **Guard against a `None` user before touching the hash.** The flow is
  `get_user_by_email()` → if `None`, fail → otherwise `check_password_hash()`.
  Never index into a possibly-`None` row.
- **One generic failure message for every credential failure:**
  "Invalid email or password." Return it for an unknown email *and* for a wrong
  password, so the form cannot be used to enumerate which emails have accounts.
  Do not reveal whether the email exists, and do not surface the raw exception.
- **Failed credentials re-render `login.html` with the error, the submitted email
  still filled in, an empty password field, and a `400`** — consistent with the
  `400` that `register()` already returns for validation failures.
- **Blank email or password** short-circuits to the same error path with `400`
  and issues no database query.
- **Establish the session as:** `session.clear()` then
  `session["user_id"] = user["id"]` and `session["user_name"] = user["name"]`.
  Clearing first prevents session fixation (a pre-existing anonymous session must
  not be promoted to authenticated). `session["user_name"]` is stored so the
  navbar can greet the user without a per-request query.
- **Logout:** `session.clear()` (not `session.pop("user_id")` — clear every key
  so no stale state survives), then `flash("You have been signed out.", "success")`,
  then `redirect(url_for("login"))`.
- **POST → redirect → GET on success.** Do not render a template from a
  successful `POST /login` or `GET /logout`.
- **Do not implement a `next`/`?next=` redirect parameter.** Post-login
  redirects always go to `landing`. Honouring an attacker-supplied `next` would
  introduce an open redirect for no benefit at this stage; adding it later is
  easy, removing it after it ships is not.
- **No CSRF tokens.** `flask-wtf` is not available and CLAUDE.md forbids new
  packages, so `/login` and `/logout` ship without CSRF protection. Do not
  hand-roll a token scheme in this step.
- **Do not change the cookie/session config** (`SESSION_COOKIE_*`,
  `PERMANENT_SESSION_LIFETIME`). Defaults are fine; a session-fixation-safe
  login does not require them.
- Do not modify `seed_db()`. The demo account (`demo@spendly.com` / `demo123`)
  must keep working and is the primary manual-test credential.
- Do not implement `/profile` or any `/expenses/*` route — Steps 4, 7, 8, 9.
  The session key `session["user_id"]` is all this step owes them.
- Do not add a login requirement / `login_required` decorator to existing routes
  in this step; `landing`, `/register`, `/login`, and the legal pages must stay
  publicly reachable.

## Definition of done

Each item is verifiable by running the app on port 5001. Manual verification
against the running app, per the convention established in Step 2.

**Sign in — happy path**
- [ ] `GET /login` returns 200 and renders the form as before
- [ ] Signing in as `demo@spendly.com` / `demo123` returns `302` and redirects
      to `/`
- [ ] After signing in, the browser holds a session cookie and the navbar shows
      `Sign out` instead of `Sign in` / `Get started` — proving the session is set
- [ ] Signing in as a newly registered account (created via `/register`) also
      works, proving `get_user_by_email()` matches what `create_user()` stored
- [ ] Signing in with `DEMO@SPENDLY.COM` / `demo123` succeeds — email lookup is
      case-insensitive, matching `create_user()`'s normalisation
- [ ] Signing in with a valid email and a mixed-case password is rejected —
      passwords are never normalised

**Sign in — failure paths (all must return 400 and re-render the form)**
- [ ] Correct email, wrong password → "Invalid email or password."
- [ ] Unknown email → byte-identical error message to the wrong-password case
      (no user enumeration)
- [ ] Blank/whitespace-only email or password → error, and no query is issued
- [ ] After a failed attempt the email field still shows what was typed and the
      password field is empty
- [ ] No `IntegrityError` text, SQL, password value, or `password_hash` appears
      in the rendered error message or in the server log

**Session behaviour**
- [ ] `GET /login` while already signed in returns `302` to `/`
- [ ] `GET /logout` while signed in returns `302` to `/login`, clears the
      session cookie, and shows "You have been signed out."
- [ ] After logout, the navbar shows `Sign in` / `Get started` again
- [ ] `GET /logout` when already signed out returns `302` to `/login` (no 500)
- [ ] After logout + browser back, a protected action is still unauthenticated —
      i.e. `session["user_id"]` is gone, not merely hidden from the nav

**Regression / constraints**
- [ ] Registration still works end-to-end, and its success message now renders
      in the success style rather than danger red
- [ ] `/`, `/register`, `/terms-and-conditions`, `/privacy-policy` all still
      return 200 while signed out
- [ ] `GET /logout` no longer returns the string `Logout — coming in Step 3`
- [ ] `grep` of `app.py` finds no `sqlite3`, no `SELECT`, and no `INSERT` — all
      DB access goes through `database/db.py`
- [ ] `grep` of `templates/` finds no hardcoded `/login` or `/logout` URL
- [ ] `grep` of `static/css/` finds no raw hex value in the new `.flash-success`
      rule (CSS variables only)
- [ ] `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`
      still return their original stub strings
- [ ] App starts cleanly on port 5001 with no errors or warnings
