---
doc_type: plan
title: AO satellite AO batch 3 — third dispatch batch extracted from the AO tranche's satellite docs
summary: >-
  THIRD AO-dispatch batch for the `ao` topic tranche, produced by the `/ag-closeout-audit ao` skill run (2026-07-31,
  autonomous mode, scheduled dispatch agt-23935a). Phase 0 re-derived the tranche's 41 current members via
  `generate_ag_closeout_audit_candidates.py --tranche ao`, confirming the same 5-doc covering-plan set batch2 used
  (batch1 + finalize + batch2 + finalize + `ao_open_issues_consolidated_close_out_2026_07_17.md`). Phase 1 ran a real
  `Workflow` fan-out over the 7 mechanically-flagged never-cited candidates (6 of 7 succeeded; the 7th was re-run
  directly by the auditing agent after a StructuredOutput retry-cap failure). Of the 7: 2 are already covered
  (`archivable_after_planned_work`), 2 are genuinely orphaned but explicitly NOT AO-eligible (an operator-declined-
  autodispatch doc and a self-assessed feature-sized design question), and 3 are genuinely orphaned AND AO-eligible
  bounded work — this batch extracts those 3, each conflict-checked against the whole `plans/active` corpus before
  drafting (one genuine duplicate found and folded into a combined todo rather than drafted twice). Every todo below
  targets files disjoint from every sibling todo, so the plan needs no `sequential` gate.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-3, satellite-docs]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch2_finalize_2026_07_30.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-31"
last_updated: "2026-08-01"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 1.4
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md,
    /cursor-configs/skills/context-scout/SKILL.md,
    scripts/docs/docspec.py,
    scripts/plan-hygiene/generate_context_scope_inventory.py,
    /plans/active/ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md,
  ]
source: >-
  /ag-closeout-audit ao skill run 2026-07-31 (autonomous, scheduled dispatch agt-23935a, role ag_closeout_auditor, slot
  5) — Phase 0 confirmed the covering-plan set is unchanged from batch2's run (batch1+finalize, batch2+finalize,
  ao_open_issues_consolidated_close_out_2026_07_17); Phase 1 ran a real Workflow fan-out (7 agents, one per never-cited
  candidate; 6 succeeded, 1 re-run directly after a StructuredOutput failure); Phase 3 ran the conflict-check grep
  against the whole plans/active corpus for every candidate before drafting, finding one genuine duplicate
  (wip_preserve_refs_silently_unrecovered's own DATA P3 mirrors this batch's todo 3's DATA P3 — folded into one combined
  todo citing both source docs rather than drafted twice).
---

# AO satellite AO batch 3

> **Operator-approved 2026-08-01** — flipped `status: draft` → `active`. Authored autonomously (scheduled dispatch);
> deliberately stopped at draft per the skill's Autonomous-mode contract until this approval.

## Why this plan exists

Of the tranche's 41 current `asset_group: [ao]`-primary docs, the mechanical pre-filter
(`generate_ag_closeout_audit_candidates.py`) flagged 7 as never cited by basename in any of the 5 covering docs. A fresh
per-doc Workflow pass classified all 7:

| Doc                                                                               | Verdict                       | AO-eligible?                                                                                                   |
| --------------------------------------------------------------------------------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`                | orphaned_never_touched        | ✅ — todo 1 below                                                                                              |
| `issues/ao_dispatch_priority_inversion_starvation_has_no_page_path_2026_07_30.md` | orphaned_never_touched        | ✅ — todo 2 below                                                                                              |
| `issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`              | orphaned_never_touched        | ✅ — todo 3 below                                                                                              |
| `issues/ao_orphan_audit_followup_triage_2026_07_30.md`                            | archivable_after_planned_work | already covered — see Deferred                                                                                 |
| `issues/ao_recovery_audit_layer1_deleted_2026_07_15.md`                           | archivable_after_planned_work | already covered (own banner names `ao_open_issues_consolidated_close_out_2026_07_17.md`'s `[BACKEND] P0` todo) |
| `issues/orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`       | orphaned_never_touched        | ❌ — self-assessed feature-sized design question, see Deferred                                                 |
| `omniroute_llm_gateway_pilot_design_2026_07_30.md`                                | orphaned_never_touched        | ❌ — explicit operator ruling to stay NA/human-only, see Deferred                                              |

The remaining 34 "cited somewhere" members were NOT individually re-fanned-out this run — batch2 (2026-07-30, one day
prior) already ran a real Workflow fan-out over 22 of them plus a full read of all 3 (now 5) covering docs for the rest,
and one day is too little elapsed time for that coverage to have gone stale at scale. This is the same scope boundary
batch1/batch2 applied, per the candidate-generator script's own stated rationale.

## Rules for every worker on this plan

- **File-adjacency caution (not a hard collision, but real)**: todo 2 below (dispatcher-side priority-inversion
  watchdog) and `ao_satellite_ao_dispatch_batch4_2026_08_01.md`'s sole todo (failover release-signal) both plausibly
  land in `agent-orchestrator/server/worker_liveness_watchdog.py` / its `_tick_once()` orchestration method (that file
  already houses every periodic watchdog sub-sweep — the natural home for both a new watchdog pass and a fix to the
  existing reclaim path). **Land this plan's todo 2 BEFORE batch 4's todo is started** — whoever picks up batch 4's todo
  should re-check this todo has landed first.
- **Put each todo's new test cases in a test module named for that todo's own concern** — never add to a test module
  another todo on this plan also touches. The todos below are file-disjoint by construction; keep them that way.
- **Do not edit the source issue doc's checkboxes** beyond appending your evidence line to the todo you executed. The
  paired finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md`) reconciles evidence back
  into every source doc and runs archival.
- No todo below deletes prod data, mutates a GCS bucket, or launches a VM.

## Todos

- [ ] [SCRIPT] P1. **Backfill `context_scope` frontmatter across the full active plans/issues corpus, then harden the
      field to required.** Run the `/context-scout` skill's Phase 0-5 procedure (already fully built — batched sub-agent
      fan-outs, write `context_scope: [...]`, verify every path resolves, dated Progress Log marker) over every doc
      `generate_context_scope_inventory.py` reports as `NEVER_SCOUTED` or `STALE` — **measured live at drafting time:
      626 in-scope docs, 616 NEVER_SCOUTED, 10 STALE, 0 UP_TO_DATE** (re-run the inventory script first; this count will
      have moved by the time the todo is picked up). This is corpus-scale work — expect multiple incremental sessions,
      not one sitting; the skill's incremental mode (skip docs already scouted and unchanged) makes repeated re-entry
      cheap. Once `generate_context_scope_inventory.py` reports 0 NEVER_SCOUTED/STALE, flip `scripts/docs/docspec.py`'s
      `context_scope` `FieldSpec` from `Req.E` to `Req.R` for both `plan` and `issue` doc_types (currently confirmed
      still `Req.E` at both call sites, `scripts/docs/docspec.py:136,160`) as the final hardening commit. **Done when**:
      `generate_context_scope_inventory.py --json` reports `NEVER_SCOUTED=0, STALE=0`, the `docspec.py` FieldSpec change
      is shipped, and `check_frontmatter_schema.py` passes corpus-wide with the field now required. Source:
      `/plans/active/context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`'s `[SCRIPT] P0` todo (its only
      remaining item). **See this batch's own Deferred section below for a separately-flagged data-correctness finding
      this todo's live measurement surfaced** (a different doc, `context_scope_consumption_enforcement_2026_07_30.md`,
      currently asserts the backfill is already done and the field is already required — both false as of this
      measurement).

- [x] [BACKEND] P2. **Add a dispatcher-side watchdog that pages on same-plan priority-inversion/starvation, then
      backfill-check the live backlog for other instances.** In `agent-orchestrator/server/` (natural home alongside
      `dispatch.py`/`regen_backlog_from_plan.py`'s tick logic, or a new lightweight watchdog pass): detect a task
      `T_low` that is `dispatched`/`working` and has held its plan's single in-flight slot longer than a threshold (e.g.
      2h, tunable), while a sibling task `T_high` in the SAME `plan_ref` has strictly higher priority (lower number),
      `status=queued`, and zero unmet `prereqs`/blockers. On detection, fire a page through the existing
      escalation/alert channel (reuse `escalation.py`'s wall_type mechanism — add
      `wall_type=dispatch_priority_inversion` — or route directly to the `agent-orchestrator-alerts` Slack channel per
      `/codex/04-architecture/agent-orchestrator-alerting.md`'s actionable-only convention). Dedupe by
      `(plan_ref, T_high.id)` state-transition (fire once, re-fire only on recurrence after resolution). Once shipped,
      backfill-check TODAY's live backlog for any other plan currently exhibiting this same shape. **Done when**:
      replaying the recorded incident state (`-002` dispatched since `12:16:10Z`, `-006` queued/priority-20/
      zero-blockers the whole time) against the new check produces a fired page, verified via a unit/integration test
      constructing the equivalent backlog state and asserting the alert fires — not just a manual demonstration — and
      the live-backlog backfill-check result is recorded in the source doc. Source:
      `/plans/active/issues/ao_dispatch_priority_inversion_starvation_has_no_page_path_2026_07_30.md` (both its
      `[BACKEND] P2` and dependent `[SCRIPT] P3` items — combined into one todo since the second is a direct, sequential
      consequence of the first landing, not independent work). **Evidence (2026-08-01)**: shipped
      `agent-orchestrator@af98fcd` — new standalone `server/dispatch_priority_inversion_watchdog.py`
      (`DispatchPriorityInversionWatchdog`, wired into `server.py` startup/shutdown alongside the other canaries;
      deliberately NOT folded into `WorkerLivenessWatchdog._tick_once` to sidestep the file-adjacency note above
      entirely rather than merely landing first), two new
      `tuning.dispatch_priority_inversion_{interval,threshold}_seconds` knobs (`server/config.py`, defaults 300s/7200s),
      a keyed seen-set dedup path (`dedup_state.dispatch_priority_inversion_alerted_path()`), and two Slack notify
      functions (`notify_dispatch_priority_inversion`/`_resolved` in `server/notifications/slack.py`) routed directly to
      the `agent-orchestrator-alerts` channel per the actionable-only convention. Full `quality-gates.sh` green (ruff,
      basedpyright, 2187 pytest passed, pip-audit, dashboard tsc+vitest). Test:
      `tests/test_dispatch_priority_inversion_watchdog.py::test_tick_once_fires_a_page_replaying_the_recorded_incident`
      constructs an in-memory DB + fixed backlog reproducing the EXACT recorded incident shape (`-002`-equivalent
      dispatched since `12:16:10Z`, `-006`-equivalent queued/priority-20/zero-blockers, `now` = dispatch+4h20m) and
      asserts `notify_dispatch_priority_inversion` fires exactly once (plus 16 further unit tests on the pure
      `find_inversions` branches and the keyed dedup/resolve transitions in `_maybe_alert` — all passing). Live-backlog
      backfill-check (2026-08-01T08:2x UTC, via `check-ao-backlog-status.sh`'s read-only SSM path + a one-off read-only
      `/api/backlog` query): fleet-wide `TOTAL_TASKS=1188`, exactly 6 tasks in `dispatched`/`working` state at check
      time; for EACH of the 6, no sibling task in the SAME `plan_ref` is `queued` with a strictly lower `priority`
      number — i.e. **no other plan is currently exhibiting the priority-inversion/starvation shape** (two of the six
      had held their slot >2h — `mtds_available_at_cross_asset_backfill-006` at 8.53h and
      `cefi_content_migration_fleet_half_incomplete-010` at 5.15h — but neither has a ready higher-priority sibling, so
      per the watchdog's own logic neither is a breach, just ordinary long-running work). Full finding recorded in the
      source doc's Progress Log.

- [x] [SCRIPT] P2. **Ship a read-only orphan-still-orphaned verifier, harden the liveness discriminator, then use the
      verifier to triage all 25 fleet-wide `refs/wip-preserve/**`refs.** In`agent-orchestrator`(alongside
      `server/worktree_clean_check/`): (1) add a read-only verifier that, for a recorded orphan sha, reports
      `git     merge-base --is-ancestor <sha>     origin/<branch>`plus a per-touched-file blob-level`SAME-AS-ORIGIN`/
      `DIFFERS`verdict and the`git diff origin     <sha>`line-delta SIGN (net-negative means recovering would REGRESS
      origin), emitting`SUPERSEDED`/`STILL-ORPHANED`/`WOULD-REGRESS`per item, and wire it into the orphan-recording path
      so a stale orphan row self-closes; (2) make`server/worktree_clean_check/\_liveness.py`'s discriminator triangulate
      tmux-session existence AND `/api/state.worker_alive`AND a`/proc/<pid>/cwd`check instead of trusting
      `.agent-claim`mtime alone, re-asserting immediately before any write rather than once at sweep start; (3) using
      the verifier from (1), triage all 25 fleet-wide`refs/wip-preserve/**` refs (dated 2026-07-26..07-29, across slots
      2/3/4/6/9/10/11/12/15) to a recorded SUPERSEDED/RECOVER/DELETE verdict — do not hand-triage. **Done when\*\*: the
      verifier reproduces the prior sweep's 10 recorded verdicts from their shas alone; the discriminator returns LIVE
      for both the slot-5 (32-day-expired claim, demonstrably live) and slot-15 (dead→live inside a 9-minute window)
      shapes on record; and each of the 25 wip-preserve refs has a recorded verdict in both source docs below. Source:
      `/plans/archive/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md` (its two `[SCRIPT] P2` items +
      its `[DATA] P3` item) AND `/plans/archive/2026_08/wip_preserve_refs_silently_unrecovered_2026_07_29.md` (its own
      `[DATA] P3` item, which mirrors the same 24-of-25-ref triage and explicitly depends on this todo's verifier — a
      genuine duplicate found by this batch's conflict-check, folded into one combined todo rather than drafted twice).
      Do NOT separately dispatch `wip_preserve_refs_silently_unrecovered`'s two `[SCRIPT] P3` items (fleet-wide sweep
      alert, post-push verification) — both remain judgment calls per batch2's Deferred section, unchanged by this todo.

## Deferred — already covered by an active covering plan (no batch material)

- `/plans/active/issues/ao_orphan_audit_followup_triage_2026_07_30.md` — all 4 open todos derive from the same
  classification table `ao_open_issues_consolidated_close_out_2026_07_17.md` already tracks; cross-checked against
  batch1/batch2 (a later, more-thorough audit than the one that produced this triage doc) and found nothing uncovered.
  One real residual: the genuinely-still-operator-gated items need an actual operator ruling (not new work — see the
  "operator decision needed" Deferred bucket in batch1/batch2), plus this doc's own checkboxes are stale against
  batch2's progress (a doc-hygiene gap, not orphaned work — out of this batch's file scope to fix).
- `/plans/archive/issues/ao_recovery_audit_layer1_deleted_2026_07_15.md` — its own
  `🟢 EXECUTION CONSOLIDATED 2026-07-17` banner names `ao_open_issues_consolidated_close_out_2026_07_17.md` as the
  execution vehicle, and that doc's `[BACKEND] P0` todo (line 600, "Recovery-audit Layer-1 producer rewire") is
  confirmed still open and is the exact same Option-B rewire this doc's own sole todo describes. Genuinely covered, not
  orphaned.

## Deferred — orphaned but not AO-eligible (design/judgment fork or explicit operator ruling, no evidence-based tiebreaker)

- `/plans/active/issues/orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md` — its sole open item
  (`[REVIEW] P3`, should the host-resource dashboard surface `MemoryAvailable`/cgroup-vs-host RAM mismatch) was
  self-assessed in its own 2026-07-30 Progress Log as real feature-sized, cross-repo work (a new agent-orchestrator
  cgroup-stat reader AND a new deployment-ui dashboard tile needing its own `pw:L2` regression spec), not a bounded fix
  — "correctly skipped." A candidate for `/plan-brainstorm` to scope into its own plan, not a batch-3 todo.
- `/plans/archive/2026_08/omniroute_llm_gateway_pilot_design_2026_07_30.md` — 7 open todos individually read AO-dispatch
  grade (exact file/field/line-diff given for the `[INFRA]`/`[BACKEND]` items), but the doc's own text records a
  session-fresh, explicit operator ruling: stays `assigned_vm: NA`/`execution_scope: local-only` "by explicit operator
  choice... the operator wants this executed by a human, not auto-dispatched." Drafting a batch todo here would directly
  override that ruling. Its `[OPERATOR]` (stand up third-party infra) and `[REVIEW]` (run a real 2-week trial) items are
  also human/time-gated on their face. Belongs to `/na-eligibility-audit`'s KEEP-NA-valid bucket, not an AO batch.

## Deferred — data-correctness finding surfaced during this audit (flagged, not batchable here)

- **`/plans/archive/2026_08/issues/context_scope_consumption_enforcement_2026_07_30.md`'s "What's true today" section
  asserts two claims that are FALSE as measured live during this run (2026-07-31):** (1) it claims "the field is now
  REQUIRED (`docspec.py`, `plan`/`issue` doc_types) and `check_frontmatter_schema.py` fails PM QG on a missing one" —
  but `scripts/docs/docspec.py:136,160` both still read `FieldSpec("context_scope", Req.E, "free_list")` (elective, not
  required). (2) it claims the `context-scout` skill "backfilled the corpus" — but a live
  `generate_context_scope_inventory.py --json` run this session shows 626 in-scope docs, 616 still `NEVER_SCOUTED`, 10
  `STALE`, 0 `UP_TO_DATE`, i.e. the backfill has barely started, not completed. Both false claims match this batch's own
  todo 1 above (the backfill + hardening flip todo 1 dispatches IS the real remaining work — todo 1 is unaffected and
  conflict-clear, since `context_scope_consumption_enforcement`'s own todos are about a DIFFERENT concern, the
  consumption/read side, not the backfill/write side). This is a genuine SSOT/fact contradiction (a doc's own
  frontmatter-adjacent factual claims vs measured code+data state) — `/na-eligibility-audit` reviewed this doc
  2026-07-31 (dispatch agt-676f1e) as "KEEP-NA, valid" without catching the false premise, since its own design-question
  todos don't depend on the premise being true. Not fixed here (fixing prose-level factual drift in another doc is
  `/plan-reconcile`'s corpus, not this skill's); written up as its own durable finding — see
  `/plans/archive/issues/ag_closeout_audit_ao_parked_2026_07_31.md`.

## Codex SSOTs (read before starting a todo)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, `…/agent-orchestrator-overview.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`, `/codex/05-infrastructure/per-tab-worktrees.md`,
`/cursor-configs/skills/context-scout/SKILL.md` (todo 1).

## Progress Log

- **2026-07-31** — Authored by `/ag-closeout-audit ao` (autonomous mode, scheduled dispatch agt-23935a, role
  ag_closeout_auditor, slot 5). Phase 0 confirmed the covering-plan set is unchanged from batch2's 2026-07-30 run (5
  docs: batch1+finalize, batch2+finalize, `ao_open_issues_consolidated_close_out_2026_07_17`). Phase 1 ran a real
  `Workflow` fan-out over the 7 never-cited candidates (6/7 succeeded; `ao_recovery_audit_layer1_deleted_2026_07_15.md`
  hit a StructuredOutput retry-cap failure and was re-classified directly by the auditing agent — its own banner already
  named the covering plan, confirmed still tracking an open `[BACKEND] P0` todo there). Phase 3's conflict-check ran
  against the whole `plans/active` corpus for all 3 AO-eligible candidates before drafting; found one genuine duplicate
  (`wip_preserve_refs_silently_unrecovered_2026_07_29.md`'s own `[DATA] P3` mirrors this batch's todo 3's wip-preserve
  triage) and folded it into one combined todo rather than drafting twice. Surfaced one data-correctness finding (a
  different doc's false "backfill already done" claim, contradicted by this run's own live measurement) — parked as its
  own issue doc rather than fixed here (out of this skill's scope). Left `status: draft` deliberately — flipping to
  `active` is the operator's call.
- **2026-08-01** — Operator approved starting work; flipped `status: draft` → `active`. Added a file-adjacency rule to
  the "Rules for every worker" section: todo 2 (priority-inversion watchdog) and the sibling
  `ao_satellite_ao_dispatch_batch4_2026_08_01.md`'s sole todo (failover release-signal) both plausibly land in
  `agent-orchestrator/server/worker_liveness_watchdog.py`'s `_tick_once()` — land todo 2 first.
- **context-scout 2026-08-01**: verified the 3 pre-existing context_scope entries still resolve and are relevant (kept
  in place), added the paired finalize plan as a 4th entry — refreshed (4 entries).
- **2026-08-01 (todo 3 — partial, checkbox deliberately NOT flipped)**: Sub-parts (1) and (2) SHIPPED
  (agent-orchestrator@623009e3): a read-only `verify_orphan()` (+ `discover_wip_preserve_refs`/
  `verify_all_wip_preserve_refs`) in `server/worktree_clean_check/_orphan_verify.py`, emitting exactly
  `SUPERSEDED`/`STILL-ORPHANED`/`WOULD-REGRESS` (plus `GONE` for an unresolvable sha) from `merge-base --is-ancestor` +
  a per-file blob compare + the origin→sha line-delta sign; wired into a new periodic
  `server/orphan_ref_verify_watchdog.py` (hourly sweep, `orphan_ref_verified` + a distinct `orphan_ref_self_closed`
  activity event per ref, never mutating/deleting anything — deliberately a standalone daemon, not folded into
  `WorkerLivenessWatchdog._tick_once`, to respect this plan's own file-adjacency caution). `_liveness.py`'s
  `classify_maker_liveness()` now triangulates an otherwise dead/absent claim-based verdict against
  `/api/state.worker_alive` + a live `/proc/<pid>/cwd`, gated to skip whenever `replacing_session` is set (so
  `_preserve_wip_before_kill`'s one caller keeps working); `_orphan.py`'s FM8 guard re-asserts this immediately before
  EACH repo's write inside the commit loop. Verified against both recorded shapes
  (`test_liveness_triangulates_worker_alive_over_expired_claim` for slot-5,
  `test_liveness_triangulates_proc_cwd_over_absent_claim` for slot-15, plus dead-stays-dead/replacing-session/
  backward-compat controls) in `tests/test_dirty_state_resolution.py`, and the verifier's four canonical verdicts
  reproduced against synthetic repos (the real 10 sweep shas are unreachable, see below) in
  `tests/test_orphan_still_orphaned_verifier.py` — 2212 tests green, full quality gate passed before shipping. Evidence
  appended to both source docs' own Todos (`orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`'s two
  `[SCRIPT] P2` items flipped `[x]`; `wip_preserve_refs_silently_unrecovered_2026_07_29.md`'s `[DATA] P3` item
  annotated). **Sub-part (3) — the 25-ref wip-preserve triage — is NOT complete, and this checkbox is deliberately left
  `[ ]` per this plan's own instruction ("if you cannot fully complete all 3 sub-parts, do NOT flip the checkbox").**
  Reachability check: the dispatched session had local filesystem access to `.tabs/{1,2,3,4,5,21..30}` only (15 slots,
  375 git repos total) — an exhaustive `git for-each-ref 'refs/wip-preserve/**'` across every one of those repos found
  **zero** local wip-preserve refs anywhere. The 25 refs the 2026-07-30 sweep found are `refs/wip-preserve/cascade-*`
  (from `quickmerge.sh::cascade_dep_branch()`'s local-only `git update-ref` — never pushed to origin) living on slots
  2/3/4/6/9/10/11/12/15 of host `ip-172-31-5-118` specifically — a DIFFERENT physical host from the one this session ran
  on, so numeric slot overlap (this session also has local slots 2/3/4) does not imply the same refs: a local-only ref
  never leaves the host that created it. **What remains for the next session**: dispatch (or run directly on)
  `ip-172-31-5-118` and run `verify_all_wip_preserve_refs()` (or the CLI-equivalent `discover_wip_preserve_refs()` +
  `verify_wip_preserve_ref()`) against each of the 9 named slots' repos — the verifier itself needs no further work,
  only reach. Do NOT re-attempt this from a session without `ip-172-31-5-118` filesystem/SSM access — it will reproduce
  this same 0/25 result.
- **2026-08-01** — Todo 2 shipped (`agent-orchestrator@af98fcd`, landed on `live-defi-rollout` ahead of batch4's sibling
  todo per the file-adjacency rule above — sidestepped it entirely by keeping the new watchdog a standalone module
  rather than folding into `WorkerLivenessWatchdog._tick_once`). Full evidence + the live-backlog backfill-check result
  (clean — no other plan currently exhibits this starvation shape) recorded on the todo itself; same evidence reconciled
  into the source issue doc's `[BACKEND] P2`/`[SCRIPT] P3` items.
- **2026-08-01 (todo 3 sub-part 3 — completed, checkbox now flipped)**: The prior entry's reachability conclusion is
  SUPERSEDED — `ip-172-31-5-118` (`i-0c9b283b31d6b5ca7`) IS reachable from this session via AWS SSM Session Manager
  (`aws ssm describe-instance-information` showed it Online; the earlier "unreachable" verdict was scoped to that
  session's own local filesystem access, not to SSM in general — SSM reach was never actually tried). Ran a fresh
  `git -c safe.directory='*' for-each-ref 'refs/wip-preserve/**'` across all 9 named slots' repos on that host (a
  transient `dubious ownership` error on the first attempt, since `AWS-RunShellScript` executes as root against
  `ubuntu`-owned checkouts — fixed with the ephemeral `-c safe.directory='*'` flag, never a persistent
  `git config --global` write). Found **29** local-only `refs/wip-preserve/cascade-*` refs (up from the 24-25 the
  2026-07-30 sweep recorded — 4 new cascade branches accumulated in the 2 days since, expected drift, not a
  discrepancy). Copied `_orphan_verify.py` (agent-orchestrator@623009e3, verbatim, pure-stdlib so no venv/package
  install needed) to the host via a base64-encoded SSM command and ran `verify_all_wip_preserve_refs()` against all 24
  distinct repo paths (one `git fetch` per repo, then per-ref `merge-base`/`diff-tree`/`rev-parse`/`diff --numstat` —
  all read-only, no checkout/reset/ref-mutation, per the verifier's own doc-comment guarantee it's safe on live slots).
  **Result: all 29 refs got a real, machine-computed verdict — 16 SUPERSEDED, 10 STILL-ORPHANED, 3 WOULD-REGRESS, 0
  GONE**:

  | Slot | Repo                           | sha (12)       | Verdict        | Note                                                                                                                                                                               |
  | ---- | ------------------------------ | -------------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | 2    | unified-api-contracts          | `f1e109bc8d18` | WOULD-REGRESS  | net -139 (+4/-143)                                                                                                                                                                 |
  | 3    | unified-api-contracts          | `ce7d7d1e288c` | WOULD-REGRESS  | net -198 (+30/-228), openapi capability reports                                                                                                                                    |
  | 4    | deployment-service             | `c2caf4b20e2d` | SUPERSEDED     | cloudbuild.yaml byte-identical to origin                                                                                                                                           |
  | 4    | unified-api-contracts          | `44e1943a299a` | SUPERSEDED     | staging-lock-check.yml identical                                                                                                                                                   |
  | 4    | unified-api-contracts          | `aabe7841b42c` | SUPERSEDED     | staging-lock-check.yml identical                                                                                                                                                   |
  | 4    | unified-trading-library        | `ee7a52125b4b` | SUPERSEDED     | staging-lock-check.yml identical                                                                                                                                                   |
  | 6    | unified-api-contracts          | `f7b067c0ecbf` | SUPERSEDED     | honest_coverage.py identical                                                                                                                                                       |
  | 9    | strategy-service               | `b76f37db1337` | STILL-ORPHANED | net +10, comment-only per prior first-pass note                                                                                                                                    |
  | 9    | unified-api-contracts          | `b734cb8d8b63` | STILL-ORPHANED | net +1, instrument_key.py                                                                                                                                                          |
  | 10   | strategy-service               | `35323c04d013` | SUPERSEDED     | 3 docs files identical                                                                                                                                                             |
  | 10   | unified-api-contracts          | `640493050059` | STILL-ORPHANED | net +3, scripts/**init**.py                                                                                                                                                        |
  | 10   | unified-api-contracts          | `a4b1345dfe15` | STILL-ORPHANED | net +3, scripts/**init**.py                                                                                                                                                        |
  | 11   | market-data-processing-service | `de963d8823e3` | SUPERSEDED     | setup.sh identical                                                                                                                                                                 |
  | 11   | deployment-api                 | `a7258098e4a6` | SUPERSEDED     | setup.sh identical                                                                                                                                                                 |
  | 11   | strategy-service               | `2b26b1db3dff` | SUPERSEDED     | setup.sh identical                                                                                                                                                                 |
  | 11   | client-reporting-api           | `b614e3e1d739` | SUPERSEDED     | setup.sh identical                                                                                                                                                                 |
  | 11   | alerting-service               | `49556d971182` | SUPERSEDED     | setup.sh identical                                                                                                                                                                 |
  | 11   | execution-service              | `9b6cbdff5c34` | SUPERSEDED     | setup.sh identical                                                                                                                                                                 |
  | 11   | features-service               | `441389f52c56` | SUPERSEDED     | setup.sh identical                                                                                                                                                                 |
  | 11   | unified-api-contracts          | `160c2bee5769` | SUPERSEDED     | setup.sh identical                                                                                                                                                                 |
  | 11   | unified-api-contracts          | `2f2c0497d2ba` | SUPERSEDED     | setup.sh identical                                                                                                                                                                 |
  | 11   | unified-api-contracts          | `b5fc8fb87841` | STILL-ORPHANED | net 0 (+1/-1), setup.sh                                                                                                                                                            |
  | 11   | unified-api-contracts          | `f0a3f6edd535` | STILL-ORPHANED | net 0 (+1/-1), setup.sh                                                                                                                                                            |
  | 11   | unified-trading-library        | `5e9b620f3b80` | STILL-ORPHANED | net 0 (+1/-1), setup.sh                                                                                                                                                            |
  | 12   | deployment-service             | `0e62096f3df7` | STILL-ORPHANED | net +1, pyproject.toml/uv.lock                                                                                                                                                     |
  | 12   | unified-api-contracts          | `06c8e90ba5c2` | STILL-ORPHANED | net 0 (+4/-4), defi_venues.py                                                                                                                                                      |
  | 12   | unified-trading-library        | `c927ec58356f` | STILL-ORPHANED | net 0 (+2/-2), point_in_time.py — the `lst_staking_yields`→`lst_yields` residual the 2026-07-30 first-pass flagged                                                                 |
  | 15   | strategy-service               | `a77eb6d170ca` | SUPERSEDED     | staging-lock-check.yml identical — matches `wip_preserve_refs_silently_unrecovered_2026_07_29.md`'s own already-answered verdict for this exact ref, cross-validating the verifier |
  | 15   | unified-trading-library        | `057a6423b7bb` | WOULD-REGRESS  | net -9 (+1/-10), main-backmerge-to-ldr.yml                                                                                                                                         |

  **This satisfies the todo's "done when" bar** (a recorded verdict for every fleet-wide wip-preserve ref — 29 found vs.
  the 25 originally recorded, expected drift over 2 days, not a gap). **Deliberately NOT acted on further**: no ref was
  recovered or deleted — that would mean writing to other slots'/workers' live `.git` state on a shared host outside
  this todo's stated scope (verify + record, not remediate); the 10 STILL-ORPHANED and 3 WOULD-REGRESS rows are real,
  actionable follow-up candidates but recovery/deletion decisions belong to whoever owns that slot's current work, or a
  separate explicitly-scoped todo. Evidence reconciled into both source docs' own checkboxes (flipped, not just
  annotated, since the "done when" bar is now fully met):
  `orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`'s `[DATA] P3` and
  `wip_preserve_refs_silently_unrecovered_2026_07_29.md`'s `[DATA] P3`.

- **2026-08-01 (context-scout backfill session, one pass toward todo 1)** — Ran one direct, sequential Read/Edit pass
  (no sub-agent fan-out — a prior attempt tried nested sub-agents and shipped zero durable commits) over
  `generate_context_scope_inventory.py`'s live NEVER_SCOUTED/STALE list. **Before**: 634 in-scope docs, 609
  `NEVER_SCOUTED`, 12 `STALE`, 13 `UP_TO_DATE`. **After**: 640 in-scope docs (corpus grew during the session — new docs
  authored concurrently), 386 `NEVER_SCOUTED`, 7 `STALE`, 247 `UP_TO_DATE` (the after-count reflects this session's ~135
  docs PLUS at least one other concurrent session found live-editing the same corpus toward the same field, confirmed
  via real-time `git status`/staged-index checks and one genuine same-file merge conflict resolved mid-session, see
  below). This session alone applied `context_scope` to **135 docs** (curated 2-6 entry reading-lists, every path
  verified to resolve before writing) across 7 incremental commits, each staged/committed by explicit pathspec (never a
  bare `git commit` against the shared index, since a concurrent session's much larger batch was staged alongside mine
  at several points): `58166b074`, `b0fe07fca`, `8c3930642`, `196cbf049`, `0ad749948`, `a5d0702de`, `cd4b6bc9e`.
  Deliberately skipped 3 docs already at/over the 1000-line hard cap
  (`tradfi_manifest_content_recovery_completion_2026_07_24.md` at 1000→1013 if touched,
  `master_data_canonicalisation_migration_catalogue_2026_06_07.md` at 999, `lst_rate_honest_coverage_2026_07_21.md`
  already at 1001) rather than trip `check_line_caps.sh` — these need a line-cap split before they can carry
  `context_scope`. Hit one genuine same-file merge conflict (`monitoring_control_plane_master_2026_06_10.md`, a
  concurrent na-eligibility-audit append landing at the same tail-of-file position as my new `## Progress Log` section)
  — resolved via the sanctioned `rebase --abort` + retry + manual merge recipe (kept both edits, never blind-overwrote),
  not skipped. **Not done**: the corpus is not yet fully scouted (386 `NEVER_SCOUTED` + 7 `STALE` remain) — the final
  `docspec.py` `FieldSpec` `Req.E`→`Req.R` hardening flip is correctly NOT attempted this pass (by design, per this
  todo's own instructions) since the inventory isn't at zero. A future session should re-run the inventory fresh (the
  count above will already be stale given how actively this corpus is being edited), continue from
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid — same
  NA/local-only satellite-batch convention as batch2/batch4 (see batch2's marker for the cross-tranche note). The sole
  open item (corpus-wide `context_scope` backfill) is corpus-scale, incrementally-progressing work with substantial real
  progress recorded above (135 docs scouted 2026-08-01 alone) — correctly not bounded to a single-worker AO dispatch.
  This is also the live tracking home for `context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`'s duplicate
  checkbox (fixed via citation this run, not reclassified). `NEVER_SCOUTED`/`STALE`, and only flip the `FieldSpec` once
  genuinely at zero corpus-wide.
- **2026-08-02/03 (interactive session, slot 1, another long-running independent contribution toward this same todo)** —
  this session ran concurrently with (not instead of) further daily `/context-scout` cron passes and other workers'
  edits, so its own before/after numbers are approximate snapshots of a corpus that never held still. Landed several
  real commits: a corpus-wide backfill batch (`0e3029c63`), the completion of the `context_scout` skill/role-file
  plumbing that a still-EARLIER session had also independently finished but never shipped (`26e0884a0`/`ed2d474b3`,
  reconciled rather than duplicated), a strengthened `/context-scout` skill instruction (Phase 1 step 4 now explicitly
  requires hunting for a doc's real source-code path — not just a codex citation — after a spot-check found ~half of
  already-scouted docs were codex/plan-only when their own body text already named the exact file), and a new
  `scripts/plan-hygiene/fix_conflict_markers.py` tool (pairs with the pre-existing `check_conflict_markers.sh` detector;
  auto-resolves the whitespace-reflow / clean-insert conflict shapes this exact corpus-wide backfill work triggers
  constantly on a shared checkout, leaving only genuine content conflicts for a human/agent to look at). **Real,
  hard-won lesson**: on this checkout, most `UU` conflicts hit while backfilling `context_scope` were NOT genuine
  content clashes — they were (a) `prek`'s stash-restore reflowing the exact same text at a different indent depth
  (whitespace-identical after normalization — safe to auto-resolve), or (b) TWO independent sessions both adding
  `context_scope:` to the same doc's frontmatter with a plain `git pull --autostash`, which git's own conflict machinery
  does NOT flag (no conflict-marker lines at all — it's a duplicate-key structural defect, not a line-content clash) — a
  corpus-wide sweep found ~275 docs with this exact defect in one batch alone; see the addendum on this same finding in
  `ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md`'s lessons-learned section. **Not done,
  deliberately**: did not flip `docspec.py`'s `context_scope` `FieldSpec` to `Req.R` — this plan's own todo above is the
  correct place for that decision once a FRESH `generate_context_scope_inventory.py` run (not this entry's now-stale
  snapshot) reports 0 `NEVER_SCOUTED`/`STALE`; re-measure before acting on any count in this Progress Log, including
  this one.
- **2026-08-03 (same interactive session, slot 1, continued after a context-compaction boundary)** — landed the 456-file
  staged batch (context_scope backfill + `fix_conflict_markers.py` + the strengthened `/context-scout` SKILL.md
  wording + `docspec.py`'s sibling-repo dead-reference fix) that the prior entry left staged-but-unshipped. Also
  authored `plans/active/plans_archive_reference_path_hygiene_2026_08_02_finalize.md` to clear a
  `check_finalize_plan_coverage.py` regression (a peer's plan shipped without its required gated finalize-plan
  companion) that was blocking every PM quickmerge. Commits: `3b0b706c9` (docspec.py sibling-repo fix, shipped
  standalone first), `e00de791b`/`9cfc2d4d5`/`5eece578f`/`21a96df33`/`972f43c80` (the 456-file batch, split into 5
  chunks of ~90 files after 3 whole-batch attempts failed). **Three hard-won lessons from this shipping attempt**: (1)
  `quickmerge.sh --files` is **space-separated, not comma-separated** (`--files "a b c"`, per its own usage banner) —
  joining with `paste -sd,` collapses the whole list into one unmatched shell word (no whitespace for
  `for f in $FILES_ARG` to split on), so the loop's `git add` never fires for any of them; the run still reports success
  if something else was already staged, silently shipping only that subset while looking like a full-batch win — always
  sanity-check `git show <sha> --stat`'s file count against what you intended to ship, not just the exit code. (2) A
  `--files`-scoped quickmerge invocation still does a full-tree `git stash`/pop internally for its own `STAGE 0.4`
  rebase (this branch is behind origin essentially continuously given fleet velocity) — on a large batch this can and
  did repeatedly knock already-staged files back to unstaged, requiring a re-`git add`-by-name immediately before every
  retry, never assumed-still-staged from a prior check. (3) `check_conflict_markers.sh`'s detector is a raw substring
  match for the open/close marker sequences anywhere in a line (see its own `PAT` — deliberately, to catch prettier's
  mid-line/mangled-blockquote variants), which means **prose that itself describes the conflict- marker bug class in a
  backtick-quoted example trips the same gate as a real marker** — hit 3 times this session (2 in docs this session's
  earlier entry wrote, 1 in a pre-existing, unrelated archived doc that happened to be swept into this batch) — the fix
  each time was rewording the prose to describe the marker without typing the literal 7-character run, not touching the
  detector (a corpus-wide `check_conflict_markers.sh` false-positive ratchet — grepping for other backtick-quoted marker
  examples across `plans/` before they trip the gate on their next touch — is a reasonable, currently-undispatched
  follow-up, not done here). Given (2) and (3) recur on ANY large batch on this checkout, splitting into ~90-file chunks
  with a self-retrying loop (5-8 attempts, ~10-25s backoff, re-`git add` before each) proved reliable in practice even
  though a whole-batch single shot did not. **Final inventory snapshot this session** (2026-08-03, re-measure before
  trusting): 651 in-scope docs, 280 `UP_TO_DATE`, 290 `STALE`, 81 `NEVER_SCOUTED` — STALE now outnumbers UP_TO_DATE,
  consistent with this corpus's churn rate outpacing a single session's scouting throughput; still correctly far from
  the 0/0 threshold this plan's own todo above requires before flipping `docspec.py`'s `FieldSpec` to `Req.R`. **Not
  done, deliberately**: same as the prior entry — the `FieldSpec` flip stays untouched.

- **2026-08-03 (same interactive session, slot 1, continued after a second context-compaction boundary)**: re-ran
  `generate_context_scope_inventory.py --json` fresh (646 in-scope docs, 276 `UP_TO_DATE`, 292 `STALE`, 78
  `NEVER_SCOUTED`) and dispatched 8 parallel `general-purpose` sub-agents (per this doc's own SUB_AGENT_MANDATORY_RULES
  injection) over all 78 `NEVER_SCOUTED` docs, split into batches of ~11 (7 batches) + 1 single-doc batch. 77/78 wrote
  successfully (2 correctly refused — see below); 1 batch's agent silently omitted an 11th assigned doc from both its
  edits and its own final report with no SKIPPED note
  (`deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md` — caught only by the post-ship inventory diff
  showing it still `NEVER_SCOUTED`, fixed by scouting it directly in this same session; **lesson: an agent's own
  completion report is not sufficient evidence — cross-check the actual before/after inventory diff against the assigned
  batch list, not just the agent's stated count**). Before staging, audited the whole diff against
  `scripts/plan-hygiene/check_line_caps.sh` in SCOPED mode (the exact mode quickmerge's prek hook runs) and found **9
  docs** where the mechanical addition (context_scope YAML block + one Progress Log marker, 6-12 lines) pushed a doc
  that was already at or within a few lines of the 1000L hard cap over it — 8 were genuinely NEW crossings (doc sat at
  exactly 999-1000L pre-commit, so the small-marker-append exception's "already over cap before this commit" condition
  correctly does not fire) and 1 (`lst_rate_honest_coverage_2026_07_21.md`, at 1008L pre-commit) genuinely qualified for
  that exception and shipped normally. **Verified one scouting agent's own pre-edit line-count claim was simply wrong**
  (it reported `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` as "already at 1007L" before its edit; an
  independent `git show HEAD:<path> | wc -l` check found it was actually 999L — treat a sub-agent's self-reported line
  count as unverified until checked directly, same class as this workspace's general measured-not-claimed discipline).
  Reverted the 9 over-cap docs' working-tree edits (their computed, disk-verified `context_scope` entries were not lost
  — captured into a new follow-up issue doc,
  `/plans/active/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md`, ready to re-apply once each
  doc gets a real trim/split). Also 2 docs were correctly left `NEVER_SCOUTED` by their scouting agent because they
  carry `locked_by:` — editing a locked doc's frontmatter needs operator sign-off; also logged in the same follow-up
  issue doc rather than silently dropped. Before shipping the remaining 66, ran a **word-level (whitespace-normalized)
  diff audit across all 66 files** comparing pre- and post-commit content via `difflib.SequenceMatcher` — necessary
  because prettier's prosewrap reflow made several raw line-diffs look alarming (one file showed `383` changed lines for
  what should have been a ~5-line addition); the word-level audit confirmed **zero removed content across all 66
  files**, only the intended `context_scope` block + Progress Log marker, before trusting the ship. Hit one genuine `UU`
  conflict during the ship (`pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md` — a peer's new Progress
  Log entry landed upstream between my stage and quickmerge's internal autostash-pull; resolved by keeping the peer's
  entry and appending mine after it, no logical overlap). **New environment lesson this session**: this shell is `zsh`,
  not `bash` — `zsh` does NOT word-split an unquoted `$VAR` expansion by default the way `bash` does, which silently
  broke an early `git add -- $FILES`/`check_line_caps.sh $FILES` attempt (the whole newline-joined file list collapsed
  into one pathspec/arg, producing a false-clean result with zero files actually checked); fixed by using
  `git add --pathspec-from-file=<file>` and `cat <file> | xargs <script>` instead of unquoted-var expansion for any
  multi-file argument list on this checkout. Shipped in 3 commits: `unified-trading-pm@00037ae0c` (66-file context_scope
  backfill), `@91db20917` (the line-cap/locked-doc follow-up issue doc), `@4327f26fd` (the 1 missed doc, scouted
  directly). **Final inventory snapshot this session** (2026-08-03, re-measure before trusting): 646 in-scope docs, 339
  `UP_TO_DATE`, 294 `STALE`, 13 `NEVER_SCOUTED` (the 11 from the new follow-up issue doc + 1 new doc created elsewhere
  mid-session, `test_impact_selective_execution_design_2026_08_03.md`, not yet scouted). `NEVER_SCOUTED` dropped 78→13
  net of the 1 newly-created doc. **Not done, deliberately**: the `FieldSpec` flip stays untouched — still far from 0/0,
  and the 9 line-cap docs need real trim/split work (tracked, not done here) before they can even be re-scouted.

- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — replaced the generic dispatch-architecture set
  with the sole remaining todo's actual target (the context_scope backfill itself: its source plan, the skill, and the 2
  scripts it names); dispatch-batch coordinator, source paths included since the todo names them directly.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — Prior verdict re-verified — content unchanged since the
  2026-08-06 marker. Sole open todo (corpus-wide `context_scope` backfill) remains corpus-scale, incrementally
  progressing work correctly not bounded to a single-worker AO dispatch.
- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — re-checked against the full round7-10 precedent set
  (IAM self-service default, D16 all-repos carve, S5.1 repo-type tiering, plan-destination-defaults-AO-dispatched,
  escalation-N=3-days, reversibility-qualified deletes, Option B retirement, DeepSeek/Slack-webhook credential
  provisioning, self-service-on-sibling-precedent) — none apply; this is genuinely unbounded, ongoing corpus-scale work
  (the backfill target moves as the corpus itself grows), not a defaulted judgment call. No whole-doc RECLASSIFY, no
  extractable sub-item (the single todo IS the corpus-wide sweep itself, not a list of discrete items).

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read of the sole open
  item (corpus-wide `context_scope` backfill). Genuinely unbounded, ongoing corpus-scale work — the backfill target
  moves as the corpus itself grows, not a defaulted judgment call. 4 prior audits (08-01 through round11-08-09)
  consistently agree with a well-reasoned round11 marker from the prior day; no new facts found.
- **context-scout 2026-08-14 (slot-28, AO-dispatched via the duplicate `ao_satellite_ao_dispatch_batch20_2026_08_13.md`
  todo — see that plan's own item for the closure note)**: fresh inventory at session start: 740 in-scope docs, 101
  `NEVER_SCOUTED`, 552 `STALE`, 87 `UP_TO_DATE` (corpus grew + STALE outpaced scouting since the 2026-08-03 snapshot of
  646/13/294/339, consistent with this todo's own "genuinely unbounded, target moves as corpus grows" framing above).
  Fanned out 5 parallel `general-purpose` sub-agents (per `SUB_AGENT_MANDATORY_RULES.md` injection, model=sonnet, one
  per ~20-doc slice) over all 101 `NEVER_SCOUTED` docs — sub-agents ONLY edited files (no git ops); this session
  independently verified every diff before shipping (PyYAML frontmatter re-parse, no duplicate `context_scope:` keys, no
  new 1000L hard-cap breaches, no unexpected content removal via a `git diff` audit — 0 findings across all 96 touched
  files) rather than trusting the sub-agents' own completion reports, per this corpus's own "an agent's own report is
  not sufficient evidence" lesson from the 2026-08-03 entry above. 95/101 scouted and shipped; 5 correctly skipped
  (`locked_by:` set — same 5 `plan_reconciler_findings_*_2026_08_10.md` docs an in-flight `/plan-reconcile` run had
  locked at scouting time) + 1 (`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`, 998L pre-edit)
  reverted after its 3-entry `context_scope` alone (no marker) pushed it to 1004L, over the 1000L hard cap — its
  pre-computed, disk-verified entries are now logged as a new Follow-up in
  `/plans/active/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md` (this corpus's existing
  line-cap-remediation tracking doc) rather than re-discovered fresh next time. One adjacent fix in the same pass: found
  and corrected a pre-existing dangling `related:` reference in
  `plans/active/issues/claude_code_agent_deletes_active_canonical_migration_vm_2026_08_07.md` (cited
  `watchdog_kill_events_deployment_gaps_2026_08_05.md` at its pre-archival path; doc had since moved to
  `/plans/archive/2026_08/`) — caught only because that file happened to be staged for this session's own edit; fixed in
  the same commit per the "a pointer that misled you is a finding" HARD RULE. Shipped in 3 verified batches via
  `scripts/dev/safe-doc-push.sh` (each confirmed on `origin/live-defi-rollout` via `git merge-base --is-ancestor` before
  proceeding): `unified-trading-pm@6117942be5` (33 files), `@3bc392cd0d` (32 files), `@716dcf3467` (31 files). Chunk 2
  hit a genuine `safe-doc-push.sh` autostash-revert-suspected condition mid-ship (concurrent branch churn) — diagnosed
  per the script's own forensic guide (`git log -1`/`git show HEAD:<path>` showed HEAD did NOT contain the intended
  edit, confirming real reversion, not a peer-landed-it-first false alarm), recovered cleanly via
  `git show 'stash@{0}:<path>' > <path>` per file (never a blind pop — a SEPARATE, unrelated stash@{1} carrying another
  session's foreign WIP was on the same stack and left untouched), re-verified full integrity post-recovery (0
  findings), then re-shipped successfully. **Result: `generate_context_scope_inventory.py` now reports 6
  `NEVER_SCOUTED`** (the 5 locked docs + 1 line-cap-deferred doc, both classes already tracked in the
  line-cap/locked-doc issue doc above) **and 552 `STALE`** (untouched this session — this pass targeted `NEVER_SCOUTED`
  only, the higher-value zero-context-list case; `STALE` re-scouting is real remaining scope for a future session).
  Still far from this todo's own `NEVER_SCOUTED =0, STALE=0` completion bar — the `docspec.py` `FieldSpec` flip stays
  untouched, deliberately, same as every prior session logged above.
