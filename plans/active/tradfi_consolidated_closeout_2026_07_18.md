---
doc_type: plan
title: TradFi consolidated close-out — one-pass code→migrations→coverage→smoke-test to MVP-backfill-ready
summary:
  Single coordination plan that AGGREGATES (references, does not duplicate) every open tradfi + tradfi-touching IS/MTDS
  plan and issue into ONE ordered pass, mirroring cefi_consolidated_closeout_2026_07_18.md but structured as the
  operator directed (2026-07-18) — Phase A get ALL the code ready (every id writer live+batch, the migration scripts
  themselves, aggregation/consolidator, adapters, PLUS the tradfi download-throughput work), Phase B run the migrations
  across all four canonicalisation surfaces, Phase C data-status + honest-coverage, Phase D re-smoke-test the backfills
  with the data-pipeline-check-mtds and data-pipeline-check-is skills ADAPTED to tradfi — so tradfi is verified complete
  and ready for the MVP backfills. GROUND-TRUTH CORRECTION (measured live 2026-07-18, superseding this plan's own
  first-draft "largely done" verdict) — the persisted tradfi manifest and catalogue are ~100 percent NON-canonical for
  derivatives — the catalogue prod/catalog.parquet has ZERO of its 1,111,322 FUTURE/OPTION rows in @LIN form (samples
  CBOE:FUTURE:VX/F1) and the market-data-tick availability_index has ZERO @LIN across all years (2026 alone 568,165 raw
  + 63,661 malformed FUTURE/OPTION ids). Only equities parquet filenames and futures_chain bundling are canonical. The
  id migration is barely started on the derivative id columns, not "largely done" — this plan scopes the full
  end-to-end.
status: active
nature: process
asset_group: [tradfi]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    features-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    tradfi,
    close-out,
    consolidation,
    canonicalisation,
    instrument-id,
    manifest,
    honest-coverage,
    backfill,
    throughput,
    mvp,
  ]
related:
  [
    cefi_consolidated_closeout_2026_07_18.md,
    canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
    tradfi_v9_stage1_finish_2026_07_06.md,
    data_completion_tradfi_2026_07_15.md,
    tradfi_massive_dual_source_2026_05_28.md,
    tradfi_multisource_backfill_2026_06_22.md,
    tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md,
    tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    instrument_id_format_canonicalization_2026_07_08.md,
    master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    data_pipeline_e2e_check_2026_07_10.md,
    consolidator_throughput_backlog_monitor_2026_07_09.md,
  ]
created: 2026-07-18
last_updated: 2026-07-18
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 14.0
estimate_calibrated_ai_days: 11.2
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  Operator, 2026-07-18 — after spotting DERIBIT:FUTURE:AVAX@LIN-20260718 missing its quote and then seeing raw symbols
  in tradfi parquet names, manifest entries, and the instruments data-status page/catalogue, directed a single one-pass
  tradfi close-out mirroring the cefi one that aggregates ALL tradfi IS/MTDS plans+issues — "one pass get all the code
  ready then migrations then anything data status and honest coverage related and then smoke test the backfills again
  with data-pipeline-check-mtds and data-pipeline-check-is skills adapted to tradfi so we know its complete and ready
  for mvp backfills" (S&P index futures + index options + delta-one single-stock equities + CME BTC/ETH futures+options
  + daily treasuries + daily KRW). Authored + ground-truth-verified from a 3-agent doc audit + direct live GCS reads
  (slot-3, 2026-07-18).
---

# TradFi consolidated close-out — one pass to MVP-backfill-ready

> **Purpose.** ONE place that aggregates every open tradfi + tradfi-touching IS/MTDS plan/issue into a single ordered
> pass. This plan **references** the source docs; it does not duplicate them. Close a track by closing its source
> doc(s), then tick it here. Mirrors `cefi_consolidated_closeout_2026_07_18.md`; ordered per the operator's directive:
> **Phase A code → Phase B migrations → Phase C data-status/honest-coverage → Phase D re-smoke-test →
> MVP-backfill-ready.**

## Ground-truth verdict (measured live 2026-07-18 — supersedes the first-draft "largely done" claim)

The operator was right: tradfi is overwhelmingly raw. Direct reads of the live prod buckets, NOT the migration docs'
claims:

| Surface                                                              | Canonical (`@LIN`/`@INV`) for FUTURE/OPTION | Reality                                                                 |
| -------------------------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------- |
| Catalogue `instruments-store-tradfi/prod/catalog.parquet`            | **0 of 1,111,322** rows                     | raw/bare (e.g. `CBOE:FUTURE:VX/F1`, `CME:FUTURE:GCQ26`)                 |
| Manifest `market-data-tick-tradfi/_index/availability_index.parquet` | **0** across all years                      | 2026 alone: 568,165 raw (`EWF6_P6490`, `ESM0_P2500`) + 63,661 malformed |
| Tick parquet **filenames** (equities / futures_chain)                | canonical                                   | `NASDAQ:EQUITY:AAPL-USD.parquet`, `CME/CRUDE.parquet` (bundled)         |
| Tick parquet **content** `instrument_key`/`symbol` column            | TBD (verify in Phase A)                     | column present; forward-write may be canonical, historical not          |

**Conclusion**: the id-canonicalisation is barely started on the derivative **id columns** (manifest + catalogue),
despite the migration scripts existing and a VM run being logged — the run either targeted a narrow slice or a different
surface, and the live manifest/catalogue never converged. The four surfaces (GCS filename / parquet `instrument_id`
column / manifest key / reader) are the CeFi model; tradfi is done on filenames only.

**Live confirmation (operator, 2026-07-18, the deployment-api instruments data-status "Upcoming expiries" widget)**:
real catalogue rows render as `CME:OPTION:E3AN6 C7960` / `E3AN6 C7975` / `E3AN6 C8000` — raw weekly-option product code
(`E3AN6`), a **literal SPACE** as sub-delimiter (the banned-whitespace class), no `@LIN`, no `-USD`, no `YYYYMMDD`,
strike glued as `C7960`. Target for this exact row: `CME:OPTION:SP500-USD@LIN-<expiry>-7960-C`. This IS the catalogue
surface — Phase A1 (writer) → B (migrate `prod/catalog.parquet`) → C (widget renders canonical) fix it end to end.

## MVP universe (operator-defined 2026-07-18 — the Phase-D readiness target)

- **S&P index futures** (ES) + **S&P index options**.
- **Delta-one single-stock equities** (S&P/NASDAQ single names — already canonical on filenames; verify the id columns).
- **CME BTC + ETH futures + options** (crypto index products on the TradFi venue).
- **Daily Treasuries** (yields, `ohlcv_24h`) + **daily KRW** (FX daily).

Everything below is scoped so these cells are canonical, honestly-covered, and smoke-tested green before MVP backfill.

> **Data-type × source priority for MVP backfills (operator, 2026-07-18 — supersedes any "restore mbp_10" framing):**
> For **Databento** tradfi, the billing entitlement is **1-month L3 + 1-year L1** — so `mbp_10`/`trades`/`tbbo` are
> **billing-gated by design (documented, NOT a bug to fix)**. The MVP backfill data_type for the instruments we care
> about is **`ohlcv_1m` only** (it has FULL history). The venue capability _declaration_ MAY still enumerate what's
> _possible_ (mbp_10/trades/tbbo within their limits), but the actual **MVP backfills = 1m candles**. For **daily**
> cells we use **Yahoo Finance** as the source (still gives **24h / 1d**): daily Treasuries `ohlcv_24h` + daily **KRW**
> FX. So Phase D smoke-tests + Phase-D MVP backfills iterate: Databento intraday shards → `ohlcv_1m`; Yahoo daily shards
> → `ohlcv_24h`/`ohlcv_1d`. This DE-SCOPES the A2 "mbp_10/trades/tbbo restoration" item to "declaration reflects the
> documented billing reality" (verify, don't chase L3 full history).

---

## Phase A — get ALL the code ready (writers live+batch · migration scripts · aggregation · adapters · download speed)

> Nothing migrates until every WRITER emits the canonical shape and the migration scripts actually apply. Includes the
> tradfi download-throughput work so the re-backfill in Phase D runs fast.

### A1 — Converge every id WRITER to the canonical `PRODUCT_ROOT-USD@LIN-YYYYMMDD[-STRIKE-C|P]` shape

> **DECIDED 2026-07-18 (operator)**: TradFi FUTURE/OPTION canonical ids carry an **explicit `-USD` quote** —
> `CME:FUTURE:SP500-USD@LIN-20300621`, `CME:OPTION:SP500-USD@LIN-20251017-5000-C`, `CBOE:FUTURE:VIX-USD@LIN-20260722`
> (equities already `NASDAQ:EQUITY:AAPL-USD`). Chosen over the bare-product-root form so "same pattern regardless of
> asset class" is literally true and consistent with the 2026-07-18 DERIBIT quote ruling. Every A1 writer + every
> Phase-B migration emits this shape; the Phase-B/D verify gate asserts the `-USD@LIN` shape (not just presence of
> `@LIN`).

- [ ] [BACKEND] P0. **IS catalogue adapter emits raw + a non-matching third shape.**
      `instruments-service/.../reference_data/adapters/tradfi/databento/adapter.py:880` writes primary
      `instrument_key = VENUE:TYPE:{sanitized_raw}` (→ `CME:FUTURE:GCQ26`, and persisted `instrument_id` shows
      `CBOE:FUTURE:VX/F1`), and `:974-999` emits
      `canonical_instrument_id = VENUE:TYPE:PRODUCT_ROOT:YYYY-MM[:STRIKE{C|P}]` (no `@LIN`, month-only, colon strike).
      Converge to the MTDS target
      (`market-tick-data-service/.../tradfi/tradfi_shared.py::derive_tradfi_row_instrument_id`); drop or make the
      additive field byte-equal. (repo: instruments-service)
- [x] ✅ [BACKEND] P0. **Manifest writer now stamps the canonical `-USD@LIN` id (forward-write) — mtds@c44d5f0d.**
      Traced: the manifest `availability_index` `instrument_id` is DERIVED from the parquet **content** `instrument_id`
      column by the shared writer (`unified_trading_library/io/streaming_writer.py`→`manifest_writer`), so once the
      content column is canonical the forward-write manifest key is canonical + byte-identical (shard atom identical
      across writer/manifest). Historical manifest rows (`EW1H0_P2785` etc.) are the Phase-B migration, not a writer
      bug. Regression test that content→manifest keying holds is tracked as the A1 test todo below. (repos:
      market-tick-data-service, unified-trading-library)
- [x] ✅ [BACKEND] P0. **Tick parquet CONTENT `instrument_id` converged to `-USD@LIN` — mtds@c44d5f0d.** The databento
      forward-write (`databento_enrichment.py::_classify_row`) and batch derive
      (`tradfi_shared.py::derive_tradfi_row_instrument_id`) both now pass `margin_marker="LIN", quote_asset="USD"`. It
      is the enriched `instrument_id` column (NOT the raw `symbol`) that flows into the manifest key. Runtime PROOF (own
      venv, "run it not read it"): `derive_tradfi_row_instrument_id` FUTURE `ESM26`→`CME:FUTURE:SP500-USD@LIN-20260619`,
      OPTION `E3AN6 C7960`→`CME:OPTION:SP500-USD@LIN-20260117-7960-C` (0 whitespace — fixes the operator-seen
      banned-space class; product root ES→SP500 resolved). (repo: market-tick-data-service)
- [x] ✅ [OPERATOR] P0. **TradFi quote/margin ruling — DECIDED 2026-07-18: explicit `-USD`** (see the A1 banner above).
      All tradfi is USD-settled (no inverse), but the quote is carried anyway for cross-asset-class uniformity +
      non-ambiguity, consistent with the DERIBIT ruling. Target =
      `VENUE:TYPE:PRODUCT_ROOT-USD@LIN-YYYYMMDD[-STRIKE-C|P]`.
- [ ] [BACKEND] P1. **Route the tradfi writers through the shared `build_canonical_instrument_id`** (re-drift
      prevention) + a QG that fails a raw-shaped tradfi `instrument_key` on write — else new writes re-drift.
      `canonical_id_builder_retrofit_checklist_2026_07_08.md`. (repos: instruments-service, market-tick-data-service,
      unified-api-contracts)

### A2 — Adapter / registry correctness (so the MVP cells actually fetch + classify)

- [ ] [BACKEND] P1. **CME `mbp_10`/`trades`/`tbbo` `VENUE_DATA_TYPE_CAPABILITIES` restoration** + no `ohlcv_15m/24h`
      aggregation writer exists (leaves `vix_features` unfed) —
      `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`. (repos:
      market-tick-data-service, unified-api-contracts)
- [ ] [BACKEND] P2. **KRX/KRW intraday registry-vs-adapter mismatch**
      (`krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md`, RESOLVED — verify it holds for the KRW MVP
      cell). **IBKR `_SEC_TYPE_MAP` / Databento `_resolve_product_root` / combo-leg** — DONE in code
      (`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`); flip its stale single-leg todo. **`mvp_mode`
      dead gate** decision (`tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`). (repos: instruments-service,
      market-tick-data-service)
- [ ] [BACKEND] P2. **Full MTDS+IS adapter smoke findings** — `mtds_is_full_adapter_smoketest_findings_2026_07_07.md`,
      `instruments_remaining_work_audit_2026_07_10.md` (tradfi slice),
      `uac_data_type_validity_combinator_fragmentation_2026_07_07.md`.

### A3 — Download / backfill THROUGHPUT (so Phase-D re-backfill is fast + reliable)

- [ ] [BACKEND] P0. **Databento DNS-starvation executor risk** — `databento_fetch.py:672` uses
      `run_in_executor(None, …)` (default pool, shared with aiohttp's `getaddrinfo`) — the SAME mechanism that wedged
      the CeFi Tardis backfill ~350x. Dedicated executor.
      `databento_default_executor_dns_starvation_risk_2026_07_17.md`. (repo: market-tick-data-service)
- [ ] [INFRA] P1. **Backfill-VM startup OOM rc137** (`mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`, open) + **OOM
      remediation baked default** (`tradfi_backfill_oom_remediation_2026_06_24.md`, e2-highmem-4, verify) +
      **consolidator throughput/backlog monitor** (`consolidator_throughput_backlog_monitor_2026_07_09.md`). (repos:
      deployment-service, market-tick-data-service)
- [ ] [INFRA] P1. **TradFi has NO working T+1 forward-fill job** (`tradfi_t1_no_working_mtds_job_2026_07_17.md`) — add
      source-scoped `…-tradfi-databento-t1-recon` (+ massive) Cloud Run jobs; live coverage erodes daily without it.
      (repos: deployment-service, market-tick-data-service)
- [ ] [BACKEND] P1. **Massive dual-source shape parity + consolidator dedup-key omits `source`**
      (`tradfi_massive_dual_source_2026_05_28.md` Phase 4b — a silent last-write-wins loss risk the moment a cell goes
      dual-source). (repos: unified-trading-library, market-tick-data-service)

## Phase B — run the migrations (all four surfaces, gated on Phase A green)

> Pre-migration drain per the VM runbook; direct-canonical-index mutation MUST pause the consolidator or use CAS /
> additive per-VM-shard writes (the EU floor-clip only "got lucky on timing" —
> `tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`).

- [ ] [DATA] P0. **Migrate the persisted derivative `instrument_id` columns** — catalogue (1.11M FUTURE/OPTION rows) +
      manifest (all years) → the A1 canonical shape, using the same `derive_row`/builder the writer uses so migrated ==
      newly-written byte-for-byte. Fix/re-run the existing scripts
      (`migrate_tradfi_single_leg_product_root_lin_2026_07_09.py`, the combo-leg migration) — they exist but did NOT
      converge the live surfaces. `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`,
      `instrument_id_format_canonicalization_2026_07_08.md`. (repos: market-tick-data-service, instruments-service)
- [ ] [DATA] P0. **Migrate GCS filenames for derivative shards** where still raw (equities/futures_chain already
      canonical; audit options/options_chain/futures single-contract layouts). Rebuild `prod/catalog.parquet`. Extend
      the verify gate to assert ZERO raw / ZERO non-`@LIN` derivative ids on all four surfaces.
- [ ] [DATA] P1. **v9 schema / manifest-status finish** (`tradfi_v9_stage1_finish_2026_07_06.md`) — fresh CF-1…CF-12
      all-GREEN re-run; confirm live `_index.schema_version` is int64 not string `'9'`
      (`cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`); Layer-1 % recorded. **Legacy-twin bucket
      DELETEs = BLOCKED-OPERATOR-DECISION** (hard-stop).
- [ ] [PM] P1. **Reconcile the stale fork** `data_completion_tradfi_2026_07_15.md` against `tradfi_v9_stage1_finish`
      (flip done todos, re-scope open ones, delete its duplicate paragraph) so the backlog is honest.

## Phase C — data-status + honest-coverage (gated on Phase B)

- [ ] [BACKEND] P1. **Honest-coverage for tradfi**: out-of-window `expected_unattempted` clipping
      (`honest_coverage_out_of_window_expected_unattempted_not_clipped_2026_07_16.md`, RESOLVED — verify for tradfi);
      reference-data shard-dimension model (`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`);
      coverage-floor registry cross-propagation (`coverage_floor_registries_no_cross_propagation_2026_07_17.md`).
- [ ] [BACKEND] P1. **Data-status page renders canonical tradfi** (the "Upcoming expiries" + instruments/catalogue
      views) — `data_status_page_ux_and_canonicalisation_2026_07_16.md`; deployment-api legacy venue-lookup gap
      (`deployment_api_legacy_instrument_availability_venue_lookup_gap_2026_07_13.md`, RESOLVED — verify tradfi).
- [ ] [BACKEND] P2. **Denominator / catalogue-completeness + new untracked findings** — 875 tradfi atoms with narrowed
      historical objects + 153 duplicate KRX row_keys
      (`tradfi_instrument_type_migration_read_stale_legacy_object_2026_07_17.md`); phantom captures
      (`phantom_captures_tradfi_2026_06_28.md`); expected_reason misclassification P3s.

## Phase D — re-smoke-test the backfills, TradFi-only, ALL shards (the post-migration completion gate)

> **This is the plan's terminal gate.** Post-migration, run BOTH pipeline-check skills scoped to **tradfi only** and
> require green across **every** tradfi shard (not just the MVP cells) — force-refetch + skip-if-fresh + a
> canonical-shape assertion — so we KNOW tradfi is complete before any MVP backfill. Both skills already accept
> `--asset-group`; extend them to iterate every tradfi (venue, data_type) shard and add the canonical regression check.

- [ ] [DATA] P0. **Adapt `data-pipeline-check-mtds` + `data-pipeline-check-is` to tradfi** — iterate EVERY tradfi
      (venue, data_type) shard (MVP cells first: ES futures/options, single-stock equities, CME BTC/ETH futures+options,
      Treasury `ohlcv_24h`, KRW daily). Per shard: force-refetch + skip-if-fresh proof + a **canonical regression cell**
      asserting the written shard's `instrument_id` is `PRODUCT_ROOT-USD@LIN-YYYYMMDD[-STRIKE-C|P]` (0 raw, 0
      whitespace, 0 non-`@LIN`). Build on the shared engine in `data_pipeline_e2e_check_2026_07_10.md`. (repos:
      unified-trading-pm, market-tick-data-service, instruments-service)
- [ ] [DATA] P0. **Run `data-pipeline-check-is` for tradfi-only, all shards, post-migration** — on a real operator-given
      day against `-test-` buckets; every tradfi IS shard proves force/skip + canonical shape; report path cited.
- [ ] [DATA] P0. **Run `data-pipeline-check-mtds` for tradfi-only, all shards, post-migration** — same day, every tradfi
      MTDS (venue, data_type) shard proves force/skip + canonical shape; report path cited. **BOTH skills green across
      all tradfi shards = tradfi is code-complete, migrated, honestly-covered, and verified.**
- [ ] [DATA] P0. **MVP backfill readiness gate** — only after A–D green: run the tradfi MVP backfills (SPOT VMs, single
      Databento IP, throughput-fixed) and verify manifest-counted canonical rows for each MVP cell.

## Codex SSOTs (read before touching a phase)

`codex/02-data/tradfi-databento-sourcing-ssot.md`, `codex/02-data/availability-manifest-and-data-status.md`,
`codex/02-data/honest-coverage-model.md`, `codex/02-data/pipeline-mode-partition.md`,
`codex/04-architecture/instruments-service-as-ssot-for-mtds.md`,
`codex/05-infrastructure/manifest-consolidator-ssot.md`, `codex/05-infrastructure/vm-launcher-runbook.md`.

## Aggregated source docs (referenced, not duplicated)

- **ID-format**: `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`,
  `instrument_id_format_canonicalization_2026_07_08.md`, `tradfi_cme_options_chain_legacy_layout_2026_07_10.md` (done),
  `canonical_id_builder_retrofit_checklist_2026_07_08.md`,
  `master_data_canonicalisation_migration_catalogue_2026_06_07.md`.
- **Manifest / v9 / status**: `tradfi_v9_stage1_finish_2026_07_06.md`,
  `tradfi_manifest_row_loss_regression_2026_07_12.md` (done),
  `tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md` (done),
  `tradfi_manifest_consolidator_row_count_varchar_crash_2026_07_12.md` (done),
  `tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md`, `phantom_captures_tradfi_2026_06_28.md`,
  `cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`,
  `mtds_available_at_cross_asset_backfill_2026_07_13.md`.
- **Coverage / sourcing**: `data_completion_tradfi_2026_07_15.md` (stale fork),
  `tradfi_multisource_backfill_2026_06_22.md`, `tradfi_massive_dual_source_2026_05_28.md`,
  `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`,
  `tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md` (done),
  `tradfi_ice_ohlcv_1m_no_working_fetch_path_2026_07_13.md` (done),
  `tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`.
- **Throughput / jobs / VMs**: `databento_default_executor_dns_starvation_risk_2026_07_17.md`,
  `mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`, `tradfi_backfill_oom_remediation_2026_06_24.md`,
  `consolidator_throughput_backlog_monitor_2026_07_09.md`, `tradfi_t1_no_working_mtds_job_2026_07_17.md`,
  `group_c_cloud_run_job_failures_triage_2026_07_16.md`.
- **Coverage/data-status/honest**: `honest_coverage_out_of_window_expected_unattempted_not_clipped_2026_07_16.md`,
  `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`,
  `coverage_floor_registries_no_cross_propagation_2026_07_17.md`,
  `data_status_page_ux_and_canonicalisation_2026_07_16.md`,
  `deployment_api_legacy_instrument_availability_venue_lookup_gap_2026_07_13.md`.
- **ML/backtest readiness (downstream, orthogonal)**: `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`,
  `features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md`.
- **Skills**: `data_pipeline_e2e_check_2026_07_10.md` + the `data-pipeline-check-mtds` / `data-pipeline-check-is`
  skills.

## Progress Log

- **2026-07-18 (slot-1) — Autonomous close-out loop STARTED; baseline re-measured live + core shape problem
  pinpointed.** Re-verified the climbing metric directly against live prod GCS (not docs), confirming the plan's ground
  truth:
  - Catalogue `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet` (1,175,390 rows; 1,111,322
    FUTURE/OPTION): `instrument_id` col **0.0% canonical** (0 in `-USD@LIN`; 997,973 carry whitespace; samples
    `CBOE:FUTURE:VX/F1`); `canonical_instrument_id` col mostly empty strings, **0.0%**.
  - Manifest `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` (5,553,510
    rows; written 2026-07-18T11:21Z so consolidator is LIVE): derivative `instrument_id` **0.0% canonical** (0 of
    989,722; samples `EW1H0_P2785`, `UD_1V__VT_...`). `instrument_type` itself is non-canonical (mixed case
    `FUTURE`/`future`, `options_chain`/`futures_chain`).
  - **CLIMBING METRIC baseline = 0% canonical across both id-column surfaces.** Filenames/parquet-content = TBD (A1).
  - **Core shape finding (drives A1+B+QG):** BOTH the MTDS "target" writer
    (`tradfi_shared.py::derive_tradfi_row_instrument_id`) and the IS adapter currently emit `@LIN` **without** the
    operator-decided `-USD` quote — MTDS builds `build_instrument_id(venue, FUTURE, product_root, margin_marker="LIN")`
    → `CME:FUTURE:SP500@LIN-...` (no `-USD`). The shared UAC builder
    (`unified_api_contracts/internal/reference/canonical_id_builder.py::_build_with_margin_marker`) rides `@marker` on
    the symbol segment; the existing CeFi convention bakes the quote INTO the symbol (`BTC-USDT@LIN`). So `-USD@LIN`
    requires the symbol segment to carry `PRODUCT_ROOT-USD`. Decision: extend the shared builder to compose
    `{SYM}-{QUOTE}@{marker}[-expiry...]` when a `quote_asset` is supplied alongside `margin_marker` (additive, opt-in,
    default `""` keeps every existing caller byte-identical), then route both tradfi writers through it with
    `quote_asset="USD"`; migration + QG + verify-gate all assert the `-USD@LIN` body. Coordinated with the parallel
    `cefi_consolidated_closeout_2026_07_18.md` (same shared builder, same DERIBIT quote ruling).
  - Env verified: 8 target repos present in slot-1; gcloud `central-element-323112` ADC; AWS `427895769566`.

- **2026-07-18 (slot-3) — Plan authored, then GROUND-TRUTH-CORRECTED against live prod GCS.** First draft (from a
  3-agent doc audit) claimed the tradfi tick surfaces + v9 schema were "largely DONE, VM-applied." Operator pushed back
  (raw symbols visible in parquet names, manifest, and the instruments data-status/catalogue). Direct live reads
  DISPROVE the "done" claim for the derivative id columns: catalogue `prod/catalog.parquet` has 0 of 1,111,322
  FUTURE/OPTION rows in `@LIN` form (raw `CBOE:FUTURE:VX/F1`); manifest `availability_index.parquet` has 0 `@LIN` across
  all years (2026 alone 568,165 raw + 63,661 malformed). Only equities/futures_chain **filenames** are canonical.
  Rewrote into the operator's one-pass structure — Phase A code (writers live+batch + migration scripts + aggregation +
  adapters + download throughput) → Phase B migrations (all 4 surfaces) → Phase C data-status/honest-coverage → Phase D
  re-smoke-test with the two pipeline-check skills ADAPTED to the tradfi MVP universe (S&P index futures+options,
  delta-one single-stock equities, CME BTC/ETH futures+options, daily treasuries + KRW) → MVP-backfill-ready. All
  tradfi + tradfi-touching IS/MTDS docs aggregated above; none duplicated. The DERIBIT missing-quote finding stays
  captured on the cefi side (`cefi_consolidated_closeout_2026_07_18.md` line 183).

- **2026-07-18 (slot-1, autonomous loop) — Phase A1 underway: UAC builder SHIPPED + MTDS forward-write converged + full
  leak trace.** Re-verified the climbing metric live myself (own measurement, not the doc) on a fresh prod snapshot:
  - **CLIMBING METRIC baseline = 0.0000% canonical (`-USD@LIN`)** on the id-column surfaces: catalogue `instrument_id`
    **0 / 1,111,322** FUTURE/OPTION (113,349 raw like `CBOE:FUTURE:VX/F1` + **997,973 whitespace** — the
    `CME:OPTION:E3AN6 C7960` literal-space class); catalogue `canonical_instrument_id` **0 / 1,111,322** (all empty
    strings); manifest `availability_index.parquet` `instrument_id` **0 / 989,723** (783,523 raw like `EW1H0_P2785` +
    206,200 whitespace). Reusable measurement tool: scratchpad `measure_metric.py` (pyarrow, matches the exact
    `VENUE:TYPE:ROOT-USD@LIN-YYYYMMDD[-STRIKE-C|P]` shape).
  - **[A1 builder] SHIPPED — `unified-api-contracts@8b7c4967`.** Extended the shared
    `canonical_id_builder._build_with_margin_marker` to compose an explicit `-USD` quote onto the _bare_ product-root
    symbol segment when `quote_asset` is passed alongside `margin_marker` → `CME:FUTURE:SP500-USD@LIN-20300621`,
    `CME:OPTION:SP500-USD@LIN-20251017-5000-C`, `CBOE:FUTURE:VIX-USD@LIN-20260722`. Additive + opt-in: default
    `quote_asset=""` keeps every existing `margin_marker` caller byte-identical (audited — all CeFi callers embed the
    quote in the symbol e.g. `BTC-USDT`/`BTC-USD` and never pass `quote_asset`, so zero risk of double-append; verified
    `BINANCE_FUTURES:PERPETUAL:BTC-USDT@LIN` / `BINANCE_DELIVERY:FUTURE:BTC-USD@INV-20260925` unchanged). Added
    `TestTradfiUsdMarginMarker`. UAC QG green (337s).
  - **[A1 writers] MTDS forward-write CONVERGED (edits made, MTDS QG/ship pending this tick):**
    `databento_enrichment.py::_classify_row` (primary databento tick forward-write) and
    `tradfi_shared.py::derive_tradfi_row_instrument_id` (batch derive) now pass `quote_asset="USD"` for FUTURE/OPTION →
    both emit `-USD@LIN`. UAC is editable-local to MTDS (confirmed) so the change resolves at runtime.
  - **LEAK TRACE (drives remaining A1 + Phase B):** (1) **IS catalogue adapter** `.../tradfi/databento/adapter.py:880`
    sets `instrument_key = VENUE:TYPE:{sanitized_raw}` (→ the catalogue's raw `instrument_id`, e.g. `CME:FUTURE:GCQ26`),
    and `_build_canonical_instrument_id` (`:974`) emits a colon/month-only non-`@LIN` additive field (mostly empty live
    because `_resolve_product_root` returns None) — BOTH must converge to `-USD@LIN` (→ IS sub-agent). (2) **Manifest**
    `instrument_id` derives from the parquet **content** `instrument_id` column via
    `unified_trading_library/io/streaming_writer.py`→`manifest_writer`, so once the content column is canonical (done),
    forward-write manifest rows are canonical too; historical manifest+catalogue rows are the Phase-B migration. (3) The
    `tardis_*` paths under `adapters/tradfi/` are CeFi (deribit `derive_row_instrument_id`) or the **futures_chain
    bundle** atom (product-symbol id = canonical by design) — NOT tradfi-databento leaks.
  - **Concurrency note:** slot-3 is running the parallel `cefi_consolidated_closeout_2026_07_18.md` (same shared UAC
    builder); QG cap = 2 (10 cores) so serialize; reconcile-not-stomp if slot-3 lands a builder change (my change is
    additive so it merges cleanly). Env: 8 repos present, gcloud `central-element-323112` ADC, AWS `427895769566`.

- **2026-07-18 (slot-1, tick 2) — MTDS forward-write SHIPPED + verified; IS convergence written, ship in progress.**
  - **[A1 writers] SHIPPED `market-tick-data-service@c44d5f0d`** — `databento_enrichment.py::_classify_row` (primary
    databento tick forward-write) + `tradfi_shared.py::derive_tradfi_row_instrument_id` (batch derive) now emit
    `-USD@LIN`. Landed on attempt 1 of an atomic re-gate+quickmerge retry loop (won the push-race vs slot-3's parallel
    MTDS cefi-script commits — those FF-staled my QG sentinel twice, so I automated the re-gate). MTDS QG green.
  - **Runtime PROOF (own venv):** FUTURE `ESM26`→`CME:FUTURE:SP500-USD@LIN-20260619`; OPTION `E3AN6 C7960`
    →`CME:OPTION:SP500-USD@LIN-20260117-7960-C` (0 whitespace, product root ES→SP500). Metric on LIVE surfaces stays 0%
    until Phase B migrates historical — writers are the gate for B, now open.
  - **[A1 IS] IS catalogue adapter convergence WRITTEN** (sub-agent, uncommitted in
    `instruments-service/.../tradfi/databento/adapter.py` + `tests/unit/test_databento_tardis_adapter.py`) — reviewing +
    gating + shipping now (sub-agent stopped pre-ship). Note: slot-3 already shipped the parallel DERIBIT
    always-BASE-QUOTE fail-loud fix `instruments-service@d72edcf7` (same 2026-07-18 quote ruling, cefi side).
  - **Scoping:** launched a 4-agent read-only Workflow (`wf_2f2c9a39-164`) mapping Phase A2/A3 + B + C + D into
    actionable change-maps (in flight). Phase-B schema recon done: catalogue+manifest carry NO strike/option_right cols
    → migration must re-parse each raw id via the databento classifier (one shared `canonicalize_raw_tradfi_id`), so
    migrated == newly-written byte-for-byte; unparseable spreads (`UD_1V__VT_...`) → quarantine not silent-drop.
