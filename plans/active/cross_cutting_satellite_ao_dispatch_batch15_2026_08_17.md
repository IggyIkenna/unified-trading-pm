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
last_updated: "2026-08-19"
parent_epic: security_and_cross_cutting_master
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
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    execution-service/execution_service/defi_execution/protocols/kamino.py,
    execution-service/execution_service/defi_execution/protocols/aave.py,
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
- [x] ✅ [DATA] P0. Verify B22 in BOTH directions, per asset group, off the manifest — manifest→path (does every entry
      have an object?) AND path→manifest (does every object have an entry?). Manifest-driven; no new whole-corpus
      GCS walk (B13 discipline). Source: `/plans/active/data_pipeline_completion_2026_08_21.md`. Done-when: a
      per-AG bidirectional reconciliation report is produced, citing the manifest as the sole read surface.
      **Done 2026-08-18** —
      [`data_pipeline_reconciliation_b22_bidirectional_2026_08_18.md`](/plans/audit/results/data_pipeline_reconciliation_b22_bidirectional_2026_08_18.md).
      Synthesized from already-published per-AG manifest-side artifacts (phantom + orphan-sweep read-backs), zero new
      GCS reads. Headline finding: direction 1 (manifest→path/phantom) has some coverage on all 5 AGs; direction 2
      (path→manifest/orphan) has **never been assessed** for cefi, tradfi, or prediction, and the two AGs that have
      been measured (defi 63.74% orphan_real, sports 27,348 objects) are both ~26 days stale — confirming the gate
      text's own warning that path→manifest is the direction that gets skipped. 4 follow-up todos filed in the
      report itself (not this doc) to close the per-AG gaps.
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
- [x] ✅ [BACKEND] P1. **DONE 2026-08-18 (slot-12, backend_engineer).** Make the three-stage benchmark
      harness portable — runnable on a laptop and on a non-Google provider, not just in-cloud, so figures
      are directly comparable rather than adjusted. Source: `/plans/active/data_pipeline_completion_2026_08_21.md`.
      Done-when: the same harness produces comparable figures run locally and against the reference
      Google-environment run. No code change was needed — `run_three_stage_benchmark()` was already
      cloud-agnostic by construction (plain callables, zero provider dependency). Confirmed empirically by
      running the unmodified CLI on a genuinely non-Google host (this slot's own worktree host, verified
      Amazon EC2 via DMI vendor string + unreachable `metadata.google.internal`) and comparing against the
      2026-08-18 GCP-`planning`-VM reference run: process latency (the host-bandwidth-insensitive stage)
      matched within ~3% (~10.2-10.6ms both sides); fetch/write throughput stayed same-order-of-magnitude
      (expected variance — memory-bandwidth-bound on the synthetic payload, not vendor/network-bound).
      Full comparison + raw JSON in `unified-trading-library@a31ab4a2a9`
      (`docs/benchmarks/three_stage_benchmark_2026_08_18.md` § "Portability confirmation — off-Google run").
- [x] ✅ [BACKEND] P2. Publish the per-shard reference ETA derived from the Google-environment figures, labelled
      REFERENCE (explicitly not a target), alongside the per-stage breakdown that explains it. Source:
      `/plans/active/data_pipeline_completion_2026_08_21.md`. Done-when: a published reference-ETA table exists,
      explicitly labelled non-binding. **DONE 2026-08-18 (backend_engineer, slot 6)** —
      `unified-trading-library@1b74a349a0`:
      [`three_stage_benchmark_reference_eta_2026_08_18.md`](https://github.com/IggyIkenna/unified-trading-library/blob/live-defi-rollout/docs/benchmarks/three_stage_benchmark_reference_eta_2026_08_18.md).
      Per-shard, per-mode reference ETA (12 rows) derived from the already-published GCP `planning`-VM
      harness-validation run (`fetch_bytes/fetch_tput + process_latency + write_bytes/write_tput`), with the
      per-stage breakdown reproduced alongside it and an explicit "REFERENCE ONLY — NOT A TARGET" banner + a
      "what would make this binding" section pointing at the still-open real-vendor-fetch follow-up. Linked from
      the parent `three_stage_benchmark_2026_08_18.md`.
- [x] ✅ [DOC] P0. Cross-link every gate (B1-B26, P1-P13, L1-L14) in `data_pipeline_completion_2026_08_21.md`'s tables
      to its owning plan/issue doc; where no owning plan exists, record that absence as the finding rather than
      silently absorbing it. Source: `/plans/active/data_pipeline_completion_2026_08_21.md`. Done-when: every gate
      row in that doc's tables carries an owning-doc link or an explicit "no owning doc" note. **Done 2026-08-18**:
      added an "Owning doc" column to all 6 gate tables (B1-B8, B9-B20, B21-B23, B24-B26, PAPER P1-P13, LIVE L1-L14),
      resolving all 53 rows. Finding: 29/53 (55%) have no dedicated owning plan/issue doc — enumerated in a new
      summary blockquote under the doc's existing "Tie-in to existing plans" bullet, most tracing to a codex SSOT
      policy rather than a tracked work item, or genuinely uncovered anywhere in the corpus (e.g. P6 stream
      continuity, L2 SLOs, L12 access control).
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
- [x] ✅ [SKILL] P1. Build the gate-evaluation skill so `data_pipeline_completion_2026_08_21.md`'s register is
      re-runnable rather than a point-in-time snapshot, mirroring the readiness-state-dump shape already used in
      the parent epic's W1/W20. Source: `/plans/active/data_pipeline_completion_2026_08_21.md`. Done-when: the
      skill exists and one full run against the register is reported. **Shipped
      `cursor-configs/skills/gate-evaluation/`** (`SKILL.md` + `scripts/gate_registry.py` +
      `scripts/evaluate_gates.py`, mirroring the `honest-coverage-dump`/`readiness-state-dump` split between a pure
      registry module and an evaluator). `gate_registry.py` transcribes all 53 gates (26 BATCH + 13 PAPER + 14
      LIVE) verbatim from the register doc's own tables, with a drift-guard assertion pinning the 29-of-53
      no-owning-doc count the 2026-08-18 cross-link pass found. Readiness is DERIVED, never declared (same
      2026-08-16 operator ruling `readiness-state-dump` follows, per
      `/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`): only 3 gates (B1 availability, B8
      honest-coverage-100%, B16 denominator-declared) have a genuine machine oracle wired — all three reuse
      `honest-coverage-dump`'s already-shipped `dump_coverage.build_report()` verbatim, never recomputed. Every
      other gate honestly reports `unverified`, tagged with its owning doc (or its confirmed absence) so a reader
      sees at a glance whether the gap is "go read `<doc>`" or genuinely untracked anywhere.

      **First live run (2026-08-19, slot 31, infra), production `coverage.json` (`2026-08-19`, 3,962 shards):**
      `TOTAL: 53 gates -- PASS=1 FAIL=2 UNVERIFIED=50`. **B1 FAIL**: 222/3,962 shards have zero honest coverage and
      are not a confirmed-empty absence. **B8 FAIL**: `reachable_coverage_pct=48.73%` (denom=120,035,432) — order-
      of-magnitude consistent with the per-AG Friday-target table this same doc's batch15-item-9 entry recorded on
      2026-08-18 (cefi 45.51%, defi 40.68%, tradfi 86.96%, sports 99.26%, prediction 92.78% — this run's 48.73% is
      the corpus-wide weighted figure across all 5 AGs together, not a re-measurement disagreement). **B16 PASS**:
      all 4 capture-state labels present + denominator carried on every percentage. The 50 `unverified` gates split
      23 BATCH / 13 PAPER / 14 LIVE, matching the register's own 23/13/14 non-automated gate counts exactly.
      Repo: unified-trading-pm (this repo; no separate service repo touched).

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
- [x] ✅ [BACKEND] P1. Verify the DeFi-address immutability assumption (can pool/contract addresses migrate or be
      proxy-upgraded) rather than carrying it as belief; if mutable, add to the declared-mutable field set. Source:
      `/plans/active/instruments_catalogue_definitions_and_field_history_2026_08_17.md`. Repo: instruments-service.
      Done-when: a written determination with citations exists (a real migration/upgrade event found, or a
      documented absence of one over the observed period). **Done (2026-08-18)**: determination = addresses are
      **NOT safely immutable** — mutable, per two independent citations. (1) The codebase's own architecture doc
      already assumes an already-cataloged instrument's on-chain address can change in place:
      `/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md:192` names "if Lido's contract address
      changes mid-day" as a scenario the hot-reload/delta-cache path must propagate — this predates and contradicts
      the immutable-by-belief assumption. (2) Real-world protocol-version migrations mint a brand-new contract
      address for the same economic market (Aave V2 `LendingPool` → V3 `Pool`; Compound V2 Comptroller/cToken
      markets → V3 Comet markets) — under this system's address-derived instrument_id scheme
      (`instrument_id = pool_address.lower()`, `unified_api_contracts/canonical/crosscutting/defi.py:259-261`), that
      class of event does NOT mutate an existing `pool_address` field in place — it mints a new instrument_id while
      the old one is retired, so it is already correctly modeled as an instrument-lifecycle event, not a field
      mutation. No dedicated "declared mutable fields" registry exists yet in UAC (0 hits for
      `mutable_fields`/`MUTABLE_FIELDS`/`declared_mutable`) — that registry is a separate not-yet-implemented P0 item
      in the parent plan, gated on operator ratification of the whole design (that plan's item #2, `[OPERATOR]`).
      Recommendation for whoever implements that registry: declare `pool_address`, `base_asset_contract_address`,
      `quote_asset_contract_address`, `atoken_address`, `debt_token_address`
      (`unified-api-contracts/unified_api_contracts/internal/reference/instrument.py:268-296`) MUTABLE — citation (1)
      above is a concrete in-place-change scenario the design must handle, not merely a hypothetical.

## From `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`

- [x] [AGENT] P3. Fix `StrategyDomainConfig` (`extra="forbid"`) breaking `TestStrategySafeFieldAllowList` against a
      normal local `.env` matching `.env.example`'s own defaults — use `extra="ignore"` or construct the test via
      `_env_file=None`. Source: `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`.
      Repo: strategy-service. Done-when: the test passes on a machine with a normal `.env` matching
      `.env.example`'s defaults, without the move-aside-and-restore workaround. **✅ DONE (2026-08-18)** — root
      cause: `StrategyDomainConfig` actually lives in `unified-trading-library`
      (`unified_trading_library/config_interface/domain_configs.py`), not strategy-service; as a `BaseSettings`
      subclass it auto-reads `.env` on every construction, and its narrow 3-field schema + inherited
      `extra="forbid"` rejected any of `.env`'s many unrelated keys. Fixed via `extra="ignore"` (matching existing
      precedent: `strategy_service/risk/config.py`, UTL's `cloud_config.py`/`ml_config.py`). Verified: all 4
      `TestStrategySafeFieldAllowList` tests pass with a real `.env` present; strategy-service's full
      `quality-gates.sh` green. Shipped `unified-trading-library@1da1a095d4`. The 2 riding GCS-compliance changes
      (`scripts/trace_all_carry_archetypes.py` + `scripts/position/capture_phase_9_evidence.py`) were also
      redone (the original uncommitted edits no longer existed in any local checkout) and shipped together:
      `strategy-service@20e9602e96`. The identical-CLASS `extra_forbidden` failure independently blocking
      execution-service was also fixed the same session — see
      `/plans/archive/issues/execution_service_pydantic_extra_forbidden_blocks_gcs_fix_2026_08_18.md` (shipped
      `execution-service@3448247dba`). **New finding, not fixed**: 7 more `DomainConfig`-family classes in the
      same UTL file share this identical shape (narrow schema + inherited `.env`-reading + `extra="forbid"`) and
      carry the same latent risk — out of scope for this todo, flagged for a follow-up.
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
- **2026-08-18 (slot 7, backend_engineer, task `cross_cutting_satellite_ao_dispatch_batch15-1d0c8d58f6ff`)**: item 2
  (B22 bidirectional) done — see the report linked on the checkbox above. Synthesized entirely from already-published
  manifest-side artifacts per B13/single-walk discipline; no new GCS reads. Real finding, not a formality: the
  path→manifest (orphan) direction has never been assessed for 3 of 5 asset groups, and the 2 that have been
  measured are ~26 days stale — the report files 4 follow-up todos to close this.
- **2026-08-18 (backend_engineer, slot 9, task `cross_cutting_satellite_ao_dispatch_batch15-c15395d2c7a6`)**: item
  (DeFi-address immutability) done — factual investigation, no code change needed. Determination: NOT immutable —
  see the citations on the flipped checkbox above. Read `unified_api_contracts/internal/reference/instrument.py`
  (address fields), `unified_api_contracts/canonical/crosscutting/defi.py` (address-derived `instrument_id`),
  `/codex/02-data/defi-canonical-naming-ssot.md` (address-collision handling), and
  `/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md` (the Lido in-place-change scenario) —
  confirmed no existing `mutable_fields`/`declared_mutable` registry in UAC (0 grep hits), so no registry edit was
  possible/needed this round; that registry itself is a separate P0 item still gated on operator ratification in
  the parent plan.
- **2026-08-18 (infra, slot 21)**: item 7 (gate cross-linking) done. Grepped `plans/active/` for a candidate owning
  doc per gate topic, read the strongest matches in full (`data_pipeline_e2e_milestones_gate_2026_07_24.md`,
  `venue_readiness_and_registry_hardening_2026_08_16.md`, `venue_smoke_test_bar_2026_08_16.md`,
  `venue_e2e_wiring_2026_08_16.md`, `manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md`), then added
  an "Owning doc" column to all 6 gate tables in `data_pipeline_completion_2026_08_21.md` (53 rows total). 24 gates
  resolved to a real plan/issue doc or codex SSOT; 29 (55%) recorded as "no owning doc found" rather than forced onto
  a weak keyword match — summarised in a new blockquote finding under that doc's "Tie-in to existing plans" section.
  `unified-trading-pm@<pending>`.
- **2026-08-19 (infra, slot 31)**: item 10 (gate-evaluation skill) done. Shipped
  `cursor-configs/skills/gate-evaluation/` mirroring the `honest-coverage-dump`/`readiness-state-dump` split
  (pure `gate_registry.py` data module + `evaluate_gates.py` evaluator), transcribing all 53 gates from
  `data_pipeline_completion_2026_08_21.md`'s own tables with a drift-guard assertion on the 29-no-owning-doc
  count. Wired 3 real machine checks (B1/B8/B16, all reusing `honest-coverage-dump`'s already-shipped
  `dump_coverage.build_report()`); every other gate honestly reports `unverified` per the same "readiness is
  derived, never declared" discipline `readiness-state-dump` already established — deliberately did not attempt
  to fabricate checks for the 50 gates needing human judgment, a live drill, or deep service-internal
  investigation (B20 sign-off, L9 DR-drill, etc.). First live run against production `coverage.json`: 1 PASS
  (B16), 2 FAIL (B1: 222/3,962 zero-coverage shards; B8: 48.73% reachable coverage, consistent with the
  already-recorded per-AG Friday-target figures), 50 UNVERIFIED. See the flipped checkbox above for full detail.

- **context-scout 2026-08-19**: refreshed context_scope (4 entries) — all 13 items sourced from
  `data_pipeline_completion_2026_08_21.md` and `instruments_catalogue_definitions_and_field_history_2026_08_17.md`
  are now done; the 3 items still open all come from `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`'s
  Kamino/Aave connector fixes, so narrowed to that source doc plus its two confirmed execution-service code targets
  (`defi_execution/protocols/kamino.py`, `defi_execution/protocols/aave.py`) and the companion finalize plan.
