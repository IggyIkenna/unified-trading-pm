---
doc_type: plan
title: AO satellite AO batch 2 — the two Deferred items whose gate cleared during batch 1's finalize pass
summary: >-
  SECOND AO-dispatch batch for the `ao` topic tranche, produced during
  `ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`'s todo 3 (re-check every Deferred item's gate). Of the 9
  items batch 1 explicitly named as Deferred, most are still genuinely gated (operator design decisions, file collisions
  with other active docs, or already resolved independent of this tranche) — full per-item disposition is recorded in
  the finalize plan's own todo 3 evidence, not duplicated here. Exactly 2 items had BOTH their stated gate clear AND a
  zero-hit file-collision check against the whole `plans/active` corpus: the failover release-signal item and the
  periodic dirty-resolution sweep. This batch is deliberately small — a proper conflict-check discipline found only 2
  items safe to dispatch, not a larger set.
status: draft
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-2, satellite-docs]
related:
  [
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md,
    /plans/active/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 0.48
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md todo 3 (Deferred-gate re-check), 2026-08-01 — full disposition
  of all 9 named Deferred items + 2 bonus finds recorded in that finalize plan's own evidence; these are the only 2 that
  cleared BOTH their stated gate and a fresh file-collision check.
---

# AO satellite AO batch 2

> **`status: draft` — NOT ingested, NOT dispatched.** Flipping this to `active` is the operator's call, per the same
> pattern batch 1 used (`/plans/PLAN_FORMAT.md`; CLAUDE.md § "Plan destination — ASK BEFORE CREATING").

## Why this plan exists (and why it's only 2 todos)

`ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s Deferred sections named 9 items to re-check once batch 1 landed
(finalize todo 3). Re-checking each one's ACTUAL current gate (not the 2026-07-31 banner alone) found: 1 item already
fully resolved independent of this tranche (AutoSpawn gap — remove from consideration entirely), 1 item's governance
gate cleared but a NEW file-collision surfaced with 2 other active docs on the same file (`/done`-semantics pair — still
held), 2 items whose core blocker is a genuine unresolved operator design decision (`_ahead_push` retry semantics; the
QG-harness worktree-isolation items), and 3 items unchanged from their original still-valid disposition (regen
positional-task-id and `slack-read-channel.py` — dispatch directly at their own source docs, not batch material;
QG-harness — needs its own scoped plan). Only these 2 cleared both their stated gate AND a fresh file-collision check
against the whole `plans/active` corpus. Full disposition for all 9 (+2 bonus finds) is in
`ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`'s own todo 3 evidence — not duplicated here.

## Rules for every worker on this plan

- Both todos below target disjoint files — no `sequential` gate needed.
- **Do not edit the source issue doc's checkboxes** beyond appending your evidence line to the todo you executed,
  mirroring batch 1's own convention.

## Todos

- [ ] [BACKEND] P2. **Before re-dispatching a `failover_allowed` task off an apparently-silent owner, require a positive
      release signal** (lease expiry with a liveness re-check, e.g. `kill -0` the owner's worker PID, or an explicit
      owner-side release) rather than ping-staleness alone — a long `quality-gates.sh` run must not look like death. The
      doc's own investigation did not conclusively pin down the single call site (checked
      `server/stale_dispatch.py::reclaim_stale_dispatches`, ruled out with caveats) — confirm the actual re-dispatch
      call path first before implementing. **Done when**: a worker that goes silent for a full QG run (>~4min) but is
      provably alive (PID up, forward progress in its pane/log) does NOT have its in-flight task re-dispatched, with a
      test simulating a silent-but-alive owner. Source:
      `/plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` (BACKEND P2 — its P3
      sibling, the `/done` idempotency item, is NOT in scope here; still file-collision-held, see this batch's source
      finalize plan).
- [ ] [BACKEND] P2. **Add a periodic dirty-resolution sweep that does not depend on a spawn attempt, then extend it to
      catch orphaned committed-but-unpushed commits too.** Reuse the existing `resolve_dirty_state` /
      `commit_and_push_dirty_repos` plus the FM8 liveness discriminator (dead or expired `.agent-claim` → inherit +
      commit; live claim or mtime <120s → PROTECT), driven from a periodic tick against slots that are dirty AND
      provably dead (no live tmux session). Then extend the same sweep to detect local commits not on origin before
      realigning a dead slot's worktree, preserving them to a `wip-preserve/` ref rather than orphaning them. **Done
      when**: a deliberately-idle dirty slot with no tmux and an expired claim is inherited within one sweep interval
      (evidenced by an activity-log event), AND a dead slot with a local commit ahead of origin gets that commit
      preserved to a ref (not orphaned) when its worktree is realigned. Source:
      `/plans/active/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md` (BACKEND P2 ×2 — both todos, since
      the second explicitly extends the first).

## Codex SSOTs (read before starting a todo)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`, `/codex/05-infrastructure/per-tab-worktrees.md`.

## Progress Log

- **2026-08-01** — Authored during `ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`'s todo 3 (Deferred-gate
  re-check). Both todos independently confirmed: their originally-stated gate cleared, AND a fresh
  `grep -rl <target-file> plans/active/*.md plans/active/issues/*.md` conflict-check (excluding their own source doc and
  the batch1/finalize plans) returned zero competing open todos. Left `status: draft` deliberately — flipping to
  `active` is the operator's call.
