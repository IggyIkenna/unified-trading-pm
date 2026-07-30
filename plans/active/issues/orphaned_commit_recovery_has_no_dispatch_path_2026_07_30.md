---
doc_type: issue
title: >-
  Ten-plus confirmed orphaned/preserved worker commits across four AO issue docs have no dispatch path at all — every
  recovery todo is `[WORKER]`/`[BACKEND/OPERATOR]` inside an `assigned_vm: NA` doc, so none is auto-dispatchable, and
  two of them are on a real GC clock
summary: >-
  Aggregation finding from the `/na-eligibility-audit ao` run (2026-07-30). Four separate `assigned_vm: NA` issue docs
  in the `ao` tranche each independently record confirmed, still-unrecovered committed worker work — orphaned by a
  `branch: Reset to origin/live-defi-rollout` (root-caused to `quickmerge.sh::cascade_dep_branch()`'s `checkout -B`,
  whose preserve-guard has a proven TOCTOU race), stranded off-origin on a dead slot, or successfully quarantined into a
  `refs/wip-preserve/cascade-*` ref that nothing then surfaces or re-applies. Individually each doc is correctly
  classified and correctly NA. Collectively they share ONE unowned root gap that no doc states: **there is no dispatch
  path for cross-slot commit recovery.** Every recovery todo is tagged `[WORKER]` or `[BACKEND/OPERATOR]` and lives in a
  non-dispatched doc; executing one needs read/write access to ANOTHER slot's worktree on `ip-172-31-5-118`, which the
  multi-agent-safety HARD RULE bars; and the main agent is charter-barred from pushing code or editing a foreign
  worktree. So the work cannot reach a worker by any existing route. `branch_reset_to_origin_orphans_unpushed_worker_
  commits_2026_07_27.md` says this outright in its own `⚠️ DISPATCH GAP` banner ("they will rot unless…") and escalated
  it 2026-07-27 — it has now sat unrouted for 3 days. Two of the items have real deadlines, not indefinite ones.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, unified-api-contracts, features-service, strategy-service]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    per-slot-worktrees,
    orphaned-commit,
    wip-preserve,
    data-loss,
    dispatch-gap,
    multi-agent-safety,
    routing,
    big-finding,
  ]
related:
  [
    /plans/active/issues/branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27.md,
    /plans/active/issues/wip_preserve_refs_silently_unrecovered_2026_07_29.md,
    /plans/active/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md,
    /plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md,
    /plans/active/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
priority: P1
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
depends_on: []
source: >-
  /na-eligibility-audit ao run, 2026-07-30 (autonomous). Surfaced by reading all 39 of the tranche's assigned_vm:NA docs
  end to end: four of them independently record unrecovered committed work, and all four are blocked on the same missing
  routing mechanism rather than on any technical question.
---

# Orphaned/preserved commit recovery has no dispatch path

> **This doc adds no new incident.** Every item below is already documented, already root-caused, and already correctly
> classified in its own doc. What is NOT owned anywhere is the shared consequence: none of it can be dispatched, so none
> of it is moving. Filed per the findings-triage HARD RULE (data-loss-class + cross-repo) because the aggregate is
> invisible from any single doc.

## The inventory (each already evidenced in its own doc — not re-derived here)

| Item                                                                           | Repo                     | Owning doc                                                 | State                              |
| ------------------------------------------------------------------------------ | ------------------------ | ---------------------------------------------------------- | ---------------------------------- |
| slot-13 `207afd62` (census-manifest persistence)                               | features-service         | `branch_reset_to_origin_orphans_unpushed_worker_commits`   | orphaned, backstop patch saved     |
| slot-13 `d1c1ad8a` (per-venue accepted-quote extension)                        | features-service         | same                                                       | orphaned, backstop patch saved     |
| slot-9 `724bd9be` (`fix(registry)` VENUE_ORDER_SEMANTICS)                      | unified-api-contracts    | same                                                       | orphaned, backstop patch saved     |
| slot-12 `559452e` (`/api/backlog/{id}/reconcile-brief` route + 240-line test)  | agent-orchestrator       | same                                                       | orphaned, backstop patch saved     |
| `refs/wip-preserve/cascade-strategy-service-a77eb6d170ca` (staging-lock-check) | strategy-service         | `wip_preserve_refs_silently_unrecovered`                   | preserved, unrecovered since 07-28 |
| slot-6 `44de0cf0` + `11ed7f09` (GMX cassette cleanup)                          | unified-api-contracts    | `idle_slot_dirty_wip_never_auto_resolves`                  | **dangling objects, GC-eligible**  |
| slot-10 `4d235caf` (3 dead-script deletions)                                   | market-tick-data-service | same                                                       | 1 ahead / 1 behind                 |
| slot-11 8 unpushed `docs(plans):` commits (top `c6610a36c`)                    | unified-trading-pm       | same                                                       | 8 ahead / 1 behind                 |
| slot-3 features-service WIP (19 files, 722+/714-)                              | features-service         | same                                                       | dirty, unowned                     |
| slot-16 / slot-10 / slot-5 stranded ahead-commits                              | agent-orchestrator, PM   | `killed_slot_orphans_committed_unpushed_work_no_push_path` | ahead/diverged, off-origin         |

## Why none of it moves (the actual finding)

Three independent blocks, all structural, none technical:

1. **Every recovery todo lives in an `assigned_vm: NA` doc**, so the backlog regenerator never derives a task from it.
   `branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27.md`'s own banner states the consequence and the
   three ways out verbatim: "(a) migrated into a dispatched plan (`assigned_vm: planning`), (b) a worker is explicitly
   routed to them, or (c) main is authorized to run the quickmerge recovery directly… **Escalated to operator for
   routing.**" That escalation is 3 days old.
2. **Execution needs foreign-worktree access.** Recovery means cherry-picking from `.tabs/<n>/<repo>`'s reflog (or
   applying a host-local `.orch-orphan-commits-recovery/*.patch`) belonging to a DIFFERENT slot. CLAUDE.md's
   multi-agent-safety block bars exactly this ("Never edit unfamiliar/untracked/recently-pushed files… a dirty file you
   don't own"), and the rule is right — the liveness gate cannot be evaluated safely from another slot.
3. **The main agent is charter-barred** from pushing code and from editing a foreign worktree, which every one of these
   docs records independently. So the one actor with fleet-wide visibility is the one actor that cannot act.

The net is a closed loop: the docs are correctly NA, the todos are correctly tagged, the safety rule is correctly
enforced — and the work is correctly stuck.

## Why it is time-sensitive (two real clocks, not indefinite)

- **slot-6's `44de0cf0`/`11ed7f09` are DANGLING objects**, not branch-reachable — subject to `gc.pruneExpire` (git
  default ~2 weeks). Recorded orphaned 2026-07-25, so the practical deadline is **~2026-08-08**. Low content value (dead
  GMX fixtures) but a genuine deadline, and a legitimate decline-to-recover is fine IF recorded before GC makes the
  choice silently.
- **The reflog-only orphans** (`207afd62`, `d1c1ad8a`, `724bd9be`, `559452e`) sit under the 90-day reflog default, so
  ~2026-10-25 — comfortable, but only while those slot clones are never re-created. A `setup-tab-worktrees.sh` re-clone
  or a disk action ends it immediately, and this fleet has already had one disk resize (2026-07-27) in this window.
- `wip-preserve` refs are durable by construction (`git update-ref`, independent of reflog expiry) — those are safe; the
  problem there is purely that nothing surfaces them.

## The one thing that would unblock all of it

A single routing decision, not a design. Options, for an operator ruling:

- [ ] [OPERATOR-DECISION] P1. **Choose the recovery route and record it here.** **(a) [RECOMMENDED]** Authorize a single
      named `infra`-role worker, dispatched ON `ip-172-31-5-118`, to run one bounded recovery sweep across the inventory
      above with an explicit liveness gate per slot (dead/expired `.agent-claim` → recover; live claim or mtime <120s →
      PROTECT and skip), shipping each recovered commit via `quickmerge --agent --files`, and recording a per-item
      recovered / superseded / deliberately-declined verdict. This is the smallest change: it needs no new mechanism, it
      reuses the liveness discriminator the FM8 gate already implements, and one sweep clears the whole backlog of
      items. **(b)** Authorize main to run the quickmerge recovery directly (a charter amendment — narrower in scope but
      changes a standing boundary). **(c)** Migrate the recovery todos into an existing active `assigned_vm: planning`
      plan and let normal dispatch pick them up (works, but each todo still hits the foreign-worktree bar, so it only
      helps if paired with (a)'s liveness-gate carve-out). **(d)** Explicitly write the whole inventory off with a
      recorded rationale — legitimate for the low-value items, and better than silent GC. **Done when**: this todo names
      the chosen route and each inventory row above reaches a recorded terminal verdict.

## Follow-ups that are NOT this doc's scope

The prevention side is already owned and should not be duplicated here:
`/plans/active/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` item 8 owns the `cascade_dep_branch`
prevention-vs-preserve fix (its item 7 proved the current preserve-guard has an inherent TOCTOU race), and
`/plans/active/issues/wip_preserve_refs_silently_unrecovered_2026_07_29.md`'s `[SCRIPT] P3` owns the
`refs/wip-preserve/**` surfacing sweep. This doc is only about routing the ALREADY-orphaned backlog.

## Progress Log

- **2026-07-30** (`/na-eligibility-audit ao`, autonomous): Filed. Not a new incident — an aggregation across four
  `assigned_vm: NA` docs read end to end during the tranche's first-ever NA-eligibility pass. Each doc's own
  classification was left unchanged (all four verdicted KEEP-NA, correctly); this doc exists because the shared blocker
  — no dispatch path — is invisible from any one of them and had no owner. No commits were touched, no worktree was
  inspected, and no recovery was attempted by this run: every route requires the authority ruling above.
