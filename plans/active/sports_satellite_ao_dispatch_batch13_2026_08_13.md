---
doc_type: plan
title: sports satellite AO dispatch batch 13 — 2026-08-13
summary: >-
  Extraction batch from the sports tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep — 16 live
  conflict-cleared, bounded/deterministic items (21 total todos, 5 marked out-of-scope, see below) pulled directly from
  10 source docs (RECLASSIFY_SPLIT bounded items from the NA audit, orphaned_never_touched/orphaned_partial_coverage
  bounded items from the AG-closeout audit). Rescoped 2026-08-13 (operator scoping instruction): 5 MDPS/features-service
  backfill/recompute items with no manifest-canonical/migration angle marked [x] OUT-OF-SCOPE (checkbox format per
  todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md -- the source items remain open in their
  own source docs, untouched by this batch; the manifest-corpus-empty features-service investigation item was KEPT live
  -- manifest-canonical work is explicitly in scope even for features-service). Each todo cites its exact source doc;
  the source docs themselves are NOT touched by this batch (checkbox reconciliation back into each source doc happens in
  the paired finalize plan). Conflict-checked against every existing active batch/finalize plan for this tranche via
  basename-citation cross-reference before drafting — no item here duplicates ground an existing dispatched Todos entry
  already claims.
status: draft
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md,
    /plans/active/issues/features_sports_compute_features_hard_fail_missing_upstream_today_2026_08_10.md,
    /plans/active/issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md,
    /plans/active/issues/sports_catalog_dp_catalog_001_oom_manifest_read_2026_08_10.md,
    /plans/active/issues/sports_features_2026_backfill_launch_window_was_today_2026_08_10.md,
    /plans/active/issues/sports_features_dp_vm_001_upstream_fixtures_gap_2026_08_10.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md,
    /plans/active/issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2.4
estimate_calibrated_ai_days: 1.9
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# sports satellite AO dispatch batch 13 — 2026-08-13

> **`status: draft` — NOT ingested/dispatched.** Flip to `status: active` only after operator review. Every todo below
> was classified bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13
> full-sweep audit and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [ ] [CODE] P2. Add a short callout to /codex/15-runbooks/incidents/rb_infra_relaunch.md instructing a worker to check
      whether a failing VM's launcher family has a supervising wrapper (grep deployment-service/scripts/vm/ for a
      _-historical-_ or loop-style caller) before relaunching, mirroring the existing 'if it re-fails the same way
      twice, STOP' pattern already in the runbook Source:
      `plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md`
- [x] [CODE] P2. Once instruments-service has written real 2026-08-10 sports_reference data, --force recompute the
      sports features backfill for day=2026-08-10 (features-service) to replace the false
      empty_confirmed(SOURCE_RETURNED_ZERO) rows the aborted 12:03 UTC run wrote **OUT-OF-SCOPE FOR THIS BATCH
      (2026-08-13, operator scoping instruction)** — MDPS/features-service backfill/recompute work is excluded from this
      batch unless manifest-canonical or migration-related. The underlying item remains open in its own source doc,
      untouched by this batch/commit. Source:
      `plans/active/issues/features_sports_compute_features_hard_fail_missing_upstream_today_2026_08_10.md`
- [ ] [CODE] P2. Track F: root-cause why the features-service sfi_progressive manifest group is corpus-empty (1 manifest
      row) despite a documented 2020->today backfill window Source:
      `plans/active/sports_consolidated_closeout_2026_07_19.md`
- [ ] [CODE] P2. Track C: venue vocabulary cleanup dispositions for the residual non-canonical values (casing/aliasing
      re-stamp + footystats legacy bundle mislabel venue=ODDS_API->FOOTYSTATS, 42,476 rows) Source:
      `plans/active/sports_consolidated_closeout_2026_07_19.md`
- [ ] [CODE] P2. Track C: QG assertion that sports data_type/venue/instrument_type/chain stay within the canonical
      vocabulary (deployment-ui Distinct Values panel reads 0 non-canonical across all four axes) Source:
      `plans/active/sports_consolidated_closeout_2026_07_19.md`
- [ ] [CODE] P2. Track E: repoint the remaining 7-file stale entity=fixtures consumer list to
      fixtures_schedule/fixtures_outcomes Source: `plans/active/sports_consolidated_closeout_2026_07_19.md`
- [ ] [CODE] P2. Track O: repair attempted_at on the 112,277 rows from the named pre-clobber snapshot (a normal,
      human-watched write window, not unsupervised) Source: `plans/active/sports_consolidated_closeout_2026_07_19.md`
- [ ] [CODE] P2. Track O: locate the emitter of the 139,620 venue=ODDS_API/source=api_football/empty_confirmed rows
      before folding into K2 Source: `plans/active/sports_consolidated_closeout_2026_07_19.md`
- [ ] [CODE] P2. Track V: execute the 5-part-proof-gated DELETE of the old raw-keyed league_id GCS objects (COPY+SWAP
      already done, reversibility-verified 604800s soft-delete window, unblocked since 2026-07-28) Source:
      `plans/active/sports_consolidated_closeout_2026_07_19.md`
- [x] [CODE] P2. Clamp the per-year sports features backfill launcher's current-year window to end_date = min(today-1,
      {year}-12-31) so a current-day's not-yet-written upstream reference can never be a hard dependency at backfill
      time -- repo: deployment-service (launcher config/logic change, single deterministic fix). **OUT-OF-SCOPE FOR THIS
      BATCH (2026-08-13, operator scoping instruction)** — MDPS/features-service backfill/recompute work is excluded
      from this batch unless manifest-canonical or migration-related. The underlying item remains open in its own source
      doc, untouched by this batch/commit. Source:
      `plans/active/issues/sports_features_2026_backfill_launch_window_was_today_2026_08_10.md`
- [ ] [CODE] P2. Track upstream sports reference entity=fixtures for day=2026-08-10 until it exists under
      instruments-store-sports-prd; confirm the af-backfill historical backfill writes it when it reaches that date
      (instruments-service reference-capture gap). Source:
      `plans/active/issues/sports_features_dp_vm_001_upstream_fixtures_gap_2026_08_10.md`
- [ ] [CODE] P2. Verify the self-heal actuator dedup (launch_budget_registry) and whether an external launcher loop
      fired ~19 features-sports-sports-* VMs (~8 with empty vm-logs) far beyond the RB-INFRA-RELAUNCH ≤2/(prefix,day)
      bound -- resource-waste investigation. Source:
      `plans/active/issues/sports_features_dp_vm_001_upstream_fixtures_gap_2026_08_10.md`
- [x] [CODE] P2. Recompute day=2026-08-10 sports features once upstream fixtures land -- the 15:42Z compute is sparse
      (row_count 1-2/league, computed from partial upstream) and must not be treated as final. **OUT-OF-SCOPE FOR THIS
      BATCH (2026-08-13, operator scoping instruction)** — MDPS/features-service backfill/recompute work is excluded
      from this batch unless manifest-canonical or migration-related. The underlying item remains open in its own source
      doc, untouched by this batch/commit. Source:
      `plans/active/issues/sports_features_dp_vm_001_upstream_fixtures_gap_2026_08_10.md`
- [ ] [CODE] P2. Verify the 2022 year-sharded features VM (features-sports-sports-2022-20260810-051126, no EXIT_STATUS,
      terminated mid-run) -- confirm 2022 features coverage in the availability index. Source:
      `plans/active/issues/sports_features_dp_vm_001_upstream_fixtures_gap_2026_08_10.md`
- [ ] [CODE] P2. Gate escalation dispatch on already-resolved status (or carry the resolution summary in the boot
      context) so a resolved DP-VM alert cannot spawn a conflicting relaunch worker -- AO/orchestrator, [CODE] P3.
      Source: `plans/active/issues/sports_features_dp_vm_001_upstream_fixtures_gap_2026_08_10.md`
- [ ] [CODE] P2. Re-roll build_instrument_catalogue.py --asset-group sports --since 2019-01-01 to pick up the +26,894
      round rows the § Q/§ T/§ W backfills already closed -- the catalogue snapshot predates them. Tracked only as
      'Track V' prose inside sports_consolidated_closeout_2026_07_19.md, a LOCAL/human plan (not assigned_vm:planning),
      so it does not meet the AO-dispatch coverage bar despite being a real, single-command, deterministic-outcome item.
      Source: `plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`
- [ ] [CODE] P2. Repoint the 7 remaining stale entity=fixtures consumers (sports_dependency.py,
      sports_fixtures_daily_repoll.py, rescan_sports_fixtures_canonical.py:328,452, enumerate_expected_universe.py:1902,
      migrate_sports_per_league.py, reconcile_sports_blank_empty_reason_2026_06_24.py) to fixtures_schedule
      (+fixtures_outcomes where scores are needed) -- instruments-service, a mechanical single-repo file-by-file repoint
      with a named, closed list. Source:
      `plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md`
- [x] [DATA] P2: root-cause why odds_features feature-export parquet is entirely missing for
      2025-10-23/2025-11-11/2025-11-13 despite odds_horizon_bucket being re-derived (resolve env=dev discrepancy in the
      features-service CLI first, per the doc's own explicit caution against --force before that) **OUT-OF-SCOPE FOR
      THIS BATCH (2026-08-13, operator scoping instruction)** — MDPS/features-service backfill/recompute work is
      excluded from this batch unless manifest-canonical or migration-related. The underlying item remains open in its
      own source doc, untouched by this batch/commit. Source:
      `plans/active/issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md`
- [ ] [REVIEW] P2: locate and re-engage the owner of 'the bucket-cutover lane' referenced in reprocess_sports_odds.py's
      code comment (ceadb45c/2026-07-16), or confirm the comment is stale Source:
      `plans/active/issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md`
- [x] [CODE] P2. Re-run MDPS odds_horizon_bucket shard4 full-mode (resume-friendly, not --force) reprocess for
      2025-01-01..2026-07-25 once the odds_api gap-backfill converges into that date range, to re-poll the ~20 remaining
      honest-gap attempted_failed dates **OUT-OF-SCOPE FOR THIS BATCH (2026-08-13, operator scoping instruction)** —
      MDPS/features-service backfill/recompute work is excluded from this batch unless manifest-canonical or
      migration-related. The underlying item remains open in its own source doc, untouched by this batch/commit. Source:
      `plans/active/issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`
- [ ] [CODE] P2. Stream the sports consolidated-manifest read (pyarrow column projection + current-data_type filter
      applied before .to_pandas()) in build_sports_catalogue_from_manifest so the catalogue rollup's peak memory stops
      scaling linearly with the ~20MB/day-growing manifest, giving durable headroom beyond the 2026-08-10 16Gi/cpu4
      provisioning bump Source: `plans/active/issues/sports_catalog_dp_catalog_001_oom_manifest_read_2026_08_10.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
