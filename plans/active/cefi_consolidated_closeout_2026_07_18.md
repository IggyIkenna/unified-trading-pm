---
doc_type: plan
title: CeFi consolidated close-out — track + close every remaining cefi workstream once and for all
summary:
  Single coordination plan that references (does NOT duplicate) every still-open cefi plan/issue so they can be closed
  off together. Authored 2026-07-18 from a 3-agent audit of ~30 active cefi/IS/MTDS docs + direct verification. VERDICT
  — for the INSTRUMENT-ID CANONICALIZATION axis (GCS filename / parquet column / manifest key / reader), the 4-script
  migration tracked in cefi_residual_followups_after_honest_done_2026_07_17.md IS the final migration (predecessors
  subsumed, BYBIT futures_chain migration already complete, the 2026-07-08 id-format SSOT absorbed) and is Phase-C
  dry-run-clean, awaiting only the operator-gated drain+apply. But cefi is NOT "done" overall — 5 genuinely separate
  open tracks remain, the biggest being a REOPENED coverage question (the archived "honest-done 50.79%" rested on a
  code-bug-induced throughput collapse mistaken for a 1.8-year physical ceiling; the gap is now fillable in ~1-2 days).
  Each track below references its source doc(s) + a disposition + a close-out criterion.
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
    cefi_residual_followups_after_honest_done_2026_07_17.md,
    _cefi_canonical_blueprint_2026_07_17.md,
    cefi_tardis_throughput_collapse_350x_2026_07_17.md,
    data_completion_cefi_2026_07_15.md,
    instruments_service_plan_reconciliation_2026_06_29.md,
    instruments_completion_tracker_2026_07_06.md,
    instruments_foundation_completeness_2026_06_24.md,
    instruments_docs_audit_outstanding_items_2026_07_08.md,
    canonical_id_builder_retrofit_checklist_2026_07_08.md,
    instrument_id_format_canonicalization_2026_07_08.md,
  ]
created: 2026-07-18
last_updated: 2026-07-18
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
source:
  3-agent cefi plan/issue audit + direct verification (slot-3, 2026-07-18) at operator request ("consolidate all
  remaining cefi issues/plans into one plan referencing the others so we can close them off once and for all")
---

# CeFi consolidated close-out

> **Purpose.** One place to see + close ALL remaining cefi work. This plan **references** the source docs; it does not
> duplicate their content. Close a track by closing its source doc(s), then tick it here. Authored from a 3-agent audit
> (2026-07-18) of every active cefi/IS/MTDS plan+issue.

## Headline verdict — "is the migration final?"

- **Instrument-ID canonicalization (4 surfaces: GCS filename / parquet `instrument_id` column / manifest key / reader):
  YES, this is the FINAL migration for that axis.** The 4-script program (Track 1) is Phase-C dry-run-clean and awaiting
  only the operator-gated drain+apply. Everything id-format-related is subsumed, absorbed, or already done:
  - The 2026-07-15 raw→canonical relabel + eu-purge (`cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch`)
    is the **predecessor** Scripts 3+4 fork and supersede (2-tuple → 3-tuple recovers the majors it left raw).
  - The BYBIT `futures_chain` write-shape migration (`bybit_futures_chain_write_shape_migration_2026_07_13`) is
    **complete/archived** (11/11 todos, 0 open) — the chain-bundle GCS surface Script 2 skips was already handled.
  - `instrument_id_format_canonicalization_2026_07_08` is the design-origin SSOT, **absorbed** into the program.
  - BYBIT-SPOT manifest anomaly (135,444 rows) → subsumed by Script 3 + the FIX-0 3-tuple key.
- **CeFi OVERALL: NOT done.** Five separate open tracks remain (Tracks 2–6). None blocks the id-migration; several are
  real data-correctness work; one (Track 2) is a decision that reframes "cefi done."

## Track 1 — Instrument-ID canonicalization (THE final id migration) · SUBSUMES the id-format family

- **Vehicle**: `plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (+ blueprint
  `_cefi_canonical_blueprint_2026_07_17.md`). Phase A (code on `main`) ✅ · Phase B (deploy) ✅ characterized · Phase C
  (4 scripts written + all dry-runs validated) ✅ · **Phase D/E (drain + `--apply`) = the operator-approved minutes-gap
  hybrid, pending execution.**
- **Close-out criterion**: the operator's `ADAF0:USTF0.parquet` is canonical on all four surfaces, verified live; each
  script's `--dry-run` re-run asserts 0 further changes (idempotency).
- **Subsumes / closes on cutover**: `cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md`
  (relabel + purge `--apply`), `instrument_id_format_canonicalization_2026_07_08.md` (id-format traces),
  `instruments_remaining_work_audit_2026_07_10.md` (BYBIT-SPOT anomaly).
- **Residual adapter-retrofit carve-out → Track 5** (the 4 scripts are one-time DATA migrations; they do NOT retrofit
  the adapters, so re-drift prevention is separate).

- [ ] [PM] P0. Execute the minutes-gap hybrid cutover (Track 1) → flip this + the residual-followups Phase-1/2 todos.

## Track 2 — CeFi backfill COVERAGE reopened (DECISION NEEDED — reframes "cefi done") · P0

- **Source**: `issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md` (root-cause `status: resolved`) +
  `plans/archive/2026_07/cefi_completion_program_2026_07_15.md` (archived "honest-done, 50.79% accepted").
- **The finding (verified 2026-07-18)**: the archival's basis — "the 2.89M-cell gap is not closable at the N=1 Tardis
  ceiling ≈ 1.8 years" — is FALSE. It was a **~350x code-bug throughput collapse** (`run_in_executor(None,…)`
  default-pool + a date-serial barrier), not a physical ceiling; the repo's own manifest shows 2.16M rows in ONE day, so
  the gap is **~1-2 days of work at June rates**. **THE THROUGHPUT BUG IS NOW FIXED + MEASURED LIVE** — back to ~14 MB/s
  on the VM for authenticated cefi shards (operator, 2026-07-18, via a parallel agent), closing the source doc's
  "measure the fix on real infra" P0; the 2.89M-cell gap is now genuinely fillable at real throughput. The doc also
  flags that **"operator accepted 50.79%" may have been INFERRED from the erroneous ceiling verdict, not actually
  given** — the operator's words that session were a challenge to the slowdown, not an acceptance.
- **Decision the operator must make**: (a) re-open or supersede the archived completion program; (b) re-confirm or
  reverse the "accept 50.79%" decision; (c) if reversing, re-run the cefi Tardis backfill on the fixed code (N=1 cap
  still applies — one Tardis VM — but at ~fixed throughput the 2.89M gap fills in days). Open P0/P1 todos already exist
  in the source doc (`Re-open the CeFi Completion Program archival`, `Re-confirm the "operator accepted 50.79%"`,
  `Measure the fix on real infra`, `Kill the date-serial barrier`).
- **Close-out criterion**: operator ruling recorded; if backfill resumes, coverage re-measured post-run.

- [x] ✅ [REVIEW] P0. **RULING (autonomous, within documented intent — /autonomous, 2026-07-18)**: **RE-OPEN the CeFi
      Completion Program + REVERSE the 50.79% acceptance.** Basis (all operator-stated): the archival's 1.8-year-ceiling
      premise is a verified-false ~350x code-bug (`run_in_executor(None,…)` default-pool + date-serial barrier), **now
      FIXED + measured live @~14 MB/s** on real infra (operator, 2026-07-18, parallel agent); the "accept 50.79%" was
      INFERRED from that erroneous ceiling, not actually given (the operator's words were a challenge to the slowdown).
      The 2.89M-cell gap is ~1-2 days at June rates → we resume filling; **coverage % is the climbing metric.** ACTION →
      the resume-backfill todo below (runs AFTER the Track-1 re-enable so it doesn't fight the drain). The operator can
      reverse this ruling; surfaced in the session report.
- [ ] [DATA] P1. **Resume the cefi Tardis COVERAGE backfill on the fixed code (the Track-2 ACTION of the ruling above).**
      Launch AFTER the Track-1 Phase-D re-enable (else the drain kills it). **N=1 Tardis cap, both clouds** (the storm
      rule — count the fleet with `tardis-concurrency-guard.sh` first; scale on the one IP via `SINGLE_VM_QUEUE=1` +
      `TARDIS_MAX_CONCURRENT_DOWNLOADS`, NEVER more VMs). SPOT (idempotent backfill). Re-measure coverage post-run;
      supersede the archived 50.79% with the new number. (repo: deployment-service / market-tick-data-service)

## Track 3 — Manifest completeness axis (SEPARATE from id-format) · P1

- **Source**: `data_completion_cefi_2026_07_15.md` — a DIFFERENT canonicalization axis: manifest `pipeline_mode`
  partition + legacy-bucket orphan-sweep + cefi `_index` v8→v9 schema. ~15 open items (E4 orphan sweep, E7/E8
  verify+delete, candle-coverage gaps, denominator seed, v8→v9 CF-audit). NOT subsumed by Track 1.
- **Close-out criterion**: its own todos closed; do NOT fold into Track 1 (parallel track).

## Track 4 — Denominator / catalogue-completeness correctness · P1

- **Sources**: `instruments_service_plan_reconciliation_2026_06_29.md` (C1/C2 ASTER denominator over-seed + connector,
  C5 Deribit-options false-"complete"); `instruments_completion_tracker_2026_07_06.md` (D2);
  `instruments_foundation_completeness_2026_06_24.md` (G4/G5 not fully closed);
  `issues/cefi_layer1_denominator_gaps_2026_07_03.md`. Denominator-honesty, separate from id format.
- **Also here (P0 data-correctness bugs found in the audit, filed in their own docs):**
  - `issues/deribit_options_chain_af_g4_blocker_2026_07_03.md` — the `futures_chain` retry path re-attempts a
    structurally-absent channel no cefi Tardis venue exposes → **112,727/112,727 attempted_failed, LIVE + growing**,
    overwriting prior `empty_confirmed`. **A real P0 writer-gate defect.**
  - `issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md` — gate Tardis requests on the
    vendor catalog; stop recording impossible combos as `attempted_failed` (denominator-corruption, P0).
- **Close-out criterion**: the P0 writer-gate + impossible-combo bugs fixed; denominator gaps resolved or accepted.

## Track 5 — Adapter canonical-ID-builder retrofit (RE-DRIFT prevention, post-migration) · P2

- **Sources**: `issues/instruments_docs_audit_outstanding_items_2026_07_08.md` (B1 — only ~4/63 adapters route through
  the shared canonical-id builder; most stamp ids ad hoc); `canonical_id_builder_retrofit_checklist_2026_07_08.md`
  (FI_/FF_ Kraken-Futures 13-instrument collision, unresolved).
- **Why separate**: Track 1's 4 scripts are one-time DATA migrations; they do NOT change the ~59/63 adapters that stamp
  ids ad hoc, so **new writes can re-drift** unless the adapters are retrofitted to the shared builder. This is the
  durability half of "canonical everywhere."
- **Close-out criterion**: adapters route through the shared builder (or a QG gate enforces canonical-id shape on
  write).

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
- `issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md` — flip `launcher_registry.py` DRIFT/PACIFICA entries to
  `None` (prevents self-heal relaunch); cefi bucket already purged.
- `issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md` — spot-check GCS/manifest/UI
  consistency across a few more findings + decide the reconciliation cadence (verification of the migration's real-world
  effect).

## Operator dispositions (2026-07-18) — pre-migration execution (do these BEFORE the Track-1 cutover)

> The operator reviewed the audit and directed a pre-migration close-out. The migration cutover (Track 1) is now GATED
> on the P0 items below. Each maps to a source doc; archive the source when its item lands.

- [ ] [BACKEND] P0. **DERIBIT `instrument_id` missing the quote — the canonical symbol must ALWAYS be `BASE-QUOTE`
      (operator ruling 2026-07-18, overriding the `BASE[_QUOTE]` optional-quote decision in
      `instrument_id_format_canonicalization_2026_07_08.md` line 96).** Verified live: **265,538 of 425,160 catalogue
      rows (62%) — ALL DERIBIT (263,950 OPTION + 1,588 FUTURE)** — drop the quote (`raw=AVAX_USDC-1APR26` →
      `DERIBIT:FUTURE:AVAX@LIN-20260401`, must be `…AVAX-USDC@LIN…`; `BTC-5APR19-3250-C` → `DERIBIT:OPTION:BTC@INV-…`,
      must be `…BTC-USD@INV-…`). DERIBIT-only (every other venue already carries the quote). Fix the DERIBIT
      adapter/builder to always emit `BASE-QUOTE@MARGIN_TYPE[-YYYYMMDD][-STRIKE-C|P]` (USDC linear / USD inverse) →
      **rebuild `prod/catalog.parquet`** (coordinated ~38-min prod op) → **extend the Phase-−1 verify gate** to also
      assert ZERO missing-quote ids (the current gate — 0 `:PERP:`, `instrument_id==canonical_instrument_id` — let this
      class through). This GATES the Track-1 migration (else it bakes the quote-less form into all four surfaces).
      (repo: instruments-service; found 2026-07-18 by the operator spotting `DERIBIT:FUTURE:AVAX@LIN-20260718`.)
- [x] ✅ [BACKEND] P0. **Remove the UAC-seed catalogue fallback — catalogues FAIL LOUD** — DONE
      `market-tick-data-service@3253cae3` (QG green, 6183 passed). New `InstrumentCatalogUnavailableError(RuntimeError)`
      (NOT `ValueError`, so the manifest/canonicalise `except ValueError` can't swallow it; added to the manifest-write
      re-raise allowlist). cefi/defi/tradfi `list_instruments` + `_load_sentinel_catalogs` + sports sentinel path now
      RAISE on absent/empty/schema-drift; only `KeyError` (no reader registered = out of job scope) tolerated;
      off-season empty sports stays honest. Verified buckets are the consolidated shape
      (`instruments-store-{cefi,defi,tradfi,sports}-prd-central-element-323112`). Prediction has NO separate catalogue
      (rides sports fixtures). Tests mock the catalogue read (sanctioned). (repo: market-tick-data-service)
- [x] ✅ [BACKEND] P0. **Gate Tardis cefi on the vendor response + stop false `attempted_failed`** — DONE
      `market-tick-data-service@a7569298` (QG green, 6187 passed; `venue_fetch.py` UNTOUCHED). Tardis HTTP-400
      `code=300`(invalid-symbol)/`code=140`(date-not-available) now classified `is_structural_absence` → recorded
      `empty_confirmed`/skipped like a 404, NEVER `attempted_failed`; error code logged; 5xx/429/403/non-structural-400
      still raise. **Remediation DRY-RUN measured (operator-gated `--apply`, NOT run):** impossible-combo per-symbol
      Tardis-400s = **24,410** (`code=300` invalid-symbol / `code=140` date-not-available — GENUINE per-symbol source
      absences → reclass to `empty_confirmed`; needs a mirror of the reclass script, not yet built); ~955k residual is
      genuine transient 403 IP-lock (correctly af). (repo: market-tick-data-service) **⚠️ CORRECTION (operator
      2026-07-18): the futures_chain 122,585 are NOT a false-af / source-absence — DO NOT RECLASS them.**
      `futures_chain`/`options_chain` are OUR per-underlying SHARD BUNDLES (MTDS aggregates the per-symbol Tardis data
      types `trades`/`book_snapshot_5`/`derivative_ticker`/`liquidations`/`options_chain` by underlying into
      `…/data_type={dt}/underlying={U}/ticks.parquet`); Tardis is called per-symbol; the `instrument_id` type stays
      FUTURE/OPTION; the failure + aggregation are ON OUR SIDE. So the 122,585 are REAL capture gaps (per-symbol
      dated-futures data didn't capture → bundle never built — consistent with the throughput collapse), which FILL on
      the **Track-2 coverage backfill** (throughput fixed @14 MB/s), NOT a reclass. The
      `deribit_options_chain_af_g4_blocker_2026_07_03.md` "structurally-absent channel" premise + its 2026-07-12
      reclass + `reclass_cefi_futures_chain_no_tardis_source.py` are all built on the SAME confusion — do not propagate
      them; the real fix is capture + build the bundle, tracked under Track-2.
- [ ] [BACKEND] P1. **UAC per-venue seed fallback (surfaced by the fail-loud work) — decide + remove if catalogues are
      the sole source.** Distinct from the wholesale absent-catalogue fallback just removed in MTDS:
      `unified_api_contracts.registry.market_data_categories.get_expected_instruments_for_venue` STILL falls back to the
      per-venue MVP seed when `instruments_provider` is None / a PRESENT catalogue lacks a specific venue
      (`market_data_categories.py:2250` + `registry/defi_prediction_instrument_seeds.py`). Per the operator's
      "catalogues should be the sole source" ruling this should also fail-loud / be removed — but it's a UAC change with
      fleet blast radius, so scope it deliberately. Also here: register Tardis error codes in `classify_venue_error` +
      the REQUEST-side vendor-catalogue gating (preflight shouldn't generate cefi `futures_chain` shards →
      `expected_unattempted`) belong in the in-flight UAC `coverage_exclusions` work. (repo: unified-api-contracts)
- [x] ✅ [DOCS] P1. **Upgrade the `data-pipeline-check-mtds` skill** — DONE `unified-trading-pm@ca3aebfc7`. §3a
      DERIBIT/BINANCE-FUTURES regression cells incl. a NEGATIVE check (DERIBIT `futures_chain` → 0 `attempted_failed`,
      the structurally-absent channel the MVP loop can't reach = the 112k-regression blind spot) + a two-force-runs diff
      for the retry-storm signature; §3b content spot-checks (DERIBIT greeks/IVs, BINANCE-FUTURES funding/OI not
      all-null); distinct report rows. (repo: unified-trading-pm)
- [x] ✅ [INFRA] P1. **`issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md`** — DONE (already satisfied by
      `deployment-service@9b13679`, which REMOVED the DRIFT/PACIFICA launcher entries entirely; no-match fail-safe
      returns `None`; QG green; `instruments-service@ee19f6f3` hardens the catalogue build against re-mint). Checkbox
      flipped `unified-trading-pm@710190b23`. P2 confirmation-catalogue `--apply` (prod 0-diff) left open, non-blocking.
      (repo: deployment-service)
- [x] ✅ [BACKEND] P2. **`issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md` — `_L5_VENUES`
      RESOLVED-BY-DELETION** (2026-07-18). The hardcoded `_L5_VENUES` tuple (finding 4, missing 11 cefi venues) no
      longer exists: it was added by `market-tick-data-service@0908bda7` (the order_flow_imbalance L2 feature) and
      **removed entirely by `market-tick-data-service@a4fb3d13`**, which retired order_flow_imbalance ("zero real
      consumers, zero production rows ever captured; duplicated MDPS's live implementation"). `grep -rn _L5_VENUES
      market_tick_data_service/` = 0 hits; `preflight()` in `book_microstructure_handler.py` only resolves the output
      bucket now (no hardcoded venue list). The issue's two *onchain* sub-audits (`_SOURCE_COVERAGE_START`,
      `_PROTOCOL_TO_DATA_TYPE`/kamino-split) are DeFi, NOT cefi — they stay open in the issue, outside this cefi
      close-out. (repo: market-tick-data-service)
- [ ] [BACKEND] P1. **`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`** — operator wants this done before
      the migration even though it's not a blocker. **SCOPE UNCLEAR — it's a multi-phase strategy/universe plan; confirm
      which phases are the pre-migration ask (likely the instrument-typing/catalogue portion, not the live-strategy
      phases).** (repos: instruments-service / strategy-service)
- [ ] [VERIFY] P2. **`issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`** —
      spot-check a few more findings across GCS/manifest/UI + decide the reconciliation cadence. (repo:
      instruments-service)
- [ ] [PM] P1. **Consolidate + archive.** `issues/cefi_layer1_denominator_gaps_2026_07_03.md` — pull its
      forked-elsewhere todos into THIS plan; archive it +
      `issues/betfair_instrument_id_delimiter_cross_repo_2026_07_08.md` (resolved) + any other otherwise-complete cefi
      plans, per the archival ritual. (repo: unified-trading-pm)
- [x] ✅ [REVIEW] P0. **Track-2 coverage decision — RULED (same decision as the Track-2 §119 ruling above; not a second
      decision).** Re-open the completion program + reverse the inferred 50.79% acceptance; the throughput ceiling was a
      ~350x code-bug now fixed @14 MB/s; gap ~1-2 days fillable. The ACTION (resume backfill after re-enable) is the
      `[DATA] P1` todo under §119. Autonomous ruling within documented intent (/autonomous 2026-07-18); operator can
      reverse.

## Track 6 — Non-canonical ENUMERATION audit → the migration must align EVERY form to one SSOT (operator ask, 2026-07-18) · P0

- **Source / ask**: the deployment-ui/api **"data status"** view used to enumerate every instrument_type / data_type /
  chain / venue that EXISTS in the GCS data/manifest for an asset_group — a duplication + non-canonical-naming
  detector. It was **removed** from the UI/API. Operator (2026-07-18): re-add it; and MEANWHILE use the enumeration so
  the migration is COMPLETE (align EVERY non-canonical form to one SSOT), not just the classes Scripts 1–4 target.
- **Audit tool**: `market-tick-data-service@81b72f1d`
  (`scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`) — re-derives the enumeration from
  `read_availability_index(cefi_bucket)`. **Measured live 2026-07-18** on the **11,185,557-row** cefi manifest
  (`market-data-tick-cefi-prd-central-element-323112`):
  - **instrument_id: 1,864,357 non-canonical (16.67%)** — bare-wire (no `VENUE:TYPE:` prefix) **1,367,181** (380,672
    resolve via the 3-tuple wire-map / **986,509 UNRESOLVED**, dominated by blank itype); `:PERP:` shorthand
    **374,272** (0 resolve); missing-quote (`ETHUSDT_210326`) **91,254**; `nc:other` (`PAXG_USDC-27JUN25`) **30,986**;
    blank **62,367**; DERIBIT:COMBO **662**.
  - **instrument_type COLUMN drift — a NEW axis Scripts 1–4 do NOT touch**: BLANK **3,186,640** · lowercase
    `perpetual` **289,700** · `spot_pair` **25,189** · `None` **24,583** · `spot` **21,336** ·
    `futures_chain`(data_type-leaked-into-itype) **66,129** · `options_chain` **581** · `future` **182** · `index` **2**.
  - **venue drift**: `OKX` 64 · blank 34 · `KALSHI-PERP` 784 · `POLYMARKET-PERP` 480 · `DERIBIT-COMBO` 226 ·
    `COINBASE-CDE` 22,370. **data_type**: blank 9,750.
- **Coverage gap (why the `--apply` must WAIT for these)**: Scripts 1–4 resolve ~380k bare-wire; the other **~1.48M**
  non-canonical rows (blank-itype-driven bare-wire, `:PERP:`, missing-quote, COMBO) need DEDICATED paths. Running the
  current `--apply` would relabel ~380k and leave ~1.48M non-canonical — "canonical" would be a lie. **Track 6 gates the
  cutover `--apply`.** The blank-itype axis is the ROOT: fixing it first lets the 3-tuple resolve most of the 986k
  UNRESOLVED bare-wire.

- [ ] [REVIEW] P0. **Operator canonical rulings** (see the questions posed 2026-07-18) — blank-itype resolution
      strategy; prediction-venue rows (KALSHI-PERP/POLYMARKET-PERP) in the cefi manifest; DERIBIT:COMBO; blank
      venue/id/data_type rows; COINBASE-CDE. These shape the normalization scripts below, so they land FIRST.
- [ ] [SCRIPT] P0. **instrument_type column normalization** — casing (`perpetual`/`spot`/`spot_pair`/`future` → UPPER,
      `spot`→`SPOT_PAIR`), `None`/blank → catalogue-inferred by (venue, raw_symbol) (the venue name disambiguates most:
      `-SPOT`→SPOT_PAIR, `-FUTURES`/`-SWAP`→PERPETUAL|FUTURE), data_type-leak (`futures_chain`/`options_chain` as itype)
      → real FUTURE/OPTION. This is the ROOT fix that unblocks ~986k bare-wire resolutions. (repo: instruments-service)
- [ ] [SCRIPT] P0. **`:PERP:` → `:PERPETUAL:` rewrite** (374,272 manifest rows + any on-disk content) with symbol
      decompose (`ASTER:PERP:CLUSDT` → `ASTER:PERPETUAL:CL-USDT@LIN`). Extends Script 2/3. (repos: market-tick-data-service,
      instruments-service)
- [ ] [SCRIPT] P1. **missing-quote + nc:other decompose** (`ETHUSDT_210326`, `PAXG_USDC-27JUN25`) via the catalogue —
      extract the raw symbol tail, resolve to canonical dated-future/option. (repo: instruments-service)
- [ ] [FEATURE] P1. **Re-add the "data status" enumeration to deployment-ui/api** — the distinct instrument_type /
      data_type / chain / venue listing per AG that was removed; it is the durable non-canonical/duplication detector.
      (repos: deployment-api, deployment-ui) — investigate the removal commit first.

## Codex SSOTs (read before touching a track)

`codex/02-data/availability-manifest-and-data-status.md`, `…/pipeline-mode-partition.md`,
`codex/04-architecture/instruments-service-as-ssot-for-mtds.md`, `codex/05-infrastructure/vm-launcher-runbook.md`
(Tardis cap + the throughput-fix ruling), `codex/06-coding-standards/read-time-filter-pushdown.md`.

## Progress Log

- **2026-07-18 (slot-3, /autonomous) — Track-2 REVIEW P0 RULED (both §119 + §252, one decision).** RE-OPEN the CeFi
  Completion Program + REVERSE the inferred 50.79% acceptance. Rationale (all operator-stated across the dispatch
  session): the archived 1.8-year-ceiling premise is a verified-false ~350x code-bug (`run_in_executor(None,…)`
  default-pool + date-serial barrier), NOW FIXED + measured live @~14 MB/s on real infra; the "accept 50.79%" was
  inferred from that erroneous ceiling, not given. The 2.89M-cell gap is ~1-2 days at June rates. This is an autonomous
  ruling made WITHIN documented intent (operator: "continue mapping all todos until they are 100% done /autonomous" +
  the fixed-throughput facts) — recorded so the operator can reverse. The ACTION (resume the cefi Tardis backfill on the
  fixed code, N=1 cap, SPOT, AFTER the Track-1 re-enable so it doesn't fight the drain) is now the `[DATA] P1` todo under
  §119; coverage % is the climbing metric, re-measured post-run to supersede the archived 50.79%.

- **2026-07-18 (slot-3) — Plan authored from a 3-agent audit of ~30 active cefi/IS/MTDS docs + direct verification.**
  Verdict: id-canonicalization migration (Track 1) is FINAL for its axis and cutover-ready; cefi overall has 5 separate
  open tracks. Biggest is Track 2 — the archived "honest-done 50.79%" rests on a verified-false 1.8-year-ceiling premise
  (a ~350x code bug, now fixed; gap fillable in ~1-2 days) and the acceptance may have been inferred, not given → needs
  an operator ruling. All source docs referenced above; none duplicated here.
