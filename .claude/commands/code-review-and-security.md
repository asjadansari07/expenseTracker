---
description: Run the code-reviewer and security-reviewer subagents in parallel over one change, then merge their findings into a single report
argument-hint: "[path | PR number | branch | git ref — defaults to the working-tree diff plus untracked files]"
allowed-tools: Agent, Task, Read, Grep, Glob, Bash
---

Two reviewers over one change: `code-reviewer` for correctness and project-rule
conformance, `security-reviewer` for security defects. They run **at the same
time**, and you merge what they return into one report. You do not review the
code yourself — you adjudicate what they send back.

## 1. Fix the scope before dispatching

Both subagents must review exactly the same thing, or the merged report is
incoherent. Resolve the target once, here, and pass the identical string to both.

- If `$ARGUMENTS` is non-empty, that is the target — a path, a PR number, a
  branch, or a ref.
- If `$ARGUMENTS` is empty, the target is the working tree: `git diff` **and**
  untracked files from `git status --porcelain`. Say so explicitly, because a
  bare `git diff` silently shows nothing for a file that was never added — and
  untracked files are exactly where new work lives.

Do not fall back to "review the whole repo" when the target is empty. A review
with no scope returns a pile of pre-existing observations and no signal about
the change. If the scope genuinely cannot be determined, ask the user and stop.

Note for the report: `tests/`, `.claude/agents/`, and `.claude/commands/` are
currently untracked in this repo, so a working-tree review will include them.

## 2. Dispatch both, in parallel

Issue **both** Agent tool calls in a **single message** — that is what makes
them concurrent. Do not launch one, wait, then launch the other; the whole point
of this command is that the two reviews overlap.

Both briefs are self-contained. Each subagent starts fresh with no memory of
this conversation, so include:

- The exact scope string from step 1, and the command to see it.
- That the other reviewer is running concurrently, so it should stay in its own
  lane: `code-reviewer` does correctness and project rules, `security-reviewer`
  does security. Overlap is merged, not duplicated.
- That `CLAUDE.md` is authoritative and overrides its defaults.
- That it is read-only — report findings, do not edit.

Launch with `subagent_type: code-reviewer` and `subagent_type: security-reviewer`.
Give each a `description` naming its lane, e.g. `Code review: <scope>`.

## 3. Merge

The two reports use the same finding shape and the same severity scale
(Critical / High / Medium / Low), so merging is mechanical:

- **One list, sorted by severity**, most severe first. Keep `file:line` on every
  entry.
- **Collapse duplicates.** If both reviewers found the same defect, merge into
  one entry and tag it — the `Class:` line from the security report is what
  tells you a finding is a security one. A defect found by both is usually the
  most important thing in the report; say so.
- **Resolve severity disagreements upward but visibly.** If they scored the same
  finding differently, take the higher and note the disagreement in one clause.
  Do not silently average it down.
- **Keep the lanes legible.** Tag each entry `[code]` or `[security]`, or `[both]`.
- **Drop the noise.** A finding with no `file:line`, no concrete trigger or
  exploit path, or one of the "do not report these" items in either agent's
  brief (the stub routes, `PLACEHOLDER_EXPENSES`, the dev `SECRET_KEY` fallback
  when untouched) does not belong in the merged report. If you drop something
  that was reported, note it once at the bottom rather than deleting it
  silently — the user should be able to see that a reviewer raised it and you
  judged it out of scope.

## 4. Report

Write the merged report directly in your reply. Do not paste either subagent's
report verbatim, and do not narrate the process — the user wants the findings,
not a transcript.

```markdown
## Review: <scope>

**Verdict:** <merge / merge with fixes / do not merge> — <one line>

**Blocking** — Critical and High only, one line each. If there are none, say
"none" rather than omitting the section.

### Findings

1. `[security]` **[High]** `app.py:298` — <title>
   - **What:** ...
   - **Trigger/Exploit:** ...
   - **Fix:** ...
   - **Confidence:** confirmed | speculative | reviewers disagreed on severity

...

### Coverage

- **Reviewed:** files and diff range, and how to reproduce the scope.
- **Not reviewed:** anything either agent could not reach, plus what you dropped.
- **Confidence in this review:** what the two reports agreed on, and where they
  left gaps — no tests run, no dynamic testing, static reading only.

### Do first

The single change to make first, if only one.
```

Then:

- If there are **no** findings, say so plainly and skip the list. Do not
  manufacture a finding to justify the run.
- **Do not fix anything.** This command reviews; it does not edit. If the user
  wants the fixes applied, that is a follow-up request.
- Close by naming the subagents you used and the scope, so a second run can be
  compared against this one.
