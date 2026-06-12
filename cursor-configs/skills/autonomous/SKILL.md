---
name: autonomous
description: >-
  Run the task to completion under the workspace autonomous-agent rules, driving it on a self-paced loop until a
  verified done-state. Trigger when the user ends a prompt with `/autonomous` (or types `/autonomous`), or says some
  version of "finish this completely while I'm away, don't ask me, I want a working <thing> when I'm back." This is the
  finish-line contract (no DEFERRED / BLOCKED-OPERATOR leftovers) + the loop mechanism that keeps you going instead of
  stopping at "done, what's next?".
---

# /autonomous — finish to DONE, on a loop

`/autonomous` means: **apply the autonomous-agent completion contract, and drive the task to completion on a loop.** It
composes two existing pieces of this workspace — do not reinvent them, read them:

1. **`cursor-configs/AUTONOMOUS_AGENT_RULES.md`** — the COMPLETION contract (the _whether_): finish completely with no
   `DEFERRED`/`BLOCKED-OPERATOR` leftovers, full chicken-and-egg authority, reconcile-everything-down-here, journal to
   the plan across context compression, parallelize with sub-agents, end with a report. **Rule 12 is the loop.**
2. **`cursor-configs/SUB_AGENT_MANDATORY_RULES.md`** — the safety FLOOR (the _how_): the workspace's hard rules. Paste
   it at the top of every sub-agent you spawn.

## On invocation

1. **Read both files above** (and the plan-of-record / source plans / `issues/` docs / codex SSOTs the task names — they
   are your documented record of intent for every decision you'll make alone). If rules injection into a sub-agent
   fails, that sub-agent MUST NOT proceed.
2. **Self-check the model tier** (CLAUDE.md § Model Tier Selection) — a long autonomous loop on a cross-repo dispatch is
   usually `opus-required`; flag a mismatch, don't silently run Sonnet on opus-required work.
3. **Run it to the end** (rule 12a). `/autonomous` means _drive to completion_ — keep going until the success criteria
   are met, never stop at the first natural break. The loop is the driver that keeps you picking up your own next
   unfinished item; arm it and keep going. (The only judgment is _cadence_, not _whether_: a genuinely short job may
   finish in one pass before the first tick fires — fine — but the default posture is "keep going to done.")

## Arming the loop (rule 12b)

Use the `/loop` skill mechanics — a background sentinel loop with `notify_on_output`, or `ScheduleWakeup`:

- **Self-paced (default):** after each tick, choose the next wake by what you're waiting on — an **event** (CI /
  backtest / PR reaching a terminal state → arm a watcher that wakes you when it fires) or a **time** (lean long for
  idle ticks).
- **Fixed interval** (e.g. `15m`) only when polling a steady external cadence.
- **Run the task once immediately** after arming, so the first tick is genuine progress, not startup.

## Each tick — the canonical loop (rule 12c–d)

1. Pick the **next open plan item** (or the next unfinished unit of the dispatch).
2. Implement it → `quality-gates.sh`-green (QG-sweep batch) → `quickmerge --agent --files '<paths>'`.
3. **Flip the plan checkbox in the same turn** (Commit+Push+Flip) → `docs(plans):` flip + push.
4. **Journal to the plan's Progress Log** (rule 6) — this _is_ the "handoff document". **Never** create a `*_HANDOFF.md`
   / `*_SUMMARY.md` / status file (no-summary-docs rule). Assume context is compressed between ticks; the log must let a
   compressed future-you resume losslessly.
5. When a whole plan's items are done → **thorough audit/analysis of what actually shipped** (rule 9 + Post-Plan-Phase
   Codex Audit) → push.

## Stop conditions (rule 12e–g)

- **Terminate when success criteria are met:** kill the loop/sleeper PID, write the rule-9 final report. A loop without
  a termination condition is a bug.
- **Stall-safety:** a progress metric must _climb_ across ticks (items flipped, plans done, rows backfilled, runs
  green). A **flat** metric = **STOP and diagnose** (`gh run view --log-failed`) — never burn ticks repeating a failing
  action.
- **Spec-change mid-loop:** a clarification within documented intent → make it, log it, keep going. A scope/spec change
  that **contradicts** the documented record of intent → take the least-bad path and document it; never quietly redefine
  the dispatch on a tick.
- **Inherits every safety rule:** hard-stops still hard-stop (live wallet keys, `1.0.0` graduation); kill-switch
  autonomy stays protective-only; ship discipline stays canonical. The loop is throttle, not bypass.
- **On operator "stop":** kill the loop/sleeper PID **immediately** and don't re-arm.
