<!-- # CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Spendly** is a Flask-based expense tracking web application designed as a step-by-step learning project. The application is currently in early development stages with basic pages and routing implemented. Core features like database operations, authentication, and expense management are planned as incremental student implementation steps.

## Development Commands

**Run the application:**
```bash
python app.py
```
The app runs on `http://localhost:5001` with debug mode enabled.

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run tests:**
```bash
pytest
```

## Architecture

### Application Structure

- **app.py**: Main Flask application with route definitions. Contains both completed routes (landing, login, register, legal pages) and placeholder routes marked for future implementation (logout, profile, expense CRUD operations).

- **database/db.py**: Placeholder for database layer. Students will implement `get_db()`, `init_db()`, and `seed_db()` functions using SQLite with row_factory and foreign keys enabled.

- **templates/**: Jinja2 templates using a base template inheritance pattern
  - `base.html`: Master template with common layout, navigation, and footer
  - Page-specific templates extend `base.html`

- **static/css/style.css**: Custom CSS using CSS variables for theming. Design system includes:
  - Color scheme: `--paper` (background), `--ink` (text), `--accent` (brand color)
  - Centered layouts with `.container` class
  - Footer with brand icon and links

- **static/js/main.js**: Client-side JavaScript (currently minimal)

### Planned Implementation Steps

The codebase includes placeholder routes marked with comments indicating implementation order:

1. **Step 1**: Database setup (database/db.py)
2. **Step 3**: Logout functionality
3. **Step 4**: User profile page
4. **Step 7**: Add expense functionality
5. **Step 8**: Edit expense functionality
6. **Step 9**: Delete expense functionality

### Design Patterns

- **Route organization**: Routes grouped by functionality with clear section comments
- **Template inheritance**: All pages extend `base.html` for consistent layout
- **CSS variables**: Theming through custom properties for maintainability
- **Semantic HTML**: Proper use of semantic tags (footer, nav, etc.)

## Important Conventions

- Port 5001 is hardcoded in `app.py` to avoid conflicts
- Footer links use relative paths (e.g., `terms-and-conditions.html`)
- Debug mode is enabled for development
- The project uses Flask 3.1.3 and includes pytest for testing

## Notes for Future Development

- Authentication routes (login/register) currently only render templates; form handling and session management are not yet implemented
- Database schema and migration strategy are not yet defined
- Test files are expected but not yet present in the codebase
- The application is not git-initialized despite being a learning project -->


# CLAUDE.md

## Project overview

Spendly is a lightweight personal expense tracker built with Flask and SQLite.

---

## Architecture
```
spendly/
├── app.py              # All routes — single file, no blueprints
├── database/
│   └── db.py           # SQLite helpers: get_db(), init_db(), seed_db()
├── templates/
│   ├── base.html       # Shared layout — all templates must extend this
│   └── *.html          # One template per page
├── static/
│   ├── css/
│   │   ├── style.css       # Global styles
│   │   └── landing.css     # Landing-page-only styles
│   └── js/
│       └── main.js         # Vanilla JS only
└── requirements.txt
```

**Where things belong:**
- New routes → `app.py` only, no blueprints
- DB logic → `database/db.py` only, never inline in routes
- New pages → new `.html` file extending `base.html`
- Page-specific styles → new `.css` file, not inline `<style>` tags

---

## Code style

- Python: PEP 8, snake_case for all variables and functions
- Templates: Jinja2 with `url_for()` for every internal link — never hardcode URLs
- Route functions: one responsibility only — fetch data, render template, done
- DB queries: always use parameterized queries (`?` placeholders) — never f-strings in SQL
- Error handling: use `abort()` for HTTP errors, not bare `return "error string"`

---

## Tech constraints

- **Flask only** — no FastAPI, no Django, no other web frameworks
- **SQLite only** — no PostgreSQL, no SQLAlchemy ORM, no external DB
- **Vanilla JS only** — no React, no jQuery, no npm packages
- **No new pip packages** — work within `requirements.txt` as-is unless explicitly told otherwise
- Python 3.10+ assumed — f-strings and `match` statements are fine

---

## Subagent Policy
- Always use a builtin explore subagent for codebase exploration 
  before implementing any new feature
- Always use a subagent to verify test results 
  after any implementation
- When asked to plan, delegate codebase research 
  to a subagent before presenting the plan
- always use a builtin plan subagent in plan mode

---

## Commands
```bash
# Setup
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run dev server (port 5001)
python app.py

# Run all tests
pytest

# Run a specific test file
pytest tests/test_foo.py

# Run a specific test by name
pytest -k "test_name"

# Run tests with output visible
pytest -s
```

---

## Implemented vs stub routes

| Route | Status |
|---|---|
| `GET /` | Implemented — renders `landing.html` |
| `GET /register` | Implemented — renders `register.html` |
| `GET /login` | Implemented — renders `login.html` |
| `GET /logout` | Stub — Step 3 |
| `GET /profile` | Stub — Step 4 |
| `GET /expenses/add` | Stub — Step 7 |
| `GET /expenses/<id>/edit` | Stub — Step 8 |
| `GET /expenses/<id>/delete` | Stub — Step 9 |

**Do not implement a stub route unless the active task explicitly targets that step.**

---

## Warnings and things to avoid

- **Never use raw string returns for stub routes** once a step is implemented — always render a template
- **Never hardcode URLs** in templates — always use `url_for()`
- **Never put DB logic in route functions** — it belongs in `database/db.py`
- **Never install new packages** mid-feature without flagging it — keep `requirements.txt` in sync
- **Never use JS frameworks** — the frontend is intentionally vanilla
- **`database/db.py` is currently empty** — do not assume helpers exist until the step that implements them
- **FK enforcement is manual** — SQLite foreign keys are off by default; `get_db()` must run `PRAGMA foreign_keys = ON` on every connection
- The app runs on **port 5001**, not the Flask default 5000 — don't change this