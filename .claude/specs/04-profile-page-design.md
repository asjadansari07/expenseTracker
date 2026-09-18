# Spec: Profile Page Design

## Overview

Give a signed-in user a page that shows who they are. Step 3 (login/logout)
established the session contract — `session["user_id"]` and
`session["user_name"]` — and made `base.html`'s navbar session-aware, but
`GET /profile` is still the raw-string stub from the scaffold
(`app.py:132-134`, returning `"Profile page — coming in Step 4"`), so it is
reachable only by typing the URL and has nothing to show when you arrive. There
is also no `login_required` guard anywhere in the app; Step 3 deliberately left
that to this step.

This step implements Step 4 of the roadmap: a signed-in-only profile page that
re-reads the user's row from the database and presents their account identity —
name, email, and member-since date — as a designed page rather than a bare
string, with a sign-out action. It creates the project's first page-specific
stylesheet, and it introduces the reusable `login_required` decorator that the
expense routes in Steps 7-9 will apply to their own views.

Reading the user from the database rather than from `session["user_name"]` is
the point of the page: the session is a cache of two fields set at login, so it
can go stale, and it carries no `created_at`. The profile page is the first
place the app renders a user's own persisted record.

**Explicitly out of scope.** Two things a "profile page" often implies are not
in this step:

- **Editing the profile.** The roadmap has no update-profile route, and adding
  one means a `POST` handler, validation, an email-uniqueness conflict path and
  CSRF considerations. The page is read-only: no forms, no `POST`, and no
  `methods=["GET", "POST"]` on the view.
- **Expense statistics.** Totals, counts, or per-category breakdowns on this
  page would read the `expenses` table, which belongs to the expense
  list/dashboard steps and would duplicate them. This step does not query
  `expenses` at all — the page is independent of Steps 7-9.

## Depends on

- **Step 1 — Database setup** (complete). Requires the `users` table
  (`id`, `name`, `email`, `password_hash`,
  `created_at TEXT DEFAULT (datetime('now'))`) and `get_db()` with `row_factory`
  set, so rows are addressable by column name.
- **Step 2 — Registration** (complete). Requires `app.secret_key` to be set;
  without it `session` and `flash()` raise.
- **Step 3 — Login and logout** (complete). Requires the session contract
  `session["user_id"]` / `session["user_name"]` set by `login()`, and the two
  `base.html` changes it made: the `{% if session.get('user_id') %}` navbar
  branch (`base.html:22-27`) and the category-aware flash block
  (`base.html:33-41`) that this step extends and relies on.

## Routes

- `GET /profile` — renders the signed-in user's profile page — **logged-in**

No new URL is introduced. `profile()` already exists as a stub and its body is
replaced in place, so `url_for("profile")` starts resolving to a real page
rather than a string. CLAUDE.md forbids raw-string returns for stub routes once
a step is implemented, so the view renders a template.

`GET /profile` while signed **out** returns a `302` to `/login` (see Rules),
not a `401` — a browser-friendly redirect, matching how `login()` already
redirects.

This step also adds one non-route function to `app.py`:

- `login_required(view)` — a decorator applied to `profile()` only in this
  step. It is the app's first access-control primitive; Steps 7-9 will decorate
  their own views with it.

## Database changes

**No database changes.**

Verified against `database/db.py`: the `users` table already stores everything
the page displays — `id INTEGER PRIMARY KEY AUTOINCREMENT`, `name TEXT NOT NULL`,
`email TEXT UNIQUE NOT NULL`, and `created_at TEXT DEFAULT (datetime('now'))`.
No new table, column, index or constraint is needed, so there is no schema
migration in this step and `init_db()` is unchanged.

Two properties of the existing schema to respect, not change:

- `created_at` is auto-filled by SQLite's `datetime('now')`, which is **UTC**
  in `YYYY-MM-DD HH:MM:SS` form. It is rendered as a date, with no timezone
  conversion (see Rules) — the roadmap has no timezone handling anywhere, and
  introducing it here would be the only place in the app that does it.
- The page must never surface `password_hash`. The row returned by the new
  helper is not handed to the template wholesale (see Rules).

## Templates

- **Create:**
  - `templates/profile.html` — extends `base.html`, fills `title`, `head` and
    `content`.
    - `{% block head %}` links the new page stylesheet:
      `{{ url_for('static', filename='css/profile.css') }}`. This makes
      `profile.html` the first template in the project to use the
      `{% block head %}` hook that `base.html:11` already provides.
    - `{% block content %}` lays out the page in two parts:
      1. **Identity header** — a round avatar showing the user's initials,
         alongside their full name and email address. Initials come from the
         first letter of the first two whitespace-separated words of `name`,
         uppercased; a one-word or empty name must not raise (fall back to the
         first letter of the email, then to a single glyph).
      2. **Account details card** — a definition-style list with three rows:
         Name, Email, Member since. `Member since` renders `created_at` through
         the new `date_display` filter. Below the list, a `Sign out` link styled
         with the existing `.btn-secondary` class pointing at
         `url_for('logout')`.
    - Everything is read from a `user` variable passed by the view; the template
      must not hardcode any user value, and must not reference `session`.
  - `static/css/profile.css` — new page-specific stylesheet. Defines the
    `.profile-*` classes (page wrapper, identity header, avatar, name, email,
    details card, detail rows). Must contain only `var(--…)` references for
    colours, spacing and radii — no literal hex values (see Rules). Responsive
    down to 375px: the avatar-and-name header stacks vertically on narrow
    screens and the page must not scroll horizontally.
- **Modify:**
  - `templates/base.html` — add a `Profile` link to the signed-in navbar branch
    (`base.html:22-27`). That branch currently renders only `Sign out`, so a
    signed-in user has no route to the page. The link is
    `<a href="{{ url_for('profile') }}">Profile</a>`, placed before the existing
    `Sign out` link, and the `{% else %}` branch (`Sign in` / `Get started`)
    must stay exactly as it is. `.nav-links a` already supplies the styling, so
    this change needs no CSS.

No `<style>` blocks anywhere — page-specific styling lives in `profile.css`.

## Files to change

- `app.py` — import `functools` and `datetime`; widen the `database.db` import
  to include the new `get_user_by_id`; add the `login_required` decorator and
  the `date_display` template filter; replace the `profile()` stub body with the
  real view.
- `database/db.py` — add a `get_user_by_id(user_id)` helper.
- `templates/base.html` — add the `Profile` navbar link.

## Files to create

- `templates/profile.html`
- `static/css/profile.css`

No test files are created. The repository has no `tests/` directory (verified),
and manual verification against the running app on port 5001 is this project's
established convention from Steps 2 and 3. `pytest` and `pytest-flask` are
pinned in `requirements.txt` but still unused by any test; introducing a suite
is a separate decision, out of scope here.

Note: `landing.css` is listed in CLAUDE.md's architecture diagram but does not
exist — the landing page's styles (`.hero`, `.mock-*`, `.features`) live in
`style.css`, and no template currently uses `{% block head %}`. This spec
follows CLAUDE.md's written rule that page-specific styles get their own file,
which makes `profile.css` the first of its kind. If the project would rather
keep one stylesheet, the `profile-*` rules go at the end of `style.css` and the
`{% block head %}` link is dropped; nothing else in this spec changes.

## New dependencies

**No new dependencies.**

Everything used is already available: `functools` and `datetime` are Python
stdlib, `session` / `flash` / `redirect` / `url_for` come from `flask==3.1.3`,
and `render_template` is already imported. No new pip packages, so
`requirements.txt` is unchanged.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only — `?` placeholders, never f-strings in SQL
- Passwords hashed with werkzeug — and never rendered: `password_hash` must not
  reach the template context
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- **No DB logic in routes.** The lookup lives in `database/db.py`; `app.py` only
  calls it. Do not open a connection or write SQL in the view.
- **Add `get_user_by_id(user_id)` to `database/db.py`.** Parameterised
  `SELECT * FROM users WHERE id = ?`, returning the `sqlite3.Row` or `None`.
  Reuse `get_db()` and close the connection in a `finally` block, exactly
  matching the shape of `get_user_by_email()`. Like that helper it makes no
  authorisation decision — it does not care whether the id came from a session,
  and it does not filter or reshape the row. `db.py` stays a data layer.
- **Add `login_required` in `app.py`, using `functools.wraps`** so the decorated
  view keeps its name (otherwise Flask raises for two views sharing an endpoint
  name). It checks `session.get("user_id")`; when absent it flashes
  `"Please sign in to view your profile."` and returns
  `redirect(url_for("login"))`. Decorate the view with the route **outermost**:

  ```python
  @app.route("/profile")
  @login_required
  def profile():
      ...
  ```

- **Do not implement a `next`/`?next=` parameter** in the `login_required`
  redirect. Step 3 explicitly declined a `next` parameter on login, and
  honouring an attacker-supplied one would open a redirect vulnerability for no
  benefit. Post-login redirects continue to go to `landing`.
- **Handle a session that points at a missing user.** `get_user_by_id()` can
  return `None` — the row can have been deleted while a browser still holds a
  valid session cookie. The view must not index into a `None` row: when the
  lookup returns `None`, `session.clear()`, flash the same
  "Please sign in…" message, and redirect to `login`. A stale session must end
  as a sign-out, never a `500`.
- **Pass only what the page needs to the template.** Build the context from the
  row's `name`, `email` and `created_at` — do not pass the whole `sqlite3.Row`
  or a dict copy of it, so `password_hash` cannot leak into the rendered page by
  accident.
- **Format `created_at` with a Jinja filter**, registered in `app.py` as
  `@app.template_filter("date_display")`, so the view stays "fetch data, render
  template, done" per CLAUDE.md. It parses the stored
  `YYYY-MM-DD HH:MM:SS` form with `datetime.strptime` and returns a readable
  date such as `17 September 2026`. Return a neutral placeholder (`—`) rather
  than raising when the value is `None` or does not parse — the column has a
  default but no `NOT NULL` constraint, so a malformed value is possible.
- **Do not convert timezones.** `created_at` is UTC; display the date as stored.
  A user in IST may see a date one day earlier than their local wall clock
  around midnight, which is acceptable at this stage and consistent with the
  rest of the app.
- **Apply `login_required` to `profile()` only.** Do not retrofit it onto
  `landing`, `/register`, `/login`, `/logout`, or the legal pages — they are
  public by design, and a redirect loop at `/login` is the obvious failure if
  this is got wrong.
- **Do not render the stub string.** After this step, `GET /profile` must never
  return `"Profile page — coming in Step 4"`.
- **Do not touch the other stubs.** `/expenses/add`, `/expenses/<id>/edit` and
  `/expenses/<id>/delete` keep their raw-string bodies (Steps 7, 8, 9).
- **Do not modify `seed_db()` and do not change the demo credentials.** The demo
  account (`demo@spendly.com` / `demo123`) is the primary manual-test login.
- **Do not modify `init_db()` or the schema.** No migrations in this step.
- **Do not read from the `expenses` table.** No totals, counts or breakdowns —
  that belongs to the expense steps.
- **No forms, no `POST`, no mutating actions** beyond the existing `GET /logout`
  link. There is nothing here to submit, so no new CSRF surface is introduced —
  and `flask-wtf` is unavailable in any case (CLAUDE.md forbids new packages).
- **No inline `<style>` or `style=""` attributes.** All new styling goes in
  `static/css/profile.css`, except the avatar tint if it varies per user, which
  should be a CSS class rather than a computed colour.
- **`url_for()` for every internal link** — the navbar link, the sign-out link,
  and the stylesheet href. No hardcoded paths.
- **Accessibility:** mark the decorative avatar as `aria-hidden="true"` (or give
  it an accessible label), give the page exactly one `<h1>` (the user's name),
  and use a real `<a>` for sign-out rather than a click-handled `<div>`. No JS
  is required for this page — `static/js/main.js` is not modified.

## Definition of done

Each item is verifiable by running the app on port 5001 against a browser and
the demo account. Manual verification, per the convention from Steps 2 and 3.

**Access control**
- [ ] `GET /profile` while signed out returns `302` to `/login` — not a `200`,
      not a `500`
- [ ] The redirect is followed by "Please sign in to view your profile." on the
      sign-in page
- [ ] `GET /profile` while signed in as `demo@spendly.com` / `demo123` returns
      `200` and renders the page
- [ ] `GET /profile` while signed in does **not** redirect to `/login`
      (no redirect loop)
- [ ] `GET /login`, `/register`, `/`, `/terms-and-conditions` and
      `/privacy-policy` still return `200` while signed out — `login_required`
      was not applied to them

**Page content**
- [ ] The page shows the signed-in user's name and email
- [ ] The email shown matches the row in `users` for that id
- [ ] `Member since` shows a readable date (e.g. `17 September 2026`), not the
      raw `2026-09-17 12:34:56` string
- [ ] The avatar shows the user's initials, and a one-word name renders without
      error
- [ ] The page contains exactly one `<h1>`
- [ ] Viewing source shows no `password_hash` value anywhere in the response
- [ ] The `Profile` link in the navbar reaches the page; when signed out the
      navbar shows `Sign in` / `Get started` and **no** `Profile` link
- [ ] `Sign out` on the page works and returns to `/login` with the
      "You have been signed out." message

**Proves the data comes from the database, not the session**
- [ ] After signing in, update the row directly —
      `sqlite3 expense_tracker.db "UPDATE users SET name='Renamed User' WHERE email='demo@spendly.com'"`
      — and reload `/profile`: the new name appears, while the navbar still
      shows the old `session["user_name"]`. This is the check that the view
      reads `users` rather than trusting the session
- [ ] Delete the row while the browser still holds the session cookie —
      `sqlite3 expense_tracker.db "DELETE FROM users WHERE email='demo@spendly.com'"`
      — and reload `/profile`: the app redirects to `/login` with the
      please-sign-in message and does **not** raise a `500`
- [ ] After that redirect, a second `GET /profile` also redirects (the session
      was cleared, not just bypassed)

**Styling constraints**
- [ ] `static/css/profile.css` loads on `/profile` only — no other page's
      rendering changes
- [ ] `grep` of `static/css/profile.css` finds no raw hex value — `var(--…)`
      references only
- [ ] `grep` of `templates/profile.html` finds no `<style>` block and no
      hardcoded `href="/…"`
- [ ] The page is legible at 375px width with no horizontal scrolling
- [ ] With JavaScript disabled the page renders and the sign-out link still
      works (no JS dependency)

**Regression / constraints**
- [ ] `GET /profile` no longer returns the string
      `Profile page — coming in Step 4`
- [ ] `grep` of `app.py` finds no `sqlite3`, no `SELECT` and no `INSERT` — all
      DB access goes through `database/db.py`
- [ ] `grep` of `app.py` finds no reference to the `expenses` table
- [ ] `/expenses/add`, `/expenses/<id>/edit` and `/expenses/<id>/delete` still
      return their original stub strings
- [ ] Registration → login → profile works end-to-end for a newly created
      account, not just the demo user
- [ ] `requirements.txt` is unchanged
- [ ] App starts cleanly on port 5001 with no errors, warnings, or
      "duplicate endpoint" errors from `functools.wraps`
