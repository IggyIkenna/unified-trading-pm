---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 19 — 2026-08-19
summary: >-
  Extraction batch from the cross-cutting tranche's 2026-08-19 `/ag-closeout-audit` sweep (Phase 1 Workflow, 49
  never-cited candidates classified) — 6 conflict-cleared, bounded/deterministic items pulled from 6 distinct source
  docs (`orphaned_never_touched`, `ao_eligible: true`). Each todo cites its exact source doc; the source doc's own
  remaining checkbox(es) get flipped with a citation once the work lands, not duplicated here. Conflict-checked
  against every existing cross-cutting satellite batch (1b, 13-18) and both consolidated-closeout docs before
  drafting via a basename grep across all of them — zero hits for any of the 6 target docs, so nothing here
  duplicates ground an existing dispatched todo already claims. `status: draft` per CLAUDE.md's "Plan destination —
  ASK BEFORE CREATING" HARD RULE — never auto-shipped, requires explicit operator approval to flip `active`.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, deployment-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [cross-cutting, ao-dispatch, satellite-batch, ag-closeout-audit]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/dp_exit_code_monitor_cadence_stale_after_hourly_reconcile_2026_08_19.md,
    /plans/active/issues/docs_reconcile_bigger_scope_findings_2026_08_19.md,
    /plans/archive/2026_08/data_pipeline_alerts_batch_remediation_2026_07_15.md,
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
    /plans/active/mvp_could_exist_rollup_dual_scope_2026_08_12.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
milestone: M2
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source: >-
  `/ag-closeout-audit cross-cutting` run 2026-08-19 (ag_closeout_auditor, dispatch agt-ae73cd, slot 27). Phase 1
  Workflow (49 agents, one per never-cited candidate) found 7 orphaned_never_touched + ao_eligible:true docs; 6 had
  a clean, conflict-free, single-bounded-item extraction (the 7th,
  `plan_reconciler_findings_security_and_cross_cutting_master_2026_08_19.md`, has real open work but it's a ~35-item
  "Filed" list from today's epic-wide sweep, not a single bounded item — left for a future batch to extract
  individually rather than force one oversized todo here).
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
---

# Cross-cutting satellite AO dispatch batch 19 (2026-08-19)

Every todo below cites its exact source doc + a Done-when clause. Flip the source doc's own citation the same way
prior batches have (a dated note + checkbox flip), not duplicated here.

## Todos

- [ ] [INFRA] P2. Close the 2 remaining open todos in
      `dp_exit_code_monitor_cadence_stale_after_hourly_reconcile_2026_08_19.md` — backport the live `0 * * * *`
      schedule into `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`'s `dp_exit_code_monitor_cron` resource
      (declared value only, do NOT `terraform apply`) and wire a Cloud Build push-trigger (path-filtered to
      `deployment_service/**` + the cloudbuild file) for `cloud-build/deployment-service-jobs-image.cloudbuild.yaml`
      mirroring deployment-api's existing auto-deploy trigger pattern. Repo: deployment-service. Source:
      `plans/active/issues/dp_exit_code_monitor_cadence_stale_after_hourly_reconcile_2026_08_19.md`. Done when: the
      terraform file's declared schedule matches live `gcloud scheduler jobs describe` output AND
      `gcloud builds triggers list` shows a trigger firing on `deployment_service/**` pushes to main, with both
      source-doc checkboxes flipped citing evidence.
- [ ] [SCRIPT] P2. Fix the 4 bounded (non-BIG-finding) doc-reconciliation items from
      `docs_reconcile_bigger_scope_findings_2026_08_19.md` — rewrite `runtime-deployment-topology.md`'s 6
      PBM-as-standalone sections/diagrams to say "embedded in strategy-service per 2026-05-20/2026-08-18"; audit
      which of `quality-gates-template.sh`/`quality-gates-service-template.sh` is actually live-consumed and
      reconcile both it and `quality-gates.md`'s Canonical Template section with the already-shipped
      `--cov-fail-under` removal; add `install-local-ratchet-gate-breach-detector-timer.sh`'s row to
      `agent-orchestrator-scheduled-jobs.md`'s timer table; rewrite `launcher-script-ssot.md`'s features-service
      consolidation narrative to match the real `launch-features-*.sh` hybrid file list. Leave findings #1
      (`cefi-batch-live.md` `EXPECTED_INSTRUMENT_NOT_LISTED`) and #3 (self-hosted-runners ADR vs `ci_master.md`) as
      separate operator/domain-owner-gated BIG findings untouched. Repo: unified-trading-pm. Source:
      `plans/active/issues/docs_reconcile_bigger_scope_findings_2026_08_19.md`. Done when: all 4 target docs match
      their cited ground-truth source files/scripts and the source doc's Progress Log cites each of the 4 fixes.
- [x] ✅ [REVIEW] P0. RESOLVED — read 34+ days of live `#data-pipeline-alerts` history (720h via
      `scripts/dev/slack-read-channel.py`, 56,706 messages) and confirmed a `:white_check_mark: RESOLVED` bookend has
      posted for EVERY sports/tradfi/cefi cell that fires `DP_RUN_MOSTLY_EMPTY`, including `tradfi/mbp_10` (the cell
      this source doc's own dead-cell-suppression fix targeted) — the 2026-07-15/16 dedup fix is proven working live,
      no code fix needed. Full evidence in the source doc's own flipped checkbox. Source doc had 0 open todos left
      after this flip — archived to
      `plans/archive/2026_08/data_pipeline_alerts_batch_remediation_2026_07_15.md`. Also flipped the duplicate
      finding in `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_19.md` and fixed the 3 active-corpus
      referrers (`plans/epics/observability_master.md`,
      `plans/active/issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`) that linked the old active path.
- [ ] [DATA] P2. File instruments-service's BYBIT daily-catalog publish-timing gap (catalog for a given UTC day
      absent at every check from VM boot through ~06:02 UTC, appearing only ~06:07:55 UTC, confirmed 2026-08-14 and
      08-15) as its own tracked instruments-service issue doc, then re-check the current
      `mtds-live-cefi-consolidated-*` VM's per-VM manifest shard for a captured BYBIT-FUTURES row now that
      `market-tick-data-service@5f88715e4b` (the PERPETUAL/FUTURE subscribe filter) has shipped. Repo:
      instruments-service + market-tick-data-service (read-only check). Source:
      `plans/active/cross_ag_live_capture_parity_2026_08_14.md` Finding C. Done when: the IS issue doc exists citing
      this evidence, and the manifest-check result (captured row found, or still `empty_confirmed` with the running
      VM's launch timestamp noted relative to the fix's ship date) is recorded back into
      `cross_ag_live_capture_parity_2026_08_14.md` Finding C.
- [ ] [AGENT] P2. Correct the stale "~16 genuinely live" DeFi-execute figure to the reachability-derived "6 of 32
      (19%)" in `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md` and any other client-facing
      disclosure artifact still citing it, per `e2e_wiring_reachability_audit_2026_08_15.md`'s own re-derived table.
      Repo: unified-trading-pm. Source: `plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md`. Done
      when: `grep` for `"~16 genuinely live"`/`"16 genuinely live"` across `plans/` and
      `codex/14-customer-journeys/` returns zero non-archived hits.
- [ ] [BACKEND] P2. Re-check `mvp_could_exist_rollup_dual_scope_2026_08_12.md`'s blocked todo 7 now that its blocker
      chain (`data_status_rollup_ml_service_full_blob_missing_2026_07_26.md` +
      `multi_timeframe_stall_residual_gap_2026_08_15.md`) is archived-resolved: read live GCS metadata
      (generation/timestamp) for all 14 `_DEFAULT_SERVICES` `full.json.gz` blobs and, if every one postdates the
      2026-08-16 fix in the dual-scope shape, delete the `unwrap_scope_compat` transition fallback and flip todo 7.
      Repo: ml-service (or wherever the rollup script lives — see source doc). Source:
      `plans/active/mvp_could_exist_rollup_dual_scope_2026_08_12.md` todo 7. Done when: fallback removed with full
      `quality-gates.sh` green and a live-GCS citation proving every service's blob postdates the fix, OR the todo
      is updated with a precise, dated list of which specific services still lack a fresh dual-scope blob.

## Deferred (not extracted this batch)

- `plans/active/issues/plan_reconciler_findings_security_and_cross_cutting_master_2026_08_19.md` —
  `orphaned_never_touched`, `ao_eligible: true` per the Phase 1 classification, but its remaining open work is a
  ~35-item "Filed" list from today's epic-wide 233-doc `/plan-reconcile` sweep (contradictions, AO-readiness
  defects, hedge-pointers, structural findings), not one bounded item — needs its own extraction pass (likely
  several distinct todos across multiple future batches), not a single line here. Time-gated on someone doing that
  extraction read, not operator-gated or conflict-gated.

## Progress Log

- **2026-08-19** — Drafted from the `/ag-closeout-audit cross-cutting` run's Phase 1 Workflow output (49 candidates
  classified, 7 `orphaned_never_touched` + `ao_eligible:true`, 6 extracted cleanly here — conflict-check against
  every existing cross-cutting batch + both closeout docs found zero overlap for all 6). `status: draft` — awaiting
  operator approval to dispatch.
- **2026-08-22 — ruling D8 (Draft satellite batches activation)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Promote all — already conflict-checked, vetted work idle only for
  lack of sign-off. Re-ran the conflict-check fresh (2026-08-22) across all 7 source docs (`dp_exit_code_monitor_
  cadence_stale_after_hourly_reconcile_2026_08_19`, `docs_reconcile_bigger_scope_findings_2026_08_19`,
  `data_pipeline_alerts_batch_remediation_2026_07_15`, `cross_ag_live_capture_parity_2026_08_14`,
  `e2e_wiring_reachability_audit_2026_08_15`, `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14`,
  `mvp_could_exist_rollup_dual_scope_2026_08_12`) — no other active plan claims the same specific sub-items this
  batch targets. Flipped `status: draft` → `active` above. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
