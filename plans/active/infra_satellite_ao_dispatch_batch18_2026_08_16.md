---
doc_type: plan
title: Infra satellite — alert-driven-revocation follow-up work (batch 18)
summary: >-
  `/na-eligibility-audit` extraction (scoped run, 2026-08-16), NOT a full tranche sweep. Three items from
  `revocation_arming_2026_08_14.md` / `alert_driven_dependency_revocation_2026_08_12.md` were left open at the end of
  this session's work — each re-assessed against the bounded/deterministic-outcome bar and found AO-eligible (no
  operator judgment call blocking the outcome itself), just defaulted to NA along with the rest of those plans. The
  source plans stay `assigned_vm: NA` — only these 3 extracted items are dispatchable here.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: [infra, ao-dispatch, revocation, alerting, satellite, batch-18]
related:
  [
    /plans/archive/2026_08/revocation_arming_2026_08_14.md,
    /plans/active/alert_driven_dependency_revocation_2026_08_12.md,
    /plans/active/issues/dp_revocation_release_never_resolves_identity_2026_08_15.md,
    /plans/active/issues/dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 1.0
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
context_scope: [deployment-service/deployment_service/data_pipeline_monitors/revocation_actuator.py, deployment-service/deployment_service/data_pipeline_monitors/consolidator_scheduler_watcher.py, deployment-service/deployment_service/data_pipeline_monitors/meta_targets.py, deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py, deployment-service/deployment_service/data_pipeline_monitors/escalation.py, deployment-service/scripts/recovery/_durable_state.py, /plans/archive/2026_08/revocation_arming_2026_08_14.md, /plans/active/alert_driven_dependency_revocation_2026_08_12.md]
supersedes:
superseded_by:
depends_on: []
source: >-
  /na-eligibility-audit, scoped run 2026-08-16 (operator-requested, scoped strictly to the 3 items below, not a
  tranche sweep) — see the conflict-check evidence in each item below and in this doc's own Progress Log.
---

# Infra satellite — alert-driven-revocation follow-up work (batch 18)

> **Scope note**: this batch was NOT produced by a full `/na-eligibility-audit` tranche run. It is a deliberately
> narrow, operator-requested extraction of exactly 3 items already known to be open at the end of a single session's
> work on `revocation_arming_2026_08_14.md`. Do not treat its absence of other extracted items as evidence those plans'
> remaining content was swept — it wasn't.

## Conflict-check (per `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3)

Checked all 4 surfaces for each item before extraction:

- **Active `assigned_vm: planning` plans under `parent_epic: observability_master`**: none claim any of the 3 items
  below by mechanism (grepped `consolidator_bucket_resolver`, `state_bucket()`, `RevocationActuator.release`,
  `_pause_schedulers` across the whole active plans+issues corpus).
- **Two genuinely related, non-duplicate issue docs found** (milestone-only overlap, not a conflict — both cross-cited
  in the relevant items below rather than silently ignored):
  - `plans/active/issues/dp_revocation_release_never_resolves_identity_2026_08_15.md` (P1, its own core fix already
    shipped `[x]`) — a DIFFERENT bug in the same release/close-bookend pathway: the release CALL SITE couldn't resolve
    an alert identity at all (fixed). Item 2 below is downstream of that fix, not a duplicate of it — release() can now
    actually be reached for FLEET_HALT identities, which is what makes item 2's gap observable/worth fixing.
  - `plans/active/issues/dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md` (P0, open) — the sweep-timeout
    root cause that `DP-VM-013` (registered this session, `unified-api-contracts@a2734aa9ba`) gives a POLICY to, not a
    fix for. Registering the policy did not resolve this issue; it remains open and is NOT part of this batch.
  - `plans/active/issues/defi_collect_schedulers_paused_since_2026_07_18_2026_08_16.md` cites
    `RevocationActuator._pause_schedulers` only as a ruled-out diagnosis (confirmed NOT the FLEET_HALT mechanism, a
    manual pause instead) — no overlap with item 2 below.
- **No sibling batch/finalize doc** for this topic exists yet (`infra_satellite_ao_dispatch_batch1..17` — none mention
  revocation/consolidator_bucket_resolver/RevocationActuator.release by grep).
- **No `status: draft` legacy artifact** for this topic found.

Verdict: clear on all 3 items — proceed.

---

- [ ] [SCRIPT] P0. **Measure p95 and max shard duration per launcher family from `vm-logs/` run.log PROGRESS
      markers** — the drain-budget denominator (worst-case waste = longest-shard-duration × dependent-count).
      Genuinely open, NOT blocked — re-verified 2026-08-17 (review-craft, slot 24): the orchestrator VM's own
      environment resolves `scripts.recovery._durable_state.state_bucket()` correctly
      (`deployment-scripts-central-element-323112`, confirmed live via direct call, not the empty string a plain dev
      checkout got on 2026-08-14/2026-08-16). The prior dev-checkout-only observation never named itself a permanent
      block — it explicitly asked the next worker to check the orchestrator VM FIRST, which this note now closes out.
      The remaining work is unattempted: list `vm-logs/{vm}/run.log` under bucket
      `deployment-scripts-central-element-323112` (`deployment_service/data_pipeline_monitors/_gcs.py`'s
      `RUN_LOG_BLOB`), parse each VM's PROGRESS markers, group by launcher family, compute p95/max shard duration per
      family. Do the actual measurement — do not re-run the credential check. Repo: deployment-service.
      **IN PROGRESS 2026-08-17 (slot 27) — do NOT re-attempt the credential check, do NOT re-derive the approach,
      just resume/finish this exact attempt**: wrote `deployment-service/scripts/measure_shard_duration_p95.py`
      (currently UNCOMMITTED, untracked — real file on disk in the repo working tree, not scratchpad) — lists every
      `vm-logs/{vm}/run.log` blob (14,040 found), resolves each `vm_name` to a launcher family via
      `launcher_registry.resolve_launcher_for_vm`, reuses the fleet monitors' own `_PROGRESS_RE`/`_LOG_TS_RE` (from
      `data_pipeline_monitors/_gcs.py`) to find shard-write timestamps per VM, pools the inter-write deltas per
      family, computes p95/max. A 30s smoke test (62/13891 blobs) already produced a real, plausible-shaped
      distribution (e.g. `launch-mtds-dex-swaps-backfill-vm.sh` p95=7373.5s/max=34072s;
      `launch-cefi-forward-poll.sh` p95=5.0s/max=2664s — heavy-tailed, as expected for backfill launchers). A full
      900s-budget, concurrency=10 run was launched in the background (`--output /tmp/shard_duration_p95.json`) —
      **check `/tmp/shard_duration_p95.json` and the launching shell's captured stdout first; if both are gone
      (session/host restart), just re-run**: `cd deployment-service && .venv/bin/python
      scripts/measure_shard_duration_p95.py --time-budget-seconds 900 --concurrency 10 --output
      /tmp/shard_duration_p95.json` (~15 real minutes; full coverage of all 13,891 relevant blobs is NOT expected —
      the script reports its own sampled coverage, which is the intended, documented method, not a shortfall). Some
      individual `download_bytes` calls stall past the 30s per-call timeout on a few very large/old logs
      (`_gcs.py`'s own bounded-retry logic already handles this — logged WARNING, not a failure) — expected, not a
      bug to chase. Once the full run's stdout table + JSON exist: (1) `git add
      deployment-service/scripts/measure_shard_duration_p95.py`, run `quality-gates.sh` (not yet run this session —
      do NOT skip it), commit + quickmerge; (2) paste the final per-family p95/max table into this todo and flip it
      `[x]`; (3) **once flipped, every todo in this plan is done — archive this plan** per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual), and check whether
      `alert_driven_dependency_revocation_2026_08_12.md`'s own CANCELLED/SUPERSEDED line for this item (line ~108)
      needs anything further (it already point here, just confirm no dangling reference remains once this plan
      archives).
- [x] ✅ [CODE] P2. **Wire `RevocationActuator`'s `consolidator_bucket_resolver` into a real production call site.**
      — `deployment-service@ae49548487` (2026-08-17). Broke the cycle with two leaf-module extractions rather than
      the single meta_targets->meta_watchers fix originally scoped: (1) `freshness_target.py` — `FreshnessTarget` +
      `DEFAULT_CATALOGUE_MAX_AGE_MIN` moved out of `meta_watchers.py`, so `meta_targets.py` no longer imports
      `meta_watchers` at all (re-exported from `meta_watchers.py` for existing callers/tests); (2)
      `consolidator_bucket_map.py` — `consolidator_job_to_bucket` moved out of `consolidator_scheduler_watcher.py`,
      since that module ALSO imports `escalation.py`/`meta_watchers.py` directly (for `EscalationTier`/`PipelineFinding`/
      `_emit`/`MissTracker`) — fixing only the `meta_targets` edge would have left those two direct edges cycling.
      Both prod call sites now pass the resolver: `escalation.py`'s `_apply_revocation` (FLEET_HALT delivery) and
      `meta_watchers.py`'s release bookend. Verified: `python3 -c "import ..."` clean for all 7 touched/new modules
      (freshness_target, consolidator_bucket_map, meta_targets, meta_watchers, escalation,
      consolidator_scheduler_watcher, revocation_actuator); 403 tests green
      (`test_revocation_actuator.py` + `test_data_pipeline_monitors.py` + `test_data_pipeline_monitors_cli.py`);
      full `quality-gates.sh` green. Repo: deployment-service.
- [x] ✅ [CODE] P2. **`RevocationActuator.release()` never resumes a FLEET_HALT's paused Cloud Scheduler jobs — only
      clears the generic hold/drain GCS marker.** `_pause_schedulers()` (the open half) calls
      `scheduler_maintenance.make_scheduler_pauser()` per job; `release()` has no symmetric `_resume_schedulers()` —
      confirmed by reading `release()`'s full body, not assumed from its docstring. A FLEET_HALT that opens has no
      code path that ever closes the actual pause; someone must resume it by hand today. Needs: (1) a way to recover
      which specific jobs THIS actuation paused (the actuator does not currently persist that list anywhere durable —
      check whether the existing `ShardedState` actuation-budget record can carry it, or whether a new small record is
      needed), (2) a `_resume_schedulers()` mirroring `_pause_schedulers()`'s shape, wired into `release()` for the
      `FLEET_HALT` action specifically. Cross-reference
      `/plans/active/issues/dp_revocation_release_never_resolves_identity_2026_08_15.md` before starting — its P1 fix
      (already shipped) is what makes `release()` reachable for FLEET_HALT identities at all; this todo assumes that
      fix is live. Needs real tests (this is pause/resume behavior on production scheduler jobs, not a nicety) — mirror
      the existing `_pause_schedulers` test shapes in `tests/unit/test_revocation_actuator.py`. Repo: deployment-service.
      — **deployment-service@7302b037e7** (2026-08-17). Added `_resume_schedulers()` mirroring `_pause_schedulers()`'s
      shape; wired into `release()` specifically for `FLEET_HALT`. Resolved question (1) by NOT persisting a job list:
      `_scheduler_jobs_for(target)` is already a pure function of `target` against the static UAC `SCHEDULER_REGISTRY`
      — the same lookup `_pause_schedulers` itself uses — so the job set is recomputed on release rather than carried
      through the `ShardedState` actuation-budget record (which only COUNTS actuations and has no read-back-the-payload
      method; overloading it would have been the wrong tool). Nothing can drift from what was paused, and a resume
      against an already-ENABLED job (e.g. one whose own pause call failed and was skipped) is a harmless no-op caught
      by the same per-job try/except tolerance `_pause_schedulers` already has — partial failure never abandons the
      rest. 6 new tests in `tests/unit/test_revocation_actuator.py` mirror the existing pause/release shapes: resume
      fires on FLEET_HALT release, the marker clear and the resume both happen, non-FLEET_HALT releases never touch
      schedulers, a failing resume doesn't abandon the remaining jobs, an unrecognised target resumes nothing, and a
      fresh actuator instance (no memory of the original `actuate()` call) still resumes correctly. Full
      `quality-gates.sh` green (3437 passed, 0 failed, sentinel-verified on the landed SHA).

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (8 entries)
- **2026-08-17 (slot 24, review-craft)**: classified item 1's flagged
  `ao_dispatch_visibility_gate_accidental_exclusions_2026_08_17.md` exclusion — verified live that
  `state_bucket()` resolves on the orchestrator VM (bucket `deployment-scripts-central-element-323112`), so the
  todo was genuinely open, not a legitimate block. Rewrote the todo to drop the stale `BLOCKED-CREDENTIALS`
  phrasing (which was tripping the AO dispatch-visibility parser's undeclared-marker exclusion) so it dispatches
  normally; the actual p95/max shard-duration measurement remains unattempted for a future SCRIPT-craft worker.
