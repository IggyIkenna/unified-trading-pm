---
doc_type: plan
title: AO satellite AO batch 4 — the Deferred item whose gate cleared during batch 1's finalize pass
summary: >-
  FOURTH AO-dispatch batch for the `ao` topic tranche, produced during
  `ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`'s todo 3 (re-check every Deferred item's gate). Of the 9
  items batch 1 explicitly named as Deferred, most are still genuinely gated (operator design decisions, file collisions
  with other active docs, or already resolved independent of this tranche) — full per-item disposition is recorded in
  the finalize plan's own todo 3 evidence, not duplicated here. Originally drafted with 2 todos (this doc was
  misnumbered "batch 2" at authoring time, colliding with the pre-existing, already-active
  `ao_satellite_ao_dispatch_batch2_2026_07_30.md` — corrected 2026-08-01, renumbered to batch 4 since batches 2 and 3
  already existed). One of the 2 original todos (the periodic dirty-resolution sweep) was found MOOT before dispatch —
  already shipped 2026-07-24 by `ao_remediation_b_code_chain_2026_07_23`, predating this doc's own drafting by a week;
  see `/plans/archive/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md` for full evidence. This batch now
  carries the one remaining genuine item: the failover release-signal fix.
status: complete
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-4, satellite-docs]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md,
    /plans/archive/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md,
    /plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.32
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md todo 3 (Deferred-gate re-check), 2026-08-01 — full disposition
  of all 9 named Deferred items + 2 bonus finds recorded in that finalize plan's own evidence; this is the one item that
  cleared both its stated gate and a fresh file-collision check (a sibling item was drafted alongside it but turned out
  moot — see summary).
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md,
    /plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md,
    agent-orchestrator/server/worker_liveness_watchdog.py,
  ]
---

# AO satellite AO batch 4

> **🔴 ARCHIVED 2026-08-06 — COMPLETE (all todos `[x]`, unlocked).** Archival ritual finished by `/plan-reconcile ao`:
> the file-move to `plans/archive/2026_08/` and the corpus-wide referrer repoint had already been done, but the
> `status:` flip (`active` → `complete`) and this banner — steps 2 and 6 of the 6-step ritual
> (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — were never applied, leaving a
> physically-archived doc still declaring itself active. Its gated successor is
> `/plans/active/ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md`.

> **Renamed from "batch 2" 2026-08-01** — this doc was originally authored as
> `ao_satellite_ao_dispatch_batch2_2026_08_01.md`, colliding with the pre-existing, already-active
> `ao_satellite_ao_dispatch_batch2_2026_07_30.md`. Batches 2 and 3 already existed by creation date, so this is
> renumbered batch 4. Operator-approved 2026-08-01 — flipped `status: draft` → `active`.

## Why this plan exists (and why it's down to 1 todo)

`ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s Deferred sections named 9 items to re-check once batch 1 landed
(finalize todo 3). Re-checking each one's ACTUAL current gate (not the 2026-07-31 banner alone) found: 1 item already
fully resolved independent of this tranche (AutoSpawn gap — remove from consideration entirely), 1 item's governance
gate cleared but a NEW file-collision surfaced with 2 other active docs on the same file (`/done`-semantics pair — still
held), 2 items whose core blocker is a genuine unresolved operator design decision (`_ahead_push` retry semantics; the
QG-harness worktree-isolation items), and 3 items unchanged from their original still-valid disposition (regen
positional-task-id and `slack-read-channel.py` — dispatch directly at their own source docs, not batch material;
QG-harness — needs its own scoped plan). 2 items cleared both their stated gate AND a fresh file-collision check against
the whole `plans/active` corpus — but a direct code read (2026-08-01, before dispatch) found one of those two, the
periodic dirty-resolution sweep, was already shipped 2026-07-24 (`agent-orchestrator@de44b255f` +
`agent-orchestrator@8aaf928a0`, `ao_remediation_b_code_chain_2026_07_23` items 7+9) — a full week before this batch was
even drafted. Three separate audit passes (na-eligibility-audit 2026-07-30, plan-reduction-marathon 2026-07-30, and this
batch's own drafting 2026-08-01) had all re-confirmed the source doc as open without checking the code; see
`/plans/archive/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md` for the full correction. Dropped from this
batch — nothing to dispatch for it. Full disposition for all 9 original Deferred items (+2 bonus finds) is in
`ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`'s own todo 3 evidence — not duplicated here.

## Rules for every worker on this plan

- **File-adjacency caution (not a hard collision, but real)**: this batch's sole todo and
  `ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s todo 2 (dispatcher-side priority-inversion watchdog) both plausibly
  land in `agent-orchestrator/server/worker_liveness_watchdog.py` / its `_tick_once()` orchestration method (that file
  already houses every periodic watchdog sub-sweep — `_sweep_dirty_slots`, `_sweep_unpushed_slots`,
  `_release_prereq_blocked_slots`, etc. — the natural home for both a new watchdog pass and a fix to the existing
  reclaim path). **Do not start this todo concurrently with batch 3's todo 2** — land batch 3's todo 2 first, then pick
  this one up against the resulting `_tick_once()` state.
- Do not edit the source issue doc's checkboxes beyond appending your evidence line to the todo you executed, mirroring
  batch 1's own convention.

## Todos

- [x] [BACKEND] P2. **Before re-dispatching a `failover_allowed` task off an apparently-silent owner, require a positive
      release signal** (lease expiry with a liveness re-check, e.g. `kill -0` the owner's worker PID, or an explicit
      owner-side release) rather than ping-staleness alone — a long `quality-gates.sh` run must not look like death. The
      doc's own investigation did not conclusively pin down the single call site (checked
      `server/stale_dispatch.py::reclaim_stale_dispatches`, ruled out with caveats — that reconciler only fires for
      slots with `tmux_session IS NULL` + a `slot_resume_pending` anchor, i.e. genuinely torn-down workers, not a
      silent-but-alive one) — confirm the actual re-dispatch call path first before implementing (check `dispatch.py`'s
      R5 dead-slot-spill path, referenced in `worker_liveness_watchdog.py`'s `_sweep_dirty_slots` docstring as sharing
      the same "slot has gone quiet" notion). **Done when**: a worker that goes silent for a full QG run (>~4min) but is
      provably alive (PID up, forward progress in its pane/log) does NOT have its in-flight task re-dispatched, with a
      test simulating a silent-but-alive owner. Source:
      `/plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` (BACKEND P2 — its P3
      sibling, the `/done` idempotency item, is NOT in scope here; still file-collision-held, see this batch's source
      finalize plan). — **Shipped `agent-orchestrator@7911083`.** Confirmed root cause by direct code read (not the
      dispatch.py R5 path alone — that's the SECOND stage): `WorkerLivenessWatchdog._reconcile_unacked_dispatches`
      (`server/worker_liveness_watchdog.py:963`) released a `dispatched` task past `dispatch_ack_timeout_seconds`
      (1800s) back to `queued` (clearing the owning slot's `current_task`) whenever a SINGLE pane-classify snapshot
      didn't read `"working"` — never checking real process liveness. Once `queued` + pinned
      (`target_slot`+`affinity=high`), `dispatch.py`'s R5 `_target_slot_is_dead()` (`high_affinity_spill_after_seconds`
      = 600s, a SHORTER ping-silence threshold than the 1800s that just fired) immediately read the same slot as "dead"
      and let ANY other slot's `pick_next_task` claim the task — while the true owner's tmux pane was still alive,
      unaware. This is the exact two-stage mechanism behind both recorded incidents. Fix:
      `_reconcile_unacked_dispatches` now requires `_pane_is_dead(sess)` (the SAME discriminator `_sweep_dirty_slots`
      already uses, no new liveness logic) before releasing — a session that exists and isn't pane-dead keeps its lease
      regardless of the pane-classify read. Proven by 3 new tests against the REAL call path in
      `tests/test_worker_liveness_watchdog.py`: `test_reconcile_unacked_silent_but_alive_owner_keeps_lease` (replays
      incident 1's shape, deployment_api_sigabrt_crash_loop-001 slots 2&8 — confirmed to FAIL pre-fix with the exact
      `"...requeued (pinned)"` warning, PASS post-fix), `test_reconcile_unacked_dead_owner_still_released` (regression
      guard on incident 2's shape, sports_satellite_ao_dispatch_batch2-001 slots 4&11 — a genuinely-dead pane still
      releases), `test_reconcile_unacked_no_session_still_released` (the pre-existing no-session branch is untouched).
      All 3 pass; full repo `quality-gates.sh` green (2215 passed, 2 skipped, basedpyright 0 errors).

## Dropped — found moot before dispatch

- ~~Add a periodic dirty-resolution sweep + extend it to catch orphaned committed-but-unpushed commits~~ — **MOOT**,
  already shipped 2026-07-24. See `/plans/archive/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md` for full
  evidence (`agent-orchestrator@de44b255f` + `agent-orchestrator@8aaf928a0`).

## Codex SSOTs (read before starting a todo)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`, `/codex/05-infrastructure/per-tab-worktrees.md`.

## Progress Log

- **2026-08-01** — Authored during `ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`'s todo 3 (Deferred-gate
  re-check), originally as "batch 2" with 2 todos. Both todos independently confirmed: their originally-stated gate
  cleared, AND a fresh `grep -rl <target-file> plans/active/*.md plans/active/issues/*.md` conflict-check (excluding
  their own source doc and the batch1/finalize plans) returned zero competing open todos. Left `status: draft`
  deliberately — flipping to `active` is the operator's call.
- **2026-08-01 (same day, before dispatch)** — Operator caught the "batch 2" naming collision against the pre-existing
  `ao_satellite_ao_dispatch_batch2_2026_07_30.md`; renamed to batch 4 (title/H1/frontmatter/filename), drafted the
  missing paired `batch4_finalize` plan, and fixed every corpus referrer. A direct code read (triggered by the
  operator's go-ahead to start work) found the dirty-resolution-sweep todo was already fully shipped a week before this
  batch was drafted — dropped, evidence in the source issue doc (now archived). Also found this batch's remaining todo
  shares a file-adjacency risk with `batch3_2026_07_31.md`'s todo 2 — documented as a sequencing rule above rather than
  a hard `depends_on` (cross-plan per-todo gates aren't expressible in this corpus's frontmatter; sequencing is enforced
  by execution order, not the schema). Operator approved starting work — flipped `status: draft` → `active`.
- **context-scout 2026-08-01**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-03**: refreshed context_scope (3 entries, trimmed from 6) — the sole todo is already `[x]`
  shipped, so scope now points only at the finalize sibling (the active remaining work), the source issue doc, and the
  real shipped fix location (`worker_liveness_watchdog.py`); dropped the generic architecture SSOTs the closed todo no
  longer needs.
- **2026-08-01 (sole todo shipped)** — Confirmed the true release call path (`_reconcile_unacked_dispatches` →
  `dispatch.py` R5 spill, both ping/pane-snapshot based, no real liveness check) and fixed it to require `_pane_is_dead`
  (existing discriminator, reused) before releasing a task off an apparently-silent owner. `agent-orchestrator@7911083`.
  3 new tests added, all pass; full evidence + root-cause detail on the todo line above and reconciled into the source
  issue doc's own `[BACKEND] P2` item. Every todo in this plan is now done — this plan is ready for archival per the
  plan-completion-and-archival-discipline SSOT (deferred to the paired `batch4_finalize` plan / operator's archival
  pass, per this batch's own convention).
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): confirmed
  ARCHIVE-eligible (0 open todos, no prose-only remaining work). **Not archived independently** —
  `ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md` (active `assigned_vm: planning`) carries its own `[INFRA] P0`
  todo owning "run the 6-step archival ritual on the batch plan itself," exactly matching this batch's own stated
  convention above. Archiving here would duplicate that already-queued AO work. `assigned_vm` unaffected — this is a
  `plan` doc's own archival-pending state, not a reclassification question (it was NA/local-only by this tranche's
  established convention from inception, per the frontmatter note the 2026-08-01 batch-1 classification pass already
  recorded).

- **na-eligibility-audit 2026-08-06**: ARCHIVE — 0 open todos — sole todo shipped agent-orchestrator@7911083 (failover
  release-signal fix + 3 tests). locked_by empty. Paired finalize plan (assigned_vm: planning) owns the full archival
  ritual. Archived 2026-08-06.
