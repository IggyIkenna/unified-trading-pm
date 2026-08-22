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
    /plans/archive/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch19_2026_08_19.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-22"
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
    /plans/archive/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md,
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

- [x] ✅ [CODE] P1. Wire `dependency_health_policy` to a real actuator for the LIVE path (the batch path already has
      one — this mirrors it): inject a `probe_fn`, register it for execution-service and strategy-service, and
      wire a SEV0 finding through to the kill-switch bus. Done when: the actuator fires on a deliberately-induced
      SEV0 condition in a test/staging check and the kill-switch bus receives it. Source:
      `/plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md` item 1 (line ~190). Repo:
      alerting-service. — `unified-api-contracts@b429c9a7`, `alerting-service@e7e7840d6f`,
      `deployment-service@b1b42ad646` (2026-08-22, slot-13). Added `DependencyHealthPolicy.kill_switch_scope`
      (opt-in, `None` default — zero behavior change for the other ~25 external/cloud-infra policies); registered
      `execution_service_health` (scope=GLOBAL) + `strategy_service_health` (scope=STRATEGY,
      `hard_escalation_seconds=900` matching the operator-ruled producer-silence SLA) in
      `deployment-service/configs/dependency_health_policies.yaml`; wired `_maybe_arm_kill_switch` into
      `dependency_health_event_handler.py` (fires `get_kill_switch_bus().fire()` only for
      `DEPENDENCY_DEGRADED_CRITICAL` + a policy that opts in — every other dependency's paging path is
      byte-identical to before); added `dependency_health_runner.py` (a real HTTP `probe_fn`, fail-open when no
      URL configured, mirroring `provider_health_probe.py`'s pattern) and wired it into `main.py`'s live-mode
      background tasks — the FIRST production `DependencyHealthProber` construction in the fleet. Removed the
      xfail markers from 2 of the 3 anti-inertness guards this satisfies
      (`test_the_prober_runs_in_production`, `test_a_critical_dependency_alert_reaches_an_actuator_not_only_a_channel`)
      — the third (`test_the_prober_emits_the_event_its_consumer_waits_for`) is outside this item's scope and
      stays xfail. New tests directly prove the "Done when" bar end-to-end: a deliberately-induced SEV0 (probe
      failing past both the consecutive-failure threshold and `hard_escalation_seconds`) drives the REAL prober +
      handler + rule ladder and asserts the kill-switch bus receives `fire(scope, None, ...)` — see
      `tests/unit/test_dependency_health_runner.py::TestDeliberatelyInducedSev0ReachesKillSwitch`. Also fixed an
      unrelated pre-existing QG-red condition hit mid-ship (2 new-baseline broad-except sites in
      `stablecoin_issuer_pause_subscriber.py`, confirmed pre-existing via a byte-identical clean-tree re-check) by
      adding cited `# noqa: broad-except` annotations — bundled into the same alerting-service ship since it was
      blocking every commit to the repo, not just this one. Full design rationale (why GLOBAL for
      execution-service, why STRATEGY with `scope_key=None` for strategy-service, why the 2 internal policies are
      hand-authored in `dependency_health_runner.py` rather than loaded from deployment-service's YAML at
      runtime) is in the code comments at each decision point — see `dependency_health_runner.py`'s module
      docstring and the YAML's own inline comments on the 2 new entries.
- [x] ✅ [TEST] P0. Add an anti-inertness CI guard for the live path, mirroring the existing batch-path guard (same
      doc, already-closed precedent). Done when: the new guard is present in CI and fails when the live path's
      actuator is deliberately disabled in a test commit. Source:
      `/plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md` item 2 (line 199-201). Repo:
      unified-trading-pm (CI config) + alerting-service (the guarded code path). — `alerting-service@80a7c52aa5`
      (2026-08-22, slot-8). See Progress Log for what already existed vs what this closed.

## From `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`

- [x] ✅ [INFRA] P0. Re-enable `uts-prod-dp-exit-code-monitor-cron` — done 2026-08-22 (slot 7, infra),
      `unified-trading-pm` doc-only (no service-repo code change; pure infra-ops verification + a live
      `gcloud scheduler jobs resume`). Verified the deploy was actually live off `deployment-service:latest`
      (not `deployment-api:latest` as this todo's own original text assumed — deployment-service has its own
      dedicated Cloud Build trigger), confirmed the deployed image (build `a4d3bfd6`, commit `59306b7`, deployed
      2026-08-22T08:44:14Z) already contains both incident fixes, resumed the scheduler, and watched fleet-size
      samples across multiple firings (spanning a session restart): stable/non-climbing, zero duplicate-cell
      dispatch. Full detail + evidence:
      `/plans/archive/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` Progress Log 2026-08-22 (now
      archived — this was its sole remaining open todo).

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
- **2026-08-22 (slot-8, backend_engineer/data_engineering)**: Item 3 (anti-inertness CI guard for the live path)
  — found `alerting-service/tests/unit/test_dependency_health_not_inert.py` already existed (shipped 2026-08-14
  by slot-4, predates this plan), carrying two `xfail(strict=True)` guards covering the PRODUCER side only
  (`DependencyHealthProber` constructed in production; the prober emits `DEPENDENCY_DEGRADED`). Neither covers
  the issue doc's actual ask for this todo — "assert the dependency-health policy has a non-test consumer that
  changes behaviour (not just logs/pages)". Confirmed by reading `dependency_health_event_handler.py`:
  `handle_dependency_health_payload` routes every alert through `route_event_with_explicit_channels` (paging
  only), never `route_event` (the only path that calls `publish_kill_switch_event`), and no
  `DEPENDENCY_DEGRADED*` rule_id is registered in UAC's `LIVE_ALERT_RULES` either — so even a fully-wired
  CRITICAL dependency alert cannot reach the kill switch today. Added a third `xfail(strict=True)` guard
  (`test_a_critical_dependency_alert_reaches_an_actuator_not_only_a_channel`), scoped to
  `dependency_health_event_handler.py`'s own source specifically rather than a whole-tree search — those
  actuator functions are already called elsewhere in alerting-service for other alert families, so a tree-wide
  check would have passed today for the wrong reason (the exact false-negative shape the file's own emit-guard
  docstring already warns about). Updated the module docstring and renamed `test_both_guards_are_strict` →
  `test_all_guards_are_strict` to cover all three. QG green (ran twice — the first pass ran pre-commit by
  mistake, so re-ran post-commit to key the sentinel to the actual shipped SHA); STEP 5.107 (untracked
  xfail/skip markers) passed, confirming the new marker correctly cites the tracked issue slug; test run showed
  `1075 passed, 3 xfailed`, all three for the expected reasons. Shipped `alerting-service@80a7c52aa5`,
  independently ancestor-verified on `origin/live-defi-rollout` (not just quickmerge's own "Landed" message).
  Item 2 (CODE, the actual actuator wiring — probe_fn injection, service registration, kill-switch wiring) is
  unaffected by this and remains open for its own separate work; this guard's xfail markers are exactly what
  will force that future change to also update this file. No literal CI-config file needed touching in
  unified-trading-pm — this test is picked up automatically by alerting-service's existing `quality-gates.sh`
  pytest run like every other test in the suite.
- **2026-08-22 (slot 7, infra)**: Item 3 (cron re-enable) done — verified deploy propagation was already complete
  (`deployment-service:latest` image, not `deployment-api:latest`), resumed
  `uts-prod-dp-exit-code-monitor-cron`, watched fleet size stable/non-climbing across multiple firings including
  across a session restart. Closed the sole remaining todo in
  `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` and archived that doc per the archive-immediately rule
  (`git mv` to `plans/archive/issues/`, `status: resolved`, banner added) — updated this plan's own `related:`
  and `context_scope:` entries to point at the new archive path in the same commit.
