---
description: Generate or run Spendly pytest tests via the test-generator and test-runner subagents
argument-hint: "generate <what to cover> | run [pytest target] | both <what to cover>"
allowed-tools: Agent, Task
---

One entry point for the two Spendly test subagents. Parse $ARGUMENTS, then
dispatch to the right one.

## Parse the arguments

Split $ARGUMENTS on the first word — that is the action, and everything after
it is the target:

| Action | Subagent | Example |
|---|---|---|
| `generate` (`gen`, `g`) | `test-generator` | `/test-agent generate login route` |
| `run` (`r`) | `test-runner` | `/test-agent run tests/test_app.py` |
| `both` (`all`) | `test-generator`, then `test-runner` | `/test-agent both database/db.py helpers` |

If $ARGUMENTS is empty, or the first word is not one of the above, ask the user
which action they want and what the target is. Do not guess — dispatching to the
wrong subagent writes or runs the wrong thing.

## `generate`

Launch the Agent tool with `subagent_type: test-generator`, and give it a
self-contained brief:

- The target from the arguments.
- Any existing files under `tests/` it should extend rather than duplicate.
- A reminder that it authors tests only and must not run pytest.

## `run`

Launch the Agent tool with `subagent_type: test-runner`. Tell it the exact pytest
target from the arguments, or that the target is the full suite if none was
given. Remind it that it is read-only: it reports failures, it does not fix them.

## `both`

Run the two subagents in sequence, never in parallel — the run has to observe
the tests the generator just wrote. Launch `test-generator` first, wait for it to
return, then launch `test-runner`. If the generator reported that it wrote no
tests, say so and skip the run rather than reporting an unchanged suite as a
pass.

## Report back

Summarise for the user; do not paste either subagent's report back verbatim.

For a generation: files created, tests added, units now covered, and anything the
generator flagged as a possible bug.

For a run: the command that ran, passed / failed / errored totals, each failure
with its likely cause, and whether the fault looks like the test or like the
application code.

If there are failures, do not fix them unless the user asks.
