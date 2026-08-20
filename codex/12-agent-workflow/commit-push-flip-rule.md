---
doc_type: codex-ssot
title: Commit + Push + Flip Plan Checkboxes As You Ship Each Item — HARD RULE
summary:
  SSOT for the Commit + Push + Flip HARD RULE — every shippable unit is committed locally (pre-commit git diff --cached
  --stat with no path arg, stage by name) AND its plan checkbox flipped in the SAME agent turn; SHIP (quickmerge/push)
  defaults to instruction-completion, not per-subtask (2026-08-20 ruling), except a shared AO plan's actively-dispatched
  items which still ship+flip per-item since other slots rely on the pushed flip as the done-signal. Covers the halves
  model (3 universal halves + a conditional Half-4 for human-fleet-registered operators), the ship-cadence ruling + why
  it's safe (AO never discards ahead-of-origin commits), the violations list, and the backfill recovery protocol.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, quickmerge, orchestrator, verification, scripts]
related:
  [
    /codex/12-agent-workflow/canonical-plan-flow.md,
    /codex/11-project-management/active-plan-inventory-tracker.md,
    plans/PLAN_FORMAT.md,
  ]
created: 2026-05-23
authoritative_for: [commit-push-flip plan-checkbox same-turn discipline]
referenced_by: [/codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md]
owner:
last_reviewed: 2026-08-20
code_refs:
---

# Commit + Push + Flip Plan Checkboxes As You Ship Each Item — HARD RULE

> **CLAUDE.md anchor**: "Commit + Push + Flip Plan Checkboxes As You Ship Each Item (HARD RULE)".
>
> **The #1 source of wasted reallocation + false-progress reporting.** Repeated violation observed 2026-05-14/15: slots
> 5+7 each shipped 15+ items without flipping work-split checkboxes; daily analysis reported ~14% progress when actual
> was ~70%. **Half-1 without Half-2 in the same agent turn is a rule violation — NOT "I'll do it later".**

## Ship Cadence — Instruction-Level, Not Per-Subtask (2026-08-20 ruling)

**Default**: when a given instruction decomposes into N related sub-tasks, do all N before running `quickmerge.sh` —
ONE ship at the end, not N separate quickmerges. Assume every instruction runs to its actual end unless told
otherwise; finishing sub-task 3 of 20 is not a stopping point, and it is not a shipping point either.

**Commit still happens per shippable unit, constantly — that part is unchanged.** Local commits are the safety net:
cheap, frequent, and lossless to hold unshipped, because `WorkerLivenessWatchdog._sweep_unpushed_slots()`
(`agent-orchestrator/server/worker_liveness_watchdog.py:947,1952`) sweeps every VM-side worktree BEFORE any kill or
respawn decision and either pushes ahead-of-origin commits once a `.qg_last_passed_sha` sentinel proves they passed
QG, or preserves the tip on a `refs/heads/wip-preserve/orchestrator-slot-<N>-<sha>` ref
(`_ahead_push.py:push_or_preserve_ahead_commits`, called from the same sweep) — it never `git reset --hard`s local
history out from under a respawned worker. Full mechanism: [`orchestrator-safety-mechanisms.md`
§F](orchestrator-safety-mechanisms.md#f-ahead-of-origin-committed-work-preservation-shipped-2026-08-16). On a laptop
`.tabs/N` session a human operator is present and decides when to close a tab, so the unattended-loss risk this
mechanism guards against is mainly the VM-side case — but "commit often, ship once" applies everywhere, because the
motivating complaint here is churn (20 quickmerges cluttering history for 20 sub-tasks of one instruction), not loss.

**Why this changes "ship at every shippable unit"**: the old per-item ship cadence existed to solve ORCHESTRATOR
VISIBILITY, not loss-prevention — an unshipped, unflipped plan item is invisible to other slots' reallocation logic
and risks silent re-dispatch + duplicated work (see the 2026-05-14/15 incident below, the reason Half-2 exists at
all). That risk is real only when other dispatched slots are actively reading the same work-split table. It does not
apply to an operator's direct instruction handled end-to-end by one session with no other slot watching its
intermediate state, and it is not a data-loss argument — data loss is independently covered by the AO sweep above.

**Exception — a shared AO plan's actively-dispatched items still ship + flip per-item**: if the work is drawn from a
plan's work-split table that other dispatched slots are currently reading, each item still ships and flips its
checkbox immediately — the pushed flip IS the done-signal other slots rely on to avoid re-dispatching it. This
exception does NOT apply to a single given instruction worked end-to-end by one session/slot with nothing else
depending on its intermediate state — that case uses the instruction-level default above.

## The Halves

### Half 1 — Commit Per Unit, Ship at Instruction-Completion

**Commit = the safety net, ship = the done-signal.** Commit at every shippable unit (constant cadence — see "Ship
Cadence" above); push/quickmerge once the whole given instruction is done, NOT per-hour, NOT per-subtask — unless the
AO shared-plan-item exception above applies, in which case ship+flip stays per-item.

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

**The first 3 halves compose**: Half-1 alone = "shipped but invisible"; Half-1+2 alone = "shipped + visible, missing
context for next agent"; Half-1+2+3 = full handoff. Half-3 matters when item is non-final; Half-2 ALWAYS matters when
item is final. **Half-4 is a separate, conditional layer** (human-fleet-registered operators only, see below) that
composes on TOP of a completed Half-1+2, not instead of it.

### Half 4 — Human-Fleet-Registered Operators Report to AO (ao_human_fleet_integration_2026_08_15.md, Phase 6)

Applies ONLY to an operator whose laptop is a registered human-fleet slot (`~/.config/agent-orchestrator/
human-fleet-token` exists — Phase 4; dormant for most sessions today, live for Ikenna's slot 9001 as of 2026-08-16).
Once registered, Half-2's checkbox flip is followed by reporting completion to AO the same way an AO-dispatched
worker's own `/done` call does:

```
AO_SLOT_ID=<slot_id> bash scripts/human_fleet/ao-done.sh <task_id> <sha> "<evidence>"
```

**Only when a task is actually AO-claimed** (`ao-claim.sh`) — most human work is plan-authoring or ad-hoc, never
AO-claimed, and Half-4 is a no-op for it; forcing a report with no real `task_id` is worse than skipping it.
**Mechanically nudged, not enforced**: a `PostToolUse` hook
(`agent-orchestrator/scripts/human_fleet/post_plan_commit_hook.py`, wired in `cursor-configs/settings.json`) detects a
landed `unified-trading-pm` doc-push that flipped a checkbox, checks whether the registered slot has a currently-claimed
task, and SUGGESTS the `ao-done.sh` call — deliberately confirm-first (per the plan's own resolved design question),
never auto-fires it. Token/spend counts are NOT part of Half-4 — those flow through the pre-existing Phase 2
`ao-usage-push.py` path regardless of Half-4, on a completely separate cadence.

## Rule Violations (review-blocking; agent should self-correct)

**Scope**: these violations are about the AO shared-plan-item exception (other slots actively reading the work-split
table) — that is the scenario "flip late" actually damages. They are not an argument against the instruction-level
ship-cadence default above; shipping once at instruction-completion with no other slot watching is not a violation.

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

- `/codex/12-agent-workflow/canonical-plan-flow.md` — orchestrator dispatch mechanics
- `/codex/11-project-management/active-plan-inventory-tracker.md` — dashboard reporting based on checkbox state
- `plans/PLAN_FORMAT.md` — checkbox syntax requirements
