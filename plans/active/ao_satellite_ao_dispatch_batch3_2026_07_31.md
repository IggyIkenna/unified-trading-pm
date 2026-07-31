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
status: draft
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-3, satellite-docs]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md,
    /plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/active/ao_satellite_ao_dispatch_batch2_finalize_2026_07_30.md,
    /plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
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
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /cursor-configs/skills/context-scout/SKILL.md,
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

> **`status: draft` — NOT ingested, NOT dispatched.** Flipping this to `active` is the operator's call
> (`/plans/PLAN_FORMAT.md`; CLAUDE.md § "Plan destination — ASK BEFORE CREATING"). Authored autonomously (scheduled
> dispatch); deliberately stops at draft per the skill's Autonomous-mode contract.

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

- [ ] [BACKEND] P2. **Add a dispatcher-side watchdog that pages on same-plan priority-inversion/starvation, then
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
      consequence of the first landing, not independent work).

- [ ] [SCRIPT] P2. **Ship a read-only orphan-still-orphaned verifier, harden the liveness discriminator, then use the
      verifier to triage all 25 fleet-wide `refs/wip-preserve/**` refs.** In `agent-orchestrator` (alongside
      `server/worktree_clean_check/`): (1) add a read-only verifier that, for a recorded orphan sha, reports
      `git merge-base --is-ancestor <sha> origin/<branch>` plus a per-touched-file blob-level `SAME-AS-ORIGIN`/
      `DIFFERS` verdict and the `git diff origin <sha>` line-delta SIGN (net-negative means recovering would REGRESS
      origin), emitting `SUPERSEDED`/`STILL-ORPHANED`/`WOULD-REGRESS` per item, and wire it into the orphan-recording
      path so a stale orphan row self-closes; (2) make `server/worktree_clean_check/_liveness.py`'s discriminator
      triangulate tmux-session existence AND `/api/state.worker_alive` AND a `/proc/<pid>/cwd` check instead of trusting
      `.agent-claim` mtime alone, re-asserting immediately before any write rather than once at sweep start; (3) using
      the verifier from (1), triage all 25 fleet-wide `refs/wip-preserve/**` refs (dated 2026-07-26..07-29, across slots
      2/3/4/6/9/10/11/12/15) to a recorded SUPERSEDED/RECOVER/DELETE verdict — do not hand-triage. **Done when**: the
      verifier reproduces the prior sweep's 10 recorded verdicts from their shas alone; the discriminator returns LIVE
      for both the slot-5 (32-day-expired claim, demonstrably live) and slot-15 (dead→live inside a 9-minute window)
      shapes on record; and each of the 25 wip-preserve refs has a recorded verdict in both source docs below. Source:
      `/plans/active/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md` (its two `[SCRIPT] P2` items +
      its `[DATA] P3` item) AND `/plans/active/issues/wip_preserve_refs_silently_unrecovered_2026_07_29.md` (its own
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
- `/plans/active/issues/ao_recovery_audit_layer1_deleted_2026_07_15.md` — its own `🟢 EXECUTION CONSOLIDATED 2026-07-17`
  banner names `ao_open_issues_consolidated_close_out_2026_07_17.md` as the execution vehicle, and that doc's
  `[BACKEND] P0` todo (line 600, "Recovery-audit Layer-1 producer rewire") is confirmed still open and is the exact same
  Option-B rewire this doc's own sole todo describes. Genuinely covered, not orphaned.

## Deferred — orphaned but not AO-eligible (design/judgment fork or explicit operator ruling, no evidence-based tiebreaker)

- `/plans/active/issues/orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md` — its sole open item
  (`[REVIEW] P3`, should the host-resource dashboard surface `MemoryAvailable`/cgroup-vs-host RAM mismatch) was
  self-assessed in its own 2026-07-30 Progress Log as real feature-sized, cross-repo work (a new agent-orchestrator
  cgroup-stat reader AND a new deployment-ui dashboard tile needing its own `pw:L2` regression spec), not a bounded fix
  — "correctly skipped." A candidate for `/plan-brainstorm` to scope into its own plan, not a batch-3 todo.
- `/plans/active/omniroute_llm_gateway_pilot_design_2026_07_30.md` — 7 open todos individually read AO-dispatch grade
  (exact file/field/line-diff given for the `[INFRA]`/`[BACKEND]` items), but the doc's own text records a
  session-fresh, explicit operator ruling: stays `assigned_vm: NA`/`execution_scope: local-only` "by explicit operator
  choice... the operator wants this executed by a human, not auto-dispatched." Drafting a batch todo here would directly
  override that ruling. Its `[OPERATOR]` (stand up third-party infra) and `[REVIEW]` (run a real 2-week trial) items are
  also human/time-gated on their face. Belongs to `/na-eligibility-audit`'s KEEP-NA-valid bucket, not an AO batch.

## Deferred — data-correctness finding surfaced during this audit (flagged, not batchable here)

- **`/plans/active/issues/context_scope_consumption_enforcement_2026_07_30.md`'s "What's true today" section asserts two
  claims that are FALSE as measured live during this run (2026-07-31):** (1) it claims "the field is now REQUIRED
  (`docspec.py`, `plan`/`issue` doc_types) and `check_frontmatter_schema.py` fails PM QG on a missing one" — but
  `scripts/docs/docspec.py:136,160` both still read `FieldSpec("context_scope", Req.E, "free_list")` (elective, not
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
  `/plans/active/issues/ag_closeout_audit_ao_parked_2026_07_31.md`.

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
