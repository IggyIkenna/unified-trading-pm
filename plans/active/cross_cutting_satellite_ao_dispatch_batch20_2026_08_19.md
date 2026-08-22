---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 20 — 2026-08-19
summary: >-
  Second extraction batch from the cross-cutting tranche's 2026-08-19 `/ag-closeout-audit` run (Phase 1 Workflow, 49
  never-cited candidates) — 3 conflict-cleared, bounded/deterministic items from 3 source docs. Named batch20, not
  batch19, because a concurrent `ag_closeout_auditor` dispatch on the same slot (this run's own "Track A" reconcile
  pass, see `ag_closeout_audit_cross_cutting_parked_2026_08_19.md`) independently ran the same Phase 1 population and
  shipped `cross_cutting_satellite_ao_dispatch_batch19_2026_08_19.md` first (`unified-trading-pm@697c15573e`) — its 6
  items and this batch's 3 items are from DISJOINT source docs (verified by direct comparison, zero overlap), so
  this is genuinely additive, not a duplicate. `status: draft` per the skill's safety rail.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-library, alerting-service, execution-service, strategy-service, deployment-service]
scope: [engineer, admin]
tags: [cross-cutting, ao-dispatch, satellite-batch, ag-closeout-audit, data-pipeline]
related:
  [
    /plans/active/issues/manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md,
    /plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md,
    /plans/active/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch19_2026_08_19.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
milestone: M2
estimate_class: infra
estimate_baseline_ai_days: 0.7
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md,
    /plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md,
    /plans/active/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md,
  ]
source: >-
  `/ag-closeout-audit cross-cutting` run 2026-08-19 (ag_closeout_auditor scheduled worker, dispatch agt-ae73cd, slot
  27). Phase 0 via `generate_ag_closeout_audit_candidates.py --tranche cross-cutting` (162 members, 50 never-cited).
  Phase 1 `Workflow` (49 agents). Conflict-check: grepped all 16 covering docs AND
  `cross_cutting_satellite_ao_dispatch_batch19_2026_08_19.md` (this session's sibling batch) for each item's source
  basename + content-signal terms before drafting — zero hits anywhere for any of the 3 items below.
---

# cross-cutting satellite AO dispatch batch 20

## From `manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md`

- [ ] [DATA] P2. Investigate + fix the manifest_writer per-VM shard flush scaling gap: (a) whether an append-only
      delta-shard pattern is viable at the `unified-trading-library` manifest_writer `_writer_io.py` write path,
      (b) whether making the flush debounce entries-threshold dominant over the interval-threshold helps large
      shards specifically; implement whichever approach (or both) resolves the scaling issue, then add a
      regression test per the source doc's own todo 3 (explicitly sequential on whichever of (a)/(b) ships,
      combined into one todo here for that reason). Done when: a stated implementation decision with evidence, the
      fix shipped, and a regression test added and green. Source:
      `/plans/active/issues/manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md` (all 3
      remaining items). Repo: unified-trading-library.

## From `live_path_has_no_stale_producer_revocation_2026_08_14.md`

- [ ] [CODE] P1. Wire `dependency_health_policy` to a real actuator for the LIVE path (the batch path already has
      one — this mirrors it): inject a `probe_fn`, register it for execution-service and strategy-service, and
      wire a SEV0 finding through to the kill-switch bus. Done when: the actuator fires on a deliberately-induced
      SEV0 condition in a test/staging check and the kill-switch bus receives it. Source:
      `/plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md` item 1 (line ~190). Repo:
      alerting-service.
- [ ] [TEST] P0. Add an anti-inertness CI guard for the live path, mirroring the existing batch-path guard (same
      doc, already-closed precedent). Done when: the new guard is present in CI and fails when the live path's
      actuator is deliberately disabled in a test commit. Source:
      `/plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md` item 2 (line 199-201). Repo:
      unified-trading-pm (CI config) + alerting-service (the guarded code path).

## From `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`

- [x] ✅ [INFRA] P0. Re-enable `uts-prod-dp-exit-code-monitor-cron` — unified-trading-pm@(this commit). Verified
      the deploy is actually live off `deployment-service:latest` (not `deployment-api:latest` as originally
      assumed — deployment-service has its own dedicated Cloud Build trigger), confirmed the deployed image (build
      `a4d3bfd6`, commit `59306b7`, deployed 2026-08-22T08:44:14Z) already contains both incident fixes, resumed
      the scheduler, and watched 4 fleet-size samples over ~15min (3+ firings): stable at 3, zero duplicate-cell
      dispatch. Full detail + evidence:
      `/plans/active/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` Progress Log 2026-08-22.

## Progress Log

- **2026-08-19 (ag_closeout_auditor, dispatch agt-ae73cd, slot 27)**: drafted as the second cross-cutting extraction
  batch from today's `/ag-closeout-audit` run, after discovering a concurrent same-slot dispatch
  (`ag_closeout_auditor` "Track A", see the parked-findings doc's Progress Log) had independently run the same
  Phase 1 Workflow population and shipped `batch19` first (`unified-trading-pm@697c15573e`) covering 6 DIFFERENT
  source docs. Compared both batches item-by-item before drafting — zero source-doc overlap — so this batch's 3
  items are genuinely additive. Full tranche orphan taxonomy (what's in batch19, what's in batch20, and the ~17
  remaining deferred docs with their gating reason) is in
  `ag_closeout_audit_cross_cutting_parked_2026_08_19.md`.
- **2026-08-22 — ruling D8 (Draft satellite batches activation)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Promote all — already conflict-checked, vetted work idle only for
  lack of sign-off. Re-ran the conflict-check fresh (2026-08-22): confirmed `mdps_fleet_duplicate_relaunch_
  explosion_2026_08_15.md`'s sole open todo (the `uts-prod-dp-exit-code-monitor-cron` re-enable) is claimed only
  here — the two other docs citing that source (`cefi_satellite_ao_dispatch_batch20_2026_08_16.md`,
  `prediction_satellite_ao_dispatch_batch14_2026_08_19.md`) explicitly did NOT claim this item (one already
  shipped a different pair of items concurrently, the other explicitly flagged-not-claimed as cross-AG-out-of-
  scope); and `live_path_has_no_stale_producer_revocation_2026_08_14.md`'s two claimed todos (actuator wiring,
  anti-inertness guard) are distinct from `producer_silence_flatten_protocol_2026_08_14.md`'s already-shipped,
  explicitly-scoped-narrower producer-liveness-detection slice ("the other 22 todos... remain open — this was a
  deliberately scoped slice, not a claim on the rest of the plan"). No conflicts found. Flipped `status: draft` →
  `active` above. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
