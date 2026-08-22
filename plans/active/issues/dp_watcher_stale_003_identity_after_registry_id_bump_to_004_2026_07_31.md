---
doc_type: issue
title:
  deployment-service consolidator-scheduler watcher carries stale DP-WATCHER-003 self-identity in its docstrings and log
  messages after its registry_id was bumped to DP-WATCHER-004
summary: >-
  The manifest-consolidator scheduler-paused watcher in deployment-service registers itself as
  `registry_id="DP-WATCHER-004"` (consolidator_scheduler_watcher.py:136) but still describes itself as "DP-WATCHER-003"
  in its module + class docstrings (consolidator_scheduler_watcher.py:1,15,71) and in several cli.py log lines
  (cli.py:87,498,516,835). Cosmetic stale-identity only — zero functional impact (the live registry_id is correct) — but
  it causes identity confusion when correlating logs/alerts to the registry. Confirmed by review (agt-86659c) and main
  (agt-26fe12) on 2026-07-31 to be tracked as a todo NOWHERE in plans/active/ (every corpus hit for DP-WATCHER-00[34] /
  consolidator_scheduler_watcher is historical build/fix narrative, not an open fix-todo). NOTE the fix is NOT a blind
  -003→-004 find-replace: cli.py:167 references DP-WATCHER-002 (a genuinely different sibling watcher,
  DP_CRON_DID_NOT_FIRE) and some -003 mentions may be legitimate cross-references to sibling keys — the fix must update
  only THIS watcher's stale self-identity, not sibling cross-references.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [deployment-service, data-pipeline-monitors, dp-watcher, stale-identity, cosmetic, docstring]
related: []
created: "2026-07-31"
author: unknown
parent_epic: security_and_cross_cutting_master
# reclassified NA -> planning 2026-08-02 (na-eligibility-audit, infra tranche) — conflict-check CLEAR
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
priority: P3
drift_direction: advance-code
source: [review-role-finding-agt-86659c, main-orchestrator-triage-agt-26fe12]
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope: [deployment-service/deployment_service/data_pipeline_monitors/consolidator_scheduler_watcher.py, deployment-service/deployment_service/data_pipeline_monitors/cli.py, /plans/active/issues/deployment_service_basedpyright_ratchet_broken_by_dep_backmerge_2026_08_15.md]
---

# What

`deployment-service/deployment_service/data_pipeline_monitors/consolidator_scheduler_watcher.py` registers the
manifest-consolidator scheduler-paused watcher as `registry_id="DP-WATCHER-004"` (line 136), but its own module
docstring (line 1), its maintenance-window comment (line 15), and its class docstring (line 71) still call it
**DP-WATCHER-003**. Several `cli.py` log lines carry the same stale label: `cli.py:87` ("KEY #2/DP-WATCHER-003"),
`cli.py:498` + `cli.py:516` (log messages "DP-WATCHER-003 off this sweep" / "skipping DP-WATCHER-003 this sweep"), and
the `cli.py:835` comment.

# Impact

Cosmetic only. The live `registry_id` is correct (`-004`), so alerting/registry correlation works; the stale strings
only mislead a human reading the source or logs into thinking this is watcher `-003`. No data loss, no functional
regression. Review observed a predecessor pinged a worker about this ~17h earlier; still unfixed on
origin/live-defi-rollout as of 2026-07-31 22:56Z.

# Fix direction (NOT a blind find-replace)

Update only THIS watcher's stale self-identity (the module/class docstrings + maintenance-window comment at lines
1/15/71 and the `cli.py` log lines/comments at 87/498/516/835 that describe the paused-scheduler watcher) from
`DP-WATCHER-003` to `DP-WATCHER-004` to match `registry_id`. **Do NOT** touch `cli.py:167`'s `DP-WATCHER-002` reference
(a different sibling watcher, `DP_CRON_DID_NOT_FIRE`), and verify each remaining `-003` mention is this watcher's own
identity and not a legitimate cross-reference to a sibling key before changing it.

# Follow-up todo

- [ ] [SCRIPT] P3. **BLOCKED-ON:deployment_service_basedpyright_ratchet_broken_by_dep_backmerge_2026_08_15 — RULED
      2026-08-22 (D13): run a deeper bisection first (a cross-slot measurement already shows 1259 is reachable on a
      current tree) — ratchets-only-go-down is a HARD RULE, raise the baseline only as a last resort.** Once that
      ratchet question resolves and the fix ships, reconcile the stale `DP-WATCHER-003` self-identity strings in
      `deployment-service/deployment_service/data_pipeline_monitors/consolidator_scheduler_watcher.py` (lines 1, 15, 71)
      and `.../cli.py` (lines 87, 498, 516, 835) to `DP-WATCHER-004` to match the registered `registry_id` (watcher line
      136). Do NOT alter `cli.py:167`'s `DP-WATCHER-002` (a different sibling watcher); before changing any `-003`
      mention, confirm it names THIS watcher and not a sibling cross-reference. Cosmetic/non-functional — no runtime
      behavior change expected; cite
      `plans/active/issues/dp_watcher_stale_003_identity_after_registry_id_bump_to_004_2026_07_31.md` in the commit.

## Progress Log

- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **RECLASSIFY `assigned_vm: NA → planning`** —
  first verdict for this doc (no prior marker). Read end-to-end; `grep -cE '^- \[ \]'` = **1**, matching this verdict's
  item count. NA was a default here, not an assessed call: the sole todo clears the dispatch-scope bar
  (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility") on every axis
  — 7 named line locations across 2 named files, an explicit carve-out (`cli.py:167`'s `DP-WATCHER-002` must NOT
  change), a stated per-mention verification step, cosmetic/no-runtime-change, not operator-gated, no GCS delete or VM
  launch. **Phase-2 conflict-check run and CLEAR** (protocol § 3): the candidate's real claim is the stale
  `DP-WATCHER-003` self-identity strings in `consolidator_scheduler_watcher.py` (1/15/71) + `cli.py` (87/498/516/835).
  Surface (a) — every `status: active`, `assigned_vm: planning` doc in `parent_epic: infrastructure_master` and every
  corpus hit for `DP-WATCHER-00[34]`/`consolidator_scheduler_watcher`: 3 planning docs mention the watcher, none claims
  these strings — `tradfi_pred_manifest_consolidator_cron_stuck_paused_2026_07_29.md`'s sole open todo extends the
  SEPARATE `uts-prod-consolidator-liveness-watchdog` to bounded auto-resume (different component, behavioural not
  cosmetic); `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md:256` and
  `mtds_available_at_cross_asset_backfill_2026_07_13.md:188,315` are prose context references to the archived
  `dp_watcher_003_consolidator_scheduler_paused_maintenance_window_gap_2026_07_29.md`, not dispatch claims. Surface (b)
  — no sibling batch/finalize drafted in this run. Surface (c) — `infra_consolidated_closeout_2026_07_25.md` does not
  name this doc at all. Verdict: zero overlap → clear. This independently corroborates the doc's own filing-time check
  (review agt-86659c + main agt-26fe12, 2026-07-31). Applied: `execution_scope: local-only → orchestrator-agent`,
  `assigned_role: infra` filled in (was missing; validated against the live `agents/*.md` registry — `agents/infra.md`).
  **No companion finalize plan authored** — this is a `doc_type: issue` under `plans/active/issues/`, and
  `check_finalize_plan_coverage.py` globs only `plans/active/*.md` (verified by direct code read, lines 117/141), so
  issue docs are structurally exempt from that gate.
- **context-scout 2026-08-03**: populated context_scope (2 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (2 entries), unchanged.
- **slot 15, 2026-08-15**: **Code WRITTEN and verified correct, NOT YET SHIPPED.** All 6 self-identity strings corrected
  `DP-WATCHER-003 → DP-WATCHER-004`: `consolidator_scheduler_watcher.py` lines 1, 15, 71 (line 15's filename citation to
  the archived `dp_watcher_003_consolidator_scheduler_paused_maintenance_window_gap_2026_07_29.md` deliberately left
  unchanged — immutable historical reference, not a live self-identity string), 204, 222; `cli.py` lines 101, 792. Note
  the doc's line numbers above (87/498/516/835) had already drifted from other edits landing in `cli.py` since this
  issue was filed 2026-07-31 — verified the correct current locations by reading full file content and matching the
  doc's quoted string text (`"KEY #2/DP-WATCHER-003"`, `"DP-WATCHER-003 off this sweep"`,
  `"skipping DP-WATCHER-003 this sweep"`), not by trusting the stale numbers. `cli.py:167`'s `DP-WATCHER-002` (sibling
  watcher) and other sibling references (`-005`, `-006`) confirmed untouched — full-file re-read after editing.
  Comment/docstring/log-string only, zero type-relevant surface touched. **Blocked on shipping** by an unrelated,
  pre-existing basedpyright ratchet break (1261 > 1259, zero deployment-service source involved) — filed as
  `plans/active/issues/deployment_service_basedpyright_ratchet_broken_by_dep_backmerge_2026_08_15.md`. Do not redo this
  work — resume by fixing that blocker, then `quickmerge.sh` this file alongside the sibling exit-code-monitor fix
  (`plans/active/issues/dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md` Todo 2), both currently sitting
  uncommitted in the same working tree for the same reason.
**context-scout 2026-08-17**: populated/refreshed context_scope (2 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **2026-08-22 — ruling D13 (Basedpyright ratchet 1259 vs 1261)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Deeper bisection first — ratchets-only-go-down is a HARD RULE and a
  cross-slot measurement shows 1259 is reachable on a current tree; raise only as last resort. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
