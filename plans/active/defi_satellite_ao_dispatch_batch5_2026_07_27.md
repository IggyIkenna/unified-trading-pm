---
doc_type: plan
title: DeFi satellite AO batch 5 — residual-orphan triage after batch4 (scheduled ag_closeout_auditor)
summary: >-
  Fifth AO-dispatch batch for defi, produced by the scheduled `ag_closeout_auditor` role running the
  `/ag-closeout-audit` skill's Phase-1 (per-doc classify) + Phase-3 (conflict-check + draft) triage over all 65 defi
  AG-primary docs, run one day after batch4 (2026-07-27). With the consolidated closeout, aggregated-sources index,
  batch1-4 (+finalize), and the forked Track/purge/extract children (defi_track01_per_instrument_and_canon_id,
  defi_lending_writer_retire_prerequisite, defi_dex_pool_symbol_fix_backfill_purge+finalize,
  defi_consolidated_native_ao_extract+finalize, defi_track5_coverage_mvp_backfill) all counted as covering, 33 of the 65
  docs came back orphaned (30 partial-coverage, 3 never-touched); 7 archivable_now, 24 archivable_after_planned_work
  (already covered by active/dispatched work), 1 exclude_cross_cutting mistag (already tracked — see below). Of the 33
  orphaned docs, only 9 carried genuinely bounded, AO-eligible remaining work; Phase 3's conflict-check cleared 7 of
  those 9 into fresh todos below and found 2 genuine conflicts with in-flight batch3 work, parked as
  BLOCKED-OPERATOR-DECISION in the Deferred section. The remaining 24 orphaned-but-not-AO-eligible docs are
  non-batchable (operator-gated / time-gated / too-large-or-risky / human-only per the skill's taxonomy) and are listed
  in the Deferred section for the next iteration or an explicit operator ruling.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    unified-api-contracts,
    deployment-api,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-5, satellite-docs, fresh-triage]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/defi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md,
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-30"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.4
estimate_calibrated_ai_days: 1.1
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch5_2026_07_27_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
depends_on: []
source: >-
  `/ag-closeout-audit defi` run 2026-07-27 (autonomous, scheduled ag_closeout_auditor, tranche=defi) — Phase 1
  classified all 65 defi AG-primary docs via a Workflow fan-out (65 agents, sonnet/medium), Phase 3 ran a conflict-check
  + candidate-todo draft over the 9 AO-eligible orphan docs via a second Workflow fan-out (9 agents, opus/high), per the
  skill's documented methodology.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 5 — 2026-07-27

**status: draft — NOT dispatched.** Flipping to `active` is an operator decision (per CLAUDE.md "Plan destination — ASK
BEFORE CREATING" HARD RULE); this batch was drafted autonomously by the scheduled `ag_closeout_auditor` and awaits
operator approval.

## Todos

- [x] ✅ [DATA] P1. **MOVED to Conflict-gated item 3 below (BLOCKED-OPERATOR-DECISION) — 2026-07-30, slot-12.** Was:
      "Run `/data-pipeline-check-is` and `/data-pipeline-check-mtds` 3x each across the defi asset_group." Both skills'
      SKILL.md § 0 forbid synthesizing `--day`; filed `/blocked` (`BLK-b5b0e61a`, duplicate of standing `BLK-d355f03a`
      already independently raised by slots 4 and 5); operator ruled **C** — park, do not invent a day. **No dated runs
      were performed; this checkbox marks the triage disposition, not the audit as complete.** See Conflict-gated item 3
      for the full detail; the substantive todo returns to this list once the operator names the baseline/mid/final
      day(s).

- [ ] [DATA] P3. For a representative sample of shards from the 5 affected pool-heavy DEX venues (PANCAKESWAP_V3-BSC,
      UNISWAP_V3-OPTIMISM, UNISWAP_V3-POLYGON, UNISWAP_V4-ETHEREUM, PANCAKESWAP_V3-BASE), load each flat-shape
      instrument_availability `instruments.parquet` and, for every set of rows sharing a duplicate `instrument_key`
      within that (day, venue) shard, compare all non-key columns to classify the duplicates as byte-identical (harmless
      re-write) or field-divergent (real dedup/write-time bug); if any venue shows divergence, root-cause why the
      instruments-service writer emits the same `instrument_key` more than once per day-shard and file a follow-up
      root-cause/fix todo against the writer. Repo: instruments-service. Done when: a recorded harmless-vs-real verdict
      exists for each sampled venue, with a fix todo filed if any venue shows real divergence. Source:
      `plans/archive/issues/defi_instrument_availability_duplicate_instrument_key_rows_2026_07_26.md`

- [x] ✅ [DATA] P2. **ALREADY DONE — discovered stale/duplicate 2026-07-30 while archiving the source issue doc.** Both
      sites this todo describes were already fixed/confirmed in the source issue doc BEFORE this todo was dispatched:
      MTDS `_run_preflight_availability_check` chain-keying fix shipped `market-tick-data-service@5bf8a3c7` (2026-07-29,
      with the exact CURVE-collision regression test this todo asks for); MDPS `orchestration_scanner.py`
      `existing_outputs` dedup confirmed NON-ISSUE via a real scoped GCS read (2026-07-29, real MDPS candle output
      filenames already embed the full chain-qualified canonical id, never the bare `pool_address`), split off + closed
      as `plans/archive/issues/mdps_orchestration_scanner_bare_instrument_id_chain_collision_2026_07_29.md`. This
      `batch5` todo was generated before that closure landed and never got flipped. No new work needed here — flipping
      to avoid a future re-dispatch of already-shipped work. Source (now archived, fully closed 2026-07-30):
      `archive/issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`

- [ ] [SERVICE] P3. Now that the staking-yields Cloud Scheduler/Cloud Run Job went live 2026-07-26 (per this doc's §6.1,
      deployment-service@bd46bf2), query the live prod corpus (`market-data-tick-defi-prd-central-element-323112`) under
      `.../asset_group=defi/venue={LIDO,ETHERFI,EIGENLAYER}/chain=ETHEREUM/instrument_type=staking/data_type=staking_yields/`
      for objects written since 2026-07-26 and confirm the per-venue leaf filenames match the sanitized-symbol
      expectation (e.g. `stETH.parquet`/`weETH.parquet`/`EIGEN.parquet`, per §3). If they match, delete the dead
      `file_name="ticks.parquet"` argument at `staking_yields_handler.py:137` (a documented no-op for non-empty rows per
      `write_defi_rows`'s own contract, §3); otherwise fix the mismatch. Repo: market-tick-data-service. Note:
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` separately wires `assert_defi_catalog_fresh()` into
      this same file at its `process()` chokepoint — a non-conflicting edit at different lines; rebase/coordinate rather
      than reverting it. Done when: a `gcloud storage ls` (or equivalent) capture of the real leaf names is recorded in
      the issue doc and the dead-parameter fix (or its justified retention) ships via scoped
      `quickmerge.sh --agent --files`. Source:
      `plans/active/issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md`

- [ ] [CODE] P2. Execute the swaps_ohlcv_* defi data_types registry fix (the two open `[CODE]` todos at lines 258/262 of
      the source doc, consolidated). GATED ON `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s completeness_pct
      simulation VERIFY (target doc line 253, marked [x]) — read that finding from the issue doc's Progress Log FIRST.
      If the simulation showed the exclusion-guard is required: add a
      `_DEFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES`-style guard to instruments-service's
      `scripts/enumerate_expected_universe.py` (mirroring `_TRADFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES` exactly,
      scoped to the 7 `swaps_ohlcv_*` keys — coordinate/sequence AFTER batch1's own line-164
      enumerate_expected_universe.py edit lands to avoid same-file collision), THEN add
      `swaps_ohlcv_{15s,1m,5m,15m,1h,4h,1d}` to unified-api-contracts' `DATA_TYPES_BY_ASSET_GROUP['defi']`. Otherwise
      (guard not needed): execute Path B stopgap — add a `DEFI_CANDLE_ACCEPTED_NONCANONICAL_DATA_TYPES` frozenset to
      deployment-api's `deployment_api/routes/data_status/_distinct_values.py::_ACCEPTED_EXCEPTIONS`. Repos:
      instruments-service, unified-api-contracts, deployment-api. Done when: the chosen path's change is committed via
      scoped `quickmerge.sh --agent --files` with `quality-gates.sh` green, and — for Path A — a cited before/after
      completeness_pct measurement is recorded, or — for Path B — confirmation the change is deployment-api-local with
      zero denominator/expected_unattempted impact. Source:
      `plans/active/issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md`

- [ ] [DATA] P2. Spot-check `dex_pool_state`/`dex_pool_swaps` GCS-object coverage for UNISWAP_V2, UNISWAP_V4,
      TRADER_JOE_V2, VELODROME_V2 across 2026-03 through today (repeat the sampled `list_blobs` existence +
      `pq.read_table` content-probe methodology from the source doc), now that the mtds-dex-pools-backfill relaunch and
      the mtds-dex-swaps-backfill-1/2/3 sharded fleet have had time to run; if network/GCS conditions allow, also re-run
      the manifest-level `capture_status` cross-check (chunked-download or pyarrow dataset+filter pattern, as the source
      doc's Todo4 prescribes) to corroborate the object-level findings. Repo: market-tick-data-service. Done when: a
      written verdict states, per (protocol, data_type) cell, whether the 2026-03→today gap identified in the source doc
      has closed (with sample-date evidence), and either the manifest cross-check ran and its capture_status
      distribution is recorded, or a stated reason it remains blocked on network conditions. Source:
      `plans/active/issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`

- [ ] [DATA] P2. Now that the `_instruments_metadata.py` layout-tolerant reader fix (todos 1-3:
      `market-tick-data-service@b94259a0` + `@cd8ce74e`) has shipped and promoted, verify against the real prod bucket
      that `load_pool_metadata_for_date` returns non-`None`, non-zero real rows for `morpho`, `fluid`, and
      `kamino_lending` (SOLANA) on a post-cutover date in 2026-07-23..2026-07-26, AND that the availability manifest
      (`read_availability_index` on the `market-data-tick-defi` bucket, filtered `data_type=risk_params`,
      `venue in     [morpho, fluid, kamino_lending / KAMINO-SOLANA]`, `date>=2026-07-23`) now shows non-zero captured
      `row_count` — i.e. production data stopped being silently stamped `captured, row_count=0`. Read-only manifest/GCS
      probe; no code changes. Repo: market-tick-data-service. Done when: a written verdict cites, per venue (morpho,
      fluid, kamino_lending), at least one post-fix date where `load_pool_metadata_for_date` returns real rows and the
      manifest confirms non-zero captured `row_count`; if any venue still reads zero, the residual is recorded rather
      than silently passed. Source:
      `plans/active/issues/mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md`

## Deferred

### Conflict-gated (parked BLOCKED-OPERATOR-DECISION — do NOT draft without operator ruling)

1. **`issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`** — proposed deleting the
   `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod` id from `tests/e2e/_shared/strategy-registry.ts:158`. REJECTED
   as an AO todo: the source doc itself explicitly left this untouched because "whether it's deleted or re-legged onto
   Jupiter is a strategy-domain call that should follow the UAC-side decision, not precede it." Both
   `defi_satellite_ao_dispatch_batch2_2026_07_26.md:203-205` and `batch3_2026_07_26.md:322-324` have already
   independently classified this as human-only / non-batchable for the same reason. **Operator decision needed**: delete
   vs. re-leg `CARRY_STAKED_BASIS` onto Jupiter — until ruled, this stays out of every batch.
2. **`defi_track5_coverage_mvp_backfill_2026_07_24.md`'s PYTH oracle_prices SPOT backfill candidate** (2023-10-01 →
   2026-07-22, converting 1,026 aiodns-crash attempted_failed rows) — overlaps
   `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s in-flight C6 Pyth oracle_prices SPOT backfill
   (2026-04-15→present) on the SAME mechanism (a single idempotent Pyth re-fetch addresses both attempted_failed rows
   and gap days over the shared window — not two different fixes). Additionally gated by an OPEN `[HUMAN-AGENT] P1`
   operator go/no-go on the Pyth Hermes coverage SSOT + backtest window scope in
   `defi_consolidated_closeout_aggregated_sources_2026_07_24.md:339-340` (the candidate's 2023-10-01 floor is exactly
   the undecided default). **Operator decision needed**: (a) confirm batch3's C6 already covers the full window once it
   completes (recommended — re-check after C6 lands, no new dispatch needed), or (b) rule on the Pyth Hermes
   coverage/backtest-window go/no-go first if a wider window than C6's is actually wanted.
3. **Run `/data-pipeline-check-is` and `/data-pipeline-check-mtds` 3x each across the defi asset_group** (gate-audit
   §11: pre-backfill baseline, mid-backfill spot-check, post-backfill final gate per skill — 0 dated runs of either on
   record for defi today; moved here from the Todos list 2026-07-30, slot-12). REJECTED as a directly-dispatchable AO
   todo: both skills' own SKILL.md § 0 hard rule states `--day` MUST come from the operator or the dispatching plan/task
   and is NEVER synthesized by the worker or main — this exact `--day` ambiguity was independently hit by 3 worker slots
   (4, 5, 12) before main stopped the re-dispatch churn at the source. Neither a single reused day nor 3 distinct days
   may be picked without an operator ruling. **Operator decision needed**: name the baseline/mid/final day(s) to use for
   the 6 runs (3 IS + 3 MTDS) — tracked as blocked question `BLK-d355f03a` (also raised independently by slot-12 as
   `BLK-b5b0e61a` before the standing question was found). Once named, this todo returns to the Todos list and
   dispatches normally. Repos: instruments-service, market-tick-data-service. Source:
   `plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md`.

### Non-batchable orphans (24 docs) — operator-gated / time-gated / too-large-or-risky / human-only

Re-check taxonomy before spinning batch6: a **conflict-gated** item above clears the moment its named competing claim
ships/resolves; the items below need direct human action (a design call, an operator ruling, elapsed time, or a
dedicated standalone plan) — re-running this skill will keep re-surfacing them unchanged until that happens.

**Operator-gated (design/judgment call, no evidence-based tiebreaker):**

- `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` — SSOT call: which of two disagreeing registries
  (`_INSTRUMENT_TYPE_ALIASES` vs legacy `venue_mapping.DataTypeConfig.instrument_data_types`) governs A_TOKEN/DEBT_TOKEN
  (and LST/YIELD_BEARING) valid data_types.
- `defi_expected_unattempted_seeder_design_2026_07_26.md` — P0 capability-vs-collectibility reconciliation (FLUID case)
  must be resolved by the operator before any of its P1-P3 design/build/verify work can start; every AO batch through
  batch4 has already correctly deferred to this plan rather than drafting competing todos.
- `issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md` — investigation-only findings (5 new,
  still-unfixed bugs scoped but not built) awaiting an operator prioritization call on which to fix first.
- `issues/defi_mvp_backfill_optimization_ready_2026_07_20.md` — blocked on expired `gcloud` CLI auth (an
  operator/credential action, not a worker-executable step) before the 2-VM TheGraph canary + pagination-fix validation
  can run.
- `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` — durable fix (declaring HYPERLIQUID/ASTER in UAC's
  `ALL_DEFI_VENUES` + `DEFI_VENUE_DATA_TYPE_CAPABILITIES`) is a registry-level architecture decision beyond the shipped
  deployment-api-local stopgap.
- `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md` — `[DESIGN] P3` retry-sweep-signal mechanism choice
  (pub/sub vs sentinel-file vs other) needs a human call on which service owns it; batch3 already acknowledged this.
- `issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md` — 3 mutually-exclusive fix approaches (rewrite /
  delete / harden-QG-gate), doc itself states "not yet actioned — needs an operator call on approach."
- `issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md` — operator ruling needed on
  ETH-underlying-units client-reporting semantics (view A vs re-derive B) before the sole remaining coverage-extension
  todo can be scoped.
- `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md` — 2 of 3 remaining items are explicit
  BLOCKED-OPERATOR-DECISION entries (916 HL + 642 ASTER redundant legacy-row reconciliation; HYPERLIQUID k-prefix
  coin-case convention).
- `issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md` — deliberately non-AO-dispatched (assigned_vm: NA, P3, "not
  urgent"); its own ask is to author a brand-new dedicated implementation plan when it becomes a priority — that
  authoring decision is the operator's, not a worker's.
- `lst_rate_honest_coverage_2026_07_21.md` — Phase 6 Solana lst_rates pipeline_mode mislabel fix needs its own scoping
  pass; E3 recursive-staking borrow leg acknowledged-but-not-yet-dispatched.
- `defi_track01_per_instrument_and_canon_id_2026_07_24.md` — large multi-item residual (R4 coverage scoring gated on
  R1-R3/R5; Wave-D ~16.7M-row LENDING migration gated on the also-uncovered
  `defi_lending_writer_retire_prerequisite_2026_07_20.md`; canon walk C2-C12; bare-factory-address resolver capture) —
  each sub-item is itself gated on other incomplete work or an existing separately-tracked operator-gated doc; not a
  single bounded todo.
- `market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md` — todo 4 explicitly requires
  `[OPERATOR]` authorization to pause the MTDS manifest-consolidator cron and run `--apply` (delete-safety-protocol §3a
  territory).

**Time-gated (elapsed time / external process, not a worker decision):**

- `issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md` — the [CODE] P2 canonical-data_type registration +
  manifest backfill should sequence AFTER batch1's VERIFY-only todo resolves whether it's even needed; re-check once
  batch1 lands.
- `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` — 4th instance (57 machine-derived
  prospectus files) needs the in-repo generator re-run, gated on confirming the generator itself has no independent bug
  first (per the doc's own open question).
- `issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md` — batch3's own D1 todo is `[BLOCKED-INFRA]`,
  explicitly cannot proceed until this doc's root-cause investigation resolves; re-check after batch3 D1's current state
  changes.

**Too-large-or-risky-for-a-batch-todo (live, multi-phase, in-flight):**

- `defi_track5_coverage_mvp_backfill_2026_07_24.md` — beyond the one cleared todo above (skill-run baseline), the doc's
  launcher/write-concurrency work is itself gated on `candle_canonical_path_migration_execution_2026_07_24`'s P8 — a
  live, actively-draining cross-cutting migration.

**Human-only, permanently (until content changes):**

- `issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md` — item 2 fully closed; no remaining action.
- `issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` — todos 1-2 done, remainder tracked elsewhere
  per the doc's own annotation.
- `archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md` — ✅ RESOLVED 2026-07-30
  (features-service@d8a643a0, slot-4): both halves of the doc's one todo shipped (orphaned tree deleted + 1508-row
  backfill registered); doc archived.
- `issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md` (see operator-gated above, dual-listed by
  reasoning shape).
- `issues/defi_morpho_lending_indices_never_wired_2026_07_12.md` — remaining item is a re-run of an existing gate,
  low-risk but explicitly tied to the backfill completing first (time-gated in practice).
- `issues/defi_adapter_dead_code_audit_2026_07_24.md` — 4 of 6 follow-ups need per-item human judgment (register vs.
  delete `jupiter.py`; re-verify feature-flag currency) rather than a single bounded fix.

### Known, already-tracked mistag (no action needed here)

- `archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` — tagged `asset_group: [defi]`
  but is fleet-wide CI/QG infra content. Already flagged by batch2/batch3 and carries an open `[DOC] P2` retag todo in
  `defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md:73-76`. Not re-flagged as a new finding.

### Self-gated covering-plan doc (no action needed — will clear on its own)

- `defi_consolidated_native_ao_extract_2026_07_25_finalize.md` — status:draft, machine-gated
  (`depends_on: [defi_consolidated_native_ao_extract_2026_07_25]`, `gate_on_depends: true`) — its 3 todos become
  dispatchable automatically once its parent plan's 4 todos complete. Not an orphan needing a fresh draft.

## Progress Log

- 2026-07-27 (slot-4, scheduled `ag_closeout_auditor`, tranche=defi): Ran a fresh full Phase-1 classification (65
  agents, sonnet/medium) over all 65 defi AG-primary docs, cross-checked against a 17-doc covering-plan set
  (consolidated closeout, aggregated-sources index, batch1-4+finalize, and the 5 forked Track/purge/extract children).
  33 orphaned (30 partial, 3 never-touched); Phase-3 conflict-check (9 agents, opus/high) over the 9 AO-eligible orphans
  cleared 7 into todos above, parked 2 as genuine conflicts (see Deferred). 24 non-AO-eligible orphans + 1 known
  mistag + 1 self-gated covering-plan doc recorded in Deferred for the next iteration / operator ruling.
- 2026-07-30 (slot-12, data_engineering): Dispatched todo 1 (the `/data-pipeline-check-is`/`-mtds` 6-run checkpoint
  cadence). Both skills' SKILL.md § 0 forbids synthesizing `--day` — filed `/blocked` (`BLK-b5b0e61a`); operator ruled
  **C** (park, do not invent a day), noting slots 4 and 5 independently hit the same question first under the standing
  blocked question `BLK-d355f03a`. Moved the todo out of `## Todos` into `### Conflict-gated` item 3, tagged
  BLOCKED-OPERATOR-DECISION, citing both blocked-question ids. No dated runs were attempted. Returns to `## Todos` once
  the operator names the baseline/mid/final day(s).

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
