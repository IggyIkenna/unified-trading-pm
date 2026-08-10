---
doc_type: issue
title:
  A plan's single dispatched slot held by a non-completable "monitoring-only" waiter permanently starves a
  higher-priority, zero-blocker, same-plan task — and this failure class generates no page (no BLK entry, no escalation
  wall_type) because neither side ever calls /blocked
summary: >-
  Concrete motivating incident (fully resolved via a `docs(plans):` issue-doc todo, not a code fix — this doc tracks the
  underlying mechanism gap that incident exposed): `cefi_content_migration_fleet_half_incomplete_2026_07_26.md`'s `-002`
  (a P2 "monitor the relaunched fleet, re-verify corpus-wide + delete the script once 44/44 shards complete" todo) was
  dispatched to slot 15 at `2026-07-30T12:16:10Z` and held that plan's one in-flight slot continuously for 4h20m+ with
  nothing to show but repeated "fleet stable at N shards" progress pings (context climbing to 99%/18 compactions) —
  while `-006` (the P1 root-cause leak-investigation todo, priority 20, the TOP of the queue, zero blockers) sat
  `queued` the entire time, never dispatched, per this plan's one-task-per-plan-doc dispatch behavior. `-002` cannot
  ever complete without `-006`'s fix landing first (the fleet keeps shrinking via OOM/freeze deaths, per
  RB-INFRA-RELAUNCH's `≤2 relaunches/(vm-prefix,day)` bound already exhausted for every surviving shard) — so this was a
  PERMANENT structural deadlock, not a transient wait. Neither task-holder ever called `/api/slots/<N>/blocked`
  (correctly — from each worker's own local view, neither was facing a genuine ambiguous judgment call: `-002`'s worker
  was doing exactly its assigned monitoring job, `-006` was simply never dispatched so had no session to notice
  anything). The review agent (agt-f99b61, slot 1, corroborating a prior review session's finding relayed by main agent
  agt-fd75de) live-reverified the deadlock via `GET /api/backlog` + `GET /api/state` and landed a `- [ ] [OPERATOR] P0`
  todo directly in the migration issue doc (`unified-trading-pm@7753422c1`) as the ONLY escalation surface either agent
  could find — `/api/escalate` is PR/CI-shaped (`repo`+`pr_number` required, `X-Orchestrator-Secret`-gated for GitHub
  Actions callers) and does not fit a backlog-dispatch deadlock; no generic "page the operator" tool exists in either
  the review or main agent's surface. This doc tracks that gap: **a whole class of real, permanent dispatch-level
  problems — priority inversion / same-plan slot starvation by a non-completable waiter — is invisible to every paging
  mechanism the fleet has**, because the only two page-triggering paths today are (a) a worker explicitly calling
  `/blocked` (doesn't fire here — neither side perceives itself as blocked-on-a-judgment-call) and (b) the PR/CI-shaped
  `wall_type` escalation system (`escalation.py::escalate()`, `EscalateRequest` requires `repo`+ `pr_number`,
  structurally can't represent "task A vs task B priority ordering within a plan"). Without operator visibility, this
  class of deadlock persists until a human happens to read the plan/backlog directly.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    alerting,
    escalation,
    dispatch,
    priority-inversion,
    starvation,
    deadlock,
    observability,
    paging-gap,
  ]
related:
  [
    /plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md,
    /plans/archive/issues/escalation_backlog_repo_collision_blind_spot_2026_07_25.md,
    /plans/archive/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-07-30
author: unknown
priority: P2
parent_epic: orchestrator_master
source:
  "review agent (agt-f99b61, slot 1), 2026-07-30, following up on main agent (agt-fd75de)'s ruling that the
  cefi_content_migration_fleet_half_incomplete -006/-002 dispatch deadlock is a real alerting gap distinct from the
  migration issue doc itself"
assigned_vm: NA
execution_scope: local-only
estimate_class: design
drift_direction: advance-code
depends_on: []
resolved_by:
archive_exempt: true # archival routed through ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md's [REVIEW] P0 todo, not standalone (see na-eligibility-audit 2026-08-01 entry)
locked_by:
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md,
    agent-orchestrator/server/dispatch_priority_inversion_watchdog.py,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md,
  ]
---

# AO dispatch priority-inversion / plan-slot starvation has no page path

## What I found

See summary above for the full motivating incident. The structural gap, stated precisely: the orchestrator's
one-task-per-plan-doc-in-flight dispatch model (observed behavior: `cefi_content_migration_fleet_half_incomplete`'s
backlog never had more than one of its own tasks in `dispatched`/`working` state at a time even though `-006` had zero
`prereqs` and outranked `-002` on priority) has no corresponding WATCHDOG — nothing periodically asks "has the task
currently holding this plan's slot been dispatched for an abnormally long time while a higher-priority, zero-blocker
sibling task in the same plan sits queued?" The two existing alert paths both miss this by construction:

- **`/api/slots/<N>/blocked`** — opt-in, worker-initiated. Fires only when a worker itself recognizes it's facing an
  unresolvable judgment call. A worker correctly executing an open-ended "monitor until X completes" todo has no reason
  to ever call this — it isn't blocked, it's working exactly as assigned; the problem is external (a sibling task can't
  get a turn), not something the worker itself can observe or fix.
- **`/api/escalate` (`EscalateRequest`)** — requires `repo` + `pr_number`, authenticated via `X-Orchestrator-Secret` for
  GitHub Actions callers (`server/escalation.py`). Every existing `wall_type` (`merge_conflict`, `sit_failure`,
  `ldr_qg_failure`, `plan_health`, `data_pipeline_failure`, etc.) models a PR-or-CI-shaped event. None model "task A
  (priority P, ready) is being starved by task B (priority P', dispatched, same plan, no forward-progress signal)" —
  there is no `repo`/`pr_number` to hang this on; it's a pure backlog-dispatch-state condition.

## Why it matters

This is a real, currently-demonstrated failure class, not a hypothetical: it ran undetected for 4h20m+ in the cefi
migration plan, discovered only because a review agent happened to read `/api/backlog` + `/api/state` directly while
following up on an unrelated queued chat message. Absent that coincidence, this deadlock would have persisted
indefinitely — `-002`'s worker has no way to know it's stuck (its job genuinely is open-ended monitoring), and `-006`
never gets a session to report anything is wrong (it's never dispatched). Any future plan with a similar shape (a
"monitor until upstream condition X" todo sharing a plan with a higher-priority "fix X" todo) will silently reproduce
this, each time invisible until someone reads the backlog by hand.

## Recommended decision

- [x] [BACKEND] P2. Add a periodic dispatcher-side check (the natural home is alongside the existing
      `dispatch.py`/`regen_backlog_from_plan.py` tick logic, or a new lightweight watchdog pass) that detects: a task
      `T_low` is `dispatched`/`working` and has held its plan's single in-flight slot for longer than a threshold (e.g.
      2h, tunable), AND a sibling task `T_high` in the SAME `plan_ref` has strictly higher priority (lower number),
      `status=queued`, and zero unmet `prereqs`/blockers. On detection, fire a page through the EXISTING
      escalation/alert channel (reuse `escalation.py`'s wall_type mechanism — add a new
      `wall_type=dispatch_priority_inversion`, or route directly to the `agent-orchestrator-alerts` Slack channel per
      `/codex/04-architecture/agent-orchestrator-alerting.md`'s actionable-only convention) rather than requiring a
      human to read the backlog directly. Dedupe by `(plan_ref, T_high.id)` state-transition (fire once, re-fire only if
      it recurs after resolution), matching this doc's sibling alerting docs' cooldown/dedup convention. **Done when**:
      replaying this exact incident's recorded state (`-002` dispatched to slot 15 since `12:16:10Z`, `-006`
      queued/priority-20/zero-blockers the whole time) against the new check produces a fired page, verified via a
      unit/integration test that constructs the equivalent backlog state and asserts the alert fires — not just a manual
      demonstration. **Evidence (2026-08-01)**: shipped `agent-orchestrator@af98fcd` — chose the direct-Slack route
      (this doc's own analysis above already showed `escalation.py`'s `wall_type` mechanism can't represent a pure
      backlog-dispatch- state condition; no `repo`/`pr_number` to hang a wall on). New standalone
      `DispatchPriorityInversionWatchdog` (`agent-orchestrator/server/dispatch_priority_inversion_watchdog.py`, wired
      into `server.py` startup/shutdown), two Slack notify functions (`notify_dispatch_priority_inversion`/`_resolved`),
      keyed `(plan_ref, T_high.id)` seen-set dedup (`dedup_state.dispatch_priority_inversion_alerted_path()`), two
      tunable knobs (`tuning.dispatch_priority_inversion_{interval,threshold}_seconds`, defaults 300s/7200s). Full
      `quality-gates.sh` green. Test
      `tests/test_dispatch_priority_inversion_watchdog.py::test_tick_once_fires_a_page_replaying_the_recorded_incident`
      replays this doc's exact recorded incident (`-002`-equivalent dispatched since `12:16:10Z`, `-006`-equivalent
      queued/priority-20/zero-blockers, `now` = dispatch+4h20m) through `tick_once()` end-to-end and asserts
      `notify_dispatch_priority_inversion` fires exactly once — not a manual demonstration — plus 16 further unit tests
      on the pure detection logic and the dedup/resolve transitions.
- [x] [SCRIPT] P3. Once the above ships, backfill a check against TODAY's live backlog for any OTHER plan currently
      exhibiting this same shape (a same-plan higher-priority queued/ready task behind a long-dispatched lower-priority
      one) — this incident may not be the only live instance, just the one a human happened to notice. **Evidence
      (2026-08-01)**: ran the backfill-check via `check-ao-backlog-status.sh`'s read-only SSM path plus a one-off
      read-only `/api/backlog` query (fleet-wide, 1188 total tasks). At check time (~08:2x UTC) exactly 6 tasks were
      `dispatched`/`working`; for EACH, no sibling task in the SAME `plan_ref` was `queued` with a strictly lower
      `priority` number — **no other plan is currently exhibiting the priority-inversion/starvation shape**. Two of the
      six had held their slot >2h (`mtds_available_at_cross_asset_backfill-006` at 8.53h,
      `cefi_content_migration_fleet_half_incomplete-010` at 5.15h — the latter is this doc's OWN motivating plan, now on
      a different, already-resolved todo) but neither has a ready higher-priority sibling, so correctly not a breach —
      just ordinary long-running work.

## Progress Log

- 2026-07-30 (review agent `agt-f99b61`, slot 1): filed after main agent (`agt-fd75de`) confirmed the cefi migration
  `-006`/`-002` deadlock had been fully surfaced through every existing fleet channel (worker `/blocked` doesn't apply,
  `/api/escalate` doesn't fit, the `[OPERATOR]` issue-doc todo in the migration doc itself is the only lever either
  agent could pull) and asked for this gap to be tracked as its own follow-up, distinct from the migration doc and the
  unrelated gcloud-identity-poisoning doc. `assigned_vm: NA` chosen to match the closest sibling doc's convention
  (`escalation_backlog_repo_collision_blind_spot_2026_07_25.md`, another AO-dispatch-mechanism structural gap) — a
  change to the orchestrator's own paging logic is a design call worth a human decision on approach, even though the
  eventual code change is bounded.
- 2026-08-01: both recommended-decision todos shipped as todo 2 of
  `/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md` (`agent-orchestrator@af98fcd`) — see that todo's
  evidence line and this doc's own updated checkboxes above for the full detail (watchdog design, test proving the
  replayed incident pages, and the clean live-backlog backfill-check result). Both items now `[x]`.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): ARCHIVE-eligible (0 open
  todos, no prose-only remaining work) — **not archived independently.**
  `ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md` (active `assigned_vm: planning`) carries its own
  `[REVIEW] P0` todo explicitly naming this doc for the standard 6-step archival ritual once its extraction is
  reconciled back. Archiving it here would duplicate that already-queued AO work. `assigned_vm` left as-is (`NA` —
  archival-pending status, not a dispatch-eligibility question).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`, dispatch agt-da0e58, slot 10): re-verified, no change —
  still 0 open todos, `archive_exempt: true` still accurate (archival still routes through
  `ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md`'s `[REVIEW] P0` todo, not standalone). The only file change
  since the 2026-08-01 verdict was an unrelated corpus-wide reference-path fix (`unified-trading-pm@17b53df1e`) — no
  content drift.
- **context-scout 2026-08-03**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **context-scout 2026-08-03 (re-pass, updated methodology)**: re-verified, unchanged (4 entries) — doc has 0 open todos
  and `archive_exempt: true` (archival routes via `ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md`); this list
  stays useful for whoever executes that archival.
- **na-eligibility-audit 2026-08-04** (autonomous, tranche `ao`): KEEP-NA, re-verified — citation still real
  (`ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md` confirmed `status: active`, `assigned_vm: planning`, and
  still names this doc in its `[REVIEW] P0` archival todo). Not archived independently, per the established ruling.
  Cross-validated: today's same-day sibling `/ag-closeout-audit ao` batch6 run reached the identical conclusion
  independently ("already the named archival target of batch3_finalize's own gated todos").
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **context-scout 2026-08-07**: populated/refreshed context_scope (4 entries) — swapped the generic
  `agent-orchestrator-single-vm-architecture.md` codex pointer for
  `/plans/active/ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md`, the doc that actually explains why this
  0-open-todo, `archive_exempt: true` doc still exists (its `[REVIEW] P0` todo is the one that will eventually archive
  it) — the single most decision-relevant pointer for a future toucher, still not previously in the list.

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 0 open todos, `archive_exempt: true` re-confirmed accurate
  (archival still routes through `ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md`'s `[REVIEW] P0` todo, not
  standalone); citation re-checked and real.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — 0 open todos,
  `archive_exempt: true`. Independently re-verified the routing plan
  (`ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md`) still carries its own open `[REVIEW] P0` archival todo
  naming this doc — routing still valid, not stale. Consistent with 6+ prior markers.
