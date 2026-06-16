---
scope: [engineer, admin]
---

# Commit + Push + Flip Plan Checkboxes As You Ship Each Item — HARD RULE

> **CLAUDE.md anchor**: "Commit + Push + Flip Plan Checkboxes As You Ship Each Item (HARD RULE)".
>
> **The #1 source of wasted reallocation + false-progress reporting.** Repeated violation observed 2026-05-14/15: slots
> 5+7 each shipped 15+ items without flipping work-split checkboxes; daily analysis reported ~14% progress when actual
> was ~70%. **Half-1 without Half-2 in the same agent turn is a rule violation — NOT "I'll do it later".**

## The Three Halves

### Half 1 — Commit + Push at Every Shippable Unit

**Pushed = real.** Per-shippable-unit cadence, NOT per-hour, NOT per-session.

Pre-commit check (MANDATORY — catches accidental bundling):

```bash
git status && git diff --cached --stat   # NO PATH ARGUMENT — see entire index
```

If anything not yours: `git restore --staged <file>` before commit.

**Foot-gun #4** (prek auto-restore): bundle Edit→stage→commit→push into ONE Bash call. `--no-verify` IS authorized when
auto-restore symptoms observed (diagnostic: "Restored working tree changes from .../prek/patches/" in output). Stage
explicitly by name; never `git add .` / `-A`.

### Half 2 — Flip the Checkbox IN THE SAME AGENT TURN as Half-1 (the most-violated half)

**"Same logical unit"** = the next Bash invocation after the code push, in the same agent turn, before starting any new
item. NOT next session. NOT end of day. NOT "when I remember". If you committed code at 14:32 and the flip commit lands
at 17:50, you violated this rule for 3h18m.

**The compliance pattern (memorize)**:

```bash
# Step 1: ship code
cd <service-repo> && git add <my-files> && git commit -m "feat: ..." && git push origin HEAD:live-defi-rollout
SHA=$(git rev-parse --short HEAD)

# Step 2: IMMEDIATELY flip the plan checkbox (next Bash call, same turn)
cd ${WORKSPACE_ROOT}/unified-trading-pm
# Edit work_split or plan-of-record:
#   N. [item description]
# becomes
#   N. ✅ [item description] — <repo>@<SHA> + brief evidence
git add plans/active/<plan>.md
git commit -m "docs(plans): flip item N — <one-line evidence>" && git push origin HEAD:live-defi-rollout
```

**`docs(plans):` prefix is MANDATORY** for flip commits (`plan(...)` is rejected by the conventional-commits hook).

**Self-check before starting the NEXT item** (MANDATORY):

```bash
git log --oneline -5
# Expected: alternating "feat/fix/refactor: ..." and "docs(plans): flip ..." commits.
# Two consecutive code commits with no docs(plans) flip in between → STOP, flip before next item.
```

### Half 3 — Session-end Deferred-work Scoreboard

Multi-item sessions with non-final state → `## Deferred work after <date> <session-tag>` table in plan body before
`## Temporary states`.

**The 3 halves compose**: Half-1 alone = "shipped but invisible"; Half-1+2 alone = "shipped + visible, missing context
for next agent"; Half-1+2+3 = full handoff. Half-3 matters when item is non-final; Half-2 ALWAYS matters when item is
final.

## Rule Violations (review-blocking; agent should self-correct)

- ❌ "I'll flip at end of session" — other slots are reading the work-split RIGHT NOW for reallocation.
- ❌ "One batch flip commit at the end" — the next reallocation sweep may re-dispatch items 3+4 during the gap.
- ❌ "The code is on LDR, the flip is bookkeeping" — a flipped checkbox is the ORCHESTRATOR'S done-signal. Without it,
  the item is functionally unfinished from dispatch's view.
- ❌ "I forgot which item this commit closed" — you committed too many items in one push. Split next commit per
  shippable unit.
- ❌ Plan-flip commit lands hours/days after code commit — window is the SAME AGENT TURN.

## Recovery Protocol

**If you find unflipped items** (during recovery / audit / reassignment):

1. STOP picking up new work.
2. Walk your tab branch's git log since last known flip; for each code commit that closed an item, flip its checkbox
   with `- [x] ✅ ... — <repo>@<sha> (backfilled <date>)`.
3. Ship as one `docs(plans): backfill plan-flips for items X/Y/Z — <repos>@<shas>` commit. Push.
4. THEN resume normal work.

## Why This is THE Wasted-Reallocation Source

Orchestrator reallocates based on work-split table state. Unflipped item → orchestrator may re-dispatch to another slot.
Other slot reads the plan, doesn't see the LDR code (it reads the checkbox, not a workspace grep), and re-implements.
Net: wasted slot-hours + merge conflicts.

**Reference 2026-05-14/15 incident**: slots 5+7 each shipped 15+ items without Half-2. Three slots looked idle in
dashboard view when they were the workspace's top performers — operator nearly reallocated load away from them. Backfill
operation required to repair.

## Composes With

- `codex/12-agent-workflow/daily-work-split-process.md` — orchestrator dispatch mechanics
- `codex/11-project-management/active-plan-inventory-tracker.md` — dashboard reporting based on checkbox state
- `plans/PLAN_FORMAT.md` — checkbox syntax requirements
