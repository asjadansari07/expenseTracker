---
name: spendly-ui
description: Designs and generates modern, production-ready UI for Spendly, a personal expense tracker built on Flask + Jinja2 + vanilla CSS (repo - https://github.com/asjadansari07/expenseTracke). Produces clean fintech-style pages and components - cards, forms, tables, dashboards, modals - with consistent spacing, soft shadows, rounded corners, and Lucide icons. Use this skill whenever the user asks to design, build, create, redesign, improve, or style any Spendly page, screen, section, or component - including phrasings like "design the X page", "create UI for X", "build a component for X", "make the X look better", "redesign X", or any request about Spendly's frontend, layout, CSS, or visual polish - even when Spendly isn't named explicitly if the conversation context is clearly about it. Always consult this skill before writing or editing any Spendly template or CSS file, even for small tweaks, to keep the design system consistent.
---

# Spendly UI

Design and build UI for **Spendly**, a personal expense tracker (Flask + Jinja2 + vanilla CSS, no frontend framework, no CSS framework/build step). The goal every time: pages that look like a small, well-funded fintech product built them — calm, confident, uncluttered — not a tutorial CRUD app.

## Before writing anything

1. **Read `references/design-system.md` first.** It has the full token set (colors, spacing, radius, shadows, type scale) and the component patterns (cards, forms, tables, dashboards, modals, nav). Do not improvise tokens from memory once this file exists — reuse it so every page stays visually consistent with every other page.
2. **Check the actual repo state before assuming structure.** Conventions in this SKILL are defaults for a typical Flask/Jinja2 layout, not guaranteed facts about this repo. If the repo or relevant files are available (uploaded, cloned, or fetchable), look at:
   - `templates/base.html` (or similar) for the current layout, nav, and however Lucide/fonts are already loaded
   - the stylesheet(s) (commonly `static/css/style.css`) for whatever tokens/classes already exist
   - one or two existing templates for the current markup conventions (block names, class naming)
   If you find real conventions that differ from this skill's defaults (different variable names, a different icon set, existing utility classes), **follow what's already in the repo** and treat this skill's defaults as a fallback for greenfield pages/components only.
3. If neither the repo nor any file is available and this is a brand-new page with nothing to match, proceed with the defaults in `references/design-system.md` and say so briefly.

## Workflow

1. **Clarify scope in one line, don't interrogate.** If the ask is clear ("design the dashboard page"), just build it. Only ask a clarifying question when the request is genuinely ambiguous (e.g. "make it better" with no target).
2. **Decide the deliverable:**
   - If asked for a preview/mockup/"show me" or to compare options → render as an HTML artifact (self-contained, Lucide via CDN script) so it can be viewed and iterated on before touching the repo.
   - If asked to implement/build/add to the actual project, or a repo file is available to edit → write real Jinja2 template(s) + CSS, following existing block/include structure.
   - When unsure, default to a quick artifact preview first, then offer to wire it into the real templates.
3. **Build using the tokens and components in `references/design-system.md`.** Don't invent a new radius, shadow, or spacing value ad hoc — pick the closest existing token. If a genuinely new pattern is needed, add it to the reference file's "component patterns" section so it's reusable next time (see "Extending the design system" below).
4. **Icons:** use [Lucide](https://lucide.dev) exclusively — never emoji, never a different icon set, never inline hand-drawn SVGs for standard concepts (money, calendar, trash, edit, filter, etc.) that Lucide already covers.
5. **Responsiveness and states are not optional.** Every component needs: a mobile-collapsed/stacked layout, a hover/focus state on interactive elements, and an empty state if it's a list/table (e.g. "No transactions yet" rather than a bare empty table).
6. **After generating**, briefly note any assumption made about repo structure (e.g. "assumed CSS variables live in `:root` in `style.css`; adjust the import if yours differs") so the user can correct it fast.

## Fintech visual language (quick reference — full detail in the design-system file)

- Generous white space over dense packing; let numbers breathe.
- Soft, low-opacity shadows (never harsh drop shadows); rounded corners (12–16px on cards/modals, 8px on buttons/inputs).
- Restrained color: one primary brand color, a muted neutral gray scale for structure, and semantic colors used *only* for meaning (green = income/positive, red = expense/negative, amber = warning) — never decoratively.
- Numbers (amounts, balances) get slightly heavier weight and a tabular/monospaced-number feel so columns of figures align.
- Clear typographic hierarchy: one clear page title, muted subtext/labels, no more than 2 font weights per screen.
- Dark mode is a first-class citizen, not an afterthought — build with CSS variables so it's free.

## Extending the design system

When a request needs a component that isn't yet in `references/design-system.md` (e.g. a new "budget progress bar" or "category badge"), design it consistent with the existing tokens, then append it to that file's component patterns section with a short comment. This keeps the skill improving over time instead of drifting inconsistent between sessions.

## Output checklist before finishing

- [ ] Uses design tokens from `references/design-system.md` (no ad hoc hex codes, shadows, or radii)
- [ ] Uses Lucide icons, not emoji or other icon sets
- [ ] Has a mobile layout and hover/focus states
- [ ] Has an empty state if it renders a list/table
- [ ] Matches existing repo conventions where they're known, otherwise notes the assumption