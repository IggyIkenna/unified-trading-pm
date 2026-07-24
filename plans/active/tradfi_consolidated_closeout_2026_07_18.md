---
doc_type: plan
title: TradFi consolidated close-out — one-pass code→migrations→coverage→smoke-test to MVP-backfill-ready
summary:
  Coordination index (umbrella) that AGGREGATES (references, does not duplicate) every open tradfi + tradfi-touching
  IS/MTDS plan/issue into ONE ordered pass, mirroring cefi_consolidated_closeout_2026_07_18.md. **2026-07-24 line-cap
  remediation** trimmed the doc from 2549 lines to an umbrella-eligible coordination index — the manifest/content
  id-canonicalisation completion work (Phase A1 residual + Phase B/B.5), the download/backfill throughput follow-ups
  (Phase A3/A3.1), and the Phase-D terminal gate were forked verbatim to 3 sibling plans (see `related:` below); this
  parent retains the ground-truth context, MVP universe, Phase A2 (adapter/registry correctness), Phase C
  (data-status/honest-coverage), the aggregated reference index, and a condensed milestone summary of the full
  historical Progress Log (full detail lives on the 3 children now). GROUND-TRUTH CORRECTION (measured live 2026-07-18,
  superseding this plan's own first-draft "largely done" verdict) — the persisted tradfi manifest and catalogue are ~100
  percent NON-canonical for derivatives at the plan's outset; see the 3 children for how much of that has since been
  closed.
status: active
nature: process
umbrella: true
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
    umbrella,
  ]
related:
  [
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
    /plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/tradfi_massive_dual_source_2026_05_28.md,
    /plans/active/tradfi_multisource_backfill_2026_06_22.md,
    /plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md,
    /plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    /plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/archive/2026_07/data_pipeline_e2e_check_2026_07_10.md,
    /plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: 2026-07-18
last_updated: "2026-07-24"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
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
  (slot-3, 2026-07-18). **On 2026-07-24** the doc was trimmed + split 3 ways per the operator-approved plan-hygiene
  line-cap remediation (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md` row 29) — this doc had grown to
  2549 lines (over the 2000L umbrella ceiling) via an ~1700-line tick-by-tick Progress Log; content moved verbatim to
  the 3 children in the related list above, and this parent now carries the umbrella flag as a trimmed coordination
  index.
---

# TradFi consolidated close-out — one pass to MVP-backfill-ready

> **Purpose.** Coordination index (umbrella) that aggregates every open tradfi + tradfi-touching IS/MTDS plan/issue into
> a single ordered pass. This plan **references** the source docs; it does not duplicate them. Close a track by closing
> its source doc(s), then tick it here. Mirrors `cefi_consolidated_closeout_2026_07_18.md`; ordered per the operator's
> directive: **Phase A code → Phase B migrations → Phase C data-status/honest-coverage → Phase D re-smoke-test →
> MVP-backfill-ready.**

## Split notice (2026-07-24 — plan-hygiene line-cap remediation)

> **This plan was trimmed from 2549 lines and forked 3 ways**, per the operator-approved split in
> `/plans/active/issues/plan_line_cap_remediation_2026_07_23.md` (row 29). The 3-way split was overwhelmingly driven by
> an ~1700-line tick-by-tick Progress Log sitting next to a small tail of genuinely open todos — every todo and every
> Progress Log line was moved **verbatim** to its destination, nothing was summarized, rewritten, or dropped. This
> parent now carries `umbrella: true` and stays under the 2000-line umbrella ceiling as a trimmed coordination index.
>
> | Child plan                                                                                                               | Carries                                                                                                                                       |
> | ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
> | [`tradfi_manifest_content_recovery_completion_2026_07_24.md`](tradfi_manifest_content_recovery_completion_2026_07_24.md) | Phase A1 residual + Phase B/B.5 — the catalogue/manifest/GCS-filename/tick-content id-canonicalisation completion work (the biggest of the 3) |
> | [`tradfi_backfill_throughput_followups_2026_07_24.md`](tradfi_backfill_throughput_followups_2026_07_24.md)               | Phase A3/A3.1 — download/backfill throughput follow-ups (DNS-starvation fix, T+1 job, OOM hardening, Databento e2e throughput optimization)   |
> | [`tradfi_phase_d_terminal_gate_2026_07_24.md`](tradfi_phase_d_terminal_gate_2026_07_24.md)                               | Phase D — the post-migration all-shards re-smoke-test terminal gate                                                                           |
>
> **Retained here**: the ground-truth verdict + MVP universe (foundational context for all 3 children), Phase A2
> (adapter/registry correctness), Phase C (data-status + honest-coverage), the aggregated Codex SSOT + source-doc index,
> and a condensed milestone summary replacing the full tick-by-tick Progress Log (see the 3 children for full historical
> detail on their respective workstreams).

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
- **CME BTC/ETH/MBT/MET futures** — FUTURES ONLY, no crypto options (operator 2026-07-21 "no CME option for BTC and
  ETH"; `option_underliers={ES}`).
- **Daily Treasuries** (yields, `ohlcv_24h`) + **daily KRW** (FX daily).
- **2026-07-21 +409 expansion** (`uac@afa2dd64`→`22e6a534`, Progress Log tick "MVP def expanded"): VIX FUTURE (CBOE),
  CBOE treasury-yield INDEX (US3M/US2Y/US5Y/US10Y/US30Y), and FX KRW (`FX:SPOT_PAIR:KRW-USD`) added to the MVP universe
  alongside the CME crypto futures above.

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

## Remaining in this coordinator — Phase A2 (adapter/registry correctness) + Phase C (data-status/honest-coverage)

> Phase A1 (writer convergence) and Phase B/B.5 (the migration itself) forked to
> `tradfi_manifest_content_recovery_completion_2026_07_24.md`; Phase A3/A3.1 (download/backfill throughput) forked to
> `tradfi_backfill_throughput_followups_2026_07_24.md`; Phase D (the terminal gate) forked to
> `tradfi_phase_d_terminal_gate_2026_07_24.md`. The two sections below (A2 + C) are the only phases that stayed on this
> parent, unchanged.

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
- [x] [BACKEND] P1. **KRX (Korean) equities carry a human-readable NAME across catalogue + manifest + data-status
      (operator, 2026-07-20)** — **instruments-service@6780f10e** (the 4th and last code surface; gate green **4712
      passed / 0 failed / 3 skipped**, `.qg_last_passed_sha == 9267e0ea` at ship time). _**CODE 4/4 LANDED 2026-07-20**
      — read-surface chain is complete and shipped: **UAC@f7e0301d** (first-class optional `InstrumentRecord.name` +
      `KRX_EQUITY_NAMES` bare-code→issuer-name SSOT, derived from the EXISTING `KrxEquityDef.name` — no new mapping
      invented, no provider re-fetch needed), **deployment-api@65f5593** (`name` on the Catalogue Explorer JSON route +
      the download-CSV, schema-aware read so a pre-`name` catalogue degrades to blank rather than raising),
      **deployment-ui@2ff1e61** (Name column, em-dash for honest-absent; `pw:L2 ✓`
      `tests/e2e/data-status-catalogue-name-column.spec.ts`). **instruments-service@6780f10e SHIPPED 2026-07-20**
      (`name` in `CATALOG_COLUMNS` + `_add_instrument_name` on-the-fly stamp mirroring
      `_add_mvp_column`/`_add_equity_tags`, + `name=eq.name` on the KRX records). *It was gate-blocked for ~4h on
      failures that were NOT from this work* — first the 5 UAC↔IS DeFi drift guards from UAC@3f79489f
      (METEORA/LIFINITY/PHOENIX + CHAINLINK/PYTH declared without matching IS adapter classes), then, once those
      cleared, a 6th unrelated cross-repo lockstep (`test_expected_matches_golden[sports]`, golden=27 vs actual=47, from
      uac@b6a1d83a adding 20 ODDS_API fan-out bookmakers). **Both were other agents' in-flight work and both
      self-resolved** — DeFi via is@793125ad + is@6506b505 (adapters wired + goldens regenerated), sports via
      is@9267e0ea (goldens regenerated). This deliverable deliberately did NOT touch either: no guard was weakened,
      excluded, or baselined, and no foreign golden was regenerated to force green. Ship gate at is@9267e0ea: **4712
      passed / 0 failed / 3 skipped, exit 0**. Residual DeFi coverage-honesty finding (3 live venues with measured-dead
      upstreams + `expected_coverage` not phase-gated) is documented in
      `plans/active/issues/uac_is_defi_oracle_dex_adapter_drift_2026_07_20.md` and is owned by DeFi T2, NOT this plan.
      **Verified on a SAMPLE (no full regen):** `_add_instrument_name` stamps `KRX:EQUITY:005930`→"Samsung Electronics",
      `KRX:EQUITY:000660`→"SK Hynix", `KRX:EQUITY:005380`→"Hyundai Motor", and also catches the legacy
      `KRX:EQUITY:005930.KS-USD` variant (same `base_asset`); non-KRX rows stay honestly blank. Live tradfi
      `prod/catalog.parquet` today has 10 KRX rows and NO `name` column — it appears on the next roll-up. **STILL
      OPEN:** (a) the availability-manifest `name` column (item 2 below) — deliberately NOT done here, the manifest is
      availability data and its shard-atom/writer is owned by another agent; catalogue-as-SSOT + display-time join is
      preferred; (b) the catalogue regeneration that makes the name land LIVE (main agent). **Audit of other
      opaque-coded venues:** KRX is the only venue needing this — DeFi pool addresses already carry human-readable
      `glued_pair_id` + `base_asset`, prediction conditionIds already carry `question`, sports fixtures already carry
      team names, and CME/CBOE/NASDAQ/NYSE roots are already readable._ KRX equities are identified by the 6-digit
      exchange code (`KRX:EQUITY:000660` = SK Hynix, `005930` = Samsung Electronics, `005380` = Hyundai Motor) — the
      code is the stable/unique official ticker (kept as the canonical `instrument_id`, analogous to
      `NASDAQ:EQUITY:AAPL`), but it is NOT human-readable. Add a first-class reference-data `name` field (romanized
      company name) resolved from a KRX code→name mapping (source: provider security description — Yahoo `.KS` /
      Databento — else a maintained KRX listing reference in instruments-service), and SURFACE it on every read surface:
      (1) deployment-api Catalogue Explorer + download-CSV (`instrument_id` + `name`), (2) the availability manifest
      (`name` column carried by the WRITER, never re-derived downstream), (3) the data-status dimensions view. GCS
      object PATHS keep the stable code id (paths must be stable/unique; names change on rebrand/merger) — the readable
      name rides as metadata/column, not in the path. Audit whether any other venue shares the numeric-code pattern.
      Regenerate catalogue + manifest so the name lands live; verify the Catalogue Explorer shows `SK Hynix` /
      `Samsung Electronics` next to the code. (repos: instruments-service, market-tick-data-service, deployment-api,
      deployment-ui)
- [ ] [VERIFY] P0. 🚧 BLOCKED-PLAN2 — **Certify tradfi Layer-1** — post the v9 migration + rebuild + IS catalogue (Plan
      2), record the fresh tradfi denominator + %. Gate: tradfi number recorded; all 5 AGs now canonical-and-measured.
      **STILL BLOCKED 2026-07-21 (only PARTIALLY unblocked)**: the v9 manifest migration/rebuild are done (task 10,
      2026-07-16), but the served catalogue has not yet been rebuilt/promoted for the +409 MVP expansion
      (`uac@afa2dd64`→`22e6a534`) — so the fresh tradfi denominator this todo must record is not yet final. Gated on the
      pending catalogue rebuild + promote (see `tradfi_consolidated_closeout_2026_07_18.md` "FINAL STEP"), not cleanly
      runnable yet. (FOLDED IN from layer1_remeasure_and_certify_2026_07_06, 2026-07-15, plan-reconcile §6 operator
      ruling)

  **Note (2026-07-24)**: relocated verbatim from `tradfi_v9_stage1_finish_2026_07_06.md`'s "Folded-in scope 2026-07-15"
  section during the plan-hygiene line-cap remediation (that plan is now archived, 0 remaining open todos). The "FINAL
  STEP" this todo's gate cites now lives on the sibling `tradfi_backfill_throughput_followups_2026_07_24.md` (gated on
  backfill completion — rebuild+promote the served catalogue so `mvp=True` reflects the +409 expansion), not on this
  parent directly — see that child for the current status.

## Codex SSOTs (read before touching a phase)

`/codex/02-data/tradfi-databento-sourcing-ssot.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/02-data/honest-coverage-model.md`, `/codex/02-data/pipeline-mode-partition.md`,
`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`,
`/codex/05-infrastructure/manifest-consolidator-ssot.md`, `/codex/05-infrastructure/vm-launcher-runbook.md`.

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
- **TradFi-specific residuals**: `issues/cme_combo_underlying_extraction_garbage_2026_07_19.md` (CME combo-leg
  underlying parse), `issues/instruments_service_fx_adapter_key_unresolved_2026_07_23.md` (FX adapter-key gap),
  `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md` (OHLCV attempted_failed cluster),
  `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` (human-signoff-gated legacy-twin bucket delete, forked from
  `tradfi_v9_stage1_finish_2026_07_06.md` in the 2026-07-24 line-cap remediation),
  `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` (tradfi slice of the instruments-foundation G1-G5 gate
  execution split).
- **Cross-cutting infra / audit (shared across asset groups, tradfi-relevant)**:
  `candle_canonical_path_migration_execution_2026_07_24.md` (MDPS candle canonical-path migration, cross-AG),
  `data_pipeline_check_mdps_features_2026_07_20.md`, `mdps_features_reduced_artifact_tracker_2026_06_28.md`,
  `issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`,
  `issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`,
  `issues/canonical_closeout_open_questions_2026_07_18.md`,
  `issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`, `issues/estate_orphan_assessment_2026_07_21.md`,
  `issues/instruments_docs_audit_outstanding_items_2026_07_08.md`,
  `issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`,
  `issues/mdps_features_deadcode_consolidation_2026_07_20.md`,
  `issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`,
  `issues/phantom_audit_estate_coverage_gap_2026_07_10.md`, `issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`,
  `issues/tarball_rotation_breaks_vm_recovery_2026_07_20.md`,
  `issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md`,
  `issues/vm_backfill_data_correctness_findings_2026_06_29.md`.

## Progress Log — condensed milestone summary (2026-07-24, replaces the pre-split ~1700-line tick-by-tick log)

> **The full tick-by-tick history was NOT deleted** — it was split verbatim across the 3 children by workstream (see the
> Split notice above). This section is a short, condensed orientation only; for exact commands, shas, measured numbers,
> and the full narrative, read the relevant child's own Progress Log.

- **2026-07-18 — Plan authored + ground-truth-corrected.** First-draft "largely done" claim disproved by direct live GCS
  reads: catalogue + manifest derivative ids measured at 0% canonical. Rewritten into the Phase A→B→C→D structure above.
  → full detail: `tradfi_manifest_content_recovery_completion_2026_07_24.md`.
- **2026-07-18 — Phase A1 writer convergence shipped** (UAC shared builder + MTDS/IS writers all emit `-USD@LIN`) →
  **Phase B migration executed**: catalogue migrated to 99.86%→99.98% canonical (prod/n + per-day sweep); manifest
  migrated via pause-consolidator→CAS-rewrite→resume to 94.78%+ FUTURE/OPTION canonical + 99.9% cash, durability
  independently re-verified live. → `tradfi_manifest_content_recovery_completion_2026_07_24.md`.
- **2026-07-18 — A3.1 Databento e2e throughput optimization shipped + measured 1.56x** (gated concurrent-date driver,
  disk-policy fix, concurrency plumbing); a P0 fleet incident (88 launchers with a truncated `gcloud` command from an
  unrelated disk-policy sweep) found and fixed mid-measurement. → `tradfi_backfill_throughput_followups_2026_07_24.md`.
- **2026-07-19 — First Phase-D pass: 36/60 red, dominated by checker bugs, not real MVP-path failures** (billing-gated
  Databento datasets misclassified as failed; `--mvp-only` not suppressing non-MVP augmentation) — both fixed. CME
  `ohlcv_1m` root-caused to a genuine shard-atom design ambiguity (chain-bundle vs per-contract), flagged
  BLOCKED-OPERATOR-DECISION. Re-run: clean MVP verdict, 2/15 hard-fail (both CME, pending the ruling). →
  `tradfi_phase_d_terminal_gate_2026_07_24.md`.
- **2026-07-20 — Operator 6h-away mandate: complete everything autonomously.** Canonical GCS-PATH migration executed on
  20 SPOT VM shards (2.65M objects classified, 0 orphans, 2 defects found+fixed mid-run); CME shard-atom ruled Option A
  (chain bundle — fix the checker, not the writer); Massive purge initially HELD (the `trades`/`tbbo` corpus was the
  only copy, billing-gated), then operator-AUTHORIZED under accepted-permanent-loss (Option C — "our subscription is
  terminated, ohlcv_1m is more than enough"), then EXECUTED (1,701,422 objects purged, 0 collateral, soft-delete safety
  net held throughout). Post-migration audit confirmed complete (a 14-object residue found+fixed); manifest surgical
  cleanup dropped 686,005 stale massive rows + 3,615 disk-verified phantom rows. →
  `tradfi_manifest_content_recovery_completion_2026_07_24.md`.
- **2026-07-21 — MVP scope expanded +409 cells** (VIX futures, CBOE treasury-yield INDEX, FX KRW, CME crypto
  futures-only); backfill fleet launched at scale. Reconciliation run found the earlier "~99.65% canonical" claim was
  OVERSTATED — historical manifest/parquet-content id-form was actually only 30.8% canonical (0% pre-2023) — and an
  ACTIVE LIVE REGRESSION was caught: the currently-running backfill fleet wrote canonical GCS filenames but
  non-canonical manifest rows for the same capture (~850K bad rows/day). Writer bug root-caused + fixed same day. →
  `tradfi_manifest_content_recovery_completion_2026_07_24.md` (writer/manifest fix) +
  `tradfi_backfill_throughput_followups_2026_07_24.md` (backfill-drive fleet launch).
- **2026-07-21/22 — Cash-bucket crash bug fixed properly** (a per-row exception-isolation gap that had silently
  truncated the 2026-07-18 migration run); content-rewrite script shipped; manifest CAS re-stamp executed on VMs
  (6,262,988 rows rewritten in place: 1,751,779 cash rows migrated to `-USD`, combos re-stamped, derivative mislabels
  corrected). All remaining migration work deliberately moved onto VM compute (operator directive, session
  time/credit-constrained). → `tradfi_manifest_content_recovery_completion_2026_07_24.md`.
- **2026-07-22 — Honest-coverage audit run for real**; KRX equities gap found + closed (new Yahoo-daily launcher, no
  prior launcher had ever targeted this venue); chain-manifest recovery script built + shipped (register phase applied
  live: 1,545 rows registered for real captured-but-unregistered data; retire phase — 50,520 candidate rows —
  deliberately left `--apply`-gated pending operator review, NOT auto-applied); CME MBO monolith investigation found
  only 30 objects (not the previously-cited 107 — discrepancy investigated but not fully explained; migration tool
  design deferred as its own follow-up). → `tradfi_manifest_content_recovery_completion_2026_07_24.md`.
- **2026-07-23 — Phase D re-run found + fixed 3 real, independently-verified checker bugs**: (1) MTDS freshness
  pre-flight read the wrong (permanently-stale `-test-` tier) bucket under `--test-run`; (2) the skip-leg vacuously
  failed on an honest-empty force leg instead of recognizing there was nothing to prove a skip against; (3) IS's
  expected-write-prefix builder went stale after an unrelated 2026-07-21 hive-path canonicalisation change. IS check
  improved 0/14 → 11/14 passed (remaining 3 explained: 1 SPOT-preemption noise, 2 genuine honest-absence). Full MTDS
  all-shards run: 21 passed / 21 failed / 18 skipped — failures mostly SPOT preemption noise (measured via
  `gcloud compute operations list`, not assumed) plus 2 known pre-existing gaps and one newly-surfaced chain-bundle
  sampler root-mismatch, filed as its own follow-up issue rather than chased further in-session. →
  `tradfi_phase_d_terminal_gate_2026_07_24.md`.

**State as of the 2026-07-24 fork**: manifest/content migration is substantially complete on the primary surfaces with
one 50,520-row retire-phase batch awaiting explicit operator sign-off before `--apply` (Child 1); backfill throughput is
measured + optimized (1.56x shipped) with further ETA/concurrency-cap tuning identified but not yet applied (Child 2);
the Phase-D terminal gate has found and fixed 3 real cross-cutting checker bugs, but is **not yet fully green** — the
MVP backfill readiness gate stays blocked pending the chain-bundle sampler follow-up or an explicit operator acceptance
of the current evidence as sufficient (Child 3).
