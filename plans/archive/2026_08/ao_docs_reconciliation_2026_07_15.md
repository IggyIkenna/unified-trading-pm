---
doc_type: issue
title:
  AO documentation reconciliation — plans / issue docs / codex / AO repo docs drift, contradiction, overlap & completion
  audit (anchored on the two AO epics)
summary: |
  Operator-requested reconciliation (2026-07-15) of the agent-orchestrator documentation corpus: active plans, issue
  docs, codex AO SSOTs, and agent-orchestrator repo docs, anchored on the two L5 epics
  (orchestrator_master + agent_operating_framework_master). Goal: find where docs are COMPLETE-but-not-archived,
  SUPERSEDED by newer plans, OVERLAPPING/duplicated, DRIFTED from the code or the single-VM architecture, CONTRADICTORY,
  or where there are GAPS. Destructive actions (archival, supersession, codex SSOT rewrites) are RECOMMENDED here and
  routed to the operator — NOT executed autonomously (both epics are locked_by: live-defi-rollout; archival is the 5-step
  ritual + ASK). This doc is the living tracker + verdict matrix; verified findings accrue here.
status: resolved
nature: issue
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, reconciliation, plan-hygiene, drift, supersession, codex-drift, epic-alignment, audit]
related:
  [
    /plans/epics/orchestrator_master.md,
    /plans/epics/agent_operating_framework_master.md,
    /plans/archive/issues/ao_skip_blind_spawn_budget_phantom_churn_2026_07_15.md,
    /plans/archive/issues/plan_reconciliation_operator_decisions_2026_07_11.md,
  ]
created: 2026-07-15
last_updated: 2026-08-04
parent_epic: agent_operating_framework_master
priority: P1
source:
  - operator-requested 2026-07-15 ("reconcile the AO plans / issue docs / codex / AO docs; find drift, contradictions,
    gaps")
assigned_vm: NA
execution_scope: local-only
resolved_by:
  "/ag-closeout-audit ao, 2026-08-04 — both remaining checkboxes (line 490, 494) were pure status-drift, independently
  re-verified against agent-orchestrator@3abe56c (2026-07-29) and unified-trading-pm@7a3cc1289 (2026-07-24). No new work
  landed; this closure is a stale-checkbox correction only."
locked_by:
locked_since:
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
supersedes:
superseded_by:
depends_on:
assigned_role: backend_engineer
drift_direction: advance-code
context_scope:
  [
    /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md,
    /codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md,
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
---

> **🟢 ARCHIVED 2026-08-04** (`/ag-closeout-audit ao`) — the doc's own "Todos — the UNABSORBED remainder" section
> (2026-07-23) reached zero open items; both remaining checkboxes were pure status-drift (6/11 days stale against
> already-shipped commits), not new work. Archiving this digest does not mean every Tier 0-6 "Recommended action" in the
> body below was executed — see `ao_open_issues_consolidated_close_out_2026_07_17.md` for what actually landed of that
> earlier prose (most of Tiers 1/2/4/5, per this doc's own 2026-07-16 Progress Log entry); this closure only concerns
> the doc's own tracked `- [ ]` items, which is what "resolved" means here.

> **🟢 EXECUTION CONSOLIDATED 2026-07-17** — this doc's open items are now tracked and executed via
> [`ao_open_issues_consolidated_close_out_2026_07_17`](../ao_open_issues_consolidated_close_out_2026_07_17.md)
> (operator-session local plan; verified-live classification table there). Do NOT start work from this doc alone — flip
> items in the plan and mirror them here. This doc stays the detail/evidence record.

> **Living tracker.** This is a multi-pass reconciliation. Verdicts are filled per cluster as they're verified; material
> findings are code/doc-checked, not taken from status fields at face value. No archival/supersession is executed
> without an operator ruling (both epics are `locked_by: live-defi-rollout`).

## Scope & method

**Corpus (all AO-related):** 2 epics · ~10 active plans · ~17 issue docs · ~25 codex AO docs (`codex/12-agent-workflow/`

- `codex/04-architecture/agent-orchestrator-*`) · ~15 `agent-orchestrator/*.md` repo docs. Ground truth = the running
  code + the single-VM architecture SSOT.

**Verdict vocabulary (per doc):** `CURRENT` (accurate + active) · `COMPLETE→ARCHIVE` (all work done, status still
active) · `SUPERSEDED→<doc>` (replaced by a newer doc) · `STALE-DRIFT` (describes an abandoned/changed design) ·
`DUPLICATE→<doc>` (overlaps another) · `STATUS-DRIFT` (status field ≠ actual completion) · `GAP` (behavior/decision not
documented).

**Anchoring architecture fact:** the **2026-06-27 single-VM pivot** — ONE central orchestrator VM (`planning`) + N slot
workers, dispatch by **role/skill** (`assigned_role`), NO per-epic VMs, NO `assigned_vm==backend` matching. SSOT:
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`. Everything describing multi-VM / 9-epic-VM /
`assigned_vm`-matching is a drift candidate.

## Completion census (hard data — todo checkboxes + status field)

**Plans (`plans/active/`):**

| plan                                                            | status     | done |  open | first-look                      |
| --------------------------------------------------------------- | ---------- | ---: | ----: | ------------------------------- |
| ao_dispatch_correctness_regen_reconcile_2026_07_07              | active     |   34 |     5 | near-complete                   |
| ao_task_lifecycle_done_gate_resume_and_slot_identity_2026_07_09 | active     |   29 |     3 | near-complete                   |
| ao_worker_lifecycle_audit_and_corrections_2026_07_10            | active     |   20 |     4 | mostly-complete                 |
| main_agent_spawn_surgery_regression_2026_07_13                  | active     |    8 | **0** | **COMPLETE→ARCHIVE?**           |
| agent_orchestrator_alert_channel_cleanup_2026_07_13             | active     |   18 |     2 | near-complete                   |
| role_registry_schema_and_broker_mvp_2026_06_25                  | active     |    4 |     4 | half; epic says DEFER           |
| data_eng_role_vertical_pilot_2026_06_25                         | active     |    0 |     4 | not-started; epic says DEFER    |
| pm_role_charter_formalization_2026_06_25                        | active     |    0 |     4 | not-started; epic says DEFER    |
| uat_role_charter_2026_06_27                                     | active     |    1 |     3 | barely-started; epic says DEFER |
| escalation_pipeline_mvp_2026_06_25                              | **paused** |    0 |     5 | paused per epic re-scope        |

**Issue docs (`plans/active/issues/`):**

| issue                                                        | status   | done | open | first-look                   |
| ------------------------------------------------------------ | -------- | ---: | ---: | ---------------------------- |
| ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07         | open     |    3 |    3 | open follow-ups remain       |
| ao_skip_blind_spawn_budget_phantom_churn_2026_07_15          | open     |    0 |    3 | today's; fix pending         |
| backlog_regen_drops_handtuned_prereqs_2026_07_12             | open     |    4 |    0 | **STATUS-DRIFT? verify**     |
| dispatcher_role_eligibility_gap_review_slots_2026_07_13      | open     |    0 |    2 | open                         |
| ao_autospawn_role_blind_dispatch_starvation_2026_07_14       | resolved |    1 |    2 | resolved + 2 open follow-ups |
| backlog_blocked_marker_stale_brief_redispatch_2026_07_08     | resolved |    1 |    0 | resolved                     |
| autospawn_should_spawn_no_revive_pinned_opus_slot_2026_06_29 | resolved |    1 |    0 | resolved                     |
| craft_scoped_slot7_ui_dispatch_mismatch_2026_07_08           | resolved |    1 |    0 | resolved                     |
| ao_operator_message_silent_drop_no_reply_ack_2026_07_08      | open     |   10 |    1 | near-resolved; verify        |
| ao_blocked_queue_operator_ruling_sync_gap_2026_07_13         | resolved |    6 |    0 | resolved                     |
| ao_ar_image_non_surface_2026_07_13                           | resolved |    4 |    1 | resolved + 1 stray open      |
| host_tmp_tmpfs_enospc_blocks_bash_tool_2026_07_12            | open     |    3 |    0 | **STATUS-DRIFT? verify**     |
| long_lived_vm_logs_not_backed_up_2026_07_02                  | open     |    0 |    3 | open                         |
| slot_venv_duplication_disk_pressure_2026_06_29               | open     |    0 |    0 | open, no todos               |
| uv_pin_fleet_drift_2026_06_22                                | open     |    5 |   14 | mostly-open                  |
| slot5_deployment_api_dirty_false_positive_2026_07_13         | open     |    1 |    0 | **STATUS-DRIFT? verify**     |
| slot13_fastapi_ceiling_widen_reverted_2026_07_13             | resolved |    5 |    0 | resolved                     |

## EPIC-LEVEL findings (verified firsthand — read both epics in full)

### F1 — `orchestrator_master.md` describes the SUPERSEDED multi-VM architecture in its load-bearing sections (STALE-DRIFT)

The 2026-06-27 single-VM pivot is acknowledged only via bolted-on notices (lines ~104-111); the **frontmatter
`assigned_vm: vm-orchestrator`**, the **"Owns"** section, the **entire Phase 0-12 roadmap** (9-epic-VM rollout), and the
**Design-SSOT table** still present the multi-VM/9-epic-VM/`orchestrator_vm_registry.yaml` model as current. Recommend:
demote the multi-VM body to an explicit "Historical (pre-2026-06-27)" appendix; fix the frontmatter; repoint the SSOT
table. **Routes to operator** (locked epic).

### F2 — [REVISED after Wave-2 verify] the `orchestrator-multi-vm-topology.md` codex doc is ALREADY correctly superseded; the residual is a stale epic SSOT-table _pointer_

Wave-2 (Agent E) verified `/codex/12-agent-workflow/orchestrator-multi-vm-topology.md` (no leading slash — **since
DELETED** — the file no longer exists as of 2026-07-23; this line is the historical record of its state at audit time)
carried a correct "🔴 SUPERSEDED (2026-07-12)" banner + `status: stale` pointing at the single-vm doc — so it is NOT an
unmarked-stale drift. The residual is only that `orchestrator_master`'s Design-SSOT **table row** still lists it as
"Owns VM shapes…" without a "(superseded)" note — cosmetic stale-pointer (a reader who follows it sees the banner), low
severity. **The real codex STALE-DRIFT is elsewhere — `canonical-plan-flow.md` (see Codex-12 section, C-E1).**

### F3 — `agent_operating_framework_master` pillar #1 (strict `assigned_vm==backend` dispatch, W1 / D1-D6) is MOOT (STALE-DRIFT, self-acknowledged)

The epic's own notice (lines ~274-283) says W1's 3 open P0 todos are "stale/not-applicable" under role-based dispatch,
and that BOTH epics claim this D1-D6 scope via DIFFERENT already-archived owners
(`dispatch_strict_vm_matching_2026_06_24` vs `orchestrator_consolidated_remaining_2026_06_25`). Recommend: close/strike
the 3 W1 P0 todos as superseded; reconcile the two epics' duplicate ownership pointer. **Routes to operator.**

### F4 — `agent_operating_framework_master` role-plan re-scope not reflected in child plan statuses (STATUS-DRIFT)

The epic's 2026-06-26 re-scope DEFERS the role/escalation pilots (`role_registry_schema_and_broker_mvp`,
`pm_role_charter_formalization`, `data_eng_role_vertical_pilot`, `escalation_pipeline_mvp`) "to next quarter" and says
"pausing those 4 child plans is the remaining O1 mechanic (operator to confirm)." But 3 of the 4 are still
`status: active` (only `escalation_pipeline_mvp` is `paused`). Either the deferral wasn't applied or the epic text is
stale. **Routes to operator** (which is true).

### F5 — cross-epic ownership seam is fuzzy (OVERLAP)

`orchestrator_master` = "the runtime" (AutoSpawn/dispatch/safety); `agent_operating_framework_master` = "the operating
model" (charters/retrieval/dispatch-policy). Both touch dispatch. `orchestrator_master`'s child census (10 active/open
children incl. all the `ao_*` dispatch plans) vs AOF's W-registry needs a single clear "which epic owns the dispatch
CODE plans" ruling. (The `ao_*` plans list `parent_epic: orchestrator_master`.)

## Plans reconciliation (Wave 1 — in progress)

_Filled from parallel cluster reconciliation + code-verification of material findings._

### Cluster A — in-flight dispatch/lifecycle plans (agent-reported; material findings pending my code-verify)

| plan                                                            | verdict                       | real open work                                                                                                                                             | action                                                                   |
| --------------------------------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| ao_dispatch_correctness_regen_reconcile_2026_07_07              | CURRENT                       | 1 real (Phase-7 DEPLOY: bump `claude` CLI ≥2.1.170 + redeploy UI); other 4 open are self-flagged deferred/optional                                         | keep-active; close the 4 deferred as won't-fix-now                       |
| ao_task_lifecycle_done_gate_resume_and_slot_identity_2026_07_09 | CURRENT (thin tail)           | 3 open: retired-tab-branch `/spawn` gate bug (P2), operator-run identity-checker (P2, operator-owned), benign kick-window (P3)                             | keep-active; archivable once operator runs identity-checker              |
| ao_worker_lifecycle_audit_and_corrections_2026_07_10            | CURRENT                       | 2 real unshipped bugfixes: pending-operator BLOCKED-visibility (P1), `worker_polling_dead` false-alarms (P2, diagnosed-not-fixed); + a P1 live-verify soak | keep-active; don't silently drop the 2 bugfixes                          |
| main_agent_spawn_surgery_regression_2026_07_13                  | **COMPLETE→ARCHIVE**          | none — 8/8 `[x]` with shas (`@43dc13d`,`@9900062`,`@d4e16cc`)                                                                                              | **archive now**; fold its 2 process-findings into task_template          |
| agent_orchestrator_alert_channel_cleanup_2026_07_13             | CURRENT (done-pending-verify) | WS-E 24-48h Slack re-pull (window elapsed → do now); + a mis-homed plan-hygiene-sweep todo                                                                 | verify now; re-home the stray todo; migrate Deferred table; then archive |

**A-overlap verdict:** Plans 1-3 are a genuine 3-way hotspot on `autospawn.py` / `worker_liveness_watchdog.py` /
`tmux_spawn.py` but each owns a **distinct function region** — healthy parallel ownership, **NOT duplicates, do not
merge**. Plan 4 is a shipped downstream regression-fix of Plan 3 → archive. Plan 5 is orthogonal (Slack/notify code).
**Dispatch/autospawn CODE owner = `ao_dispatch_correctness` (Plan 1)** (sole `dispatch.py` owner + created
`model_tier.py` + owns `slot_skips` hygiene).

> **Ties to [[ao_skip_blind_spawn_budget_phantom_churn_2026_07_15]]:** no in-flight plan ships the skip-aware spawn
> budget; its natural home is **Plan 1** (owns `dispatch.py`+`autospawn.py` tier logic + the `slot_skips` table),
> reusing Plan 2's `_should_spawn` pre-check pattern. Plan 3's open `worker_polling_dead false-alarms` todo overlaps the
> churn's death-driver — coordinate the two.

### Cluster B — role-spine plans (agent-reported)

| plan                                           | verdict                                   | detail                                                                                                                                               | action                                                               |
| ---------------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| role_registry_schema_and_broker_mvp_2026_06_25 | STATUS-DRIFT                              | Phase 0-1 (W6 charters) SHIPPED (`ao@acbf930`); Phase 2-3 (W9 broker) = the deferred scope; `active`, no pause banner                                | **set-paused** (remaining W9 scope) like escalation                  |
| data_eng_role_vertical_pilot_2026_06_25        | STATUS-DRIFT                              | 0/4 done; in epic defer-list; `active`, no banner. Stale `harsh_pc` in Success Criteria; a self-referential correction note has wrong line-ref+value | **set-paused**; fix 2 textual errors; add escalation to `depends_on` |
| pm_role_charter_formalization_2026_06_25       | STATUS-DRIFT                              | 0/4 done; **never touched by any reconciliation pass** (0 hits in the 3922-line decisions doc); `active`, no banner                                  | **set-paused**; resolve `role: main` vs `project_management` first   |
| uat_role_charter_2026_06_27                    | **CURRENT** (correctly active)            | NOT in the defer-4; it's KEEP-scope W6; Phase 0 shipped `ao@acbf930` (matches spec, no discrepancy)                                                  | keep-active; add to epic `related_plans`; add Progress-Log entry     |
| escalation_pipeline_mvp_2026_06_25             | **CURRENT** (correctly paused — exemplar) | `status: paused` + full banner; verified against parent epic                                                                                         | keep-paused (no action)                                              |

**B-root-cause:** the pause cascade fired only for `escalation_pipeline_mvp` (finding 338, scoped to the escalation
epic). The sibling re-scope in `agent_operating_framework_master` naming 3 MORE of its own children was never separately
actioned → F4. **3 plans need `status: paused` + a banner** matching escalation's.

**New contradictions/gaps surfaced by B (to verify + log below):**

- **G1 — [WITHDRAWN after code-verify 2026-07-15] NOT a real contradiction.** Agent B reported a charter design↔shipped
  drift (`main.md role: main` vs wanted `project_management`; `data_engineering.md lifecycle: one_shot` vs wanted
  `scheduled`) — but that came from the spine's STALE 2026-06-27 Progress Log. The live charters were verified:
  `main.md` = `role: project_management` ✓, `data_engineering.md` = `lifecycle: scheduled` ✓ — both already MATCH the
  plans. No mismatch. (Pause banners on data_eng/pm_charter corrected to remove the false note.)
- **G2 — stale VM ids:** `escalation_and_disaster_recovery_master.md:19` still `assigned_vm: vm-cross-cutting` (retired
  per-epic-VM value); `data_eng_role_vertical_pilot` Success Criteria still cites `harsh_pc`.

### Cluster C — dispatch/spawn issue docs (agent-reported + my code-verify: ALL thread commits confirmed ancestors of HEAD)

| issue                                                        | verdict                                                    | action                                                                                                                                                                                                                                 |
| ------------------------------------------------------------ | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| backlog_regen_drops_handtuned_prereqs_2026_07_12             | **STATUS-DRIFT → resolved**                                | fix shipped `ao@8dd5763` (`priority_override`, verified in code L104/L1419) → flip open→resolved; BUT first capture its Addendum's **task-ID-instability-across-regen** finding as a new todo (orphan, prose-only)                     |
| ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07         | CURRENT-OPEN                                               | keep-open; RC-1/2/3 done; **3 open todos are ORPHANED** (mixed-tier spawn #4 code-confirmed still real; monitor-over-generalization; opus/sonnet-mix guidance) — 8+ days stale, in no in-flight plan → consider splitting into own doc |
| ao_skip_blind_spawn_budget_phantom_churn_2026_07_15          | CURRENT-OPEN (canonical for skip-exhaustion)               | keep-open; **CORRECT its stale gap-1** (regen-park-revert is FIXED, not open); core skip-aware-budget fix genuinely unshipped                                                                                                          |
| dispatcher_role_eligibility_gap_review_slots_2026_07_13      | CURRENT-OPEN                                               | keep-open; code-confirmed (review/main slots never set `slot_role` → unfiltered); ready-to-fix, well-scoped, orphaned                                                                                                                  |
| ao_autospawn_role_blind_dispatch_starvation_2026_07_14       | RESOLVED-CONFIRMED (`8a423bb`)                             | keep-resolved; annotate its "skip-exhaustion" bullet **superseded-by → ao_skip_blind**; **spin its surviving "high-affinity→dead-slot spill" orphan into its own issue doc** before archival                                           |
| backlog_blocked_marker_stale_brief_redispatch_2026_07_08     | RESOLVED-CONFIRMED (`3995384`)                             | none                                                                                                                                                                                                                                   |
| autospawn_should_spawn_no_revive_pinned_opus_slot_2026_06_29 | RESOLVED-CONFIRMED (`826a496`)                             | none — note: was itself a status-drift corrected 2026-07-12 (finding 219) = precedent for the backlog_regen flip                                                                                                                       |
| craft_scoped_slot7_ui_dispatch_mismatch_2026_07_08           | RESOLVED-CONFIRMED (`69870f4`, code cites the doc by name) | none                                                                                                                                                                                                                                   |

**Duplication map (5 threads):**

1. **Model-tier spawn** — ao_fleet_stall#4 (open, orphaned) · autospawn_should_spawn_no_revive (resolved, adjacent).
   KEEP ao_fleet_stall as tracker.
2. **Role/craft WORKER dispatch** — craft_scoped_slot7 → ao_fleet_stall RC-2 → ao_autospawn_role_blind. **Clean LAYERED
   fix, NOT duplicates. Keep all 3, no action.**
3. **Skip / spawn-budget churn** — ao_fleet_stall RC-3 (TTL, fixed) → ao_autospawn_role_blind "skip-exhaustion" bullet
   [SUPERSEDED] → **ao_skip_blind [CANONICAL]**. Annotate the bullet superseded-by.
4. **Park/BLOCKED mechanisms** — backlog_blocked_marker (resolved, in-TEXT marker) + backlog_regen_drops (→resolved,
   YAML/priority_override park). Correct ao_skip_blind's gap-1.
5. **Non-worker role dispatch** — dispatcher_role_eligibility (open, standalone, ready-to-fix).

**MATERIAL CORRECTION to [[ao_skip_blind_spawn_budget_phantom_churn_2026_07_15]] (my own doc):** its "gap 1 = regen
silently reverts the false-prereq park (OPEN)" is STALE — the park fix (`priority_override`) shipped `ao@8dd5763` on
2026-07-12, 3 days before the doc; I reused pre-fix evidence verbatim. **Corrected framing:** the park mechanism WORKS;
the 5 phantom tasks simply were never parked (operational gap), so the durable fix is "apply the park recipe /
auto-park," NOT "fix regen." The **Layer-1 skip-aware spawn budget remains genuinely unshipped** (Agent C code-verified
`_queued_undispatched_count` filters only on prereqs) — core finding stands.

**Orphan open items (in NO in-flight plan — need a tracking home):** ao_fleet_stall's 3 (mixed-tier/monitor/opus-mix) ·
ao_autospawn_role_blind's high-affinity→dead-slot spill · dispatcher_role_eligibility's 2 · ao_skip_blind's
skip-aware-budget · backlog_regen's task-ID-instability Addendum.

### Cluster D — subsystem/host issue docs (agent-reported; live-verified by the agent)

| issue                                                   | verdict                                                            | action                                                                                                                                                                                                                                                                                                                                              |
| ------------------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| host_tmp_tmpfs_enospc_blocks_bash_tool_2026_07_12       | **STATUS-DRIFT → resolved**                                        | all 3 done (`ao@fd9c002` structural fix), no recurrence → flip open→resolved, set `resolved_by`                                                                                                                                                                                                                                                     |
| slot5_deployment_api_dirty_false_positive_2026_07_13    | **STATUS-DRIFT → resolved**                                        | evidence-backed closure (`pm@0c08a0afe`+`ao@f3b803371`) → flip open→resolved, set `resolved_by`                                                                                                                                                                                                                                                     |
| ao_blocked_queue_operator_ruling_sync_gap_2026_07_13    | RESOLVED-CONFIRMED                                                 | none (already correct)                                                                                                                                                                                                                                                                                                                              |
| ao_ar_image_non_surface_2026_07_13                      | RESOLVED-CONFIRMED                                                 | none; the 1 open checkbox is an explicitly out-of-scope future option                                                                                                                                                                                                                                                                               |
| slot13_fastapi_ceiling_widen_reverted_2026_07_13        | RESOLVED-CONFIRMED                                                 | none (already correct)                                                                                                                                                                                                                                                                                                                              |
| ao_operator_message_silent_drop_no_reply_ack_2026_07_08 | CURRENT-OPEN                                                       | keep-open; P1 core fixed (`ao@8076257`), 2 small P2 leftovers (UI badge, tmux-nudge verify)                                                                                                                                                                                                                                                         |
| long_lived_vm_logs_not_backed_up_2026_07_02             | CURRENT-OPEN (operator-deferred)                                   | keep-open; **see G3 codex tension**                                                                                                                                                                                                                                                                                                                 |
| slot_venv_duplication_disk_pressure_2026_06_29          | ~~CURRENT-OPEN (needs-triage)~~ **RESOLVED + ARCHIVED 2026-07-17** | formal todo was added 2026-07-16 AND is now `[x]` with the live SSM measurement (verdict: guard-running-but-outgrown → cadence 2h + prune cron, via `ao_host_disk_pressure_2026_07_16`, archived). Same day: operator reversed the 30G parking → cache deleted (18G measured freed), `[unlock-plan]` granted, doc moved to `../../archive/issues/`. |
| uv_pin_fleet_drift_2026_06_22                           | CURRENT-OPEN (needs-triage)                                        | 2 core infra fixes confirmed still-unshipped (live grep); strike 4 moot checkboxes                                                                                                                                                                                                                                                                  |

**New cross-finding G3 (feeds F1/F2 + Wave 2 codex):** the "epic VMs retired" premise is only _partially_ applied —
`/codex/04-architecture/runtime-deployment-topology.md` (edited **2026-07-12, post-pivot**) still says "central + epic
VMs are long-lived systemd services," and `launch-epic-vm*.sh` still exist (last touched 2026-06-23). So the multi-VM
drift isn't just "epic stale, codex current" — **codex itself is unreconciled**. F1/F2 need code/codex-verify in Wave 2,
not face-value on the pivot notices.

**D-note:** no true duplicates; `host_tmp_tmpfs` (/tmp tmpfs) vs `slot_venv_duplication` (root disk) are
related-but-distinct, correctly separate.

## Issue docs reconciliation (Wave 1 — in progress)

## Codex AO docs reconciliation (Wave 2)

### Cluster E — codex/12-agent-workflow (agent-reported + code-verified by the agent)

| doc                                          | verdict                                            | action                                                                                                                                                                                                                                                                                                                                         |
| -------------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| agent-orchestrator-single-vm-architecture.md | **CURRENT (the live SSOT)**                        | keep — every claim code-verified (role_registry, assigned_role matching, regen 1800s, VM-match retirement)                                                                                                                                                                                                                                     |
| orchestrator-multi-vm-topology.md            | **SUPERSEDED-CORRECT**                             | keep — banner present, `status: stale`, 2026-07-12 → **F2 revised**                                                                                                                                                                                                                                                                            |
| **canonical-plan-flow.md**                   | **STALE-DRIFT (C-E1, highest-priority codex hit)** | its "REQUIRED" plan frontmatter still mandates `assigned_vm: vm-<id>` via `orchestrator_vm_registry.yaml` (contradicts `{planning,NA}` in PLAN_FORMAT.md + single-vm doc); also calls the 6h regen "current" when 1800s shipped; `status: current`, no banner. **AND it's a cited `codex_ssots` of the AOF epic** → add banner + rewrite §3/§6 |
| orchestrator-safety-mechanisms.md            | PARTIALLY-RECONCILED                               | mechanisms code-verified current, but "Composes with" points at the superseded topology doc + "every VM" framing → repoint to single-vm doc                                                                                                                                                                                                    |
| local-slot-host-symmetric-worker-model.md    | PARTIALLY-RECONCILED                               | Host-Behaviour-Matrix row still says `tab/<op>/N` (RETIRED → Path-B), no banner → fix that row                                                                                                                                                                                                                                                 |
| stale-blocker-reaper.md                      | CURRENT                                            | keep (code-verified)                                                                                                                                                                                                                                                                                                                           |
| claude-cli-multi-account-headless-auth.md    | CURRENT                                            | keep                                                                                                                                                                                                                                                                                                                                           |
| harsh-laptop-migration-2026-05-20.md         | CURRENT (self-bannered Path-B)                     | keep                                                                                                                                                                                                                                                                                                                                           |

**G3 EXTENDED to code (Agent E):** the retired epic-VM model still has live CODE artifacts —
`deployment-service/scripts/vm/launch-epic-vm*.sh` (Lifecycle: permanent, last touched 2026-06-23) +
`deployment_service/vm_prefix_registry.py:987-994` still register
`agent-orch-vm-{defi,cefi,tradfi,sports,prediction,ml,trading-core}-` as `LONG_LIVED_LIVE`. So "epic VMs retired" is a
doc-level claim with **unreconciled code + a partially-reconciled codex** underneath — a real cleanup gap (feeds the
`long_lived_vm_logs` / `uv_pin` "epic VM" ambiguity from Cluster D).

### Cluster F — codex/04-architecture (agent-reported + code-verified by the agent)

| doc                                                                             | verdict                                    | action                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **recovery-defence-in-depth-layers.md**                                         | **CODE-DRIFT — 🔴 BIG FINDING**            | Layer-1 documents a live `recovery-audit` AO role backed by `agents/recovery-audit.md` — but that file is **DELETED** (`NEVER_LAUNCH=frozenset()` empty; `overview.md` says "removed end-to-end"). Recovery/kill-switch domain + cross-doc contradiction → **NOTIFY OPERATOR** (was Layer-1 dropped intentionally or does it need re-impl?)                                                                                                          |
| **agent-orchestrator-host-offline-failover.md**                                 | **STALE-DRIFT (strongest VM case)**        | entire premise = multi-host fleet failover; no valid target under single-VM (`failover.py` exists, default-off). Unbannered, last_reviewed 2026-05-30 → banner + rewrite as inert holdover                                                                                                                                                                                                                                                           |
| agent-orchestrator-overview.md                                                  | PARTIALLY-RECONCILED (widest blast radius) | frontmatter summary + tech-stack "82 slots" + deployment diagram + "Fleet topology" all say "10 epic VMs" current (last_reviewed 2026-07-12 = partial patch, not a coherent pass) → rewrite those 4 sub-sections                                                                                                                                                                                                                                     |
| agent-orchestrator-backlog-state-alignment.md                                   | PARTIALLY-RECONCILED→STALE                 | "Per-VM scope filter" invariant uses `assigned_vm: vm-ml` examples the single-vm SSOT explicitly names as stale → rewrite section (mechanism vestigial/inert)                                                                                                                                                                                                                                                                                        |
| agent-orchestrator-worker-liveness.md                                           | PARTIALLY-RECONCILED                       | core watchdog current + code-verified; "10/11 VMs / vm-ml broken SSM" rollout framing stale → banner/rewrite those 2 sections                                                                                                                                                                                                                                                                                                                        |
| runtime-deployment-topology.md                                                  | PARTIALLY-RECONCILED (G3)                  | AO paragraph L589-595 (added **2026-07-12, post-pivot**) says "central + epic VMs" while citing the doc that retires them — fresh self-contradiction → rewrite to singular                                                                                                                                                                                                                                                                           |
| **agent-orchestrator-autospawn.md**                                             | CURRENT + **documentation GAP**            | code-verified: spawn budget is prereq-only, `slot_skipped_tasks` in `dispatch.py` but NOT `autospawn.py` → **third independent corroboration of [[ao_skip_blind_spawn_budget_phantom_churn_2026_07_15]]**; doc should add a "skip-blind spawn budget" known-limitation                                                                                                                                                                               |
| agent-orchestrator-alerting.md · ci-alerting.md · autonomous-recovery-matrix.md | CURRENT                                    | keep                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| role-registry.md                                                                | **DELETED** (option B, 2026-07-15)         | consolidated to ONE SSOT — the `agent-role` frontmatter schema is enforced by `scripts/docs/docspec.py` `PER_TYPE['agent-role']` (QG-gated), per-role data is the frontmatter in each `unified-trading-pm/agents/<role>.md`, and `[TAG]→role` lives in `regen_backlog_from_plan.py::_TAG_TO_ROLE`; all live codex + AO-code references repointed. Historical worked-example refs in the role-charter plans left for each plan's own review/archival. |

**F confirms F1/F3 independently:** `orchestrator_master.md` still `assigned_vm: vm-orchestrator` + summary "multi-VM
runtime" while `agent_operating_framework_master` was corrected to `planning` — same-week touch, only one fixed.

**G-M1 [verified + nuanced]:** `codex_vs_repo_docs_ssot_audit_2026_06_01.md` line 192 =
`[x] ✅ agent-orchestrator … vs codex/12 + codex/04 — SHIPPED` (2026-06-22). Two gaps: (a) it only covered the **codex
side**, never the repo `docs/`; (b) it shipped **5 days BEFORE the 2026-06-27 pivot**, which then re-drifted codex/04
(host-offline-failover, overview, backlog-state-alignment, worker-liveness) with **no follow-up re-sweep**. So the
`[x] SHIPPED` is accurate-as-of-06-22 but the pivot invalidated it and nothing re-audited.

## AO repo docs reconciliation (Wave 2 — Agent G; 13 of 15 actually live in `agent-orchestrator/docs/`)

| doc                                                                                                         | verdict                                      | action                                                                                                                                                                                                                                                |
| ----------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ENV_VARS.md · SLOTS_AGENTS_AND_FLEET.md · WORKER_SPAWN_PREREQUISITES.md · OPERATIONS.md · AUTH_INVENTORY.md | **CURRENT-OPERATIONAL**                      | keep — code/codex-cited, post-pivot accurate (2 tiny fixes: AUTH_INVENTORY has a dangling pointer to the superseded multi-vm codex doc; OPERATIONS "Multi-machine" §523 dated pre-pivot — spot-check)                                                 |
| MAIN_AGENT_CUTOVER_REVIEW.md · WORKER_SPAWN_PREREQUISITES.md                                                | **STALE-HISTORICAL, ALREADY BANNERED**       | keep — the model pattern (dated SUPERSEDED banner + successor pointer); no action                                                                                                                                                                     |
| CUTOVER_DAY_BLOCKERS_2026_05_19.md · LANDSCAPE.md · TODO.md                                                 | **STALE-HISTORICAL, unreferenced**           | archive (clean candidates — fully closed, cited only in-cluster)                                                                                                                                                                                      |
| AUDIT_FINDINGS_2026_05_18.md                                                                                | **STALE-HISTORICAL, code-pinned**            | banner (NOT archive — `slots_worker.py:606` cites it as a live spec)                                                                                                                                                                                  |
| PROBLEM.md                                                                                                  | STALE-HISTORICAL                             | archive, or banner just the "Solution: Per-Operator Server" section (its "Problem" narrative is fine)                                                                                                                                                 |
| **PLAN.md**                                                                                                 | **STALE-DRIFT (top) + code-pinned (middle)** | **split, do NOT blanket-delete**: banner the per-operator/no-central-server sections (wrong), but repoint `server/db.py:48`+`orm.py:1`+`models/__init__.py:1` docstrings off its Schema/API/Concurrency sections first                                |
| README.md                                                                                                   | CURRENT + stale tree                         | keep; fix "Files in This Directory" (lists deleted `agents/` dir + only 4 of 13 docs) → replace with a pointer                                                                                                                                        |
| REPO_PROVENANCE.md                                                                                          | CURRENT + 1 stale clause                     | keep; drop the retired `tab-> ... ->staging` flow clause (LDR→main-direct now)                                                                                                                                                                        |
| main-agent-checkpoint.md                                                                                    | **OUT-OF-CLASS** (live agent scratch memory) | leave alone; infra note: untracked-but-unignored → a cron already wiped it once today; `.gitignore` it or exempt it. (It currently records "ACTIVE OUTAGE — backend down since 2026-07-15 05:15:58Z" — consistent with the operator-stopped backend.) |

**META-FINDING G-M1 (cross-cutting):** the existing plan `plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md`
marks agent-orchestrator `[x] SHIPPED @2026-06-22`, but that only fixed the **codex-side** docs to match code — it never
touched/redirected/archived the repo's own `docs/`. So the repo-doc half of that line item is
**incomplete-but-marked-done** (a STATUS-DRIFT in that plan) and this reconciliation is the open remainder of an
already-scoped initiative. → verify + either reopen that line item or file the repo-doc cleanup as its follow-on.

## Cross-cutting contradictions & gaps (synthesis)

**X1 — THE dominant theme: the 2026-06-27 single-VM pivot is substantially UNRECONCILED across codex + code + one epic**
(the plans/issues are mostly clean; the drift lives in the reference layer). The single-vm SSOT doc is correct and
code-verified, but the retired multi-VM/epic-VM model still reads as _current_ in: `orchestrator_master.md`
(frontmatter + Owns + Phase 0-12 + SSOT-table row, F1) · `canonical-plan-flow.md` (an AOF-cited SSOT, C-E1) · **5 of 11
codex/04 docs** (host-offline-failover STALE, overview 4 sections, backlog-state-alignment, worker-liveness,
runtime-deployment-topology — some _re-drifted post-pivot_, F/G3) · **code** (`launch-epic-vm*.sh`,
`vm_prefix_registry.py` LONG*LIVED_LIVE). The sibling epic `agent_operating_framework_master` WAS corrected
(`planning`); `orchestrator_master` wasn't, same week. **Root cause:** the one codex-reconciliation audit
(`codex_vs_repo_docs_ssot_audit_2026_06_01`) shipped 2026-06-22, \_5 days before the pivot*, and nothing re-swept after.
→ this is one coherent remediation, not 10 scattered edits.

**X2 — 🔴 BIG FINDING (recovery/kill-switch domain, operator-notify per triage rule):**
`/codex/04-architecture/recovery-defence-in-depth-layers.md` documents Layer-1 as a live `recovery-audit` AO agent, but
`agents/recovery-audit.md` was deleted end-to-end (code-confirmed). Either Layer-1 audit-signoff was intentionally
dropped (doc must say so) or it needs re-implementation — an operator call.

**X3 — the skip-exhaustion / spawn-budget thread is real, triple-corroborated, unfixed, undocumented, and its home is
clear.** Confirmed by: the open todo in `ao_autospawn_role_blind` (superseded by ao_skip_blind), Agent C's code-read,
and Agent F's codex-vs-code check. Fix belongs in `ao_dispatch_correctness` (owns
`dispatch.py`+`autospawn.py`+`slot_skips`); codex `agent-orchestrator-autospawn.md` should document the limitation.

**X4 — a cluster of ORPHANED genuinely-open dispatch items sits in no in-flight plan** (ao_fleet_stall's
mixed-tier/monitor/opus-mix, ao_autospawn_role_blind's high-affinity→dead-slot spill, dispatcher_role_eligibility,
ao_skip_blind's budget fix, backlog_regen's task-ID-instability). They fall out of active execution tracking — need one
home.

**X5 — recurring STATUS-DRIFT class with precedent.** Issues/plans whose `status`/checkboxes lag reality:
`backlog_regen_drops`, `host_tmp_tmpfs`, `slot5_dirty` (→resolved); `main_agent_spawn_surgery` (complete→archive); 3
role plans (active→paused). The corpus has swept this before (findings 218/219) — a periodic status-reconcile is
missing, not a one-off.

**X6 — minor drifts:** G1 charter design↔shipped (`main.md role:main` vs wanted `project_management`;
`data_engineering.md lifecycle`) · G2 stale VM ids (`escalation…master:19 vm-cross-cutting`; data_eng Success-Criteria
`harsh_pc`) · README `agents/` tree · REPO_PROVENANCE tab-branch clause · AUTH_INVENTORY dangling multi-vm pointer.

## Recommended actions (routed to operator — nothing applied yet; both epics locked)

**Tier 0 — NOTIFY (this message):** X2 recovery-audit Layer-1 contradiction (operator decision: dropped vs re-impl).

**Tier 1 — SAFE status flips (evidence-backed; I can apply on your OK):** `backlog_regen_drops_handtuned_prereqs`,
`host_tmp_tmpfs`, `slot5_deployment_api_dirty` → `open`→`resolved` + populate `resolved_by` (commits verified
ancestors). First capture backlog_regen's task-ID-instability addendum as a todo so it isn't lost.

**Tier 2 — operator ruling, tracked plans:** archive `main_agent_spawn_surgery` (8/8 done, verified); set
`role_registry`/`data_eng`/`pm_charter` → `paused` (match escalation's banner).

**Tier 3 — the single-VM reconciliation (X1) — needs a dedicated remediation plan + your ruling:** rewrite
`orchestrator_master` body/frontmatter to single-VM (locked epic); banner/rewrite the 5 codex/04 docs +
`canonical-plan-flow.md`; repoint the stale pointers; decide the fate of the epic-VM _code_ artifacts
(`launch-epic-vm*.sh`, `vm_prefix_registry` rows); reopen/refile the `codex_vs_repo_docs_ssot_audit` AO line as a
post-pivot re-sweep.

**Tier 4 — orphaned open items (X4):** consolidate into ONE "AO dispatch residuals" issue (or route each into
`ao_dispatch_correctness`), so the skip-blind budget + 4 siblings are tracked.

**Tier 5 — small mechanical fixes (X6):** low-risk, batchable.

**Tier 6 — repo-doc hygiene (Agent G):** archive `CUTOVER_DAY_BLOCKERS`/`LANDSCAPE`/`TODO`; banner
`AUDIT_FINDINGS`/`PROBLEM`; split `PLAN.md` (repoint 3 docstrings first); fix README tree + REPO_PROVENANCE clause;
`.gitignore` `main-agent-checkpoint.md`.

## Progress Log

- **2026-07-16** — **⚠️ The 2026-07-15 "EDITS APPLIED (local, uncommitted)" batch below LARGELY NEVER LANDED** —
  verified file-by-file this session. It was left local/unpushed and is now lost: `orchestrator_master.md` frontmatter
  is **still `assigned_vm: vm-orchestrator`** (F1 claim false); the `⚠️ CODE-DRIFT` banner claimed on
  `recovery-defence-in-depth-layers.md` was **absent** (`rg CODE-DRIFT` → 0 hits); `backlog_regen_drops` and `slot5`
  were **still `status: open`**. Only `host_tmp_tmpfs`'s flip appears to have survived. **Lesson (feeds X5):** "applied
  locally, awaiting operator review" is not a durable state — an un-pushed reconciliation edit is indistinguishable from
  no edit. Land edits or don't claim them.
- **2026-07-16** — **Tracker partially STALE-COMPLETE: the plan/issue layer (Clusters A–D, F4) is now genuinely DONE**,
  via work this tracker predates: 3 role-charter plans **ARCHIVED** (not `paused` as the 07-15 entry proposed —
  `pm_role_charter`/`data_eng_role`/`uat_role_charter` → `plans/archive/2026_07/`, `cdd3cc47c`+`98413f37e`);
  `role_registry_schema` archived (broker NOT REQUIRED, superseded by `assigned_role` dispatch); **8 code-verified
  resolved AO issue docs archived** → `plans/archive/issues/` (`01d621f70`, each independently re-verified against
  ground-truth code by a dedicated agent — all 8 GENUINELY_RESOLVED, no false-resolved). Today additionally:
  `backlog_regen_drops` + `slot5` flipped `open→resolved` **for real** + archived; `slot_venv_duplication`'s 2026-07-13
  recurrence formalised as a `- [ ]` todo (it was narrative-only → invisible to every sweep — same X5 class).
- **2026-07-16** — **X2 (recovery-audit Layer-1) RULED: operator chose B — re-home the producer, DEFERRED to last.** The
  A/B/C framing rested on a **false premise**: re-verification showed the deletion was **NOT end-to-end** — only the AO
  `recovery-audit` **worker-role producer** was removed; the whole consuming half is LIVE (alerting-service
  `POST /safety-ops/signoffs` ingest + `gateway_state.py` `DISPUTE`→SAFE_MODE, UAC contract, strategy subscriber, DART
  feed serving `_mock_signoffs()`). So Layer-1 is a **producer-less half-dismantled safety layer** (no automated
  DISPUTE→SAFE_MODE tripwire; caught only at Layer-5 human ack), not a clean descope. Accurate banners **now landed for
  real** on `recovery-defence-in-depth-layers.md` § Layer 1 + a scope-clarifier on `agent-orchestrator-overview.md`'s
  "removed end-to-end" line. Rewire tracked in [[ao_recovery_audit_layer1_deleted_2026_07_15]] (stays `open`).
- **2026-07-16** — **Still open here (the real remainder):** X1 — the single-VM-pivot codex sweep (`canonical-plan-flow`
  C-E1, `agent-orchestrator-overview` "10 epic VMs/82 slots", `host-offline-failover` premise-moot,
  `backlog-state-alignment` `vm-ml` examples, `worker-liveness` "10/11 VMs", `runtime-deployment-topology` L589
  self-contradiction, `autospawn` skip-blind doc-gap) + **F1** `orchestrator_master`. X3/X4 (skip-blind budget +
  dispatch residuals) are being taken up as the AO dispatch-correctness work — operator's current scope is "make the AO
  work properly". Once X1/F1 land, this tracker archives.
- **2026-07-15** — **EDITS APPLIED (local, uncommitted — operator to review diffs before push).** Tier 1: 3 issues
  `open→resolved` + `resolved_by` (`backlog_regen_drops`/`8dd5763`, `host_tmp_tmpfs`/`fd9c002`,
  `slot5`/`f3b803371`+`pm@0c08a0afe`) + resolution banners. Tier 2: `main_agent_spawn_surgery` → `status: complete` +
  banner (physical archive-move + epic-census flagged for operator); `role_registry`/`data_eng`/`pm_charter` →
  `paused` + pause banners (F4). F1: `orchestrator_master` frontmatter `assigned_vm: vm-orchestrator → planning` (body
  kept-historical per its own notice). New docs: `ao_recovery_audit_layer1_deleted_2026_07_15` (X2) +
  `ao_dispatch_residuals_2026_07_15` (X4). Repo-doc hygiene (Agent Q, 10 files): STALE/SUPERSEDED banners on
  AUDIT_FINDINGS/CUTOVER_DAY_BLOCKERS/LANDSCAPE/ TODO/PROBLEM/PLAN, REPO_PROVENANCE clause, AUTH_INVENTORY pointer,
  README tree→pointer, `.gitignore` main-agent-checkpoint. Codex banners (Agent P) in progress. **Code-touching items
  deliberately NOT done (flagged):** PLAN.md docstring-repoint (`server/*.py`),
  `launch-epic-vm*.sh`/`vm_prefix_registry` epic-VM artifacts.
- **2026-07-15** — **Wave 2 complete + full synthesis** (codex/12, codex/04, AO repo docs — 3 parallel agents,
  code-verified). Dominant theme X1: the single-VM pivot is substantially unreconciled across codex + code + the
  `orchestrator_master` epic (5 of 11 codex/04 docs, canonical-plan-flow, launch-epic-vm code) — root cause = the one
  codex audit shipped 5 days pre-pivot with no re-sweep. Big finding X2 (recovery-audit Layer-1 = deleted agent) →
  operator-notify. Skip-blind budget triple-corroborated (X3). Cross-cutting X1-X6 + Tier 0-6 actions filled. Exercise
  reconciliation-complete; actions await operator ruling (nothing applied — both epics locked).
- **2026-07-15** — **Wave 1 complete** (plans + issues, 4 parallel agents). Material findings code-verified (all cited
  commits confirmed ancestors of HEAD). Duplication map (5 threads) built. Applied a correction to
  [[ao_skip_blind_spawn_budget_phantom_churn_2026_07_15]] (regen-park-revert is FIXED `ao@8dd5763`, not open — I'd cited
  stale evidence). Launched Wave 2 (codex + AO-repo-doc reconciliation).
- **2026-07-15** — Tracker created. Read both epics firsthand (F1-F5). Computed the plan + issue completion census.
  Launched Wave 1 (plans + issues cluster reconciliation). Codex + AO-repo-doc passes (Wave 2) queued.

## Todos — the UNABSORBED remainder (added 2026-07-23 by `/plan-reconcile`, AO scope)

> **This doc was NOT archivable, despite its 🟢 EXECUTION CONSOLIDATED banner.** A conservation check of all 6 tiers
> against `../ao_open_issues_consolidated_close_out_2026_07_17.md` found most content did land (Tier 1/2/4/5 verified
> executed, several via archived child plans), but **Tier 3 and Tier 6 left real remainders that no plan tracked**. The
> tracker's own `- [ ]` "`ao_docs_reconciliation` close-out pass — verify tier-by-tier (1–6) what has since landed" is
> the gate for exactly this; the todos below ARE its answer, so that todo can close once these are owned.

- [x] [DOCS] P1. ✅ **DONE 2026-07-23 — `/codex/12-agent-workflow/canonical-plan-flow.md` corrected (operator-ruled).**
      This was this doc's own **highest-priority codex hit** and it sat untouched for 8 days while agents read it as
      `status: current`: it mandated `assigned_vm: vm-<id>` as REQUIRED and described `parent_epic` as routing "to the
      right VM via `orchestrator_vm_registry.yaml`" — the multi-VM fleet deprecated 2026-06-27, contradicting
      `plans/PLAN_FORMAT.md`'s `{planning, NA}`. Fixed under an explicit operator ruling (codex edits are never
      autonomous): frontmatter block now reads `assigned_vm: planning | NA`, with a dated CORRECTED banner; two further
      stale lines in the same doc were fixed with it (the `tab/<operator>/<N>` branch model in §[4] and §[8]-[10], and
      "plan-level `assigned_vm` matches the slot's VM context" → role-based dispatch).
- [x] ✅ [OPERATOR] P2. **Rule on the epic-VM code artifacts — they have never been ruled on, by anyone.**
      `deployment-service/scripts/vm/launch-epic-vm.sh` + `launch-epic-vm-aws.sh` still ship, and
      `deployment_service/vm_prefix_registry.py` still registers **10**
      `agent-orch-vm-{defi,cefi,tradfi,sports,     prediction,ml,trading-core,operator-ops,cross-cutting,orchestrator}-`
      prefixes as `LONG_LIVED_LIVE`, commented "planning VM + per-epic VMs … run until operator tears them down".
      Per-epic VMs were deprecated **2026-06-27**; CLAUDE.md says delete deprecated code, no shims — but the failover
      module got an explicit **KEEP** ruling on the "multi-VM may return for resilience" argument, so this is genuinely
      a judgment call, not a cleanup. **Operator direction 2026-07-23: file it, decide later** — the point of this todo
      is that the decision stops being invisible. **Gate**: a recorded keep-or-delete ruling; if KEEP, the named
      scenario under single-VM that still needs it (mirroring the failover precedent). — **RULED 2026-07-24: DELETE**
      (not the KEEP-with-scenario first recorded same day — operator overruled it: don't want the code debt, recreate
      from git history if the per-epic model ever returns). **Shipped `deployment-service@7438ec5`**: both scripts + all
      10 registry entries + the mirrored `launcher_registry.py` relaunch table removed, dependent tests + packer README
      fixed, full QG green. The failover-precedent argument this todo cited doesn't actually transfer: that ruling keeps
      `FailoverLoop` for CENTRAL-VM host resilience (a second host takes over), a different axis from per-epic workload
      VMs — confirmed `launch-central-brain-aws.sh` (the central-VM DR relaunch tool) never depended on the epic-VM
      scripts. One new gap surfaced in the process: that relaunch tool doesn't re-provision the self-hosted GitHub
      Actions "glue" runner pool also hosted on this VM — separately tracked, not resolved here.
- [x] ✅ [REVIEW] P3. **DONE (found stale 2026-08-04, `/ag-closeout-audit ao`).** Gate met via
      `agent-orchestrator@3abe56c` (2026-07-29): `codex_vs_repo_docs_ssot_audit_2026_06_01.md`'s agent-orchestrator line
      now reads "REOPENED 2026-07-24... RE-CLOSED 2026-07-29 (slot-11, fresh audit against current single-VM/ Path-B
      code) — agent-orchestrator@3abe56c" — both halves of the gate (explicit reopen AND re-verification date)
      satisfied. Checkbox lagged reality by ~6 days.
- [x] ✅ [DOCS] P3. **DONE (found stale 2026-08-04, `/ag-closeout-audit ao`).** Gate met via
      `unified-trading-pm@7a3cc1289` (2026-07-24):
      `/codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md`'s Host-Behaviour-Matrix row now reads
      "Per-slot Path-B reference-clone on `live-defi-rollout`" (bare `tab/<op>/N` cell removed) and its
      interactive-session bullet explicitly bannered "RETIRED — corrected 2026-07-23." No unbannered `tab/<...>`
      instruction remains. Checkbox lagged reality by ~11 days.
- [x] ✅ [REVIEW] P2. **The Tier-6 remainder is now its own issue doc — track it there, not here.** Tier-6's per-file
      dispositions were executed as a blanket delete, leaving 5 dead doc-references in shipped code and a tracker
      Progress Log claiming "0 dead links" that never covered that batch. Filed 2026-07-23 as
      [`ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md`](ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md).
      **Gate**: that doc reaches 0 open todos; this line closes with it. **DONE (na-eligibility-audit 2026-08-03)** —
      gate met: that doc is `status: resolved` with all 4 of its own todos `[x]` (5 dead doc-refs repointed/removed,
      `README.md` + `REPO_PROVENANCE.md` fixed, the tracker's stale "0 dead links" Progress Log claim corrected).
- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
- **context-scout 2026-08-01**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-03**: trimmed context_scope 7→4 entries (the prior pass carried 7, over this skill's 2-6
  target) — kept the two direct targets of the doc's 2 remaining open todos
  (`codex_vs_repo_docs_ssot_audit_2026_06_01.md`, `local-slot-host-symmetric-worker-model.md`) plus the execution
  redirect (`ao_open_issues_consolidated_close_out_2026_07_17.md`, "do NOT start work from this doc alone") and the
  anchoring single-vm-architecture SSOT; dropped both epics and the now-resolved `..._dead_code_refs_2026_07_23.md` as
  no longer load-bearing for the remaining work.
