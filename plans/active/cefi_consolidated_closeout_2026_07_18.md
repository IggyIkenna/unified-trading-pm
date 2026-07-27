---
doc_type: plan
title: CeFi consolidated close-out — track + close every remaining cefi workstream once and for all
summary:
  Single coordination plan that references (does NOT duplicate) every still-open cefi plan/issue so they can be closed
  off together. Authored 2026-07-18 from a 3-agent audit of ~30 active cefi/IS/MTDS docs + direct verification;
  restructured 2026-07-25 into a lean coordination index over 4 new forked children (migration-cutover critical path,
  coverage-backfill checkpoints, candle-namespace residual, misc-audits) plus the pre-existing execution-log,
  aggregated-sources, satellite-batch, and native-extraction docs. VERDICT — for the INSTRUMENT-ID CANONICALIZATION axis
  (GCS filename / parquet column / manifest key / reader), the migration is Phase-C dry-run-clean, awaiting only the
  operator-approved cutover (now the sequential critical path in
  cefi_migration_cutover_and_track8_completion_2026_07_25.md). CeFi is NOT "done" overall — a REOPENED coverage question
  (the archived "honest-done 50.79%" rested on a code-bug-induced throughput collapse mistaken for a 1.8-year physical
  ceiling, now fillable in ~1-2 days) and an operator-ruled "done first" side-quest
  (cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md's Phases 1/1b/1c/2/5) both remain open.
status: active
nature: process
asset_group: [cefi]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [cefi, close-out, consolidation, canonicalisation, manifest, coverage, backfill, denominator, adapter-retrofit]
related:
  [
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /plans/active/issues/_cefi_canonical_blueprint_2026_07_17.md,
    /plans/archive/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md,
    /plans/active/data_completion_cefi_2026_07_15.md,
    /plans/active/issues/instruments_service_plan_reconciliation_2026_06_29.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    /plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md,
    /plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md,
    /plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /plans/active/cefi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/cefi_consolidated_native_ao_extract_2026_07_25_finalize.md,
  ]
created: 2026-07-18
last_updated: "2026-07-25" # 2026-07-25: 4-child split (migration-cutover, coverage-backfill, candle-namespace, misc-hygiene) + Track 0 cryptovenue-phases embed (cefi.1) + 11 AO-readiness fixes; was 2026-07-24
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 8.0
estimate_calibrated_ai_days: 6.4
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
  [
    cefi_4surface_migration_execution_log_2026_07_24,
    cefi_migration_cutover_and_track8_completion_2026_07_25,
    cefi_track2_coverage_backfill_checkpoints_2026_07_25,
    cefi_track7_candle_namespace_residual_2026_07_25,
    cefi_misc_audits_and_hygiene_2026_07_25,
  ]
source:
  3-agent cefi plan/issue audit + direct verification (slot-3, 2026-07-18) at operator request ("consolidate all
  remaining cefi issues/plans into one plan referencing the others so we can close them off once and for all");
  restructured 2026-07-25 into a 4-child split (read-only design pass + operator-resolved ambiguities cefi.1-4).
---

# CeFi consolidated close-out

> **Purpose.** One place to see + close ALL remaining cefi work. This plan **references** the source docs; it does not
> duplicate their content. Close a track by closing its source doc(s), then tick it here. Authored from a 3-agent audit
> (2026-07-18) of every active cefi/IS/MTDS plan+issue; restructured 2026-07-25 into a lean coordination index — see
> "Reachability map" below for where each piece of real work now lives.

## Headline verdict — "is the migration final?"

- **Instrument-ID canonicalization (4 surfaces: GCS filename / parquet `instrument_id` column / manifest key / reader):
  YES, this is the FINAL migration for that axis.** The 4-script program is Phase-C dry-run-clean; the operator-gated
  drain+apply is now the sequential critical path in `cefi_migration_cutover_and_track8_completion_2026_07_25.md`.
  Everything id-format-related is subsumed, absorbed, or already done — see that child plan for the full
  predecessor-subsumption record.
- **CeFi OVERALL: NOT done.** Several separate open tracks remain — none blocks the id-migration; several are real
  data-correctness work; Track 2 (coverage) is a decision that reframes "cefi done."

## Reachability map — how a reader gets to every piece of real work from here

1. **Migration-completion critical path** → `cefi_migration_cutover_and_track8_completion_2026_07_25.md`
   (`sequential: true`, 5 todos: DERIBIT quote fix → on-disk `:PERP:` rename → cutover `--apply` → post-cutover flip →
   terminal enumeration checkpoint) → its gated finalize.
2. **Coverage-backfill path** → `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` (gated on path 1 finishing) →
   its gated finalize.
3. **Candle-namespace path** → `cefi_track7_candle_namespace_residual_2026_07_25.md` (gated on
   `cefi_consolidated_native_ao_extract_2026_07_25.md`'s verify+backfill todo finishing) → its gated finalize.
4. **Misc-audit path** → `cefi_misc_audits_and_hygiene_2026_07_25.md` (ungated, 3 independent todos) → its gated
   finalize.
5. **Native-todo AO extraction** (a PARALLEL, independently-drafted triage of this parent's OWN 32 native todos,
   distinct from paths 1-4 above — 12 AO-eligible candidates) → `cefi_consolidated_native_ao_extract_2026_07_25.md` →
   its gated finalize.
6. **Satellite-doc AO batch** (every OTHER cefi plan/issue's AO-eligible work, 33 todos) →
   `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` → its gated finalize.
7. **Full execution history** (day-by-day Progress Log, DELTA checkpoints) →
   `cefi_4surface_migration_execution_log_2026_07_24.md` (LOCAL, historical record — see Progress Log below).
8. **Discoverability index** (every other cefi-relevant plan/issue's open-todo digest) →
   `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`.

## Track 0 — CeFi equity perps/tokenized stocks: finish Phases 1/1b/1c/2/5 (operator ruling 2026-07-25, "done first") · P0/P1

> **Source**: `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` — the operator ruled (2026-07-25) that this
> doc's Phase 1 (incl. 1b, 1c), Phase 2, and Phase 5 should finish and be embedded HERE as high-priority work, sequenced
> ahead of/alongside the migration-critical-path work (path 1 in the Reachability map above), NOT buried in
> misc-hygiene. Phase 1 itself is 100% done (its 1 todo already checked in the source doc). The 11 todos below are
> everything still unchecked in Phases 1b/1c/2/5 as of 2026-07-25 — read the source doc for full context (per-venue
> live-listing counts, probed Yahoo/Databento limits) before touching any of these.

- [ ] [SCRIPT] P0. **Propagation ops (B1/B3/B4) — run the IS→catalogue→enumerator→MTDS wave chain to completion** for
      the new Binance tradfi-perp cash-twin equities (IS instruments backfill → `build_instrument_catalogue` rollup →
      `enumerate_expected_universe.py` v2 tradfi → MTDS wave). Repos: deployment-service, instruments-service. **Done
      when**: the catalogue shows the new MVP tickers; the manifest shows them `expected_unattempted`; a sample equity
      captures non-NaN OHLCV. Source: Phase 1b.
- [ ] [DATA] P2. **BLOCKED-DATA — source a Korea-equity vendor** for HYUNDAI/SAMSUNG/SK-Hynix cash-twin coverage (no
      US-listed twin on Databento DBEQ.BASIC; neither current vendor covers KRX). Repo: instruments-service (vendor ask
      → operator). Source: Phase 1b.
- [ ] [SCRIPT] P1. **Capture Binance/OKX/Bybit `indexPrice`/`markPrice`/`fundingRate`** for the equity-perps as a
      first-class data_type (rides the existing premiumIndex/funding endpoints). Repo: market-tick-data-service. Source:
      Phase 1b.
- [ ] [SCRIPT] P2. **Wire a recurring daily funding/basis scan** across all crypto-venue equity-perps (annualized
      funding + perp-vs-index basis + market-hours-vs-off-hours flag) → opportunity-sizing report. Repo: e2e-testing.
      Source: Phase 1b.
- [ ] [DESIGN] P2. **strategy-service — decide the single-stock basis execution-venue/hedge approach** (IBKR / tokenized
      / cross-crypto-venue dispersion; off-hours = no-cash-hedge). Repo: strategy-service. Source: Phase 1b.
- [ ] [UAC] P0. **Map the index perps** (`SPXUSDT`/`NAS100`/`SPYUSDT`/`XAUUSDT`) to the CME index-future + Databento
      index canonical, carrying the scale/multiplier (Binance SPX-perp is a SCALED micro unit — sizing MUST use the
      multiplier for the ES hedge ratio). Repo: unified-api-contracts. Source: Phase 1c.
- [ ] [DESIGN] P1. **strategy-service — design the INDEX-perp cash-and-carry archetype** (short Binance SPX/NAS perp +
      long CME ES/NQ real hedge, scale-adjusted) — the FIRST fully-executable equity-perp basis archetype (deep real
      hedge, both legs already in universe+data, CME Globex ~23h/day). Repo: strategy-service. Source: Phase 1c.
- [ ] [SCRIPT] P1. **Launch the CeFi Tardis backfill for the equity-perp window** (sub-item 4 of Phase 2, explicitly out
      of scope until now — the un-filter + type-stamping code landed 2026-07-18, this is the actual backfill). Verify
      manifest `capture_status` for an EQUITY_PERP-tagged shard. Repos: instruments-service, deployment-service. Source:
      Phase 2.
- [ ] [SCRIPT] P1. **Backfill the 3 KRX stocks via guardrailed Yahoo** (1d since 2019-01-01 + 1h 730d + 15m 89d
      (range=60d) + 1m 28d-chunked). Repos: deployment-service, market-tick-data-service. Source: Phase 5.
- [ ] [UAC] P1. **Measure the exact Databento L-floor boundary per level** (L0/L1/L2/L3) live + update
      `LEVEL_MAX_LOOKBACK_DAYS`/`earliest_allowed_start`/`assert_lookback_allowed` to the measured values. Repo:
      unified-api-contracts. Source: Phase 5.
- [ ] [REFACTOR] P2. **Deprecate + remove all Barchart code** (its only role, the VIX cash-index preload, was already
      replaced by VX-futures-via-databento) — delete the adapter/client/source-entries, no shim. Repos:
      unified-api-contracts, market-tick-data-service, unified-trading-pm. Source: Phase 5.

**Close-out criterion**: all 11 todos above closed or explicitly re-deferred by the operator; the source doc's own
Phases 1/1b/1c/2/5 sections show 0 remaining open todos.

## Track 1 — Instrument-ID canonicalization (THE final id migration) · FORKED

> **Forked 2026-07-25** to `cefi_migration_cutover_and_track8_completion_2026_07_25.md` (sequential 5-todo critical path
> — path 1 in the Reachability map above). This section stays as a compact pointer + the historical subsumption record.

- **Vehicle**: `plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (+ blueprint
  `_cefi_canonical_blueprint_2026_07_17.md`). Phase A (code on `main`) ✅ · Phase B (deploy) ✅ · Phase C (4 scripts
  dry-run-clean) ✅ · **Phase D/E (drain + `--apply`) tracked in the forked child plan.**
- **Close-out criterion**: the operator's `ADAF0:USTF0.parquet` is canonical on all four surfaces, verified live; each
  script's `--dry-run` re-run asserts 0 further changes (idempotency).
- **Subsumes / closes on cutover**: `cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md`
  (relabel + purge `--apply`), `instrument_id_format_canonicalization_2026_07_08.md` (id-format traces),
  `instruments_remaining_work_audit_2026_07_10.md` (BYBIT-SPOT anomaly).
- **Residual adapter-retrofit carve-out → Track 5** (the 4 scripts are one-time DATA migrations; they do NOT retrofit
  the adapters, so re-drift prevention is separate).

## Track 1b — 🟢 RESOLVED 2026-07-25: CeFi raw-tick capture outage (was HALTED 2026-07-21..24, OOM crash-loop)

- [x] ✅ [INFRA] P0. **The batch-download Cloud Run Job was crash-looping on SIGKILL/OOM within 10-40s of every
      execution since ≥2026-07-23** — 3 days of zero manifest writes. Fixed by bumping memory 8Gi→16Gi + a verification
      run (full 10m2s success, measured `peak_rss=8646.5MB`). Capture flowing again as of 2026-07-25T01:44Z. Root-cause
      attribution + a permanent bound remain open follow-ups (not blockers) — full detail:
      `/plans/active/issues/cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md`.

## Track 2 — CeFi backfill COVERAGE reopened · FORKED to its own gated plan · P0

> **Forked 2026-07-25** to `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` (gated on Track 1's cutover
> finishing — path 2 in the Reachability map above). This section stays as the decision record + pointer.

- **Source**: `issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md` (root-cause `status: resolved`) +
  `plans/archive/2026_07/cefi_completion_program_2026_07_15.md` (archived "honest-done, 50.79% accepted").
- **The finding (verified 2026-07-18)**: the archival's basis — "the 2.89M-cell gap is not closable at the N=1 Tardis
  ceiling ≈ 1.8 years" — is FALSE. It was a **~350x code-bug throughput collapse** (`run_in_executor(None,…)`
  default-pool + a date-serial barrier), not a physical ceiling; the gap is **~1-2 days of work at June rates**. **THE
  THROUGHPUT BUG IS NOW FIXED + MEASURED LIVE** (~14 MB/s on the VM). The doc also flags that "operator accepted 50.79%"
  may have been INFERRED from the erroneous ceiling verdict, not actually given.
- [x] ✅ [REVIEW] P0. **RULING (autonomous, within documented intent — /autonomous, 2026-07-18)**: **RE-OPEN the CeFi
      Completion Program + REVERSE the 50.79% acceptance.** Basis (all operator-stated): the archival's premise is a
      verified-false ~350x code-bug, now fixed + measured live; the "accept 50.79%" was inferred, not actually given.
      Coverage % is the climbing metric. The operator can reverse this ruling; surfaced in the session report.
- **Close-out criterion**: operator ruling recorded (done, above); coverage re-measured post-resume-backfill (tracked in
  the forked child plan).

### Checkpoint cadence

Per `task_template.md` §3 finding K, this plan needs 3 distinct DATED run checkpoints per skill. The 2 PRE-BACKFILL
baselines are drafted, ungated, as candidates 3/4 of `cefi_consolidated_native_ao_extract_2026_07_25.md`; the MID/POST
checkpoints (timing-coupled to the backfill) are in the forked
`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`.

## Track 3 — Manifest completeness axis (SEPARATE from id-format) · P1

- **Source**: `data_completion_cefi_2026_07_15.md` — a DIFFERENT canonicalization axis: manifest `pipeline_mode`
  partition + legacy-bucket orphan-sweep + cefi `_index` v8→v9 schema. ~15 open items (E4 orphan sweep, E7/E8
  verify+delete, candle-coverage gaps, denominator seed, v8→v9 CF-audit). NOT subsumed by Track 1.
- **Close-out criterion**: its own todos closed; do NOT fold into Track 1 (parallel track).

## Track 4 — Denominator / catalogue-completeness correctness · P1

- **Sources**: `instruments_service_plan_reconciliation_2026_06_29.md` (C1/C2 ASTER denominator over-seed + connector,
  C5 Deribit-options false-"complete"); `instruments_completion_tracker_2026_07_06.md` (D2);
  `instruments_foundation_completeness_2026_06_24.md` (G4/G5 not fully closed);
  `issues/cefi_layer1_denominator_gaps_2026_07_03.md` (being archived via `cefi_misc_audits_and_hygiene_2026_07_25.md`).
  Denominator-honesty, separate from id format.
- **Also here (P0 data-correctness bugs found in the audit, filed in their own docs):**
  - `issues/deribit_options_chain_af_g4_blocker_2026_07_03.md` — **⚠️ its "structurally-absent channel" premise is
    DEBUNKED**: the futures_chain 122,585 `attempted_failed` are NOT source-absence — the failure + aggregation are ON
    OUR SIDE (per-symbol capture gap → bundle never built). Not a writer-gate fix; it FILLS on the Track-2 coverage
    backfill. Do not propagate the debunked premise; do not treat this as an open Track-4 fix.
  - `issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md` — gate Tardis requests on the
    vendor catalog; stop recording impossible combos as `attempted_failed` (denominator-corruption, P0).
- **Close-out criterion**: the impossible-combo bug fixed; denominator gaps resolved or accepted.

## Track 5 — Adapter canonical-ID-builder retrofit (RE-DRIFT prevention, post-migration) · P2

- **Sources**: `issues/instruments_docs_audit_outstanding_items_2026_07_08.md` (B1 — only ~4/63 adapters route through
  the shared canonical-id builder); `canonical_id_builder_retrofit_checklist_2026_07_08.md` (FI_/FF_ Kraken-Futures
  13-instrument collision, unresolved).
- **Why separate**: Track 1's scripts are one-time DATA migrations; they do NOT change the ~59/63 adapters that stamp
  ids ad hoc, so new writes can re-drift unless retrofitted. This is the durability half of "canonical everywhere."
- **Close-out criterion**: adapters route through the shared builder (or a QG gate enforces canonical-id shape on
  write). **Dispatched**: the `*_ccxt.py`/`*_native.py` BINANCE/BYBIT/OKX dead-code audit is candidate 1 of
  `cefi_consolidated_native_ao_extract_2026_07_25.md`.

## Track 6 — Independent cefi data-correctness / hygiene items · P2

Real but non-blocking, each in its own doc; listed for completeness so nothing is orphaned:

- `issues/aster_mtds_failure_count_regression_2026_07_07.md` — ASTER `attempted_failed` 3,491→17,675, untouched 11 days
  (NOTIFY-OPERATOR class, unresolved).
- `issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md` — 273 rows `venue=DERIBIT/type=COMBO` mislabel (should
  be `DERIBIT-COMBO`); post-migration check.
- `issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md` — MTDS `_L5_VENUES` hardcoded, missing 11 cefi
  venues → read from `VENUE_DATA_TYPE_CAPABILITIES`.
- `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` — `DATA_TYPE_CAPABILITY_REGISTRY` missing entries; consolidator
  incremental no-op root cause never fixed (worked around); Tardis HTTP-400 from IS-catalog missing `available_to`.
- `issues/mtds_ungated_test_families_2026_07_17.md` — reader-surface test
  (`test_canonical_parquet_reader_integration.py`) sits in the ungated `tests/integration/**` (`RUN_INTEGRATION=false`),
  so the D3 reader-bridge half of Track 1 has **no CI enforcement** yet.
- `issues/cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md` — blank-itype `attempted_failed` re-tag,
  gated on `cefi-recapture-sweep-complete` (still false).
- `issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md` — `lighter` Tardis entitlement
  (BLOCKED-CREDENTIALS, scaffold correct).
- `issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md` — ✅ DONE (`deployment-service@9b13679`, launcher entries
  removed).
- `issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md` — spot-check GCS/manifest/UI
  consistency (dispatched as a bounded slice via `cefi_misc_audits_and_hygiene_2026_07_25.md`) + decide the
  reconciliation cadence (stays human).
- `issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md` —
  `deribit_volatility_index_handler.py` and `book_microstructure_handler.py` stamp `available_at` from BATCH-run
  wall-clock instead of a deterministic per-row/`as_of` timestamp. Audit-only finding, code fix not yet started.

**Dispatched**: the non-Tardis cefi VM cross-machine-sharding sweep is candidate 2 of
`cefi_consolidated_native_ao_extract_2026_07_25.md`.

## Operator dispositions (2026-07-18) — pre-migration execution

> The operator reviewed the audit and directed a pre-migration close-out. Each maps to a source doc; archive the source
> when its item lands.

- **DERIBIT missing-quote fix + `prod/catalog.parquet` rebuild** → forked to
  `cefi_migration_cutover_and_track8_completion_2026_07_25.md` (todo 1) — see the Reachability map above.
- [x] ✅ [BACKEND] P0. **Remove the UAC-seed catalogue fallback — catalogues FAIL LOUD** — DONE
      `market-tick-data-service@3253cae3`. New `InstrumentCatalogUnavailableError(RuntimeError)`; cefi/defi/tradfi
      `list_instruments` + sentinel paths now RAISE on absent/empty/schema-drift; off-season empty sports stays honest.
- [x] ✅ [BACKEND] P0. **Gate Tardis cefi on the vendor response + stop false `attempted_failed`** — DONE
      `market-tick-data-service@a7569298`. Tardis HTTP-400 `code=300`/`code=140` now classified structural-absence. **⚠️
      CORRECTION (operator 2026-07-18): the futures_chain 122,585 are NOT source-absence** — see Track 4 above; they
      FILL on the Track-2 coverage backfill, not a reclass.
- **AUDIT the UAC per-venue seed fallback's blast radius** → dispatched as candidate 9 of
  `cefi_consolidated_native_ao_extract_2026_07_25.md`.
- **[OPERATOR] Decide whether to remove the UAC per-venue seed fallback** → forked to
  `cefi_misc_audits_and_hygiene_2026_07_25.md` (non-dispatchable, feeds off the audit above).
- [x] ✅ [DOCS] P1. **Upgrade the `data-pipeline-check-mtds` skill** — DONE `unified-trading-pm@ca3aebfc7` (DERIBIT
      futures_chain negative check, DERIBIT/BINANCE-FUTURES content spot-checks).
- [x] ✅ [INFRA] P1. **`issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md`** — DONE (`deployment-service@9b13679`
      removed the DRIFT/PACIFICA launcher entries; `instruments-service@ee19f6f3` hardens against re-mint).
- [x] ✅ [BACKEND] P2. **`_L5_VENUES` RESOLVED-BY-DELETION** (2026-07-18) — the hardcoded tuple no longer exists
      (`market-tick-data-service@a4fb3d13` retired `order_flow_imbalance` entirely). The 2 onchain sub-audits stay open
      in the issue doc (DeFi, not cefi — outside this close-out).
- **Track 0 above**: `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Phases 1/1b/1c/2/5 (operator ruling
  2026-07-25 — see Track 0, embedded natively in this doc, sequenced ahead of/alongside the migration).
- **Reconciliation-gap spot-check** → dispatched (bounded slice) as part of
  `cefi_misc_audits_and_hygiene_2026_07_25.md`.
- **Consolidate + archive** `issues/cefi_layer1_denominator_gaps_2026_07_03.md` (+
  `issues/betfair_instrument_id_delimiter_cross_repo_2026_07_08.md`, already archived) → dispatched (re-scoped to the 2
  named docs) as part of `cefi_misc_audits_and_hygiene_2026_07_25.md`.
- [x] ✅ [REVIEW] P0. **Track-2 coverage decision — RULED** (same decision as the Track-2 ruling above; not a second
      decision). Re-open the completion program + reverse the inferred 50.79% acceptance. Autonomous ruling within
      documented intent (/autonomous 2026-07-18); operator can reverse.

## Track 8 — Non-canonical ENUMERATION audit → align EVERY form to one SSOT (operator ask, 2026-07-18) · P0

> **Numbered 8, not 6 or 7 (pre-existing, unchanged by this pass)** — this section was renumbered off a duplicate "Track
> 6" heading collision with the hygiene-items section above; Track 7 (candle-namespace, below) already existed at the
> time, so this became Track 8 rather than re-colliding. Reading order (Track 8 before Track 7) does not match numeric
> order — a pre-existing quirk, not introduced by the 2026-07-25 split.

- **Source / ask**: the deployment-ui/api "data status" view used to enumerate every instrument_type / data_type / chain
  / venue in the GCS data/manifest for an asset_group — a duplication + non-canonical-naming detector. Removed from the
  UI/API; operator (2026-07-18): re-add it, and use the enumeration so the migration is COMPLETE (align EVERY
  non-canonical form to one SSOT), not just the classes Scripts 1-4 target.
- **Audit tool**: `market-tick-data-service@81b72f1d`
  (`scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`). Measured live 2026-07-18 on the
  **11,185,557-row** cefi manifest: **instrument_id 1,864,357 non-canonical (16.67%)**; **instrument_type COLUMN drift**
  (BLANK 3,186,640, lowercase `perpetual` 289,700, etc.); minor venue/data_type drift. Full breakdown moved to
  `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`'s live-manifest-worklist table.
- **Coverage gap (why the `--apply` must WAIT)**: Scripts 1-4 resolve ~380k bare-wire; ~1.48M non-canonical rows
  (blank-itype-driven bare-wire, `:PERP:`, missing-quote, COMBO) need DEDICATED paths — Track 8 gates the cutover
  `--apply` (now `cefi_migration_cutover_and_track8_completion_2026_07_25.md`).

- [x] ✅ [REVIEW] P0. **Operator canonical rulings — RECEIVED 2026-07-18.** The rebuilt catalogue is the SSOT: (1)
      blank/missing instrument_type → catalogue-resolve + venue-suffix-infer; (2) orphans not in catalogue → DROP unless
      cleanly mappable; (3) KALSHI-PERP/POLYMARKET-PERP → DROP (100% `empty_confirmed`, no real data); (4) DERIBIT:COMBO
      is CANONICAL (gets migrated, not excluded).
- [x] ✅ [SCRIPT] P0. **instrument_type column normalization** — DONE `instruments-service@555ddf1c` (dry-run measured:
      3,824,258 itype rows changed; canonical-fraction 84.98%→99.41%). **`--apply` DRAIN-GATED under the Track-1
      cutover.** Casing freeze lifted 2026-07-20 (ruling D1, UPPERCASE ratified) — ruling recorded in
      `plans/active/data_pipeline_reconciliation_skill_2026_07_20.md` § D1.
- **`:PERP:` → `:PERPETUAL:` rewrite** — manifest side SHIPPED (`instruments-service@555ddf1c`, 374,227/374,272 rows).
  **On-disk GCS rename** → forked to `cefi_migration_cutover_and_track8_completion_2026_07_25.md` (todo 2).
  **Writer-side fix** (future captures) → dispatched as candidate 8 of
  `cefi_consolidated_native_ao_extract_2026_07_25.md`.
- [x] ✅ [SCRIPT] P1. **bare-wire / missing-quote / DATED-contract recovery** — DONE `instruments-service@555ddf1c`
      (operator Option A + resolver-gap fix). +115,225 captured dated rows / ~40.7B ticks recovered via the dated-wire
      itype-fix; +3,531 rows / 186M ticks via the `-SPOT`/`-SWAP` override. Result: adjusted canonical-fraction 99.41%.
      Residual 53,965 captured rows / 7.46B ticks, all genuinely-unresolvable (captured-with-data dropped = 0).
- **POST-CUTOVER: flip the smoke-check + downloader to canonical ids** → forked to
  `cefi_migration_cutover_and_track8_completion_2026_07_25.md` (todo 4). Full evidence:
  `issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md`.
- **Re-add the "data status" enumeration to deployment-ui/api** — code COMPLETE + `quality-gates.sh`-green
  (deployment-ui shipped `deployment-ui@3fb6779`; deployment-api blocked only on 3 dirty sibling-repo deps as of
  2026-07-18, now **7 days stale — re-check before trusting**). Investigation found no single removal commit; shipped as
  a NEW read-only endpoint (`GET /api/data-status/axis-value-census`) rather than touching the legitimate math fix that
  eroded the raw-value signal. **Dispatched**: landing the quickmerge (with a fresh dirty-deps re-check first) is
  candidate 5 of `cefi_consolidated_native_ao_extract_2026_07_25.md`.
- **Enumeration-audit terminal checkpoint** → forked to `cefi_migration_cutover_and_track8_completion_2026_07_25.md`
  (todo 5).

## CEFI CANONICAL SPEC (operator-authoritative, 2026-07-18 — the migration target)

> ⚠️ **Possible overlap with the "Pass-through" section, flagged not resolved** — see
> `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`'s own flag on that moved section.

**Shard atom** (identical across writer/manifest/status/gate/UI):
`pipeline_mode({mode}_{source}) · date · asset_group · venue · [chain] · instrument_type · data_type · (instrument_id OR underlying) · [quote · margin] · source`.
Flat-per-contract shards key on `instrument_id` (filename == column == manifest key). **BUNDLE shards
(`options_chain`/`futures_chain`) key on `underlying`; per-row `instrument_id` MAY BE NULL by design.**

**Representative canonical ids (cefi)**: `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` · `BINANCE-SPOT:SPOT_PAIR:BTC-USDT`
(no margin on spot) · `BYBIT:FUTURE:BTC-USD@INV-20231201` (per-contract, not a bundle) ·
`DERIBIT:OPTION:BTC-USD@INV-20260401-3250-C` (options_chain bundle, **quote ALWAYS**) ·
`DERIBIT:FUTURE:AVAX-USDC@LIN-20260401` (futures_chain bundle; USDC=linear) · `OKX-SWAP:PERPETUAL:BTC-USD@INV` (folds to
OKX in Layer-1) · `HYPERLIQUID:PERPETUAL:BTC-USDC@LIN` (USDC-margined) · `ASTER:PERPETUAL:BTC-USDT@LIN` (USDT
corrected). Margin: quote∈{USDT,USDC,…}→`@LIN`, quote==USD→`@INV`; SPOT no marker.

**Drop venues (cefi purge, remove entirely, snapshot-first)**: BITSTAMP/HUOBI/GEMINI/PHEMEX (defunct); Solana-perp cull
DRIFT/PACIFICA/MANGO/ZETA/FLASH/SOLAYER/PICASSO/CAMBRIAN. **KEPT registered (NOT purged)**: **BINANCE-DELIVERY** (live
COIN-M product — descope from MVP backfill, keep the UAC scaffold + its real captured data; operator ruling 2026-07-18,
overriding the earlier "purge" framing — do NOT delete its data), KALSHI-PERP + POLYMARKET-PERP (roadmap — do NOT drop
despite being empty), LIGHTER-ZKSYNC (blocked-scaffold), EXTENDED-STARKNET (MVP). SSOT:
`/codex/02-data/cross-asset-canonical-target-ssot.md` §10. (Bundle keys on `underlying`, NOT a synthesized `VENUE:BASE`
id.)

## MVP universe (SSOT: `/codex/02-data/mvp-scope-canonical.md`)

> Consolidates the per-venue MVP status scattered across the Operator dispositions section and the CEFI CANONICAL SPEC
> above into one place, cross-checked against the codex SSOT's CeFi MVP table (config v16). States which cells are
> **PROVEN WIRED** (real captured data flowing, evidenced elsewhere in this plan) vs. just **DECLARED IN-SCOPE**
> (registered/planned but not yet flowing data).

**Codex MVP venue list (config v16)**: BINANCE-SPOT/-FUTURES · BYBIT(/-SPOT) · OKX-SPOT/-SWAP/-FUTURES · DERIBIT ·
HYPERLIQUID · ASTER · KRAKEN-SPOT/-FUTURES · COINBASE-SPOT/-FUTURES · BITFINEX-SPOT/-FUTURES · BITGET-SPOT/-FUTURES ·
UPBIT · LIGHTER-ZKSYNC · EXTENDED-STARKNET.

| Venue(s)                                                                                                                                                                               | Codex MVP status                                                                                                                                | Wired status (this plan's evidence)                                                                                                                                                                                                                                     |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BINANCE-SPOT/-FUTURES, BYBIT(/-SPOT), OKX-SPOT/-SWAP/-FUTURES, DERIBIT, HYPERLIQUID, ASTER, KRAKEN-SPOT/-FUTURES, COINBASE-SPOT/-FUTURES, BITFINEX-SPOT/-FUTURES, BITGET-SPOT/-FUTURES | MVP                                                                                                                                             | **PROVEN WIRED** — real captured rows throughout the 11.19M-row cefi manifest; KRAKEN-SPOT independently re-verified fully clean 2026-07-23                                                                                                                             |
| EXTENDED-STARKNET                                                                                                                                                                      | MVP                                                                                                                                             | **PROVEN WIRED** — "live MVP" per the CEFI CANONICAL SPEC + Operator dispositions sections                                                                                                                                                                              |
| LIGHTER-ZKSYNC                                                                                                                                                                         | MVP                                                                                                                                             | **PARTIAL** — scaffold + real captured data exist (~11,283 raw objects, mostly bare numeric market-index stems); resolver code shipped (`mtds@8835b899`); live capture is BLOCKED-CREDENTIALS and the canonical-rename backfill of the existing objects has not run yet |
| UPBIT                                                                                                                                                                                  | MVP                                                                                                                                             | **NOT EVIDENCED anywhere in this plan's audit trail** — dispatched as candidate 6 of `cefi_consolidated_native_ao_extract_2026_07_25.md`                                                                                                                                |
| BINANCE-DELIVERY                                                                                                                                                                       | **NOT MVP** (COIN-M inverse/delivery, decision #3)                                                                                              | Registered/kept in UAC (not purged) with real historical captured data, but explicitly descoped from MVP backfill going forward — do not re-add to MVP scope                                                                                                            |
| KALSHI-PERP, POLYMARKET-PERP                                                                                                                                                           | **NOT in the codex CeFi MVP table today** — this plan's "roadmap, will be added" framing is a future-scope declaration, not a current MVP grant | **NOT WIRED** — verified 2026-07-18: 100% `empty_confirmed`, `row_count=0`, `instrument_count=0`; kept registered purely for the roadmap                                                                                                                                |
| BITSTAMP-SPOT, HUOBI-SPOT/-FUTURES, GEMINI-SPOT, PHEMEX-SPOT (defunct); Solana-perp cull (DRIFT/PACIFICA/MANGO/ZETA/FLASH/SOLAYER/PICASSO/CAMBRIAN)                                    | **NOT MVP**                                                                                                                                     | Being PURGED entirely (snapshot-first) per the Operator dispositions venue-purge ruling — never re-add                                                                                                                                                                  |

## Track 7 — Candle namespace bundle-collision residual (`processed_candles/`) · FORKED · P2

> **Forked 2026-07-25.** The verify (6 remaining affected days) + targeted MDPS `--force` backfill are dispatched,
> combined into one ordering-safe todo, as candidate 7 of `cefi_consolidated_native_ao_extract_2026_07_25.md`. The
> terminal `[OPERATOR]`-gated delete of the 149 stale objects is `cefi_track7_candle_namespace_residual_2026_07_25.md`
> (machine-gated on the native-extract plan finishing, so the delete cannot race ahead of verify/backfill).

- **Source**: `issues/candle_feature_canonical_path_divergence_2026_07_20.md` todo 19 (folded 2026-07-23). CEFI's live
  `processed_candles/` corpus is 99.98%+ clean (405,259/405,408 objects `CANONICAL_NOOP`); the residual is exactly 149
  objects (93 BYBIT `futures_chain` + 56 DERIBIT `options_chain`), listed in
  `plans/audit/results/cefi_todo19_149_residual_objects_2026_07_23.csv` — real, distinct per-contract-leg candle files
  that lost a bundle-target-collision race, NOT redundant duplicates (deleting first = permanent data loss).
- **Close-out criterion**: the 8 affected `(day, venue)` cells re-derived via MDPS backfill, the regenerated bundle
  verified complete, the 149 stale objects then safely deleted, and todo 19 updated to reference this track's
  resolution.

## Codex SSOTs (read before touching a track)

`/codex/02-data/availability-manifest-and-data-status.md`, `…/pipeline-mode-partition.md`,
`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`, `/codex/05-infrastructure/vm-launcher-runbook.md`
(Tardis cap + the throughput-fix ruling), `/codex/06-coding-standards/read-time-filter-pushdown.md`.

## Aggregated source docs

> Full discoverability index of every other cefi-relevant plan/issue (with open-todo digest) lives in
> [`cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`](/plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md)
> — including, as of 2026-07-25, the "Pass-through from the 2026-07-18 consolidated canonicalisation audit" section
> (operator decisions + live manifest worklist table) moved there verbatim from this doc.

## Progress Log

> **Full day-by-day Progress Log + DELTA checkpoints** live in
> [`cefi_4surface_migration_execution_log_2026_07_24.md`](/plans/active/cefi_4surface_migration_execution_log_2026_07_24.md)
> — read that file for the complete narrative (PRE-COMPACT checkpoints, DELTA session updates, deferred-work tables)
> from plan-authoring (2026-07-18) through the 2026-07-24 ~13:35Z Step 8 verdict. **Fully mirrored as of 2026-07-25**
> (the 4-child split moved every remaining DELTA section there verbatim — nothing stays duplicated here). Keep appending
> new session entries to that child file, not here, going forward.
>
> **Current status** (as of the child's last entry, 2026-07-24 ~13:35Z Step 8 verdict): CeFi 4-surface migration still
> IN FLIGHT. KRAKEN-SPOT rename is DONE (Surface A genuinely clean for that venue); LATE colliding-venue renames +
> Surface C v2 manifest-dedup `--apply` + LIGHTER-ZKSYNC backfill remain the critical-path items (tracked in the child's
> Deferred-work table) — do NOT assume done without re-measuring. The `/autonomous` loop is OFF; resuming requires a
> fresh explicit invocation.

- **2026-07-27** — Discoverability fix (`na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` Phase 4): 2
  cefi-tagged docs reclassified `assigned_vm: NA → planning` this session were not mentioned anywhere in this hub, the
  exact "orphan invisible to sweep" bug class fixed twice before (entry #18/#25 in
  `autonomous_session_operator_decisions_2026_07_25.md`). Added here for future tranche-sweep discoverability:
  `issues/cefi_threaded_resolver_dns_starvation_risk_2026_07_26.md` (DNS-starvation Tardis-client fix, mechanical
  apply-of-proven-pattern) and `mdps_candle_manifest_population_disconnect_2026_07_25.md` (candle-manifest root-cause +
  fix, multi-AG tagged cefi-first). Neither is tracked in any Track above; both are now `assigned_vm: planning` and live
  in the AO backlog.
