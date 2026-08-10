---
doc_type: plan
title: AO satellite AO batch 6 — sixth dispatch batch extracted from the AO tranche's satellite docs
summary: >-
  SIXTH AO-dispatch batch for the `ao` topic tranche, produced by the `/ag-closeout-audit ao` skill run (2026-08-04,
  autonomous mode, scheduled `ag_closeout_auditor` dispatch). Phase 1 ran a real `Workflow` fan-out over all 64 current
  `ao`-tagged AG-primary members (not just the mechanical never-cited pre-filter — the full member set, since a doc
  merely NAMED in a Deferred section reads as "cited" by the cheap filter while still being genuinely orphaned). Result:
  50 of 64 orphaned (43 `orphaned_never_touched`, 7 `orphaned_partial_coverage`), 12 `archivable_after_planned_work`, 2
  `archivable_now`. Of the 50 orphaned, 5 cleared AO-dispatch-scope eligibility (45 stayed operator-gated/too-large/
  human-only/conflict-gated — see Deferred). Phase 0.3's Orthogonality HARD CHECK separately found + retagged 8 more
  genuine `ao` mistags (bare `meta`/`cross-cutting` docs with AO `parent_epic`) not in the original 64-member scan; 5 of
  those contribute 5 more eligible todos here after direct review. Total: 10 todos, each conflict-checked against the
  whole `plans/active` corpus before drafting (one soft same-file adjacency found and handled via a caution note, per
  batch3/4/5's own precedent, not exclusion).
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-6, satellite-docs]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md,
    /plans/active/ao_satellite_ao_dispatch_batch5_2026_08_03.md,
    /plans/active/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 1.4
assigned_role: backend_engineer
drift_direction: advance-code
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit ao skill run 2026-08-04 (autonomous, scheduled ag_closeout_auditor dispatch, slot 10) — Phase 0
  confirmed the tranche's covering-plan set (batch1+finalize archived; batch2/2f, batch3/3f, batch4/4f, batch5[draft]/5f
  active; ao_open_issues_consolidated_close_out_2026_07_17.md). Phase 1 ran a real Workflow fan-out (64 agents, one per
  current ao-tagged AG-primary member, all 64 succeeded, 0 errors). Phase 0.3's Orthogonality HARD CHECK found + fixed 8
  more genuine ao mistags outside the 64-member scan. Phase 3's conflict-check ran against the whole plans/active corpus
  for every candidate target file/mechanism before drafting.
---

# AO satellite AO batch 6

> **`status: active`** — approved 2026-08-08 after a fresh conflict-check found no blocking overlap (see Progress Log).
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** — the `ao` tranche's 2026-07-17 "local execution
> only" ruling was explicitly LIFTED 2026-08-08 (operator, interactive); see this doc's Progress Log and batch5's own
> Progress Log for the full citation trail. AO-dispatchable now, same as every other tranche. Authored autonomously
> (scheduled dispatch) and originally shipped `status: draft` pending operator approval.

## Why this plan exists

A fresh `/ag-closeout-audit ao` run (2026-08-04) re-derived the tranche's full 64-member set (not just the "never-cited"
mechanical pre-filter batch5 used — that filter is now near-useless for finding fresh orphans in THIS tranche, since
batch5's own Deferred section text-cites ~39 basenames, sweeping most of the corpus into "cited somewhere" even though
being named in Deferred is explicitly non-coverage) and ran a real per-doc `Workflow` fan-out over all 64. Verdict
counts: 2 `archivable_now`, 12 `archivable_after_planned_work`, 7 `orphaned_partial_coverage`, 43
`orphaned_never_touched` (50 orphaned total). Of those 50, 5 cleared the AO-dispatch-scope eligibility bar — this batch
extracts those 5, plus 5 more found by a separate corpus-wide Orthogonality sweep (8 genuine `ao` mistags retagged
on-sight from bare `meta`/`cross-cutting`, of which 5 carry their own eligible bounded work; see that sweep's citation
in `ao_consolidated_closeout_2026_07_25.md`'s Sources digest). The remaining 44 declined-orphan docs stay exactly where
they are: operator-gated (25, the largest class), too-large-or-risky-for-a-batch-todo (10), genuinely-human-only (5), or
conflict-gated against another doc's own claim (5). Full per-doc reasoning for all 64 Phase-1 verdicts lives in this
run's own Workflow journal, cited in the Progress Log below rather than duplicated here.

**2 `archivable_now` docs found, NEITHER independently archived here**:
`ao_dispatch_priority_inversion_starvation_has_no_page_path_2026_07_30.md` is already the named archival target of
`ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md`'s own gated todos (still waiting on batch3's own open todo to
clear) — archiving it here would duplicate/race that flow. `ao_docs_reconciliation_2026_07_15.md` had no other plan
queued to archive it, so it was archived directly as part of this audit run (see Progress Log) — a clean,
evidence-backed, zero-risk housekeeping action, not new work.

## Rules for every worker on this plan

- Put each todo's new test cases in a test module named for that todo's own concern.
- **File-adjacency #1 (soft caution, not a hard collision)**: todo 4 (clear stale slot-side `current_task` on
  re-dispatch) and todo 6 (`/done` empty-`sha` data-integrity fix) both likely touch dispatch/`/done`-handling code in
  `agent-orchestrator/server/` (exact modules TBD by each worker — `dispatch.py`/`routes/slots_worker.py` are the
  probable homes). Re-grep for a fresh diff before starting either; if they land in the literal same function, land todo
  4 first (it's the older, more-corroborated finding — 6 recurrences on record) and rebase todo 6 on top.
- **File-adjacency #2 (soft caution, not a hard collision)**: todo 1
  (`ao_open_issues_consolidated_close_out_2026_07_17.md`, Phase-8 read-only re-measurements) touches the same file as
  `ao_satellite_ao_dispatch_batch5_2026_08_03.md`'s (still draft, unapproved) todo 2 and todo 3 — those two edit a
  DIFFERENT part of the file (the "Split-out child plans" status table's stale MISTAGGED-row cell and a MOVED-item count
  sentence), not the Phase 2/5/8/LAST todos this batch's todo 1 touches. No content overlap, but re-pull fresh
  immediately before editing regardless — this file sits close to its 1000-line hard cap (verify headroom before adding
  any new Progress Log text) and is edited almost daily by na-eligibility-audit/context-scout passes.
- Do not edit a source issue doc's checkboxes beyond appending your evidence line to the todo you executed. The paired
  finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md`) reconciles evidence back into
  every source doc and runs archival.
- No todo below deletes prod data, mutates a GCS bucket, or launches a VM.

## Todos

- [x] ✅ [BACKEND] P0. **Two read-only DB/activity-log measurements on the orchestrator host (no external credential
      needed — same host every dispatched worker already runs on).** (1) Re-measure the `tmux_session_lost` rate vs. the
      192-events-since-2026-07-18 baseline and record the delta (Phase 8's own stated gate). (2) The stale-dispatch
      invariant 24h spot-check: confirm live `dispatched`-status backlog count equals the live worker-held-task count —
      the fix + 9 regression tests already shipped (`agent-orchestrator@aa81706`); only the operational proof remains.
      **Done when**: a new dated Progress Log entry on the source doc records both measurements with their raw numbers
      and the delta/pass-fail verdict; both `- [ ]` items (Phase 8, "Re-measure the `tmux_session_lost` rate" and
      "Stale-dispatch invariant — the live 24h spot-check") flip `[x]`. Source:
      `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md` (its Phase-8 items 5+6 only — the doc's other
      6 open items stay local/NA, see this run's Workflow journal for why). Repo: agent-orchestrator (read-only). —
      unified-trading-pm@4f5a1e6ba

- [x] ✅ [DOC] P3. **Document the accepted BLOCKED‑marker `/done`-disposition convention in `task_template.md`.** Added
      a "`/done`-time disposition markers" bullet (right after the pre-existing `BLOCKED-<TOKEN>` ingestion-gate bullet)
      documenting all three server-recognized closures — CANCELLED/SUPERSEDED, DEFERRED-BY-DESIGN, and
      `BLOCKED-ON:<ref>` — with the `BLOCKED-ON:<ref>` entry explicitly distinguished from the `BLOCKED-<TOKEN>`
      ingestion-gate family (the ingestion-gate family keeps a todo OUT of the backlog; the disposition markers are how
      a DISPATCHED todo closes at `/done` without a false `[x]` flip). — unified-trading-pm@79565c404

- [x] ✅ [BACKEND] P3. **CLOSED 2026-08-08 — already shipped, found during this review's re-verification.** The source
      doc (`external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md`) is now `status: resolved` +
      archived (`last_updated: 2026-08-06`) at
      `/plans/archive/issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md`, its own text
      recording: "The single `[BACKEND] P3` todo is `[x]` done — implemented + shipped `agent-orchestrator@23bd0b3`
      (Part 1 `auto_park.py` docstring documenting `priority_override` vs `auto_unpark__` prereq, Part 2
      `park_now`/`manual_park` …)" — matching this todo's own done-when (both halves: the durability-difference
      documentation AND the durable self-park mechanism) exactly. Original text follows. **Give a worker that hits an
      EXTERNAL dispatch gate (a commit/promote not yet on a target branch) a way to park the task DURABLY, and document
      why a `priority_override` park doesn't survive backlog re-derivation while a named `auto_unpark__` prereq does.**
      In one change: (1) confirm/document the priority_override-vs-prereq durability difference (cross-ref RULES.md §4 +
      the batch2-011 park precedent) — if `priority_override` parks are meant to be durable, that's a separate bug/its
      own todo; if not, workers should stop relying on them for anything that must outlast a re-derivation tick. (2)
      Give the worker a durable self-park mechanism keyed on the external gate — either (a) a named
      `auto_unpark__<task-id>` prereq (mirroring batch2-011, dispatcher already honors it, survives re-derivation) or
      (b) an explicit "gated on external ref reaching branch X" blocker-type; pick using (1)'s finding. A related but
      distinct mechanism now exists (`agent-orchestrator@5bfde668`'s `POST /api/backlog/{task_id}/park` /
      `server/auto_park.py::manual_park`, MAIN/operator-triggered) — check whether it's reusable as the worker-callable
      primitive before building a parallel one. **Done when**: both halves land; a promote-gated task parks after the
      FIRST worker detects the gate and does NOT re-dispatch to a fresh worker every tick, resuming only when the gate
      clears; a test simulates "ref not yet on main." Source:
      `/plans/archive/issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md` (its sole
      remaining item — GATED-prefix cleared 2026-08-03, see that doc's own inline note). Repo: agent-orchestrator.

- [x] ✅ [BACKEND] P3. **On re-dispatch, clear/invalidate the prior owner's slot-side `current_task`** (and log a
      warning naming both slot ids + the task) so `/api/state` never shows one task `working` in two slots — makes the
      double- dispatch condition observable instead of something main has to catch by pane inspection. **See this plan's
      file-adjacency rule #1 before starting.** **Done when**: a regression test proves a re-dispatched task's prior
      slot no longer reports it as `current_task`, and the loud log line fires; full `agent-orchestrator`
      `quality-gates.sh` green. Source:
      `/plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` (its 2nd `[BACKEND] P3`
      item ONLY — the 3rd item, `/done` idempotency, stays conflict-gated against 3 other open docs sharing the same
      mechanism, see Deferred). Repo: agent-orchestrator. — **agent-orchestrator@82578c3** (`assign_task_to_slot` in
      `server/state_store/slots.py` now clears a DIFFERENT slot's stale `current_task` before assigning the task to a
      new slot, logging `orchestrator.state_store.logger.warning(...)` naming both slot ids + the task_id;
      `tests/test_redispatch_clears_stale_owner.py` covers the collision case, the no-prior-owner no-op, and the
      same-slot-reclaims-itself no-op; full `quality-gates.sh` 2799 passed, 2 skipped).

- [x] ✅ [DOCS] P2. **Mirror the shipped liveness-by-progress check into the review-role wedge/escalation heuristic,
      then record operator sign-off.** `agents/review.md` step 3d still classifies a long-dirty worktree as dead/stale
      from tmux-session and heartbeat state alone — the exact signal that produced the 2026-07-21 false positive the
      already-shipped backend fix (`agent-orchestrator@0757a751`/`@0cc12fdb`) addressed for the automated emitters. Add
      the same explicit commit-recency + live-process check before review recommends escalation or recycle. Then record
      explicit operator sign-off on the suppression predicate (same safety class as the cross-role reply fix) — no such
      sign-off exists anywhere in the corpus despite the backend half shipping 2026-07-24. **See this plan's
      file-adjacency rule #2 note — different file (`agents/review.md`) from rule #1, but ALSO independently shared with
      `ao_satellite_ao_dispatch_batch5_2026_08_03.md`'s (draft) todo 1, which edits `agents/review.md` STEP 2
      (peer-vs-operator reply routing) — a different section, re-grep before starting regardless.** **Done when**: the
      diff lands in `agents/review.md` step 3d citing a checked progress signal, not just session state; the next
      long-dirty escalation cites it; operator sign-off is recorded in the source doc's Progress Log before the diff
      ships. Source: `/plans/archive/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md` (its
      2 remaining items — its 1st item was a same-doc stale-checkbox correction, fixed directly by this audit run, not
      drafted here). Repo: unified-trading-pm. — unified-trading-pm@c6fde000a

- [x] ✅ [SCRIPT] P2. **Guard `server/prompts.py::_compose()` so slot-bearing lifecycle roles (`review`, and any
      `main`/`monitor` spawned with a `slot_id`) route to the slot-less register/poll STEP block their role file
      documents, instead of the worker `/boot` handshake branch** — add a `_REGISTER_POLL_ROLES` guard before the
      `elif slot_id is not None:` branch (`prompts.py:184`), keep the escalation-role branch (line 166) unchanged. Add a
      `_compose()` unit test asserting review/main/monitor render the register/poll block with `slot_id` set. Then
      extend the SAME guard's role classification to cover **one-shot lifecycle/audit roles** (`ag_closeout_auditor` and
      siblings) — otherwise the identical data-loss variant persists for those roles after the review/main/monitor guard
      lands. **Done when**: the unit test passes for all of `{review, main, monitor}` AND for at least one one-shot
      lifecycle role; full `agent-orchestrator` `quality-gates.sh` green. Source:
      `/plans/active/issues/boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md` (its 1st +
      3rd items, combined — the 3rd explicitly extends the 1st's guard). Repo: agent-orchestrator. —
      **agent-orchestrator@6166269** (2026-08-08, "fix(prompts): route review/main/monitor to register/poll shape even
      with slot_id" — shipped by slot-32, ancestor-verified on `origin/live-defi-rollout`;
      `_REGISTER_POLL_ROLES =     {"review", "main", "monitor"}` now guards both the STEP 0 and STEP 2/3 branches in
      `_compose()`, with `test_register_poll_role_gets_slotless_shape_even_with_slot_id` covering
      `{review, main, monitor}` and `test_one_shot_lifecycle_role_unaffected_by_register_poll_guard` confirming
      `ag_closeout_auditor` — the one-shot lifecycle-role extension already shipped separately at
      `agent-orchestrator@0a8ed16` via `_ONE_SHOT_ESCALATION_ROLES` — still renders its correct STEP 2/3 shape
      unaffected by the new guard). This slot only flipped the checkbox; no new code was needed.

- [x] [SCRIPT] P1. **Fix `/done` so an empty `sha` does NOT mark a task `status=done`.** ✅ agent-orchestrator@41da3e578
      — added early 409 guard in `done_slot` + regression test `test_done_empty_sha_gate.py`; QG 2684 passed. A
      release-not-complete signal (`done_sha=""`) must return the task to `queued` (or be rejected outright), never
      record a terminal `done` with empty evidence — this is the data-integrity defect that turned the 2026-07-31
      boot-misroute incident from benign into silent data loss, independent of the composer-routing fix above. Pair with
      the existing `/api/backlog/{id}/reopen` correction path and the `no_plan_flip` hardening it already has. **See
      this plan's file-adjacency rule #1 before starting.** **Done when**: a regression test asserts a `/done` call with
      an empty `sha` never leaves the task `status=done`; full `agent-orchestrator` `quality-gates.sh` green. Source:
      `/plans/active/issues/boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md` (its 2nd item
      — independent of the composer-guard fix above per the doc's own text). Repo: agent-orchestrator.

- [x] [INFRA] P3. **MOOT 2026-08-05 — do not dispatch.** The source doc's host (`i-0dd9812a96cdda5dc`/`ip-172-31-0-185`)
      was terminated 2026-08-03 (`ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`) — there is no host left to
      allowlist. See `/plans/archive/issues/fleet_git_health_ip_185_known_human_planning_vm_2026_08_03.md` (now
      `status: resolved`) for the full resolution.

- [x] [DOC] P2. **Add a 4th conflict-check surface to the shared AO-dispatch protocol.** ✅ unified-trading-pm@c2083029d
      — added surface "(d) any `status: draft` `{ag}_satellite_ao_dispatch_batch{N}_*.md` for the same tranche, from
      EITHER `/ag-closeout-audit` or `/na-eligibility-audit`'s prior runs (not just the current run) — grep its
      `Source:`/`## Deferred`/`## Already     covered` citations for the candidate doc's path before finalizing a
      RECLASSIFY or drafting a new extraction" to
      `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3; wired both
      `na-eligibility-audit/SKILL.md` (its Phase 2) and `ag-closeout-audit/SKILL.md` (its own Phase 3 conflict-check
      section) to reference the new surface explicitly. Source:
      `/plans/archive/2026_08/issues/na_and_ag_closeout_audit_population_overlap_2026_07_31.md` (its 1st item — its 2nd
      item was operator-ruled 2026-08-08; source doc fully closed + archived 2026-08-10). Repo: unified-trading-pm.

- [x] ✅ [BACKEND] P2. **Rescue the 3 orphaned slot-12 commits onto `origin/live-defi-rollout`, one repo at a time —
      MOOT, all 3 already independently landed under fresh SHAs before this run.** For each of
      (`unified-trading-library c927ec58`, `unified-api-contracts 06c8e90b`, `deployment-service 0e62096f`): fetched
      `refs/wip-preserve/*`, re-confirmed each SHA still NOT an ancestor of `origin/live-defi-rollout` (orphan status
      held), then content-diffed each against current LDR tip instead of blind-cherry-picking: -
      `unified-trading-library c927ec58` (point_in_time.py docstring `lst_staking_yields`→`lst_yields`) — byte-identical
      file-change already on LDR as `unified-trading-library@60c840f2` ("... (rescue orphaned slot-12 WIP)" +
      `Quickmerge:       agent` trailer — a prior rescue attempt landed this exact patch under a fresh SHA). -
      `unified-api-contracts 06c8e90b` (AAVE-PLASMA phase pipeline→live) — same outcome (`"AAVE-PLASMA": "live"` in
      `defi_venues.py`) already on LDR as `unified-api-contracts@06c54fee` ("feat(defi): flip AAVE-PLASMA venue phase
      pipeline to live", dated 2026-08-01, independently authored). - `deployment-service 0e62096f` (fastapi/starlette
      cap-lift) — identical `pyproject.toml`/`uv.lock` state (fastapi>=0.137, starlette 1.3.1) already on LDR as
      `deployment-service@eff55ae7` ("chore(deps): lift fastapi/starlette caps to fastapi>=0.137/starlette>=1.3.1", same
      commit subject). **Done when** (outcome-defined, per the source issue doc's own reasoning) — all 3 commits'
      CONTENT is an ancestor of `origin/live-defi-rollout` under some SHA: MET for all 3, no rescue action needed.
      Source: `/plans/archive/2026_08/issues/orphaned_wip_slot12_slot8_recovery_2026_08_04.md` (its 1st item only —
      items 2/3 are conditionally gated on a main-agent confirmation this run could not re-verify, see Deferred). Repo:
      unified-trading-library, unified-api-contracts, deployment-service.

## Deferred — the 45 declined orphans from the Phase-1 fan-out + 3 conditional items from the orthogonality sweep

**Ledger check**: 64 members − 2 `archivable_now` − 12 `archivable_after_planned_work` − 7 `orphaned_partial_coverage`
(none independently eligible) − 5 orphaned-and-eligible (drafted as todos 1-4 above, todo 1 covers 2 sub-items) = 38
`orphaned_never_touched`-and-declined, all named below by category (count verified against the Phase-1 Workflow journal
`wf_8c217203-b49`, not eyeballed) — plus 5 more items from the 8-doc orthogonality sweep (5 drafted as todos 5-10 above,
3 conditionally deferred below).

- **Operator-gated** (largest class, 24 — corrected 2026-08-06 (/plan-reconcile ao): was 25,
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` removed below, RESOLVED 2026-08-06 — see
  annotation): `ao_backlog_no_collision_gate_long_running_driver_todos_2026_08_02.md`*,
  `ao_boot_stub_session_vars_field_name_mismatch_2026_08_02.md`,
  `ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26.md`,
  `ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md`, `ao_orphan_audit_followup_triage_2026_07_30.md`,
  `ao_residuals_after_dispatch_hardening_2026_07_17.md`, `ao_tranche_full_content_audit_findings_2026_07_31.md`,
  `blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md`,
  `blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md`,
  `context_scope_consumption_enforcement_2026_07_30.md`,
  ~~`dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`~~ **RESOLVED 2026-08-06** (its own Progress Log:
  "Option A operator-confirmed + implemented; both todos closed" — removed from this count, corrected 2026-08-06
  (/plan-reconcile ao)), `long_lived_vm_logs_not_backed_up_2026_07_02.md` (checked 2026-08-06, still genuinely
  operator-gated — 3 open todos, explicit 2026-07-02 operator decision "not needed right now... revive by scheduling
  these todos" — correctly stays here),
  `mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27.md`,
  `mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md`,
  `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md`,
  `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md`,
  `orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md`,
  `per_slot_ff_pull_status_report_crons_stale_fleet_wide_2026_07_27.md`,
  `qg_owner_gate_full_workspace_rglob_walk_hangs_quickmerge_2026_07_31.md`,
  `tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md`,
  `unified_trading_pm_stash_pile_accumulation_2026_07_26.md`,
  `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`,
  `omniroute_llm_gateway_pilot_design_2026_07_30.md`, `omniroute_multi_provider_routing_evaluation_2026_08_03.md`,
  `orchestrator_vm_e2e_hardening_2026_07_24.md`, `backlog_regen_reverted_p1_2_park_2026_08_01.md`'s `[OPERATOR] P0` item
  - its `[SCRIPT] P2` "consider a standing assertion" item (an unscoped design fork), plus
    `p1_2_backlog_hand_park_did_not_persist_2026_07_31.md`'s `[OPERATOR] P1` item (re-apply the park — operator-only
    `backlog.yaml` write). **`backlog_regen_reverted_p1_2_park_2026_08_01.md`'s `[AO] P1` root-cause item is NOT
    operator-gated — it's a stale-checkbox-vs-a-sibling-doc situation, fixed directly by this audit run (see Progress
    Log): `p1_2_backlog_hand_park_did_not_persist_2026_07_31.md` already root-caused the exact same incident ("a
    one-time process gap... the fix is simply to perform the edit; the code path is sound") — cited back rather than
    re-investigated.**
- **Too-large/unscoped-design** (10): `ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md`,
  `ao_backlog_no_collision_gate_long_running_driver_todos_2026_08_02.md`*,
  `backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md`,
  `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md`,
  `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`,
  `orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`,
  `regen_positional_task_ids_not_content_stable_2026_07_17.md`,
  `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md`,
  `utl_shared_clone_commits_repeatedly_reset_2026_07_22.md`, `wip_preserve_refs_silently_unrecovered_2026_07_29.md` (its
  2 `[SCRIPT] P3` items only — its `[DATA]` items are already done via batch2/batch3, see 2026-08-01 Progress Log). _(\*
  `ao_backlog_no_collision_gate...` straddles both categories per its own doc — an unresolved design fork AND an
  explicit operator-timing note; listed once, cause noted twice for completeness.)_
- **Genuinely human-only**: `ao_context_pct_0_for_monitor_heavy_workers_2026_07_29.md`,
  `git_health_not_clean_since_pinned_constant_2026_07_27.md`,
  `nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md` (optional leg only),
  `orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29.md`,
  `prediction_trades_migration_concurrent_dispatch_2026_07_28.md`.
- **Conflict-gated** (against another doc's own open claim on the same mechanism):
  `data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md`,
  `orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md`,
  `reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md`,
  `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`,
  `slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md`, and
  `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md`'s 3rd item (`/done` idempotency — shares
  `slots_worker.py`'s `/done` handler with `reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md`'s own
  `/done`-on-origin item, "must land as one change" per that doc, plus 2 more NA/undispatched docs on the same ground).
- **Conditionally gated** (orthogonality-sweep finds, precondition not independently re-verifiable this run):
  `orphaned_wip_slot12_slot8_recovery_2026_08_04.md`'s 2nd item (slot-8's `bd0e231f` — gated on "main confirms slot 8
  did not self-resolve post-boot," unverified here) and 3rd item (slot-4's `~036c568` throttle fix, P3, "main could NOT
  independently re-check," same reachability gap); `fleet_git_health_ip_185...`'s scanner-home is TBD between
  deployment-service/agent-orchestrator (noted in the drafted todo, not a hard block).

None are re-triageable by re-running this same mechanical filter again without new information — the next
`/ag-closeout-audit ao` pass should re-check each one's _specific named gate_ (per the skill's iterative-drain
methodology step 1), not re-derive the classification from scratch.

## Codex SSOTs (read before starting a todo)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, `…/agent-orchestrator-overview.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`, `/codex/05-infrastructure/per-tab-worktrees.md`,
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`.

## Progress Log

- **2026-08-04** — Authored by `/ag-closeout-audit ao` (autonomous mode, scheduled `ag_closeout_auditor` dispatch, slot
  10). Phase 0 confirmed the covering-plan set is unchanged in shape from batch5's own run (batch1+finalize archived,
  batch2+finalize, batch3+finalize, batch4+finalize active, batch5[draft]+finalize,
  `ao_open_issues_consolidated_close_out_2026_07_17.md`). Phase 1 ran a real `Workflow` fan-out over the FULL 64-member
  set (not the narrower never-cited pre-filter batch5 used) — 64/64 agents succeeded, 0 errors. Verdicts: 2
  `archivable_now`, 12 `archivable_after_planned_work`, 7 `orphaned_partial_coverage`, 43 `orphaned_never_touched` (50
  orphaned total, 5 eligible). Separately, Phase 0.3's Orthogonality HARD CHECK found 8 genuine `ao` mistags (bare
  `meta`/`cross-cutting` with AO `parent_epic`) outside the 64-member scan, each verified by reading the doc — all 8
  retagged directly (see `ao_consolidated_closeout_2026_07_25.md`'s Sources digest for the list + citation, which also
  closed a `check_ag_closeout_linkage.py` regression the retags introduced, netting the corpus from 69→65 orphans, BELOW
  baseline). Of those 8: 2 are self-dispatched already (no action needed), 1
  (`na_audit_multi_tranche_shared_doc_ownership_and_draft_p0_park_2026_07_30.md`) was already reclassified `NA→planning`
  by na-eligibility-audit 2026-08-03 (self-covering), 1 (`p1_2_backlog_hand_park_did_not_persist_2026_07_31.md`) has
  only an `[OPERATOR]`-tagged remainder, 5 contribute the eligible work drafted as todos 5-10 above. Also fixed 2
  same-doc stale-checkbox findings directly (not batch material):
  `wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md`'s todo 1 (shipped
  `agent-orchestrator@0757a751`/`@0cc12fdb`, re-verified live) and `backlog_regen_reverted_p1_2_park_2026_08_01.md`'s
  `[AO] P1` root-cause item (answered by a sibling doc's own confirmed root-cause finding, cited not re-derived).
  Archived `ao_docs_reconciliation_2026_07_15.md` directly (both its 2 remaining checkboxes were pure status-drift,
  independently re-verified against 2 live commits 6-11 days old — see that doc's own archived Progress Log entry for
  the full evidence). Phase 3's conflict-check ran against the whole `plans/active` corpus for every candidate's target
  file/mechanism before drafting; found one soft same-file adjacency (todo 4 + todo 6, both near dispatch/`/done`-
  handling code) and one cross-batch soft adjacency (todo 1 vs. draft batch5's todo 2/3, same file different content) —
  both handled via caution notes rather than exclusion, matching batch3/4/5's own precedent. Left `status: draft`
  deliberately — flipping to `active` is the operator's call. Full per-doc Phase 1 verdicts + reasoning for all 64
  candidates (including the 45 declined): Workflow run `wf_8c217203-b49`, journal at
  `subagents/workflows/wf_8c217203-b49/journal.jsonl` (this session's transcript dir).
- **2026-08-08 (operator-authorized draft→active review)** — Re-ran the shared 3-surface conflict-check against (a)
  active `assigned_vm: planning` plans in `parent_epic: orchestrator_master` (only the batch finalize twins, all
  correctly `gate_on_depends`-held), (b) sibling batches 5/7/8 (no new overlap), (c)
  `ao_open_issues_consolidated_close_out_2026_07_17.md` (Phase-8 items 5+6, todo 1's target, re-confirmed still `[ ]`
  open at lines ~789-793). Spot-checked every open todo's Source doc for post-drafting closure and found todo 3's Source
  (`external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md`) independently resolved+archived
  2026-08-06 (`agent-orchestrator@23bd0b3`) — closed todo 3 above via verification, hard evidence: the archived doc's
  own `[x]` checkbox + inline resolution note. Todos 1, 2, 4-7, 9, 10 re-verified still genuinely open (source docs
  still `status: open` with the specific referenced items still `[ ]`). Applied the same `assigned_vm`/
  `execution_scope`-unchanged treatment as batch5 (see that doc's Progress Log for the full investigation — this is the
  `ao` tranche's own established, operator-rooted convention, not an oversight); flipped `status: draft → active` only.
  Fixed the stale draft-era H1 banner to match.
- **2026-08-08 (operator, interactive)**: RULED — the 2026-07-17 local-only ruling is LIFTED going forward; see batch5's
  Progress Log for the full note. `assigned_vm: NA → planning`, `execution_scope: local-only → orchestrator-agent`
  applied here too.
- **2026-08-08 (ao_satellite_ao_dispatch_batch6-001, slot-3)**: Todo 1 completed. Both Phase-8 measurements done against
  orchestrator SQLite (`data/state/state.db`): (1) `tmux_session_lost` post-fix 2-day rate = ~322/day vs pre-fix ~95/day
  — rate INCREASED ~3.4×, orphan-reaper NOT the driver; (2) stale-dispatch invariant PASS (dispatched=6 ==
  worker-held=6). Evidence: `unified-trading-pm@4f5a1e6ba` (Phase-8 checkboxes flipped + Progress Log in source doc).
