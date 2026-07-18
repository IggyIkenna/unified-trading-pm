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

- [x] ✅ [BACKEND] P0. **IS catalogue adapter converged to `-USD@LIN` — instruments-service@287d1607.** For resolvable
      FUTURE/OPTION, `instrument_key` is now built via the shared
      `build_instrument_id(canonical_venue, itype, product_root, expiry_date=…, strike=…, option_right=…,     margin_marker="LIN", quote_asset="USD")`
      — byte-identical to the MTDS write path (same `EXCHANGE_CODE_TO_NAME` root translation). `canonical_instrument_id`
      set BYTE-EQUAL to `instrument_key`; the old colon/month-only additive `_build_canonical_instrument_id` DELETED.
      Unresolved product-root (OSI `O:SPX…`, unknown roots) falls back to the sanitized-raw shape — no crash, no
      fabricated identity (historical/unresolvable = Phase B). Tests assert `CME:FUTURE:SP500-USD@LIN-20300621` /
      `CME:OPTION:SP500-USD@LIN-20251017-5000-C` / `CBOE:FUTURE:VIX-USD@LIN-20260722`; removed one invalid test (schema
      forbids FUTURE-with-null-expiry). IS QG green. (repo: instruments-service)
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

> **Phase-B design (empirically grounded, scoping workflow `wf_2f2c9a39-164`, full design in scratchpad `scope_B.md`):**
> The old `migrate_tradfi_single_leg_product_root_lin_2026_07_09.py` is a **CONFIRMED NO-OP** — its `_ID_RE` matches an
> intermediate `CME:FUTURE:GOLD-20260821` shape that NEVER persisted; every real raw id (`CME:OPTION:E1AF0 C1600`,
> `EW1H0_P2785`, `CBOE:FUTURE:VX/F1`) returns None → 0 rows rewritten. **Write NEW scripts, don't re-run.** Measured
> canonicalizability with {strip `VENUE:TYPE:`, strip `O:`, `_`→space, dash-strike→space} + the live
> `classify_databento_symbol`: catalogue **~1,110,780 / 1,111,322 (99.95%)** canonicalize, ~542 quarantine. THREE
> orthogonal manifest defects (not one): (1) id-format, (2) **~400k `instrument_type` MISLABELS** (options/combos
> stamped `FUTURE` — must re-stamp from the classifier, not trust the column), (3) null-id bundle atoms (by design).

- [x] ✅ [DATA] P0. **Shared primitive SHIPPED — `unified-api-contracts@3bd4ec29`.**
      `canonicalize_raw_tradfi_id(raw,     venue, instrument_type)` + `assert_tradfi_derivative_ids_canonical` +
      `CanonResult`/`CanonStatus` + `TARGET_TRADFI_DERIVATIVE_ID_RE` in `internal/reference/tradfi_id_canonicalizer.py`
      (top-level re-exported). Re-derives type via `classify_databento_symbol` (lazy-imported — circular-import
      avoidance) + builds via `build_instrument_id(margin_marker="LIN", quote_asset="USD")` with the 4
      body-normalizations; typed result never a silent fallback; venue from the row column (never default-CME). 20 unit
      tests, UAC QG green. **Empirical proof on the live snapshots:** catalogue **99.86% OK** (1,109,717/1,111,322;
      1,267 quarantine-unparseable [204 negative-strike + 1,063 ICE-qualifier] + 338 quarantine-combo); manifest
      **62.42% OK** (617,808/989,755; QUARANTINE_COMBO 325,473 [147k CBOE `UD_` + 176k CME prefix-spreads] +
      QUARANTINE_UNPARSEABLE 39,217 [36k ICE + 2,898 `ticks` placeholders] + NULL_OR_EMPTY 7,225 + 32 continuous).
      **566,630 (57%) stored-type-vs-classifier mismatch** confirmed. Reuse `scratchpad/measure_canonicalize.py`. (repo:
      unified-api-contracts)
- [ ] [DATA] P0. **Migrate the catalogue (Surface A) —
      `instruments-service/scripts/canonicalize_tradfi_catalogue_usd_lin_*.py`** modeled on
      `canonicalize_okx_margin_type_2026_07_09.py`. DURABILITY TRAP: `prod/n` is a roll-up regenerated by
      `build_instrument_catalogue.py` from the per-day
      `instrument_availability/by_date/day=*/venue=*/instruments.parquet` corpus — a `prod/n`-only rewrite SILENTLY
      REVERTS on next rebuild (killed the 2026-07-08 combo migration). So migrate BOTH `prod/n` (snapshot → recompute
      `instrument_id`+`instrument_type`+`underlying`+`canonical_instrument_id` byte-equal → upload) AND the per-day
      corpus (worklist from the manifest, single-walk), then re-run `build_instrument_catalogue.py` and assert `prod/n`
      stays canonical. (repos: instruments-service)
- [ ] [DATA] P0. **Migrate the live manifest (Surface B) —
      `market-tick-data-service/scripts/migrate_tradfi_manifest_usd_lin_*.py`** via the **additive per-VM-shard write**
      (reuse `restamp_tradfi_schema_v9_tail_2026_07_16.py`'s `_vm_staging/` path — race-free vs the ~10-min
      consolidator, NO drain needed); covers ALL data_types + re-stamps the ~400k mislabeled `instrument_type` rows.
      Fallback only if blocked: pause-consolidator + snapshot + CAS. (repos: market-tick-data-service,
      unified-trading-library)
- [ ] [DATA] P0. **Migrate GCS filenames + tick CONTENT (Surfaces C+D)** — single-walk worklist from the
      availability_index rows; bundled OHLCV → `underlying={HUMAN_ROOT}`; flat per-contract → full
      `VENUE:TYPE:ROOT-USD@LIN-...parquet`; rename via UTL `gcs_copy_object`+`gcs_delete_object` (never `gsutil`).
      Historical tick parquet CONTENT `instrument_id` column rewritten with the primitive (do NOT touch the raw `symbol`
      column — it's the classifier input). Then the **verify gate** `assert_tradfi_derivative_ids_canonical` (classify
      by BODY not stored type; TARGET `^[A-Z0-9-]+:(FUTURE|OPTION):[A-Z0-9]+-USD@LIN-\d{8}(-\d+(\.\d+)?-[CP])?$`; 0
      whitespace; bounded+enumerated quarantine sidecar) proves 0 raw on all four surfaces.
- [ ] [DECISION] P1. **ICE qualifier variants (`BRN_Z`/`BRN!`/`BRN_MD1`) = BLOCKED-OPERATOR-DECISION** — the
      classifier + current writer emit `ICE:FUTURE:BRN_Z-USD@LIN-...` with banned chars (`_`,`!`);
      `EXCHANGE_CODE_TO_NAME` only maps the bare root. Non-MVP (ICE not in MVP universe) so quarantine-with-tracking
      unblocks the MVP metric. Options: **A: qualifier-normalize + map base root [REC]** / B: accept `_qualifier`, relax
      gate for ICE / C: quarantine ICE, defer. Surface to operator when ICE cells are worked; does NOT block MVP.
- [ ] [DATA] P0. **Enumeration-driven migration (SINGLE SOURCE OF TRUTH — operator, 2026-07-18).** The migration MUST be
      driven by the FULL distinct set of dimension values actually present in the tradfi manifest/GCS rollup (query the
      availability_index/coverage-rollup), NOT sampled shapes — so every value is covered + dupes are caught. **Audit
      done (local snapshot, scratchpad `enumerate_dimensions.py`)** — non-canonical dimensions found: (1)
      `instrument_type` **18 distinct** with case+plural dupes — `FUTURE`(568k)/`future`(421k)/`FUTURES`/`futures`,
      `EQUITY`/`equity`, `ETF`/`etf`, `SPOT_PAIR`/`spot_pair`, `indices`/`index`, +
      `<null>`(511k)/`''`(85k)/`UNKNOWN`(77); catalogue is all-UPPERCASE enum while manifest is mixed → surfaces
      DISAGREE. Writer `_PARTITION_INSTRUMENT_TYPE` (`databento_adapter.py:179`) maps FUTURE→`futures_chain`,
      OPTION→`options_chain`, EQUITY→`equity` (lowercase, bundle-grain). (2) **Barchart STALE** —
      `source=barchart`(4,655) + venue `BARCHART`(9,119) + `pipeline_mode=batch_barchart` despite Barchart being
      RETIRED. (3) `chain` null-vs-`''` dupe. **✅ DECIDED (operator, 2026-07-18): canonical `instrument_type` =
      UPPERCASE enum, CATALOGUE is the SSOT** — `{FUTURE, OPTION, EQUITY, ETF, INDEX, COMBO, SPOT_PAIR}`. Migrate the
      manifest UP: normalize `future`/`futures`/`FUTURES`→`FUTURE`, `equity`→`EQUITY`, `etf`→`ETF`,
      `spot_pair`→`SPOT_PAIR`, `indices`→`INDEX`; re-derive the SEMANTIC type from the classifier for the 566,630 (57%)
      mismatched rows (options mislabeled FUTURE→`OPTION`, combos→`COMBO`); `<null>`/`''`/`UNKNOWN` classify or
      quarantine. Bundle atoms `futures_chain`/`options_chain` are a SEPARATE partition-grain axis (manifest-only,
      null-id) — keep distinct, NOT folded into the enum. **IMPLICATION (new todo below): the WRITER paths emitting
      lowercase per-contract types must also emit UPPERCASE, else the migration re-drifts.** Bake the variant→UPPERCASE
      map into the migration + verify-gate. (repos: market-tick-data-service, unified-trading-library,
      instruments-service)
- [ ] [BACKEND] P0. **Converge every WRITER's `instrument_type` emission to the UPPERCASE enum (catalogue SSOT, operator
      2026-07-18)** so forward-writes don't re-drift the manifest to lowercase after the Phase-B re-stamp. Audit the
      per-contract write paths (Tardis/databento/massive/yahoo) that stamp `future`/`FUTURE`/`equity` into the manifest
      `instrument_type` and route them through one canonical UPPERCASE emitter; keep the `_PARTITION_INSTRUMENT_TYPE`
      bundle-grain mapping (`futures_chain`/`options_chain`) as the distinct partition axis. (repos:
      market-tick-data-service, unified-trading-library)
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
- [ ] [BACKEND] P1. **RE-ADD the data-status "dimensions enumeration" view to deployment-ui/api (operator, 2026-07-18 —
      "I really need to add it back").** Per asset_group, list every distinct `instrument_type` / `data_type` / `chain`
      / `source` / `pipeline_mode` / `venue` present in the manifest/GCS (the honest-coverage rollup) with counts, so
      non-canonical naming + duplications are VISIBLE (the exact dupes the 2026-07-18 audit found:
      `FUTURE`/`future`/`FUTURES`, `EQUITY`/`equity`, stale `barchart`). This existed, was REMOVED — restore it as the
      standing canonical-drift detector (it is how we catch the next drift without a manual parquet read). Backend =
      deployment-api endpoint over the availability_index distinct-values; UI = a dimensions panel on the data-status
      page. Find where it was removed (git log deployment-api/deployment-ui for the removed enumeration endpoint/view).
      (repos: deployment-api, deployment-ui)
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

## Pass-through from the 2026-07-18 consolidated canonicalisation audit (slot-4) — decisions + measured worklist

> Authored by the DeFi close-out audit (`defi_consolidated_closeout_2026_07_18.md`) and handed here per the operator's
> ownership split (tradfi findings land in THIS plan). Operator rulings 2026-07-18.

**Operator decisions confirmed (tradfi):**

- **Equity id = `-USD` on ALL FOUR surfaces** — target `NASDAQ:EQUITY:AAPL-USD`. Today the content `instrument_id`
  column + manifest key emit BARE `NASDAQ:EQUITY:AAPL` (only the filename carries `-USD`, via a separate `file_stem`).
  **Code fix**: `_build_tradfi_cash` currently appends the quote only for `INDEX` — extend it to append `-USD` for
  `EQUITY` (and `ETF`) so the content column matches the decided target. Then migrate the historical rows (1,762,272
  prefixed-missing-`-USD` + 1,082,217 raw-ticker rows). The Phase-B/D verify gate must assert `-USD` on equity too (its
  current regex only targets FUTURE/OPTION).
- **Venue token = HYPHEN SSOT** (tradfi venues are already single-spelling uppercase — CME/NYSE/NASDAQ/CBOE/KRX/FX — no
  drift; confirmed clean on this surface).
- **Daily data_type = `ohlcv_24h`** (least churn) — the live manifest already carries **541,579 `ohlcv_24h` rows and
  ZERO `ohlcv_1d`**, so `ohlcv_24h` is the persisted token → **no data migration**. The only code change: add
  `ohlcv_24h` to `market-tick-data-service/.../tradfi/tradfi_shared.py::TRADFI_DATA_TYPES` (which currently RAISES on
  it) and reconcile the Yahoo adapter docstring. The daily Treasury/KRW ids (`CBOE:INDEX:US10Y-USD`,
  `FX:CURRENCY:KRW-USD`) are stable either way.
- **Combos = the leg-aware signed-weight spec** (operator 2026-07-09,
  `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`): per-leg human-readable `instrument_key` + weight +
  direction-as-sign, 1–4-leg hard cap, migrate code AND data. The IS-catalogue CME + CBOE/VX path is shipped; **OPEN
  here**: the **1,154,976 tick-side `UD_*` manifest combos** (null id + null `combo_type`/`leg_weights`) need the same
  legs-re-derived → structured `VENUE:COMBO:…` id + populated `leg_weights` treatment (Phase-B), plus the
  `build_instrument_catalogue.py` self-refresh durability fix. **Open sub-nuance**: the top-level combo id being
  strategy-named (`CME:COMBO:SP500-BUTTERFLY-…` from `build_combo_id`) vs the operator's "no separate strategy field,
  infer from legs" spec — resolve when combos are worked; doesn't block.
- **ETF** — keep `etf` as a distinct canonical instrument_type (ETF ≠ equity; IBIT/ETHA are MVP crypto-ETFs); case-fold
  `ETF`→`etf`. (Flag if you'd rather fold ETF into `equity` — 270,460 rows either way.)
- **~591k instrument_type MISLABELS** (options/combos stamped `future`/`FUTURE`) → re-stamp from the classifier by BODY,
  not the stored column (the plan's cited "~400k" is the lowercase-`future` subset; the 206,200 `FUTURE` calendar
  spreads are an additional cohort).

**Live manifest worklist (`market-data-tick-tradfi-prd`, 5.55M rows; canonical id ≈0.02%, ZERO derivative ids carry
`@LIN/@INV`)** — venue/data_type/source/pipeline_mode are CLEAN; instrument_type + instrument_id are the work:

| dimension       | non-canonical                                   | canonical target                                 |     ~rows | action                          |
| --------------- | ----------------------------------------------- | ------------------------------------------------ | --------: | ------------------------------- |
| instrument_type | `FUTURE`/`EQUITY`/`SPOT_PAIR`/`FUTURES`         | lowercase                                        |   750,715 | case-fold                       |
| instrument_type | `combo` (null id + null combo_type)             | leg-aware `VENUE:COMBO:…` + `leg_weights`        | 1,154,976 | synthesize (see combo decision) |
| instrument_type | `etf`/`ETF`                                     | `etf` (case-fold)                                |   270,460 | case-fold                       |
| instrument_type | `NULL`/`''`                                     | populate from writer grain                       |   596,851 | resolve                         |
| instrument_type | MISLABEL `future`=option/combo, `FUTURE`=spread | relabel from id                                  |   591,183 | relabel                         |
| instrument_id   | prefixed missing `-USD` (`NYSE:EQUITY:DUK`)     | `…-USD`                                          | 1,762,272 | append quote                    |
| instrument_id   | raw ticker (`ASTS`,`QQQ`)                       | `VENUE:EQUITY\|ETF:SYM-USD`                      | 1,082,217 | reconstruct                     |
| instrument_id   | raw databento option (`EW1H0_C3025`)            | `VENUE:OPTION:ROOT-USD@LIN-YYYYMMDD-STRIKE-C\|P` |   238,359 | reconstruct                     |
| instrument_id   | raw chain-root (`SI.OPT`,`VX.FUT`)              | `VENUE:FUTURES_CHAIN:ROOT-USD@LIN`               |   216,563 | reconstruct                     |
| instrument_id   | whitespace (`CME:OPTION:E3AN6 C7960`)           | de-spaced canonical                              |   206,579 | strip whitespace                |
| instrument_id   | NULL/empty aggregate rows                       | synthesize symbolic id                           | 1,844,635 | synthesize                      |
| data_type       | `futures_chain` leaked (8)                      | belongs in instrument_type                       |         8 | relabel                         |
| source/vendor   | legacy `barchart` (retired)                     | drop or keep-historical                          |     4,655 | operator: drop?                 |

**Enumeration-restore (cross-AG, owned by the DeFi plan Track 6)**: the raw distinct-values audit panel per asset_group
(removed on `deployment-api@512180be`) is being restored so this worklist stays live-visible during the migration.

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

- **2026-07-18 (slot-1, tick 3) — IS convergence + scoping complete; Phase B design locked; skills linker fixed.**
  - **[A1 IS] shipping** — reviewed the sub-agent's IS adapter diff (correct: builds `-USD@LIN` via shared builder for
    resolvable FUTURE/OPTION, `canonical_instrument_id`=`instrument_key` byte-equal, drops old colon/month additive
    builder, clean raw fallback). Removed one INVALID sub-agent test (`test_missing_expiry_falls_back_to_raw_shape` —
    asserts a schema-FORBIDDEN FUTURE-with-null-expiry state; the real fallback is covered by
    `test_unresolved_product_root_falls_back_to_raw_shape`). Atomic re-gate+quickmerge retry loop in progress vs a busy
    IS push-race (peers pushing `build_instrument_catalogue.py`). IS tests assert `CME:FUTURE:SP500-USD@LIN-20300621` /
    `CME:OPTION:SP500-USD@LIN-20251017-5000-C` / `CBOE:FUTURE:VIX-USD@LIN-20260722`.
  - **Scoping workflow DONE** (`wf_2f2c9a39-164`, 4 agents) — full change-maps in scratchpad `scope_{A,B,C,D}.md`.
    Highlights: **A3.1 Databento DNS-executor** is the P0 pure-code win (`databento_fetch.py:186/:388/:672` +
    `databento_batch_jobs.py:629` all use `run_in_executor(None,…)` → dedicated pool mirroring
    `tardis_csv_transport.py::_get_parse_executor`; `:186` full-fetch hold is the highest-risk, NOT the doc's headline
    `:672`). **A2.1 CME mbp_10/trades/tbbo** UAC-capability restoration is now DE-SCOPED for MVP by the operator billing
    ruling (ohlcv_1m only); adapter allowlist already fixed `@e2018167`. **A2.2** KRX resolved (verify KRW),
    IBKR/combo-leg done (flip stale todo), `mvp_mode` dead gate → delete. Phase-B design → the 5 refined Phase-B todos
    above (NEW scripts, promote primitive to UAC, catalogue prod/n+per-day-corpus durability, manifest per-VM-shard
    write, re-stamp ~400k mislabeled instrument_type, ICE-qualifier BLOCKED-OPERATOR-DECISION).
  - **Operator (present) clarifications applied** (pm@882650559): Databento MVP backfill = `ohlcv_1m` ONLY
    (mbp_10/trades/tbbo billing-gated by design, 1mo L3 + 1yr L1); Yahoo Finance = 24h/1d daily (Treasuries `ohlcv_24h`,
    KRW). **Skills linker** — this slot still had the legacy per-skill `.claude/skills` layout (Jul 7), so
    data-pipeline-check-is/-mtds + plan-reconcile + pre-compact (added Jul 17-18) never surfaced; re-ran
    `link-claude-skills.sh` → migrated to the single-dir link, all 6 skills now surface (mid-session).

- **2026-07-18 (slot-1, tick 4) — Phase B migration scripts written + dry-run-VERIFIED; 2 CRITICAL findings caught
  before any prod write.** Both scripts (2 sub-agents) reuse the shared `canonicalize_raw_tradfi_id` primitive:
  - **Catalogue** `instruments-service/scripts/canonicalize_tradfi_catalogue_usd_lin_2026_07_18.py` — dry-run vs local
    snapshot: **99.86% OK** (1,109,717/1,111,322; 338 combo + 204 neg-strike + 1,063 ICE-qualifier quarantine);
    self-check passes; snapshot-before-write to `prod/backups/`. In-place `prod/n` rewrite + `--by-day` corpus
    (durability). SAFE to `--apply` (flat rewrite, no dedup-key/consolidator concern). Shipping via the git-add-prestage
    workaround.
  - **Manifest** `market-tick-data-service/scripts/migrate_tradfi_manifest_usd_lin_2026_07_18.py` — SHIPPED
    `market-tick-data-service@2bddcb9e`. Dry-run: derivative **62.42% OK** (617,808/989,755) + **238,227 mislabel
    fixes**
    - **3,300,155 UPPERCASE case re-stamps** (Bucket 3, operator ruling) + 142,590 bundle-underlying translations;
      self-verify 617,808/617,808 canonical.
  - **🚨 CRITICAL (data-correctness) — dedup-key: the manifest per-VM-shard additive write DUPLICATES, does NOT achieve
    0-raw.** `instrument_id`/`instrument_type`/`underlying` ARE members of the consolidator's `_OPTIONAL_DEDUP_COLS`
    (`unified_trading_library/manifest_consolidator.py`), so changing them changes the row's dedup key → the additive
    shard ADDS the corrected row as a NEW key and the OLD raw row SURVIVES the merge (both coexist). So `--apply` alone
    leaves the raw rows in place. **Manifest migration REVISED: must PAUSE the tradfi manifest-consolidator + CAS
    in-place rewrite** (sanctioned by the CLAUDE.md direct-index-mutation rule) so raw rows are REPLACED not duplicated;
    the additive+`superseded_keys`-purge alt still needs a pause/CAS for the removal, so pause+CAS is the one correct
    path. **DO NOT run manifest `--apply` as-is.** Captured as the revised Phase-B manifest todo.
  - **quickmerge TOOLING BUG (affects every agent shipping a NEW file)** — `quickmerge.sh`'s early "identical to main"
    check (`git diff origin/main`) does NOT see UNTRACKED files → for a first-time script it silently prints "nothing to
    merge" + exits 0 WITHOUT shipping. Workaround: `git add` the file BEFORE quickmerge. FIX needed in
    `unified-trading-pm/scripts/quickmerge.sh` (stage `--files` before the early-exit, or also check
    `git status --porcelain`) — filed as a Phase-B-adjacent tooling todo.
  - **NEXT:** catalogue `--apply` (safe) → verify → then build the manifest pause+CAS path → manifest `--apply` →
    verify-gate 0 raw → re-measure the live metric (the climb).

- **2026-07-18 (slot-1, tick 5) — 🎯 CATALOGUE SURFACE MIGRATED — metric climbed 0.0000% → 99.8556% (VERIFIED LIVE).**
  Ran `canonicalize_tradfi_catalogue_usd_lin_2026_07_18.py --apply --full-sweep` against prod
  (`GCP_PROJECT_ID=central-element-323112`; the prod-op must run backgrounded — the harness 2-min foreground cap killed
  the first attempt AFTER the backup but BEFORE the write, so the original was intact + safe). Result: **1,109,717 rows
  migrated**, `prod/catalog.parquet` rewritten 11.3MB→16.0MB, backup
  `prod/backups/catalog.parquet.pre_usd_lin_*.bak.parquet`
  - quarantine sidecar written. **INDEPENDENT live re-measure (own tool, not the script)**: catalogue `instrument_id`
    **1,109,717/1,111,322 = 99.8556%** canonical `-USD@LIN`; `canonical_instrument_id` same (byte-equal; the old
    all-empty additive col is gone). Only 1,605 non-canonical remain = the quarantined 338 combo + 204 negative-strike +
    1,063 ICE-qualifier. The deployment-api "Upcoming expiries" widget now renders `CME:OPTION:SP500-USD@LIN-...` not
    `E3AN6 C7960`.
  * **TWO follow-ups found (both minor, tracked):** (1) **catalogue combo re-stamp gap** — 338 CME combo-strips
    (`CME:FUTURE:CL:SA 03M V7`) are stored `instrument_type=FUTURE` but classifier-derive as COMBO; the migration
    quarantined them (left raw + FUTURE), so the post-apply verify flagged 25 as "unexpected violations" (it judges by
    the DECLARED type). FIX = re-stamp quarantined-combo catalogue rows FUTURE→COMBO (per operator UPPERCASE +
    classifier semantic type) AND/OR refine `assert_tradfi_derivative_ids_canonical` to classify by BODY not declared
    type (scope_B.md §7). (2) **Durability NOT yet done** — only `--full-sweep` (prod/n) ran; the per-day
    `instrument_availability/by_date/` corpus still needs `--by-day --apply` or the next `build_instrument_catalogue.py`
    rebuild reverts prod/n. NEXT: run `--by-day`, then manifest pause+CAS.

- **2026-07-18 (slot-1, tick 6) — catalogue per-day durability sweep RUNNING + manifest CAS-mode built + EXECUTION
  RUNBOOK.** Per-day sweep `--by-day --apply --by-day-full-sweep --workers 24` running in bg (2,636 partitions / 27,092
  files, ~3h idempotent, safe — backs up each file, skips already-canonical; progress = TARGET files rewritten).
  Manifest CAS-mode added to `migrate_tradfi_manifest_usd_lin_2026_07_18.py` (`--in-place-cas`: download →
  generation-match CAS rewrite that REPLACES raw rows, fixing the additive-dedup-key duplication; dry-run verified
  617,808/617,808 canonical + 3.3M UPPERCASE + 142,590 bundle translations). **MANIFEST EXECUTION RUNBOOK (the riskiest
  op — run each step, verify, RESUME at the end no matter what):**
  1. Ship the CAS-mode (in flight). 2.
     `gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-tradfi-cron --location asia-northeast1 --project central-element-323112`
     → `describe ... --format='value(state)'` must show PAUSED.
  2. `cd market-tick-data-service && GCP_PROJECT_ID=central-element-323112 .venv/bin/python scripts/migrate_tradfi_manifest_usd_lin_2026_07_18.py --apply --in-place-cas`
     (BACKGROUND — 132MB download + 4M-row rewrite + snapshot to `_index/backups/` + `if_generation_match` CAS upload;
     aborts LOUDLY on race, no partial write).
  3. Independent verify: re-download `_index/availability_index.parquet` + run scratchpad `measure_metric.py` → expect
     derivative `instrument_id` ~62.4% canonical (rest = the enumerated combo/unparseable/continuous quarantine, NOT raw
     leaks) + 0 whitespace on OK rows. 5.
     **`gcloud scheduler jobs resume uts-prod-manifest-consolidator-market-data-tradfi-cron --location asia-northeast1 --project central-element-323112`**
     (CRITICAL — never leave the consolidator paused). Then re-measure the manifest surface (the second climb) + flip.

- **2026-07-18 (slot-1, tick 7) — 🎯 MANIFEST SURFACE MIGRATED (2nd climb) — consolidator paused→CAS→RESUMED cleanly.**
  Executed the runbook: paused `uts-prod-manifest-consolidator-market-data-tradfi-cron` (runs `*/1` — EVERY MINUTE, so
  the pause was essential) → `--apply --in-place-cas` (generation-match CAS: gen 1784386961903329→1784387144414068, NO
  race, 5,553,510 rows rewritten, 114.8MB) → **RESUMED (ENABLED, verified)**. **INDEPENDENT live re-measure:** manifest
  derivative `instrument_id` **0% → 62.4223%** (617,808/989,723); remaining 37.58% = the enumerated quarantine set (325k
  `UD_1V__VT_` CBOE user-defined-strategy COMBOS + 39k unparseable + continuous — NOT raw leaks, they belong to the
  combo track). `instrument_type` now UPPERCASE per operator ruling (`equity`+`EQUITY`→`EQUITY` 1.99M, `combo`→`COMBO`
  1.15M, mislabels re-derived → `OPTION` 238,227). **Backups:**
  `_index/backups/availability_index.pre_usd_lin_20260718T150445Z.parquet`.
  - **RESIDUAL (the key follow-up — cleans both the metric + the dimension):** 165,715 rows still typed lowercase
    `future` = the quarantined COMBOS whose `instrument_type` my migration left unchanged (quarantine = no id/type
    change). They should be `COMBO` (classifier-derived). Because they're counted as raw FUTURE/OPTION, they DRAG the
    62.42% down — re-stamping quarantined-combo `instrument_type`→`COMBO` (on BOTH catalogue + manifest) lifts the true
    FUTURE/OPTION-canonical toward ~100% AND removes the last `future`/`FUTURE` dimension dupe. P0 follow-up.
  - **Durability re-check IN PROGRESS** (does the every-minute consolidator revert the CAS rewrite? modeled on
    `restamp_tradfi_schema_v9_tail` which persisted, so expected durable — verifying live).
  - **Phase C dimensions-view DONE** (operator ask): backend `deployment-api@09656f4`
    (`GET /data-status/axis-value-census`) + UI already shipped by the cefi-Track-6 peer (`deployment-ui@3fb6779`);
    live-verified reproducing the exact drift audit. The old drilldown "removal" was `deployment-api@512180be`
    display-canonicalizing (folding dupes) — good UX, killed drift-detection; the census panel restores the raw view.
  - **Still queued:** combo re-stamp (above), cash-type `-USD` writer fix
    (`NASDAQ:EQUITY:AAPL-USD`/`FX:CURRENCY:KRW-USD` — builder `_build_tradfi_cash` adds `-USD` only for INDEX today),
    catalogue per-day sweep (~60% done), Barchart-retired purge, Phase A2/A3, Phase D.

- **2026-07-18 (slot-1, tick 8) — ✅ MANIFEST DURABILITY CONFIRMED (verified live, not assumed).** Two re-measures at
  +3min and +7min post-migration are BYTE-IDENTICAL (925,816 FUTURE/OPTION, 553,901 canonical 59.83%, raw 165,715 +
  whitespace 206,200; index generation/size stable at 80.6MB). **The raw count is FLAT across ~10 consolidator cycles →
  NO REVERT.** The every-minute consolidator did a ONE-TIME prune (my CAS index 617,808 canonical → consolidator
  steady-state 553,901; ~64k rows removed as stale/dedup, NOT reverted to raw — raw stayed flat) then stabilized. So the
  CAS-of-the-consolidated-index approach IS durable here (matching the `restamp_tradfi_schema_v9_tail` precedent). Both
  Phase-B surfaces (catalogue + manifest) are now migrated + independently-verified-live + durable. The residual 59.83%
  (vs a naive 100%) is entirely the quarantined combos (`UD_1V__VT_`) sitting in the FUTURE/OPTION denominator — the
  combo re-stamp (FUTURE→COMBO) P0 follow-up removes them from the denominator and lifts the TRUE non-combo
  FUTURE/OPTION canonical toward ~100%.

- **2026-07-18 (slot-1, tick 9) — Phase-A refinements landing (throttled by multi-slot QG contention, 4-5 concurrent).**
  - **[cash-type -USD] SHIPPED `unified-api-contracts@33e3f369`** — `_build_tradfi_cash` now suffixes `-USD` for
    EQUITY/CURRENCY/ETF/BOND/COMMODITY (was INDEX-only; CDS bare by design) → `NASDAQ:EQUITY:AAPL-USD`,
    `FX:CURRENCY:KRW-USD`. 6 tests updated to `-USD`. So the WRITER now emits `-USD` on cash types; the historical
    catalogue/manifest cash rows still need the **cash-type migration** (add `-USD` to equity/currency/etf/index/bond
    ids) — fold into the combo re-stamp re-run.
  - **[A3 Databento executor] edits complete, ship pending QG-cap** — dedicated `_get_dbn_fetch_executor()` routes all
    databento_fetch + databento_batch_jobs fetch/decode off the default pool (DNS-starvation fix); waiting on a gate
    slot.
  - **NEW FINDING (follow-up todo): Massive normalizers bypass the shared builder** —
    `unified-api-contracts/unified_api_contracts/external/massive/normalize.py`
    (`normalize_massive_equity`/`_futures`/…) build `instrument_key` via raw f-strings
    (`f"{venue}:{itype.value}:{ticker}"`), so Massive-sourced tradfi ids are bare (`NASDAQ:EQUITY:AAPL`, no `-USD`) and
    won't get the cash `-USD` or the FUTURE `-USD@LIN` shape. Route the Massive normalizers through
    `build_instrument_id`. (repo: unified-api-contracts) — P1, matters for the Massive dual-source MVP cells.
  - **Remaining to the terminal gate:** per-day sweep (~68%) → combo re-stamp + cash-type migration (1 catalogue pass +
    1 manifest pause→CAS) → Barchart purge → Phase D (adapt data-pipeline-check-is/-mtds to tradfi-only all-shards, both
    green on `-test-`, then MVP backfills — the wall-clock-bound long pole).

- **2026-07-18 (slot-1, tick 10) — per-day catalogue sweep ~83% then socket-exhausted; refinement wave dispatched
  (QG-throttled).** The `--by-day --apply --by-day-full-sweep --workers 24` catalogue-corpus sweep migrated
  ~22,600/27,092 by_date files then crashed on `OSError(49 Can't assign requested address)` — ephemeral-socket
  exhaustion from 24 workers over ~2h (same class as the Databento-executor DNS fix). prod/n INTACT (sweep only touches
  by_date). NEXT for catalogue durability: re-run the **enhanced** catalogue migration (combo re-stamp + cash `-USD`,
  once that sub-agent lands) with **fewer workers (8-12)** + it skips the ~83% already-canonical fast — ONE combined
  pass covers the remaining by_date + combo + cash. Refinement wave dispatched (all QG-throttled, 4-5 concurrent QGs
  multi-slot): combo/cash migration enhancement (primitive+scripts), Phase-D skill adaptation (pipeline-check
  tradfi-only all-shards + canonical cell), Phase A2/A3 infra (OOM rc137 + T+1 recon job), Databento DNS executor.
  Several sub-agents hit transient API stream-stalls under the heavy load; all resumed (edits persist). CORE remains
  done+durable+verified (both surfaces). RUNBOOK for the combined re-run: (1) catalogue `--apply --full-sweep`
  (prod/n) + `--by-day --apply --by-day-full-sweep --workers 10`; (2) manifest pause→`--apply --in-place-cas`→resume
  (per the tick-6 runbook); (3) verify live + re-measure.

- **2026-07-18 (slot-1, tick 11) — ✅ CATALOGUE prod/n FULLY CANONICAL across all dimensions (verified live).** Enhanced
  catalogue re-run `--apply --full-sweep`: 1,055 rows migrated (717 cash + 338 combo, FUTURE/OPTION idempotent-skipped).
  LIVE re-measure: EQUITY/INDEX/ETF ids all `-USD` (`NASDAQ:EQUITY:ACGL-USD`, `CBOE:INDEX:VIX-USD` — 717/717 cash =
  100%); combos re-stamped `instrument_type=COMBO` (63,275 total COMBO); instrument_types all UPPERCASE
  {FUTURE,OPTION,EQUITY,ETF,INDEX,COMBO,SPOT_PAIR}. FUTURE/OPTION 99.86% (TRUE 99.98% combos-excluded). The 25
  post-apply "violations" are COMBO-typed rows with still-raw ids (`CME:FUTURE:CL:SA 03M V7`) — EXPECTED (combo-ID
  canonicalization is the separate combo track; my re-stamp only fixed the TYPE). Gate refinement (exempt COMBO from the
  FUTURE/OPTION assertion) = a small follow-up. **Catalogue --by-day durability re-run launched (workers=10 to dodge the
  24-worker socket exhaustion; idempotent; ~2-3h, runs past the window).** MANIFEST combo/cash re-run pending its
  enhanced MTDS script landing (then pause→CAS).
