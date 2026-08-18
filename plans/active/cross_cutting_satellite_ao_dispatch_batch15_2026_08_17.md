---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 15 — 2026-08-17
summary: >-
  Extraction batch from the cross-cutting tranche's 2026-08-17 /na-eligibility-audit sweep (same-day re-run,
  na_eligibility_auditor, dispatch agt-775398, slot 23) — 16 conflict-cleared, bounded/deterministic items pulled
  from 3 source docs (RECLASSIFY per-todo split bounded items). Each todo cites its exact source doc; the source
  docs themselves are NOT touched by this batch beyond having the extracted checkbox flipped with a citation (done
  in the same audit pass, not deferred to this batch's finalize). Conflict-checked against every active
  assigned_vm:planning plan, the cross-cutting consolidated closeout, and existing satellite batches (13/14) before
  drafting — no item here duplicates ground an existing dispatched todo already claims.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos:
  [
    instruments-service,
    unified-api-contracts,
    strategy-service,
    execution-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    deployment-api,
  ]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, satellite-batch, na-eligibility-audit]
related:
  [
    /plans/active/data_pipeline_completion_2026_08_21.md,
    /plans/active/instruments_catalogue_definitions_and_field_history_2026_08_17.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
assigned_role: infra
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/data_pipeline_completion_2026_08_21.md,
    /plans/active/instruments_catalogue_definitions_and_field_history_2026_08_17.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17_finalize.md,
  ]
source: >-
  Drafted by the 2026-08-17 /na-eligibility-audit cross-cutting-tranche run (na_eligibility_auditor, dispatch
  agt-775398, slot 23) — Phase 1 classification (5 parallel general-purpose hunters over 20 in-scope docs) + Phase 2
  conflict-check (3 RECLASSIFY-split candidates conflict-clear via grep against every active planning doc + the
  consolidated closeout doc's 24 Tracks). Ships status: active (not draft) per the skill's own authorization — this
  skill (unlike the read-only /ag-closeout-audit) applies its verdicts directly.
---

# cross-cutting satellite AO dispatch batch 15 — 2026-08-17

> Companion finalize: [`cross_cutting_satellite_ao_dispatch_batch15_2026_08_17_finalize.md`](/plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17_finalize.md).
> Every item below is independently dispatchable unless noted — different files/repos per item, per the
> intra-plan-concurrency default.

## From `data_pipeline_completion_2026_08_21.md`

- [x] ✅ [DATA] P0. Verify B21 — Distinct Values in the deployment UI shows zero non-canonical values, per asset group.
      Source: `/plans/active/data_pipeline_completion_2026_08_21.md`. Done-when: the deployment UI's Distinct
      Values view is queried for every asset group and either zero non-canonical entries are confirmed, or the
      specific non-canonical entries are named and reported. **RESULT: B21 FAILS — 113 non-canonical entries**
      (cefi 1, defi 38, prediction 1, sports 71, tradfi 2; all but 5 `<blank>` sentinels are real, non-blank
      drift). Queried live via the exact `deployment_api.routes.data_status._distinct_values` code path backing
      `GET /distinct-values/{asset_group}` against the newest nightly honest-coverage rollup (source_date
      2026-08-18). Full per-value breakdown + 8 follow-up todos filed:
      [`/plans/active/issues/b21_distinct_values_noncanonical_live_2026_08_18.md`](/plans/active/issues/b21_distinct_values_noncanonical_live_2026_08_18.md).
- [ ] [DATA] P0. Verify B22 in BOTH directions, per asset group, off the manifest — manifest→path (does every entry
      have an object?) AND path→manifest (does every object have an entry?). Manifest-driven; no new whole-corpus
      GCS walk (B13 discipline). Source: `/plans/active/data_pipeline_completion_2026_08_21.md`. Done-when: a
      per-AG bidirectional reconciliation report is produced, citing the manifest as the sole read surface.
- [x] ✅ [DATA] P0. Establish whether B23's schemas (the 51-column instruments schema) are locked and versioned, and
      if not, what locking them requires. Source: `/plans/active/data_pipeline_completion_2026_08_21.md`.
      Done-when: a written determination (locked-and-versioned: yes/no) is recorded, plus, if no, a concrete
      proposal for what locking requires. Determination: NO (evidence + 4-part proposal recorded in
      `data_pipeline_completion_2026_08_21.md`'s B23 blockquote and filed as tracked follow-up todos in
      [`instruments_schema_not_locked_versioned_2026_08_18.md`](/plans/active/issues/instruments_schema_not_locked_versioned_2026_08_18.md)).
- [x] ✅ [BACKEND] P1. Instrument the three pipeline stages per shard — fetch throughput, process latency, GCS write
      throughput — recorded separately, per MODE (batch/paper/live). Source:
      `/plans/active/data_pipeline_completion_2026_08_21.md`. Done-when: per-stage, per-mode figures are recorded
      for at least one representative shard per asset group. Shipped: `unified_trading_library/core/stage_benchmark.py`
      (portable `run_three_stage_benchmark()` harness) + `scripts/three_stage_benchmark.py` (CLI) —
      unified-trading-library@cf266661e3. First recorded run (4 asset groups × 3 modes) + interpretation notes in
      [`docs/benchmarks/three_stage_benchmark_2026_08_18.md`](https://github.com/IggyIkenna/unified-trading-library/blob/live-defi-rollout/docs/benchmarks/three_stage_benchmark_2026_08_18.md)
      (unified-trading-library repo) — figures are HARNESS-VALIDATION (synthetic fetch payload), not a
      production-vendor throughput claim; wiring real vendor fetch/write per asset group is a follow-up.
- [ ] [BACKEND] P1. Make the three-stage benchmark harness portable — runnable on a laptop and on a non-Google
      provider, not just in-cloud, so figures are directly comparable rather than adjusted. Depends conceptually on
      the todo above landing a real harness to make portable — same file, do not dispatch concurrently with it.
      Source: `/plans/active/data_pipeline_completion_2026_08_21.md`. Done-when: the same harness produces
      comparable figures run locally and against the reference Google-environment run.
- [ ] [BACKEND] P2. Publish the per-shard reference ETA derived from the Google-environment figures, labelled
      REFERENCE (explicitly not a target), alongside the per-stage breakdown that explains it. Source:
      `/plans/active/data_pipeline_completion_2026_08_21.md`. Done-when: a published reference-ETA table exists,
      explicitly labelled non-binding.
- [ ] [DOC] P0. Cross-link every gate (B1-B26, P1-P13, L1-L14) in `data_pipeline_completion_2026_08_21.md`'s tables
      to its owning plan/issue doc; where no owning plan exists, record that absence as the finding rather than
      silently absorbing it. Source: `/plans/active/data_pipeline_completion_2026_08_21.md`. Done-when: every gate
      row in that doc's tables carries an owning-doc link or an explicit "no owning doc" note.
- [x] ✅ [DATA] P0. Tuesday checkpoint: record BATCH/PAPER/LIVE readiness stage per shard across instruments-service
      through features-service, all asset groups (`unverified` is a legitimate recorded value where no check
      exists). Source: `/plans/active/data_pipeline_completion_2026_08_21.md`. Done-when: a per-shard stage table
      is committed covering every asset group. — `unified-trading-pm@7f2b621ad0`. The `readiness-state-dump` skill
      (already shipped `unified-trading-pm@5b3dbf99bd`, W1/Tuesday-dumps-deliverable-1) had verified live counts
      recorded, but no per-shard TABLE had actually been committed — re-ran it live against
      `gs://central-element-323112-honest-coverage/2026-08-18/coverage.json` (288 venues x 3 modes = 864 rows) and
      derived a pipeline-only stage (declared + instruments_service + market_tick_data + market_data_processing +
      features legs — excludes strategy/execution, a distinct gate set per `data_pipeline_completion_2026_08_21.md`)
      per shard. Committed both the full per-shard row table and a per-asset-group x mode summary:
      `/plans/audit/results/readiness_pipeline_stage_per_shard_2026_08_18.json` (864 rows) +
      `/plans/audit/results/readiness_pipeline_stage_per_shard_2026_08_18_summary.md`. Covers every asset group
      present in the coverage manifest (cefi, defi, prediction, sports, tradfi) plus an `UNKNOWN` group (8 venues,
      24 rows — captured but unattributed to a known asset_group; a real finding, not a dump gap). Overall: 0 ready
      / 624 not_ready / 240 unverified across 864 rows at pipeline-only scope — `unverified` used honestly per the
      done-when.
- [x] ✅ [DATA] P1. Done 2026-08-18 (slot 17). Friday target: record all shards at BATCH readiness pending backfill
      completion, with the residual explicitly scoped to B8 (honest coverage 100%) and nothing else. Source:
      `/plans/active/data_pipeline_completion_2026_08_21.md` § "Friday-target table — BATCH readiness per
      asset_group (2026-08-18)". Verdict: the residual is NOT B8-only — B20-B25 (already tracked) plus two new
      registry-gap findings (`declared=not_ready`, `features=not_ready`) flagged as a separate finding there, each
      with a fresh P1 follow-up todo.
- [ ] [SKILL] P1. Build the gate-evaluation skill so `data_pipeline_completion_2026_08_21.md`'s register is
      re-runnable rather than a point-in-time snapshot, mirroring the readiness-state-dump shape already used in
      the parent epic's W1/W20. Source: `/plans/active/data_pipeline_completion_2026_08_21.md`. Done-when: the
      skill exists and one full run against the register is reported.

## From `instruments_catalogue_definitions_and_field_history_2026_08_17.md`

- [x] ✅ [DATA] P1. Re-measure findings 3 (path duplication / stale `.bak` backups) and 4 (sports path grammar) across
      all four asset groups (cefi/defi/tradfi/sports), off the manifest — no new whole-corpus GCS walk. Source:
      `/plans/active/instruments_catalogue_definitions_and_field_history_2026_08_17.md`. Done-when: a per-AG table
      of non-canonical/duplicate/`.bak` counts is produced, cross-checked against the doc's existing bounded cefi
      sample (1,000 non-canonical / 270 `.bak` in a 4,000-blob sample). **Done (2026-08-18)**: bounded prefix-scoped
      listing (`instrument_availability/by_date/`, sanctioned route #1/#3, not a new whole-corpus walk) run per AG —
      cefi 1,706 non-canon/4,649 `.bak` of 49,340; defi 31,522/0 of 141,866; tradfi 67/**17,132** of 32,945; sports
      **182,316**/0 of 362,347 (confirms finding 4 corpus-wide). Full table + cross-check against the bounded cefi
      sample added to `instruments_catalogue_definitions_and_field_history_2026_08_17.md` (same commit).
- [ ] [BACKEND] P1. Verify the DeFi-address immutability assumption (can pool/contract addresses migrate or be
      proxy-upgraded) rather than carrying it as belief; if mutable, add to the declared-mutable field set. Source:
      `/plans/active/instruments_catalogue_definitions_and_field_history_2026_08_17.md`. Repo: instruments-service.
      Done-when: a written determination with citations exists (a real migration/upgrade event found, or a
      documented absence of one over the observed period).

## From `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`

- [ ] [AGENT] P3. Fix `StrategyDomainConfig` (`extra="forbid"`) breaking `TestStrategySafeFieldAllowList` against a
      normal local `.env` matching `.env.example`'s own defaults — use `extra="ignore"` or construct the test via
      `_env_file=None`. Source: `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`.
      Repo: strategy-service. Done-when: the test passes on a machine with a normal `.env` matching
      `.env.example`'s defaults, without the move-aside-and-restore workaround.
- [ ] [AGENT] P2. Migrate Kamino's `supply()`/`withdraw()` uncited `0x01`/`0x02` discriminator bytes to Kamino's
      real Transactions API (`POST /ktx/klend/{deposit,withdraw}`), the same pattern already used for this
      connector's own `borrow()`/`repay()`. Source:
      `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`. Repo:
      execution-service. Done-when: `supply()`/`withdraw()` call the real API instead of hand-rolled discriminator
      bytes, existing tests still green.
- [ ] [AGENT] P2. Fix `AAVEConnector.get_user_account_data()` to make a real `Pool.getUserAccountData()` view call
      instead of returning hardcoded placeholder values (`total_collateral_eth=10`, `total_debt_eth=5`). Source:
      `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`. Repo:
      execution-service. Done-when: the method returns live collateral/debt figures verified against a real Aave
      V3 pool; `RecursiveLoopOrchestrator`'s HF-gate check exercised against real values.
- [ ] [DATA] P3. Re-count the READ-side coverage figure in
      `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`'s "READ SIDE" section to include Kamino's
      bespoke adapter (shipped 2026-08-16, one day after the existing "8" count was written). Source:
      `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`. Done-when: the doc's
      title/summary/table figures state the new total.

## Progress Log

- **2026-08-17 (na_eligibility_auditor, dispatch agt-775398, slot 23)**: drafted from the cross-cutting-tranche
  RECLASSIFY(per-todo split) verdicts on 3 source docs. Conflict-check clear against every active `assigned_vm:
  planning` plan (grepped for each item's distinctive claim terms) and `cross_cutting_consolidated_closeout_2026_07_25.md`'s
  24 Tracks (unrelated subject matter). Source docs' own checkboxes already flipped with citations to this batch in
  the same pass.
- **2026-08-18 (backend_engineer, slot 8)**: item 8 (Tuesday readiness checkpoint). Confirmed the underlying
  `readiness-state-dump` skill already existed and had been run live twice (2026-08-17, 2026-08-18) per
  `system_readiness_master.md` W1 and `data_pipeline_completion_2026_08_21.md`'s Tuesday-dumps section, but only
  rollup counts had been recorded — no per-shard table had actually been committed, which is this item's explicit
  done-when. Re-ran the skill live and committed both the full per-shard row table and a per-asset-group summary
  under `plans/audit/results/`. See the flipped checkbox above for the artifact paths and headline numbers.
- **2026-08-18 (data_engineering, slot 9)**: item 3 (B23 determination) done. Read `INSTRUMENTS_PARQUET_SCHEMA`
  (unified-api-contracts), `SchemaContract` (no version field), `check_schema_versions.py` (excludes
  `internal/domain/instruments/`), the schema-version-matrix framework (no instrument references), and every test
  touching the schema (membership-only, never freeze/hash-gated) — determination: locked-and-versioned = NO.
  Recorded in `data_pipeline_completion_2026_08_21.md`'s B23 blockquote; 4-part fix filed as tracked follow-up in
  `instruments_schema_not_locked_versioned_2026_08_18.md` (new discovered scope, not absorbed into this item).
