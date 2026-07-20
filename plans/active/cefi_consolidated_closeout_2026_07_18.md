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
- [ ] [DATA] P1. **Resume the cefi Tardis COVERAGE backfill on the fixed code (the Track-2 ACTION of the ruling
      above).** Launch AFTER the Track-1 Phase-D re-enable (else the drain kills it). **N=1 Tardis cap, both clouds**
      (the storm rule — count the fleet with `tardis-concurrency-guard.sh` first; scale on the one IP via
      `SINGLE_VM_QUEUE=1` + `TARDIS_MAX_CONCURRENT_DOWNLOADS`, NEVER more VMs). SPOT (idempotent backfill). Re-measure
      coverage post-run; supersede the archived 50.79% with the new number. (repo: deployment-service /
      market-tick-data-service)

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
      consumers, zero production rows ever captured; duplicated MDPS's live implementation").
      `grep -rn _L5_VENUES     market_tick_data_service/` = 0 hits; `preflight()` in `book_microstructure_handler.py`
      only resolves the output bucket now (no hardcoded venue list). The issue's two _onchain_ sub-audits
      (`_SOURCE_COVERAGE_START`, `_PROTOCOL_TO_DATA_TYPE`/kamino-split) are DeFi, NOT cefi — they stay open in the
      issue, outside this cefi close-out. (repo: market-tick-data-service)
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
  chain / venue that EXISTS in the GCS data/manifest for an asset_group — a duplication + non-canonical-naming detector.
  It was **removed** from the UI/API. Operator (2026-07-18): re-add it; and MEANWHILE use the enumeration so the
  migration is COMPLETE (align EVERY non-canonical form to one SSOT), not just the classes Scripts 1–4 target.
- **Audit tool**: `market-tick-data-service@81b72f1d`
  (`scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`) — re-derives the enumeration from
  `read_availability_index(cefi_bucket)`. **Measured live 2026-07-18** on the **11,185,557-row** cefi manifest
  (`market-data-tick-cefi-prd-central-element-323112`):
  - **instrument_id: 1,864,357 non-canonical (16.67%)** — bare-wire (no `VENUE:TYPE:` prefix) **1,367,181** (380,672
    resolve via the 3-tuple wire-map / **986,509 UNRESOLVED**, dominated by blank itype); `:PERP:` shorthand **374,272**
    (0 resolve); missing-quote (`ETHUSDT_210326`) **91,254**; `nc:other` (`PAXG_USDC-27JUN25`) **30,986**; blank
    **62,367**; DERIBIT:COMBO **662**.
  - **instrument_type COLUMN drift — a NEW axis Scripts 1–4 do NOT touch**: BLANK **3,186,640** · lowercase `perpetual`
    **289,700** · `spot_pair` **25,189** · `None` **24,583** · `spot` **21,336** ·
    `futures_chain`(data_type-leaked-into-itype) **66,129** · `options_chain` **581** · `future` **182** · `index`
    **2**.
  - **venue drift**: `OKX` 64 · blank 34 · `KALSHI-PERP` 784 · `POLYMARKET-PERP` 480 · `DERIBIT-COMBO` 226 ·
    `COINBASE-CDE` 22,370. **data_type**: blank 9,750.
- **Coverage gap (why the `--apply` must WAIT for these)**: Scripts 1–4 resolve ~380k bare-wire; the other **~1.48M**
  non-canonical rows (blank-itype-driven bare-wire, `:PERP:`, missing-quote, COMBO) need DEDICATED paths. Running the
  current `--apply` would relabel ~380k and leave ~1.48M non-canonical — "canonical" would be a lie. **Track 6 gates the
  cutover `--apply`.** The blank-itype axis is the ROOT: fixing it first lets the 3-tuple resolve most of the 986k
  UNRESOLVED bare-wire.

- [x] ✅ [REVIEW] P0. **Operator canonical rulings — RECEIVED 2026-07-18. The rebuilt catalogue is the SSOT; align the
      manifest to it.** 1. **Blank/missing instrument_type (3.19M)** → **catalogue-resolve by (venue, raw_symbol) AND
      venue-suffix-infer when not in the catalogue** (operator chose the most aggressive option): `-SPOT`→`SPOT_PAIR`,
      `-FUTURES`/`-SWAP`/`-PERP` venue→derivatives (dated symbol→`FUTURE`, else `PERPETUAL`). Accept the small mis-type
      risk on delisted symbols the catalogue no longer knows. 2. **Orphans (not in catalogue)** → **DROP unless cleanly
      mappable to canonical.** Bare-`OKX` (64) → remap to `OKX-SWAP`/`-SPOT`/`-FUTURES` where the symbol resolves
      cleanly, else drop; blank venue/id/data_type → drop. 3. **KALSHI-PERP (784) + POLYMARKET-PERP (480) → DROP** —
      VERIFIED 2026-07-18: **100% `empty_confirmed`, `row_count=0`, `instrument_count=0`, blank `instrument_id`** — no
      real perp data (the "Polymarket perps that don't work" that were dropped originally; these are just empty probe
      rows for 8 data_types × dates). If they ever capture real perp data they'd map cleanly to canonical, but there is
      none today. 4. **DERIBIT:COMBO is CANONICAL** (catalogue has `instrument_type=COMBO` 138,544 + venue
      `DERIBIT-COMBO` 69,272) — my audit's canonical-set was missing COMBO; combos get MIGRATED, not excluded.
      `COINBASE-CDE` (99 in catalogue) legit.
- [x] ✅ [SCRIPT] P0. **instrument_type column normalization** — DONE `instruments-service@555ddf1c` (supersedes
      `@4b4b9a7d`/…; QG green; DRY-RUN validated live on the **11,185,557-row** cefi manifest; `--apply` DRAIN-GATED
      under the Track-1 cutover, NOT run). Built as the itype leg of the SHARED `resolve_canonical(…)` resolver in
      Script 3 (`complete_cefi_manifest_canonical_dedup_2026_07_17.py`): casing/alias, data_type-leak
      (`FUTURES_CHAIN`/`OPTIONS_CHAIN`→FUTURE/OPTION), blank/`None`/unknown → **INFER** (catalogue 2-tuple, chain-hint,
      venue-suffix), the **DATED-WIRE override** (a dated wire whose itype is a mis-set PERPETUAL/blank →
      FUTURE/OPTION), and the **DEFINITIVE `-SPOT`/`-SWAP` override** (a `-SPOT` venue is ONLY SPOT_PAIR, a `-SWAP` ONLY
      PERPETUAL — fixes BYBIT-SPOT rows carrying a stray PERPETUAL). Dry-run measured: **3,824,258 itype rows changed**.
      canonical-fraction (adjusted, excl. canonically-null bundle/blank shards) **84.98% → 99.41%** (raw 83.15% →
      97.49%). (repo: instruments-service)
- [ ] [SCRIPT] P0. **`:PERP:` → `:PERPETUAL:` rewrite** (374,272 manifest rows + any on-disk content) with symbol
      decompose (`ASTER:PERP:CLUSDT` → `ASTER:PERPETUAL:CL-USDT@LIN`). Extends Script 2/3. (repos:
      market-tick-data-service, instruments-service) — **MANIFEST SIDE SHIPPED** in Script 3
      `instruments-service@555ddf1c`: `resolve_canonical` decomposes `VENUE:PERP:SYM` + forces `PERPETUAL`; dry-run
      rewrote **374,227** manifest rows (matches the audit's 374,272). REMAINING before this ticks: on-disk GCS content
      rename + the MTDS writer-side fix.
- [x] ✅ [SCRIPT] P1. **bare-wire / missing-quote / DATED-contract recovery** — DONE `instruments-service@555ddf1c`
      (operator Option A + resolver-gap fix, 2026-07-18). Recovery paths in `resolve_canonical`, all catalogue-SSOT
      (zero fabrication): (1) **dated-wire itype-fix** — a dated wire whose itype is a mis-set PERPETUAL/blank →
      FUTURE/OPTION, which UNBLOCKS the existing wire-map (it already keys the venue-native dated `raw_symbol`):
      **+115,225 captured dated rows / ~40.7B ticks** (the 41B-tick lever); base-quote-WITH-DATE fallback +1,286. (2)
      **`-SPOT`/`-SWAP` definitive itype override** (RESOLVER-GAP FIX found by the residual diagnostic): BYBIT-SPOT rows
      carrying a stray PERPETUAL made the wire-map miss → **+3,531 rows / 186M ticks**. (3) base-quote SSOT map (2,605,
      incl. MATIC→POL) + Kraken/underscore reconstruct (132). **Result: adjusted canonical-fraction 84.98% → 99.41%**
      (raw 83.15% → 97.49%). Big classes CONFIRMED resolving (undashed `MATICUSDT`→`MATIC-USDT` via wire-map, dashed
      `SC-USDT`/`BTC-USDC` via base-quote, slash `XBT/USD` — 0 slash residual). Residual **53,965 captured rows / 7.46B
      ticks**, all genuinely-unresolvable: bare-no-quote 11,487/6.08B (`DERIBIT:ETH` index, `BYBIT:BTCUSD`
      spot/perp-ambiguous), catalogue-absent delisted, CME-no-day, EXTENDED-STARKNET `SUI-USD@LIN` bare-marker (1,108).
      captured-with-data dropped = 0. (repo: instruments-service)
- [ ] [BACKEND] P0. **POST-CUTOVER: flip the smoke-check + downloader to canonical instrument ids** — MUST land with (or
      immediately after) the cutover `--apply`, else targeted re-fetch silently breaks fleet-wide. Today the
      downloader's `--instrument-ids` matches **RAW venue-native symbols EXACTLY** (no substring/underlying expansion,
      no canonical→raw resolution), so the moment a venue's objects are canonical-named there is no raw symbol left to
      pass and a targeted fetch returns **0 rows with no error**. Measured 2026-07-18 mid-migration: 8 of 46 provable
      Tardis cells were already canonical-only (BITFINEX-FUTURES ×4, BYBIT-SPOT ×2, COINBASE-FUTURES ×2) and could not
      be force-fetched at all. Three coupled changes: (1) make `--instrument-ids` accept canonical ids (or resolve
      canonical→raw) in the MTDS download path; (2) revert the smoke-check sampler
      (`scripts/pipeline_e2e_check.py::_sample_raw_symbol_from_prod_listing`) to sample the CANONICAL id and drop the
      `':' in stem` skip-guard added for the mixed-naming window (market-tick-data-service@1875b95b); (3) drop the
      `--tardis-only` docs' "verdicts are unreliable mid-migration" caveat once manifest lookups key on the same id form
      the writer records — that mismatch is what makes the check report `failed` on shards that genuinely succeeded (IS
      reported `failed=17` while all 18 venues wrote records). Full evidence:
      `issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md`. (repos:
      market-tick-data-service, unified-trading-pm)
- [ ] [FEATURE] P1. **Re-add the "data status" enumeration to deployment-ui/api** — the distinct instrument_type /
      data_type / chain / venue listing per AG that was removed; it is the durable non-canonical/duplication detector.
      (repos: deployment-api, deployment-ui) — investigate the removal commit first.

      **INVESTIGATED 2026-07-18 (slot-3) — no single removal commit exists; the capability eroded across several
                                                                                                      legitimate "fix" commits, not one deletion.** `git log -S"distinct"/-S"enumerate"` + `--grep` across the full
                                                                                                      deployment-api/deployment-ui history found no commit that deletes a raw-enumeration feature. What actually
                                                                                                      happened: (1) `BreakdownsAccordion`/`coverage.py:_build_breakdowns` (the "Instrument Coverage Summary") still
                                                                                                      groups by the RAW manifest string per axis (venue/chain/instrument_type/data_type via
                                                                                                      `SHARD_AXIS_MATRIX`-derived `BREAKDOWN_AXES`) and never canonicalises the query key — only its P4-A DISPLAY
                                                                                                      label went canonical-friendly (`deployment-ui@7853409`, raw value still on hover) — so this surface never
                                                                                                      literally lost the raw-value signal. (2) The NEWER hierarchical drilldown (`data_status_hierarchical.py`)
                                                                                                      picked up a same-day (2026-07-18 08:14, `deployment-api@512180b`) DISPLAY canonicalisation that MERGES
                                                                                                      instrument_type/venue duplicate rows into one tree node for correct completion-percentage rollups — this is
                                                                                                      the closest thing to an actual regression of the "spot the dupe" signal, and its own commit message documents
                                                                                                      the exact kind of raw diversity the operator described (`COINBASE-SPOT instrument_types = ['', 'SPOT_PAIR',
                                                                                                      'spot', 'spot_pair']`). (3) A DIFFERENT, adjacent feature — the Catalogue Explorer's
                                                                                                      `/catalogue-filter-options` (`deployment-api@2fc46eb`, shipped 2026-07-17) — already returns raw distinct
                                                                                                      venue/instrument_type/data_type values, but reads the per-instrument IDENTITY catalogue
                                                                                                      (`prod/catalog.parquet`) for cefi/defi/tradfi, NOT the raw manifest, and has NO `chain` axis at all — so it
                                                                                                      only partially covers the ask. **Restoration shipped as a NEW, dedicated, read-only endpoint** (the operator's
                                                                                                      own suggested shape) rather than un-doing 512180b's legitimate math fix or bolting onto the filter-dropdown
                                                                                                      endpoint: `GET /api/data-status/axis-value-census` (`deployment_api/routes/data_status/_axis_census.py`) reads
                                                                                                      `read_availability_index(bucket, columns=[venue, chain, instrument_type, data_type])` directly (single bounded
                                                                                                      slim read) and returns every distinct RAW value + row count per axis, honest-absence per axis (chain omitted
                                                                                                      entirely outside DeFi rather than a fabricated `[]`). UI: `AxisValueCensus.tsx` (new panel, IS-only phase-1 —
                                                                                                      mirrors `CatalogueExplorer`'s scope decision) flags raw `instrument_type` values that fold to the same
                                                                                                      canonical label via the existing `canonicalInstrumentTypeLabel` alias map (reuses P4-A's table; other axes
                                                                                                      list raw values unflagged — no registry exists to safely fold venue/chain without false-positiving two
                                                                                                      genuinely different venues together).

                                                                                                      **Shipped: deployment-ui@3fb6779** (full `[UI]` gate green — tsc/eslint/vitest 1007 passed/build; `pw:L2 ✓`
                                                                                                      `tests/e2e/data-status-axis-value-census.spec.ts`). **deployment-api: code complete, tests green, full
                                                                                                      `quality-gates.sh` PASSED** (`.qg_last_passed_sha` written at HEAD `e765660`) — includes a real, unrelated
                                                                                                      pre-existing-bug fix found+fixed while chasing a false-positive test failure:
                                                                                                      `_has_active_migration_vm` (`services/data_status/manifest.py`) leaked a raw `ValueError` from
                                                                                                      `get_compute_engine_client` on any non-GCP `CLOUD_PROVIDER` (the unit-test-default `local` —
                                                                                                      `tests/unit/conftest.py:429`) straight through a helper whose own docstring promises "failures return False,
                                                                                                      never a gate" — `ValueError` was simply missing from its except tuple; proven pre-existing + zero-overlap via
                                                                                                      a stash/baseline re-run on the clean tree before diagnosing it. **NOT YET QUICKMERGED** — blocked at STAGE 2
                                                                                                      Pre-Flight by 3 DIRTY sibling deps (`unified-trading-library`, `unified-api-contracts`, `deployment-service`,
                                                                                                      all carrying an unrelated in-flight "features FOLD A" / `fold_a_cutover_spec` cross-repo bucket-naming
                                                                                                      migration, stale mtime but substantial/multi-file — not a small drive-by dep edit safe to inherit-commit under
                                                                                                      the dirty-deps carve-out without its author's context). **Next step once those clear (no code change
                                                                                                      needed):** `cd deployment-api && bash scripts/quickmerge.sh "feat(data-status): restore raw manifest
                                                                                                      axis-value census — non-canonical-naming / duplication detector (Track-6)" --agent --files
                                                                                                      'deployment_api/routes/data_status/__init__.py deployment_api/routes/data_status/_axis_census.py
                                                                                                      tests/unit/test_route_data_status_axis_census.py deployment_api/services/data_status/manifest.py'` (working
                                                                                                      tree already has all 4 files + the green sentinel; re-verify sentinel still matches HEAD before re-running).

## Pass-through from the 2026-07-18 consolidated canonicalisation audit (slot-4) — decisions + measured worklist

> Authored by the DeFi close-out audit (`defi_consolidated_closeout_2026_07_18.md`) and handed here per the operator's
> ownership split (cefi findings land in THIS plan). Operator rulings 2026-07-18.

**Operator decisions confirmed (cefi):**

- **Venue token = HYPHENATED** (`BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN`), NOT underscore — the builder only `.upper()`s
  the venue and it must equal the GCS `venue=` axis (always hyphen); underscore would FAIL the verify-gate `[A-Z0-9-]+`.
  So the live manifest's ~9.5M "hyphen" rows are ALREADY canonical → **no `-`→`_` rename** (the underscore illustrative
  form in earlier docs is wrong).
- **ASTER quote = PER-SYMBOL REAL quote** (operator ruling 2026-07-18): use each symbol's actual on-chain `quoteAsset`
  (predominantly USDT — 504/509 — but the tail carries its real USD1/USDC/`U`; `aster.py` already embeds the per-symbol
  quote). ASTER data is REAL (its own Binance-compatible endpoints `fapi.asterdex.com`, not a Binance proxy).
  Representative id = `ASTER:PERPETUAL:BTC-USDT@LIN`; **NOT hardcoded USDT** — the earlier `ASTER=USDT` note was the
  majority, not the rule. Fix the stale docs (`shard-granularity-cefi.md:106` = USDC, `DEFI_DOWNLOAD_STRATEGY.md:164`).
- **DERIBIT always-quote** — confirmed the gating P0 (already Track-1 / §195).
- **Venue purge (operator ruling, refined 2026-07-18)** — remove the CULLED/defunct venues ENTIRELY from UAC + manifest
  - GCS data + MVP catalogue + docs, **snapshot-first** (irreversible): BITSTAMP-SPOT / HUOBI-SPOT/-FUTURES /
    GEMINI-SPOT / PHEMEX-SPOT (defunct), and the Solana-perp cull
    (DRIFT/PACIFICA/MANGO/ZETA/FLASH/SOLAYER/PICASSO/CAMBRIAN). **KEEP registered (NOT purged)**: **BINANCE-DELIVERY**
    (live COIN-M product — descope from MVP backfill, keep the UAC registration/scaffold; the audit found it still fully
    registered across UAC, which is fine — just mark non-MVP), KALSHI-PERP + POLYMARKET-PERP (roadmap — will be added),
    LIGHTER-ZKSYNC (blocked-credentials MVP scaffold — external-data-always-available rule), EXTENDED-STARKNET (live
    MVP). Clean the STALE `codex/02-data/mvp-scope-canonical.md` PACIFICA-as-MVP bolding.
- **DERIBIT-COMBO leg-aware combos (cross-AG)** — adopt the operator's 2026-07-09 leg-aware signed-weight spec (per-leg
  human-readable `instrument_key` + weight + direction-as-sign, 1–4-leg hard cap) for DERIBIT-COMBO by extending the
  shared `build_leg()` path to `cefi/deribit_combo_adapter.py` + `cefi/tardis/combos.py` — the open cross-AG P2 in
  `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`.

**Live manifest worklist (`market-data-tick-cefi-prd`, 11.19M rows; ~44.3% of ids non-canonical)** — the migration must
map these (measured via the distinct-values audit; counts approximate):

| dimension       | non-canonical                                     | canonical target                                   |     ~rows | action                                          |
| --------------- | ------------------------------------------------- | -------------------------------------------------- | --------: | ----------------------------------------------- |
| instrument_type | `PERPETUAL`/`SPOT_PAIR`/`FUTURE`/`OPTION`         | lowercase (`perpetual`…)                           |     7.58M | case-fold (column only; id segment stays UPPER) |
| instrument_type | `''`/`NULL`/`spot`/`index`                        | resolve from id / remap                            |     3.23M | resolve                                         |
| instrument_id   | perp missing `@LIN`/`@INV`                        | append margin marker                               | 2,402,330 | reconstruct                                     |
| instrument_id   | raw no-colon (`SPELLUSDT`)                        | `VENUE:TYPE:BASE-QUOTE@MARGIN`                     | 1,362,316 | reconstruct                                     |
| instrument_id   | DERIBIT option (0% canonical)                     | `DERIBIT:OPTION:BASE-USD@INV-YYYYMMDD-STRIKE-C\|P` |  ~428,600 | add quote + YYYYMMDD                            |
| instrument_id   | `VENUE:PERP:RAW` (HL/LIGHTER/ASTER)               | `VENUE:PERPETUAL:BASE-QUOTE@LIN\|INV`              |   374,272 | reconstruct                                     |
| instrument_id   | DERIBIT future `BASE-DDMMMYY`                     | `DERIBIT:FUTURE:BASE-USD@INV-YYYYMMDD`             |  ~250,600 | add quote                                       |
| instrument_id   | KRAKEN raw `FI_/FF_`                              | `KRAKEN-FUTURES:FUTURE:BASE-USD@…-YYYYMMDD`        |    68,469 | reconstruct                                     |
| source          | `''`/`NULL`                                       | vendor token (`tardis`/native)                     | 3,441,207 | backfill vendor                                 |
| pipeline_mode   | `NULL`                                            | `{mode}_{source}`                                  |   345,492 | backfill                                        |
| venue           | `OKX` bare (64) · `DERIBIT-COMBO`→`DERIBIT` (226) | resolve family / encode combo in id                |      ~290 | resolve/collapse                                |

**Enumeration-restore (cross-AG, owned by the DeFi plan Track 6)**: a raw un-canonicalised distinct-values audit panel
per asset_group (the view removed on `deployment-api@512180be`) is being restored so this worklist stays live-visible.

## CEFI CANONICAL SPEC (operator-authoritative, 2026-07-18 — the migration target)

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
`codex/02-data/cross-asset-canonical-target-ssot.md` §10. (Bundle keys on `underlying`, NOT a synthesized `VENUE:BASE`
id.)

## Codex SSOTs (read before touching a track)

`codex/02-data/availability-manifest-and-data-status.md`, `…/pipeline-mode-partition.md`,
`codex/04-architecture/instruments-service-as-ssot-for-mtds.md`, `codex/05-infrastructure/vm-launcher-runbook.md`
(Tardis cap + the throughput-fix ruling), `codex/06-coding-standards/read-time-filter-pushdown.md`.

## Progress Log

- **2026-07-20 (slot-3, /autonomous) — NO-ORPHANS ACCOUNTING (deliverable A) + READY MVP-gap BACKFILL (deliverable B).**
  Live re-run of the shipped audit (`mtds/scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`) on the
  10,085,983-row cefi tick manifest + a per-id MVP categorizer that reuses Script-3's EXACT resolver
  (`is/scripts/complete_cefi_manifest_canonical_dedup_2026_07_17.py` `resolve_canonical` + `_build_*` maps) and the UAC
  shared predicate `is_in_mvp_capture_universe` (perp-gate derived by parsing catalogue ids). Full artifact:
  `/tmp/cefi_no_orphans_accounting_2026_07_20.json`; categorizer + logs in the slot-3 scratchpad.

  **A. NO ORPHANS — verdict: SATISFIED for captured data; residual is id-LABELING, not missing data.** Of **3,216,054
  captured rows, 98.36% (3,163,413) are already canonical+catalogued.** The **1.64% (52,641) captured-not-clean rows
  carry ZERO missing data** — every one is an id-form problem: **32,730 blank-`instrument_id`** rows (captured tick data
  whose manifest row lost its id — data present in GCS, needs a manifest re-derivation, NOT a backfill; incl. 9,750 also
  blank `data_type`) + **19,911 bare-wire** captured ids (BYBIT `ETHUSD`/`BTCUSD` inverse, bare `BTC`/`ETH` majors,
  BITGET dated COIN-M letter-month `BTCUSDH/M/U/Z`) that the v2 recanon (itype-fix + wire-map/decompose) canonicalizes.
  The **173,453 §4 non-canonical + 33,144 §6 orphan** rows categorize (by MVP membership) into:
  - **FIXABLE_RECANON — 5,086 distinct ids / 2,159,453 rows** (bare-wire→canonical, marker-less-perp→`@LIN/@INV`); the
    MAIN agent's v2 re-canonicalization+dedup fixes them. **RESOLVER GAP FOUND (hand to the v2 pass):** Script-3
    `resolve_canonical` returns a marker-less canonical-shaped perp UNCHANGED (does NOT add `@LIN/@INV`) even though
    `marker_base` HAS the mapping — the v2 `--apply` needs an explicit marker-add leg or ~4,500 marker-less perp ids
    persist as orphans. (The audit's `_CANON_RE` makes the margin marker optional, which is why these hide inside the
    "canonical" bucket and surface only as §6 orphans.)
  - **NON_MVP_HISTORICAL — 31,829 ids / 770,996 rows / 28 captured** → PROVED legit-absent: expired dated contracts
    (expiry < 2026-07-20) **30,268 ids** (the DERIBIT 2019-2025 options dominate §6, e.g. `BTC-10APR20-4750-C`),
    mvp-base **delisted** with no data **1,307 ids** (WAVES/EOS…), base not in the 556-member `CEFI_BASE_ASSET_UNIVERSE`
    **254 ids**. EXPECTED honest-raw, NOT defects.
  - **MVP_GAP — 311 ids / 45,650 rows / 0 captured** → real current-MVP instruments with `attempted_failed` + no capture
    (deliverable B). Venues: **DERIBIT 191** (dated futures `BTC/ETH-25SEP26/25DEC26/26MAR27` + combos), **BYBIT 80**,
    **BITGET-FUTURES 17** (`*USD_CM` COIN-M), **KRAKEN-FUTURES 9** (majors BTC/ETH/ADA/…-USD), **BINANCE-FUTURES 8**
    (SYS/B3/VINE/DENT/LRC-USDT@LIN), **OKX-SWAP 4** — ALL Tardis venues. Full list + per venue×data_type×date-range in
    the JSON (`bucket_2_MVP_instrument_gaps`).
  - **UNRESOLVED_INDET — 673 ids / 63,621 rows** (blank-id + bare-wire the resolver can't map standalone; the 33,027
    captured here = the blank-id manifest-labeling defect above). Resolve via the v2 itype-fix pass.

  **B. OPTIMIZED BACKFILL — READY (validated launch-ready via DRY-RUN, NOT run — cap-1 slot is occupied).**
  Authoritative gap: **cefi honest coverage 48.80%** (`measure_honest_coverage --diagnose-layer1`: 3,065,577 captured /
  6,281,484 reachable; Layer-1 denominator COMPLETE, 0 holes). **The Track-2 [DATA] P1 backfill is ALREADY LIVE**:
  `cefi-queue-heavy-binancefutu-x17-20260720-102103` (SPOT, `VM_TARDIS_CONSUMER=1`, ALL 17 Tardis venues, HEAVY group
  `trades;book_snapshot_5`, 2026-02-27→2026-07-19) — it holds the single Tardis slot now. Whole-corpus gap = **668,695
  `attempted_failed` (re-fetch) + 2,547,212 `expected_unattempted` (never attempted)** — `eu` dominates. Per-venue
  coverage (worst gaps first; full table in `/tmp/cefi_no_orphans_accounting_2026_07_20.json` →
  `deliverable_B_coverage`): BINANCE-FUTURES 48.2% (af 176k/eu 497k) · BITGET-FUTURES 25.8% (af 116k/eu 394k) · BYBIT
  53.3% (af 109k/eu 217k) · KRAKEN-FUTURES 55.7% · **DERIBIT 8.6% (af 114k — worst)** · OKX-SPOT 35.6% · and the
  **NON-Tardis (cap-EXEMPT) venues with real `eu` gaps: ASTER 41.3% (eu 163k) · HYPERLIQUID 38.4% (eu 140k) ·
  EXTENDED-STARKNET 37.8% (eu 37k) · LIGHTER-ZKSYNC 0.0% (eu 28,648, ZERO captured)**. **CORRECTION to the earlier
  orphan-only note:** the on-chain venues DO have large `eu` gaps (they showed no `attempted_failed` in the §6 orphan
  set, hence absent from MVP_GAP) → the cap-EXEMPT `launch-cefi-hl-aster-historical-backfill.sh` (DRY-RUN validated
  launch-ready: `cefi-hyperliquid-/aster-/ lighter-zksync-/extended-starknet-*` VMs, `SHARD_DAYS` parallelizable) should
  run **IN PARALLEL** with the Tardis waves (they never touch the licensed Tardis IP, so parallelism is free
  throughput). Tardis venues → the sharded launcher below. **Cap-1-safe Tardis waves to run AFTER the heavy VM frees the
  slot (each sequential; `tardis-concurrency-guard.sh` refuses a 2nd Tardis VM):**
  - Wave-2 LIGHT/perps (1 VM):
    `DRY_RUN=0 SINGLE_VM_QUEUE=1 LAUNCH_GROUPS=light VENUES="BINANCE-FUTURES BYBIT OKX-SWAP KRAKEN-FUTURES BITFINEX-FUTURES BITGET-FUTURES" TARDIS_MAX_CONCURRENT_DOWNLOADS=32 TARDIS_BOOK_SNAPSHOT_MAX_CONCURRENT=8 bash scripts/vm/launch-cefi-sharded-backfill.sh --env prod`
    (uniform `derivative_ticker;liquidations;futures_chain` → exactly ONE `cefi-queue-light-*` VM).
  - Wave-3 DERIBIT LIGHT (1 VM, separate — options_chain): same command with `VENUES="DERIBIT"`.
  - Wave-4 earlier-year HEAVY (2020-2025) if coverage still <target after the recent window: same,
    `LAUNCH_GROUPS=heavy YEARS="2024 2025"` etc.
  - Wave-P NON-Tardis (run NOW, in PARALLEL — cap-EXEMPT, no Tardis slot contention):
    `DRY_RUN=0 SYMBOLS=ALL SHARD_DAYS=21 bash scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` (fills the
    ASTER/HL/ LIGHTER-ZKSYNC/EXTENDED-STARKNET `eu` gaps; LIGHTER-ZKSYNC at 0% is the priority). SPOT-default; not
    year-clamped so it covers each venue's genesis→today.
  - **CAP-1 FINDING (surfaced):** `SINGLE_VM_QUEUE=1 LAUNCH_GROUPS=light` over DERIBIT+perp venues flushes **2** VMs
    (DERIBIT's `options_chain` data_types differs → separate bucket) while the guard's planned-count counts light as
    **1** — a latent cap-1 breach. Keep DERIBIT-light its own wave (above) until the guard's `_QUEUE_BUCKETS` is taught
    to count per (group|data_types), not per group.
  - **Optimizations applied (SSOT `codex/05-infrastructure/vm-launcher-runbook.md` §Tardis,
    `…/spot-vms-for-backfill.md`):** Tardis **cap-1 both clouds** (guard wired in; scale on the ONE IP, never more VMs)
    · **SINGLE_VM_QUEUE=1** bundles every venue onto one VM · **TARDIS_MAX_CONCURRENT_DOWNLOADS=32 /
    TARDIS_BOOK_SNAPSHOT_MAX_CONCURRENT=8** (defaults 16/4 leave the box ~93% idle) · **SPOT-default** + the shipped
    PROGRESS.json checkpoint auto-resume (`deployment@c138957`+`utl@3de3296b`; `RelaunchPreemptedVm` re-enters through
    the guard) · pd-balanced 250GB boot disk (kills the throughput cliff) · `STALL_PROGRESS_REGEX=uploaded`. HL/ASTER
    launcher (`launch-cefi-hl-aster-historical-backfill.sh`, cap-EXEMPT, `SHARD_DAYS` parallelizable) also validated
    launch-ready if on-chain gaps surface. **Do NOT launch a 2nd Tardis VM while `cefi-queue-heavy-*` runs.**

- **2026-07-18 (slot-3, /autonomous) — CUTOVER STATUS: surface C DONE+durable; surfaces A/B staged + BRIDGED; both
  sub-agents died on a session limit (resets 21:40 Europe/London).** The reader-bridge (D3) resolves wire→canonical at
  read time, so the system reads canonical NOW even before A/B physically complete.
  - **Surface C (manifest) — ✅ APPLIED + DURABLE** (see entry below): 16.67%→1.59% non-canonical, gate passed, survived
    consolidator re-enable. `is@555ddf1c`.
  - **Surface A (rename, Script 2) — BLOCKED on a bounded, verified data issue**: 12-day dry-run clean (11,141
    would-rename) EXCEPT **15 DERIBIT USDC dual-name collisions**. VERIFIED (read both parquets, day=2023-11-21):
    `BTC_USDC-PERPETUAL.parquet` (symbol=`BTC_USDC-PERPETUAL`, id=`DERIBIT:PERPETUAL:BTC_USDC-PERPETUAL`, 1,090,049
    rows) and `BTC_USDC.parquet` (symbol=`BTC_USDC`, id=`DERIBIT:PERPETUAL:BTC_USDC`, 449,580 rows) are the SAME DERIBIT
    USDC perp under two Tardis symbol aliases, overlapping timestamps — both → canonical
    `DERIBIT:PERPETUAL:BTC-USDC@LIN` (same for ETH_USDC etc.). Script 3 ALREADY deduped these to ONE manifest row; the
    two PHYSICAL files collide on rename. **HANDLING (for the resume): MERGE** the two objects into the canonical stem
    (concatenate + de-dup book rows by timestamp) OR keep the manifest-retained one; keep STOP-ON-SURPRISE for any
    non-same-instrument collision. Row-count asymmetry (2.4×) means dedup-by-timestamp, not blind concat. Script 2 +
    shared module are staged (dirty) in MTDS.
  - **Surface B (content, Script 1) — NOT STARTED**: to run on a SPOT cefi-migration VM via dirty tarball
    (`create-code-tarballs.sh --allow-dirty-tarball` → `launch-cefi-migration-vm.sh` with `VM_MIGRATION_CMD`→Script 1,
    DRY-RUN first). Agent hadn't packaged the tarball before the session limit.
  - **RESUME PLAN** (when the session limit lifts / sub-agents available): (1) B finishes the Script 2 merge +
    re-dry-run → I run rename `--apply --stamp <ts>`; (2) content-VM agent packages the tarball + dry-runs Script 1 on a
    VM → I review → `--apply` on the VM (~day). Then verify `ADAF0:USTF0` + `DERIBIT AVAX-USDC@LIN` on all 4 surfaces.

- **2026-07-18 (slot-3, /autonomous) — ✅ MIGRATION 1/3 APPLIED + DURABLE: the manifest (surface C) is canonicalized on
  the LIVE cefi tick manifest and it STUCK.** Sequence: (1) first `--apply` of Script 3 canonicalized the index but its
  post-verify gate caught 42,915 eu/captured 5-col collisions the eu-reconcile missed (cross-`pipeline_mode`: a
  `batch_tardis` eu vs a `batch_native` captured — the 6-col dedup can't catch it). (2) Root discovery: the **manifest
  CONSOLIDATOR cron `uts-prod-manifest-consolidator-execution-cefi-cron` runs EVERY MINUTE and re-rawed the index** —
  this is why "nothing stuck" before; the Track-1 drain is mandatory, not optional. (3) A shipped the eu-reconcile fix
  (`instruments-service@555ddf1c`: reconcile against the FULL post-relabel captured-key set, on ALL blobs). (4)
  **DRAIN**: paused the consolidator cron + stopped the live cefi backfill VM. (5) **RE-APPLY** (drained, 555ddf1c) →
  `GATE PASSED: 0 further-resolvable captured, 0 eu/captured collisions` (id_changed=1,535,266, itype_changed=3,519,879,
  perp=374,227, eu-dropped=70,114, orphans-dropped=167,859 non-captured, cull PACIFICA 2,960 EMPTY rows, snapshot
  `_index/snapshots/pre_d4_*`). (6) **RE-ENABLE** consolidator → **STICK TEST PASSED**: manifest stays **97.94%
  canonical / 1.59% non-canonical** (captured-non-canonical 425k→**18,983** genuinely-unresolvable) after the
  consolidator rebuilt from the now-canonical per-VM shards. Fleet restored (consolidator ENABLED). Surface A (rename) +
  surface B (content on a VM) next; then verify `ADAF0:USTF0` + `DERIBIT AVAX-USDC@LIN` on all four surfaces.

- **2026-07-18 (slot-3) — Script 3 `--apply` RAN by operator; POST-APPLY GATE FAILED (42,915 eu/captured collisions) →
  eu-reconcile FIXED + shipped (`instruments-service@555ddf1c`; supersedes `@ae4030ef`).** The canonicalization landed
  (itype_changed 3.5M, relabeled 436,934, perp 374,227, dated_itype_fixed 888,752, cull PACIFICA 2,960 empty, dedup
  collapsed 1.12M, orphans dropped 168,129, NON-cull captured-with-data=0 ✓, snapshots `pre_d4_20260718T190342Z`), but
  the post-apply verify gate exited 1 on **42,915 `expected_unattempted` rows still colliding (5-col) with a captured
  row**. **ROOT CAUSE (confirmed by diagnostic):** the eu-reconcile dropped only eu twins of RELABELED (id-changed)
  captured rows, MISSING eu twins of ALREADY-CANONICAL captured rows (and dropping 0 on an idempotent re-apply). 100% of
  the residual collisions were cross-`pipeline_mode` with venue-prefixed canonical ids (which is why the 6-col de-dup
  couldn't catch them — the 5-col eu-reconcile must). **FIX:** (1) reconcile against the FULL post-relabel captured
  5-col key set (not just id-changed); (2) run on EVERY loaded blob (not main-only — cross-blob collisions); (3) skip
  the candidate/`:PERP:` VOLUME STOP bands on an idempotent re-apply (before-fraction ≥ 90%). eu rows carry no data →
  dropping is always safe; captured-with-data-safe invariant intact. Dry-run drops **71,662** eu rows → 0 residual. **⚠️
  OPERATIONAL FINDING surfaced to the coordinator:** the LIVE index measured RAW AGAIN post-apply (candidates=547,886) —
  **the manifest CONSOLIDATOR re-consolidated OVER the `--apply`** between 19:03 and ~20:31. So the re-apply is a FULL
  apply, and it will be OVERWRITTEN again unless the consolidator + live cefi backfill VMs are DRAINED first (the plan's
  Track-1 "pre-migration drain, then apply"). DRY-RUN only; operator drives the gated re-apply.

- **2026-07-18 (slot-3) — Track-6 resolver-gap fix (`-SPOT`/`-SWAP` itype) + operator-CONFIRMED drop-venue cull SHIPPED
  (`instruments-service@ae4030ef`; supersedes `@4b4b9a7d`).**
  - **RESOLVER-GAP FIX (coordinator suspicion confirmed + fixed):** a residual diagnostic over ALL captured rows found a
    gap — BYBIT-SPOT rows carrying a mis-set `PERPETUAL` itype COLUMN made the 3-tuple wire-map miss (a `-SPOT` venue
    trades ONLY spot). Added a **DEFINITIVE venue-suffix itype override** (`-SPOT`→SPOT_PAIR, `-SWAP`→PERPETUAL) that
    corrects the mis-set column. **+3,531 captured rows / 186M ticks; adjusted canonical-fraction 99.30%→99.41%** (raw
    97.39%→97.49%). CONFIRMED the big classes resolve — undashed `MATICUSDT`→`MATIC-USDT` (via wire-map, counted as
    `catalogue` not `base_quote_map`, which is why base_quote_resolved is only ~2.6k yet 431k bare-wire resolve), dashed
    `SC-USDT`/`BTC-USDC` (base-quote map), slash `XBT/USD` (0 slash residual).
  - **EXACT RESIDUAL (post-resolver, post-cull): 53,965 captured rows / 7.46B ticks**, all genuinely-unresolvable
    without fabrication: bare-no-quote 11,487 / 6.08B ticks (`DERIBIT:ETH`/`BTC` index, `BYBIT:BTCUSD` spot/perp
    AMBIGUOUS — catalogue holds a stale no-marker `BYBIT:PERPETUAL:BTC-USD` dup alongside `@INV`, worth a catalogue
    cleanup), undashed-delisted 3,633 (BITGET CME `ETHUSDH` no year), OKX 3-seg `TRX-USD-SWAP` 2,525, EXTENDED-STARKNET
    bare-marker `SUI-USD@LIN` 1,108, nonascii junk 384, delisted 170, CME-no-day 33, DERIBIT hex-strike 26. Plus 34,597
    null-id bundle/roadmap KEPT (canonically null).
  - **DROP-VENUE CULL (operator-CONFIRMED "yeah cull drop venue"):** implemented snapshot-first, drops ALL rows incl
    captured-with-data for 13 venues (the ONE authorized captured-data exception; STOP bound + per-venue impact log;
    matches the venue-chain-glued form). **FINDING — 12 of the 13 cull venues have ZERO rows in the cefi TICK manifest**
    (BINANCE-DELIVERY appears 0× anywhere — its COIN-M is only in the instruments CATALOGUE as reference, NOT captured
    into cefi tick data). Only **PACIFICA** matches (stored as `PACIFICA-SOLANA`): **2,960 rows / 0 captured-with-data /
    0 ticks** (all empty probes). So the cull is a **near-no-op on THIS manifest** — surfaced to the operator: the
    BINANCE-DELIVERY COIN-M data you expected to cull is not in the cefi manifest. captured-with-data (non-cull) dropped
    = 0 (invariant held). DRY-RUN only; `--apply` NOT run.

- **2026-07-18 (slot-3) — Track-6 DATED-WIRE itype-fix SHIPPED — the 41B-tick lever (`instruments-service@4b4b9a7d`;
  supersedes `@a63a0556`).** Operator Option A. A dated contract is a FUTURE/OPTION, never a PERPETUAL; the manifest's
  itype column is often mis-set to PERPETUAL/blank on a dated wire (`OKX-FUTURES`/`LTC-USD-210625`), so the 3-tuple
  wire-map — which ALREADY keys the venue-native dated `raw_symbol` — missed. `_resolve_itype` now detects a genuine
  date tail (numeric `[-_]YY[YY]MMDD`, DERIBIT text date `-5APR19`, CME letter-month `…USDH25`, option strike
  `…-3250-C`) and overrides PERPETUAL/blank → FUTURE/OPTION, which UNBLOCKS the existing wire-map. **KEY FINDING: the
  itype-fix ALONE (via the existing wire-map) resolves ~115,225 of ~118,204 captured dated rows / ~40.7B ticks — the
  base-quote-WITH-DATE map the coordinator specified is largely redundant (the wire-map already keys the dated
  raw_symbols; it adds only 1,286).** Also: MATIC→POL rebrand alias (folds into base-quote); bare-underlying
  bundle-vs-genuine split (0 bundle unresolved / 6,214 genuine no-quote single instruments, honest-raw); race-tolerant
  per-VM shard load (a live-VM shard consolidated mid-run → skip; documented in `QUALITY_GATE_BYPASS_AUDIT.md`).
  **canonical-fraction: raw 83.15%→97.39%, adjusted (excl. the 63,776 canonically-null bundle/blank captured shards)
  84.98%→99.30%.** Residual ~93.8k honest-unresolved is genuinely-unresolvable without fabrication (no-quote bare
  underlyings, delisted alts absent from the catalogue, BITGET CME with no derivable expiry day). captured-with-data
  dropped = 0 (invariant held). DRY-RUN only; `--apply` NOT run. Surfaced to the coordinator.

- **2026-07-18 (slot-3) — Track-6 follow-up: base-quote SSOT map + Kraken/underscore reconstruct + operator CORRECTIONS
  SHIPPED (`instruments-service@a63a0556`; supersedes `@9bb339f9`).** Extended Script 3's `resolve_canonical` with a
  SECOND catalogue map keyed on each id's `BASE-QUOTE` segment (undated perp/spot) — resolves the dashed manifest value
  to the EXACT catalogue id (the catalogue IS complete, incl. delisted; the bare-wire miss was a key-form mismatch, not
  a delisting gap) — plus a narrow Kraken-slash/underscore reconstruct. Applied the operator CORRECTIONS:
  **KALSHI-PERP/POLYMARKET-PERP KEPT** (roadmap venues, removed from the drop set); **bundle rows
  (`futures_chain`/`options_chain`) KEPT untouched with NO id synthesis** (null id valid, keyed on `underlying`); KEEP-
  trend (only genuine catalogue-orphans drop, non-captured only; captured-with-data ALWAYS protected — invariant held,
  **0 captured-with-data dropped**); per-VM shard load made race-tolerant (a live-VM shard consolidated mid-run → skip).
  **KEY FINDING (authoritative re-measure — the "420k clean dashed" model was WRONG):** the base-quote map recovers only
  **~2,737 rows**, because the unresolved-captured population (172,721 rows / **48.3B ticks**) is dominated by
  **dated_contract 115,251 rows / 41.0B ticks** (`OKX-FUTURES` dated futures + DERIBIT options — DATED, out of scope for
  the undated base-quote map; ROOT = itype mis-set to PERPETUAL on a dated wire so the wire-map misses; the real lever
  to ~100% is a **dated-wire itype-fix**, next follow-up), null-id bundle/blank 34,596 (KEPT), undashed bare underlyings
  18,687 / 7.0B ticks, OKX 3-seg 2,525, MATIC→POL renames 1,157. Canonical-fraction: raw **83.15%→93.90%**, adjusted
  (excl. the 63,776 canonically-null bundle/blank captured shards) **84.98%→95.75%**. DRY-RUN only; `--apply` NOT run.
  Surfaced to the coordinator with the dated-wire itype-fix as the recommended next step.

- **2026-07-18 (slot-3) — Track-6 `[SCRIPT] P0` instrument_type-column normalization SHIPPED + DRY-RUN validated
  (`instruments-service@9bb339f9`).** Extended Script 3 (`complete_cefi_manifest_canonical_dedup_2026_07_17.py`) with a
  shared `resolve_canonical(venue, raw_itype, id_or_symbol, data_type)` resolver that aligns the newly-enumerated
  non-canonical axes to the rebuilt catalogue SSOT. Dry-run over the whole 11,185,557-row cefi manifest (main index +
  `_legacy_seed` per-VM shard), `--apply` NOT run (drain-gated for the parent to drive). **Measured before→after:**
  itype-column changed **3,639,041** (of which blank/`None`/unknown → **inferred 3,110,955** — the ROOT that unblocks
  the bare-wire 3-tuple resolution); captured bare-wire **relabeled 346,719**; `:PERP:`→`:PERPETUAL:` **rewritten
  374,227** (matches the audit's 374,272); de-dup collapsed **1,091,710** (captured only 2,896); eu-reconcile dropped
  18,888; bare-OKX remapped 0/48; canonical-fraction (captured venue-prefixed) **83.15% → 94.86%**. All STOP-ON-SURPRISE
  bands green (candidates 558,072 ∈ [400k,700k]; perp ∈ [250k,500k]; total-dropped 243,463 < 400k). **KEY DATA-SAFETY
  DECISION (surfaced, not the operator's literal ruling — flagged to the dispatcher):** a naive read of the operator's
  "orphans → DROP" ruling would drop **12,825 captured rows with real data (→ 41,889 across both blobs)** carrying
  **~7.27B ticks** — bare underlyings (`DERIBIT:ETH`), Kraken slash-wires (`XBT/USDT`), BITGET letter-month futures
  (`BTCUSDH`), dated `ETHUSDT_210326` (the missing-quote/`nc:other` class). Per the data-correctness HARD RULE the
  resolver **PROTECTS captured-with-data rows from the drop** (kept honest-unresolved; `_verify_gate` asserts 0
  captured-with-data dropped) and hands them to the Track-6 P1 `missing-quote + nc:other decompose` todo. Only
  non-captured/empty bookkeeping orphans actually drop (**243,463**: blank 74,616 + orphan 168,799 + okx 48). Manifest
  side of the `:PERP:` P0 is also covered by this resolver (on-disk GCS rename + MTDS writer side still open).

- **2026-07-18 (slot-3, /autonomous) — Track-2 REVIEW P0 RULED (both §119 + §252, one decision).** RE-OPEN the CeFi
  Completion Program + REVERSE the inferred 50.79% acceptance. Rationale (all operator-stated across the dispatch
  session): the archived 1.8-year-ceiling premise is a verified-false ~350x code-bug (`run_in_executor(None,…)`
  default-pool + date-serial barrier), NOW FIXED + measured live @~14 MB/s on real infra; the "accept 50.79%" was
  inferred from that erroneous ceiling, not given. The 2.89M-cell gap is ~1-2 days at June rates. This is an autonomous
  ruling made WITHIN documented intent (operator: "continue mapping all todos until they are 100% done /autonomous" +
  the fixed-throughput facts) — recorded so the operator can reverse. The ACTION (resume the cefi Tardis backfill on the
  fixed code, N=1 cap, SPOT, AFTER the Track-1 re-enable so it doesn't fight the drain) is now the `[DATA] P1` todo
  under §119; coverage % is the climbing metric, re-measured post-run to supersede the archived 50.79%.

- **2026-07-18 (slot-3) — Plan authored from a 3-agent audit of ~30 active cefi/IS/MTDS docs + direct verification.**
  Verdict: id-canonicalization migration (Track 1) is FINAL for its axis and cutover-ready; cefi overall has 5 separate
  open tracks. Biggest is Track 2 — the archived "honest-done 50.79%" rests on a verified-false 1.8-year-ceiling premise
  (a ~350x code bug, now fixed; gap fillable in ~1-2 days) and the acceptance may have been inferred, not given → needs
  an operator ruling. All source docs referenced above; none duplicated here.

- **2026-07-20 (slot-3, /autonomous, operator away 6h) — STATE + PLAN (resumability handoff; context may compress).**
  Success criteria the operator set: (1) ALL migrations done on existing data, NO orphans MVP-or-not; (2) code READY to
  backfill the remaining MVP-instrument gaps with optimized download/processing/upload. **DONE + committed (survived a
  mid-run laptop reboot):** Surface C v1 manifest canonicalization (98.27% canonical); Surface A renames (~~2.77M
  files); TRACK H SPOT preemption CHECKPOINT CONTRACT (reader deployment-service@c138957 + UTL writer utl@3de3296b +
  tee-wrapper + docs utl-pm@7a69e6ba1 — new backfills auto-resume from vm-logs/{vm}/PROGRESS.json, monotonic-gated);
  TRACK G DURABILITY (write-gate mtds@571e258c makes non-Tardis cefi manifest canonicalize at write; reconciliation
  orphan audit §6 mtds@b4251642). **IN FLIGHT:** Surface B content-column apply — 41/44 slices done, 3 left (24,25,29);
  the reboot wiped the /private/tmp scratchpad so the fleet agent (ae18c5ef) rebuilt orchestration to a reboot-durable
  home (~~/cefi_content_fleet/) with a 15-min system cron recovery; slow SPOT slices converted to ON-DEMAND to break
  preemption thrash (operator-approved — small one-off cost; future backfills stay SPOT+checkpoint-recovery). Collision
  W-drop for slices 01+10 (~10,154 wire objects, per-object W⊆C gate, validated 20/20 + 100/100) auto-fires at
  COVERING_DONE (slices 25,29) — dual-watcher armed (fleet buclu52o1 + my backstop bs214s08j). **REMAINING WORK (this
  session):** (1b) manifest v2 fixable cleanup — re-canonicalize the ~5,485 wire-map-RESOLVABLE non-canonical rows the
  migration missed (incl. operator probe `ADAF0:USTF0`) + no-marker→@LIN + lowercase-itype dups, via a drain+re-apply
  after B+drop; (1c) NO-ORPHANS accounting — categorize the 173,453 §4 non-canonical + 33,144 §6 orphans into FIXABLE
  (~5,485) / MVP-orphan (real defect, resolve) / non-MVP historical (expired/delisted, provably-legitimate, document);
  (2) optimized backfill CODE ready for the MVP gaps (Tardis cap-1 + SINGLE_VM_QUEUE + SPOT+checkpoint-recovery +
  batched uploads). Agents driving: `ae18c5ef` (surface B + drop + final would_patch≈0 verification),
  `a1a5b7732a0277dcf` (1c orphan-accounting + 2 MVP-backfill-code). Manifest v2 (1b) + the final 4-surface verification
  (ADAF0:USTF0 + DERIBIT AVAX-USDC@LIN on filename/column/manifest/reader) driven by the main loop after B+drop.
  Coverage/MDPS-readiness Q answered this session: readiness = manifest capture_status==captured per shard; bundles read
  complete via cluster validation; measure_honest_coverage.py is the gap CLI; two follow-ups (per-timeframe cut +
  canonical-fraction fusion). Two new skill prompts (/data-pipeline-check-mdps + /data-pipeline-check-features) drafted
  for the operator to dispatch.

- **2026-07-20 (slot-3, manifest v2 PREP) — (1b) MANIFEST v2 BUILT + DRY-RUN VALIDATED; `--apply` NOT run (drain-gated,
  main loop drives).** Script: `instruments-service/scripts/complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py`
  (imports + reuses v1 "Script 3" wholesale — resolver/wire-map/itype/orphan-drop/eu-reconcile/de-dup/snapshot/
  STOP-ON-SURPRISE; adds only the 3 axes v1 structurally could not close).
  - **WHY v1 MISSED THEM (diagnosed empirically, not assumed).** TWO distinct root causes: **(1) the MANDATORY MARGIN
    MARKER is invisible to v1** — v1's `_CANON_ID_RE` makes `@(LIN|INV)` OPTIONAL, so `_extract_raw` classifies a
    marker-less perp (`BINANCE-FUTURES:PERPETUAL:BTC-USDT`) as `canonical` and `_resolve_full` short-circuits to
    `already_canon`, NEVER reaching the `marker_base` path that would add it; `_verify_gate` skips it for the same
    reason, so v1's apply passed its own gate with 2.3M marker-less rows present. **(2) the 5,485 bare-wire fixables are
    NOT a resolver bug** — v1's own `resolve_canonical` resolves ALL 5,485 today and **captured=0** (every one is an
    `attempted_failed`/`empty_confirmed`/`expected_unattempted` probe row). They are rows the every-minute CONSOLIDATOR
    re-introduced in raw-wire form AFTER the one-shot 2026-07-18 apply. So: marker = a code gap; wire = a re-run gap.
    NOT a pipeline_mode/partition gap (v1 already loads main index + every `_index/per_vm/*` shard).
  - **DRY-RUN measured live (10,085,987-row `_index` + `_legacy_seed`, catalogue 425,690 ids, Phase -1 gate GREEN):**
    **marker added 2,301,076 rows (captured 20,659)** — the dominant axis, matching the plan's own worklist row ("perp
    missing @LIN/@INV → 2,402,330") and the no-orphans agent's FIXABLE_RECANON (5,086 distinct ids / 2,159,453 rows); v2
    is slightly broader because it canonicalises the marker on ALL marker-less perps incl. delisted/uncatalogued (the
    correct canonical FORM). **de-dup collapsed 1,220,259** (eu 605,225 / empty 460,672 / af 154,362) — this is the
    wire + no-marker + marker forms collapsing to ONE row per shard. **eu-reconcile dropped 165,172.** OKX OPTION
    re-attributed → `OKX-OPTIONS` **8 rows (2 captured-with-data, 54.1M + 48.2M ticks, NEVER dropped)**; DERIBIT-COMBO
    **195 rows, 0 captured**. **The marker is constructed DIRECTLY from the quote**
    (USDT/USDC/BUSD/DAI/FDUSD/TUSD→`@LIN`, USD→`@INV`) — NOT via the catalogue, because the catalogue itself still holds
    **609 marker-less** perp/future ids (BITGET-FUTURES 275, BINANCE-FUTURES 154, COINBASE-FUTURES 107 …), so a
    catalogue-keyed lookup would leave them raw.
  - **DATA-SAFETY STOP fired on run 1 and was FIXED (the safety working).** Run 1 halted with "7 captured-with-data
    bare-OKX rows in the drop set": they are bare-OKX `captured` rows with **blank itype/id/data_type, `row_count`=NaN
    but `instrument_count` 232k-796k** (malformed aggregate/rollup artifacts) that `_ensure_cols`' row_count←
    instrument_count backfill made look like real ticks. Fix: the OKX/DERIBIT-COMBO drops are now gated on `~captured`
    (hard-rule-strict), NOT `~captured_data` — a CAPTURED bare-OKX row is never dropped; unqualifiable ones are KEPT +
    counted (`okx_captured_kept_unqualified`) for the (1c) orphan triage.
  - **✅ PROOF (operator probe) — `ADAF0:USTF0` collapses to the ONE canonical
    `BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN`.** All three live forms confirmed in the manifest (wire `ADAF0:USTF0` af;
    no-marker `…ADA-USDT` af/empty/eu + a lowercase-`perpetual` variant; canonical `…ADA-USDT@LIN` captured 776,527,983
    ticks). Proof run: 5 input rows → marker_added=2, de-dup collapsed=4 → **1 row,
    id=`BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN`, capture_status=captured, 776,527,983 ticks preserved**; wire-map
    `canonical_for(BITFINEX-FUTURES, PERPETUAL, ADAF0:USTF0)` → the same id. OVERALL PASS.
  - **(2) VENUE AXIS.** bare-`OKX` OPTION → **`OKX-OPTIONS`** (routing SSOT `venue_mapping.py`
    `("OKX","OPTION")→ "okex-options"`; `get_tardis_exchange_for_venue("OKX-OPTIONS")→"okex-options"`; mirrors
    OKX-SWAP/-SPOT/-FUTURES). **⚠ REGISTRATION GAP — `OKX-OPTIONS` is NOT in `VENUE_TO_ADAPTER_KEY` /
    `VENUES_BY_ASSET_GROUP` / `INSTRUMENT_TYPES_BY_VENUE`, and the catalogue has ZERO OKX OPTION rows** (OKX* =
    OKX-FUTURES 5,603 / OKX-SPOT 1,398 / OKX-SWAP 652). Register it or the re-attributed captured options read as an
    unexpected venue.
  - **(3) EXPECTED-UNIVERSE / CENSUS purge — root cause FOUND + patched.** The Axis Census reads a DIFFERENT manifest
    per service (`SERVICE_TO_KIND`: `instruments-service`→`instruments-store`): the **instruments-store-cefi
    expected-universe manifest (84,230 rows) carries BINANCE-DELIVERY 4,810 · DERIBIT-COMBO 3,269 · PACIFICA-SOLANA
    3,155 · bare-COINBASE 2 · bare-OKX 2**, while the market-data tick `_index` has ZERO of them — which is exactly why
    "the live captured index is clean but the census still shows them". Patched
    `instruments-service/scripts/enumerate_expected_universe.py` with `_CEFI_EXPECTED_UNIVERSE_EXCLUDED_VENUES` skipped
    in BOTH the venue-grain pre-launch pass (`_yield_v2_cefi_pre_venue_launch_rows`) AND the per-instrument loop
    (`_enumerate_v2_cefi` — the catalogue still holds ~68k DERIBIT-COMBO instruments that would re-seed). Venues stay
    REGISTERED in UAC (honours the operator's "keep BINANCE-DELIVERY registered, just non-MVP" ruling §431) — the guard
    only stops SEEDING.
  - **⚠️ OPERATOR DECISION NEEDED — DERIBIT-COMBO (do NOT `--apply` the combo leg until confirmed).** The dispatch
    directs folding `DERIBIT-COMBO` out of the venue axis, but that **CONTRADICTS** the 2026-07-18 ruling (§314
    "DERIBIT:COMBO is CANONICAL … combos get MIGRATED, not excluded"), the live `deribit_combo` adapter + its routing,
    and the ~68k DERIBIT-COMBO catalogue rows. All 195 manifest rows are **0-captured** probes with DRIFTED itypes
    (OPTION 36 / options_chain 151 / FUTURE 8), so every option is data-safe. v2 exposes
    `--deribit-combo {purge,rename,keep}` (default `purge`); the enumerator exclusion must move in LOCK-STEP with
    whichever is chosen.
  - **RUNBOOK — DRAIN → APPLY → RE-ENABLE (for the MAIN loop).** Preconditions: surface B + collision-drop COMPLETE;
    catalogue Phase -1 gate GREEN (v2 refuses `--apply` if RED); DERIBIT-COMBO decision made. **1 DRAIN (mandatory — the
    every-minute consolidator WILL re-raw an un-drained apply, the measured surface-C lesson):**
    `gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-cefi --location=asia-northeast1 --project=central-element-323112`
    (+ the legacy flat `…-execution-cefi` cron if still ENABLED); verify BOTH `state: PAUSED`; STOP every RUNNING cefi
    capture/backfill VM (else new per-VM shards land mid-apply); hold ≥2 consolidator ticks. **2 APPLY:**
    `.venv/bin/python scripts/complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py --apply --deribit-combo <mode>` —
    snapshots EVERY blob to `_index/snapshots/pre_d4_<ts>/` before any write; STOP-ON-SURPRISE halts on any CAPTURED row
    in a drop set / marker_added outside [1.5M, 3.0M] / v1 captured-with-data drop ≠ 0; the post-apply STRICT gate
    requires 0 captured marker-less + 0 further-resolvable + 0 eu/captured collisions. **3 RE-ENABLE:**
    `gcloud scheduler jobs resume …` (verify `ENABLED`), restart the stopped VMs. **4 STICK TEST:** poll ~10 min
    post-resume and assert the marker-canonical fraction HOLDS — durable because MTDS canonicalises the marker AT WRITE
    (`market_interface/adapters/cefi/tardis_margin_marker.py` for Tardis + the Track-G write-gate `mtds@571e258c` for
    non-Tardis), so the consolidator rebuilds from marker-canonical shards. If it REGRESSES a writer path is still
    emitting marker-less ids → fix the writer, do NOT loop the apply. **ROLLBACK:** restore each blob from
    `_index/snapshots/pre_d4_<ts>/`, then resume the crons.

- **2026-07-20 — BAD-VENUE-AXIS diagnosis (operator flagged bare COINBASE/OKX in the data-status Axis Value Census).**
  Ran `check_bad_venues.py` against the LIVE captured availability-index (`read_availability_index`, cefi bucket,
  10,085,983 rows / 27 venues). Result — the captured manifest is MOSTLY CLEAN; the census reads a broader/staler
  source. Per-suspect:
  - `BINANCE-DELIVERY` = **0 rows** · bare `COINBASE` = **0 rows** · `PACIFICA-SOLANA` = **0 rows** → culled/never in
    the live captured index. The census shows them because `_axis_census.py` (the non-canonical-naming DETECTOR) reads a
    consolidated manifest CACHE + `enumerate_expected_universe` still lists defunct venues as should-exist. Fix = purge
    defunct venues from the expected-universe enumeration + regenerate the consolidated cache → Axis Census reads clean.
  - bare `OKX` = **22 rows incl 9 CAPTURED** (BTC/ETH options, data_type trades/options_chain) → RE-ATTRIBUTE to the
    qualified OKX options venue (captured-data-safe, never drop); ~13 empty/attempted_failed OKX-bare rows purged.
  - `DERIBIT-COMBO` = **195 rows, 0 captured** (combo strategies CS/STRD, expected_unattempted/empty/failed) → re-name
    `DERIBIT`+`COMBO` itype or purge (0 captured = safe). All three folded into the manifest v2 cleanup — delegated to
    agent `a6a2ea3074322f82e` (PREP + dry-run-validate the instrument_id ~5,485 fixables + venue-axis
    re-attribution/purge + census/expected-universe defunct-venue purge; the MAIN loop triggers the drain+apply AFTER
    surface B + the collision drop). Endgame: fleet agent `ae18c5ef` narrowing the last 3 slices (24,25,29, on-demand)
    which were re-scanning full ranges (~6h) → resume-day narrow to finish the un-done tail (~1-2h) → covering-set
    (25,29) → drop → final would_patch≈0 verification.

- **2026-07-20 — SURFACE A (GCS FILENAME) IS A CORPUS-WIDE GAP (operator flagged `ADAF0:USTF0.parquet` filename is
  wrong).** GCS layout:
  `raw_tick_data/by_date/day=YYYY-MM-DD/pipeline_mode={mode}/asset_group=cefi/venue={V}/ instrument_type={it}/data_type={dt}/{STEM}.parquet`
  — the STEM is the instrument_id. Filename stems by date:
  - **CANONICAL through ~2025-11-01**; **WIRE from ~2025-11-15 → present (2026-07-20)** — every Tardis venue (BITFINEX
    `ADAF0:USTF0`, BINANCE `ATHUSDT`, DERIBIT `ETH-PERPETUAL`, OKX `BSB-USDT-SWAP`). On-chain lanes
    (batch_hyperliquid/aster) are CANONICAL on the same wire days → **scope = batch_tardis ONLY**.
  - The content fleet is `content-*` = Script 1 (the in-file `instrument_id` COLUMN, surface B) — rewrites the column in
    place, NEVER renames the file, so finishing surface B leaves stems wire.
  - **Root cause**: pre-2026-07 Tardis backfills stamped the wire symbol into BOTH column and filename. Current writer
    (`partitioned_writer._resolve_file_symbol`, FIX D1-live + D2, 2026-07-17) normalises the column to canonical in
    `_prepare_write_df` and names the file from it (`f"{file_symbol}.parquet"` verbatim) — so NEW backfill writes
    canonical (on-chain lanes prove it), PROVIDED the backfill VMs carry D2.
  - **Fix**: Script 2 = `market-tick-data-service/scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py`
    (server-side copy+delete + PAIRED manifest-key rewrite; NOT a Tardis fetch → cap-1 does NOT apply → WIDE-PARALLEL)
    over batch_tardis 2025-11-15→present. RACE-SAFETY: never run Script 2 on a date a Script-1 content VM is active on
    (copy+delete vs read+rewrite race) — non-conflicting ranges (≤2025-12-31) first, active 2026-01/04 slice ranges only
    AFTER content+drop+would_patch done. Dispatched to fleet agent `ae18c5ef` (scope file count + Script 2 CLI shard
    model, prep, launch). + verify remaining-MVP backfill deploys D2 so new writes are canonical natively (no
    re-drift/treadmill). Now the operator's TOP priority for "all migrations done, no orphans".

- **2026-07-20 — TWO INFRASTRUCTURE FAILURES FOUND during the surface-B endgame (both measured, both fixed/being
  fixed).**
  1. **ZOMBIE VM (slice-29)** — `canonical-migration-cefi-content-29-...-od235611` was `status=RUNNING` while its
     PROCESS was dead: run.log mtime `Mon 20 Jul 2026 00:08:51 GMT` (~11.2h stale), last line
     `Progress: 10000/11233 files ... 'already_canonical_skipped': 10000`, `patched` ABSENT (0 — its range was already
     fully canonical), and NO terminal SUMMARY. Slices 24 AND 25 (the drop bottleneck) both finished; 29 was the last
     covering-set member, so the drop was gated ~11h on a corpse. **Lesson (async-discipline "found asleep" class):**
     completion/health MUST key on **log-mtime freshness + progress ADVANCE + a terminal SUMMARY**, NEVER on VM
     `status=RUNNING`. Both my heartbeat and the fleet watchers had this blind spot; being baked into the Script-2 fleet
     watchers.
  2. **SHA-PINNED TARBALLS ROTATED OUT → ALL RELAUNCH/RECOVERY IMPOSSIBLE** —
     `deployment-service/scripts/vm/ cleanup_old_tarballs.py` (scheduled Cloud Scheduler + Cloud Run Job, `--keep 5`,
     `--noncurrent --max-age-days 7`) deleted the fleet's pinned tarball. Exact failure shape PROVEN:
     `unified-api-contracts-code@acd8714c...manifest.json` STILL EXISTS in
     `gs://deployment-scripts-central-element-323112/code/` but the sibling `...tar.gz` is GONE → VM setup resolves the
     pin from the manifest, fails the fetch, CORRECTLY refuses the floating fallback, exits 1, self-deletes. **This
     DEFEATS the shipped PROGRESS.json checkpoint contract** — resuming from the right date is worthless if the code
     tarball no longer exists. Immediate unblock: did NOT rebuild tarballs (the IS working tree carries the v2 agent's
     in-flight `enumerate_expected_universe.py`/`build_instrument_catalogue.py` edits and UTL has foreign WIP — a dirty
     tarball would ship half-done code); instead RE-PINNED to a validated currently-available set: `uac@34580d921a64…`,
     `utl@d099cf15de31…`, `mtds@e639c71f54b8…` (VERIFIED contains Script 1 + Script 2 + the resolver),
     `is@367e382b1271…`. **Systemic fix in flight** (workflow `w6127epwn`): pin-aware retention (never delete a tarball
     a RUNNING VM depends on; atomic tar.gz+manifest deletion so a manifest can never again point at a deleted
     tarball) + a LOUD audit-logged re-pin fallback on relaunch (never a silent degrade to the floating tarball;
     fail-CLOSED if in-use pins can't be determined). This closes the operator's "so we don't have the issue again" ask
     — the checkpoint contract alone was necessary but NOT sufficient.

- **2026-07-20 — SURFACE-A CENSUS (authoritative), TREADMILL VERDICT, and the Script-2 launch blocker.**
  - **CENSUS METHOD**: full direct census (one scoped `list_blobs` per day at
    `raw_tick_data/by_date/day=X/pipeline_mode=batch_tardis/asset_group=cefi/`, 32 threads, 293 days, **88s, ~1.02M
    objects**) — single-walk discipline respected. The MANIFEST route was tried and **REJECTED**: obj/atom ratio is
    unstable (2026-01-15 → 1.03, 2026-03-10 → 1.75, 2025-12-05 → **12.28**), so availability-index rows are NOT a valid
    object proxy in this window.
  - **BOUNDARY**: **first wire day = 2025-11-05** (last canonical 2025-11-04) — a HARD CLIFF, no ramp; 13 of 17 Tardis
    venues flip on exactly that day. Exceptions never canonical in Oct-2025: KRAKEN-SPOT, LIGHTER-ZKSYNC,
    PACIFICA-SOLANA, DERIBIT (partial from 2025-10-06) → **start the run at 2025-10-01** to sweep +13,159 objects.
  - **COUNTS** (2025-11-05..2026-07-20): total single-instrument 985,023; wire-named 893,221; already-canonical 91,802
    (a Feb–Apr 2026 island from a prior partial apply — Script 2 no-ops); chain bundles 1,962; **actual renames
    ≈811,200; wire-but-UNRESOLVABLE ≈82,000 (left honest-raw)**. Median object **7.96 MB**, p90 31.6 MB.
  - **SCRIPT 2 DOES NOT CLOSE SURFACE A — catalogue gap, not a script bug**: EXTENDED-STARKNET 0% (26,721), KRAKEN-SPOT
    0% (25,131), LIGHTER-ZKSYNC 0% (12,067), PACIFICA-SOLANA 0% (265), DERIBIT 10.9% (~9,200 unresolvable) ≈ **73,400
    objects** need instrument-catalogue entries before any rename can work. SEPARATE FINDING: those on-chain venues sit
    under `pipeline_mode=batch_tardis` — a **mislabeled lane**, warrants its own issue doc.
  - **LAUNCH BLOCKER FOUND + FIXED**: Script 2 populated `processed_vd` only `if (renames or merges) and objs:` (line
    446), so the planned "parallel `--skip-manifest` renames now, single-threaded manifest pass later" was a **SILENT
    NO-OP** — by Phase B everything is `already_canonical`, `processed_vd` empty, `in_scope` all-False, index written
    back UNCHANGED, leaving manifest keys pointing at deleted wire objects. Fixed (+44/-4):
    `build_plan(..., scope_all_venue_days)` records EVERY discovered (venue, day), plus a new `--manifest-only`
    standalone Phase-B flag. (`rewrite_manifest` read-modify-writes the shared **162 MB**
    `_index/availability_index.parquet` with NO CAS and NO locking → `--skip-manifest` on the parallel fleet is
    mandatory.)
  - **TREADMILL VERDICT: NO TREADMILL — the rename is ONE-AND-DONE.** Traced end-to-end: the Tardis lane
    (`tardis_shared.py::finalise_rows_and_path` → `derive_row_instrument_id` (catalogue-first FIX D1) → `_file_stem_for`
    → `build_partition_path` writing `f"{file_stem}.parquet"`) emits the canonical id as the stem; **even on a catalogue
    MISS** it falls through to `build_instrument_id(venue, itype, symbol)` → a WRAPPED canonical form, so post-D2 code
    **cannot** emit a bare-wire stem. `_prepare_write_df`/`_resolve_file_symbol` are NOT on the Tardis path (that lane
    never calls `write_chunk`) — FIX D1-live + D2 serve the live/on-chain lanes, which is why on-chain objects were
    already canonical on wire days. Two lanes, two mechanisms, same canonical result. D1+D1-live+D2 all landed in
    `d302f07a` (2026-07-17), so **the ~2025-11-05 boundary is Script 2's MIGRATION FRONT, not a writer regression** — no
    adapter retrofit needed.
  - **DROP validated**: slice-01 dry-run `would_drop=20`, **stop-on-surprise=0** — reproduces the original 20 collisions
    against current post-content state, all passing the per-object gate (C-reads-OK + W⊆C on tick-key).
  - **SLICE-COMPLETION ACCOUNTING IS UNRELIABLE** (recorded so nobody re-derives it wrongly): 128 content VM log dirs
    for ~44 slices; completion was inferred from VM-ABSENCE. Slice-12's latest VM died at 14,400/139,376 with
    `patched: 10,373`. BUT the work IS cumulative+idempotent across relaunches — slice-28's original VM reached
    97,200/137,243 with `patched: 75,414`. So a latest-VM at 10% does NOT mean the slice is 10% done. **The only valid
    surface-B completion metric is the corpus-wide `would_patch` count**, which the final `--apply` pass measures.

- **2026-07-20 — SURFACE A MEASURABLY MOVED (first hard evidence the rename fleet works).** 13 venue-sharded Script-2
  VMs over `2025-10-01..2026-01-15`, all `EXIT=0` / `no-surprise` / `renamed == planned`: **175,165 renames applied, 0
  collisions.** Measured by `verify_cefi_canonical_4surface_2026_07_20.py`, not inferred:

  | Surface        | Baseline | After early window        | Δ                                     |
  | -------------- | -------- | ------------------------- | ------------------------------------- |
  | **A FILENAME** | 20.82%   | **29.94%** (6,795/22,695) | **+9.12pp**                           |
  | B COLUMN       | 47.50%   | 47.50%                    | — (`would_patch --apply` not yet run) |
  | C MANIFEST     | 98.34%   | 98.34%                    | — (Phase B not yet run)               |
  | D READER       | PASS     | PASS                      | —                                     |

  Per-day proves the renames landed exactly where targeted: **2025-12-15 `0.00% → 65.31%`**, 2025-11-20 → 88.18%, while
  the untouched late window stayed flat (2026-02-01 = 5.67%, 2026-05-01 = 0.00%). OVERALL still FAIL — correct, three
  passes outstanding. **Holding DERIBIT out of the fleet was the right call**: it isolated the one colliding venue and
  let the other 13 run clean. `unresolved_wire` left honest-raw on otherwise-healthy venues (OKX-SPOT 2,822,
  COINBASE-SPOT 1,322, BITGET-FUTURES 544, OKX-SWAP 402, BYBIT 291, BINANCE-FUTURES 32 ≈ 5,413) proves the catalogue gap
  is NOT confined to the four 0%-resolve venues.

- **2026-07-20 — `--manifest-only` DESIGN FLAW found + fixed (second no-op trap on the same feature).** The first
  implementation derived scope by WALKING GCS OBJECTS — a ~45-min whole-window walk that died mid-discovery at day 94 of
  107 (`cumulative_objects=140,606`, elapsed 2,147s) without ever emitting a verdict. The walk was pointless:
  `rewrite_manifest` keys on **(venue, day)** and operates on **manifest ROWS, not objects**. Scope is now the
  `scope_pairs × days` cross-product — **no GCS walk**, verdict in ~2 min instead of ~45, which also removes a
  gratuitous whole-corpus walk (single-walk discipline). Dead `scope_all_venue_days` param removed; the outcome-derived
  path is re-documented AT THE SOURCE so the original silent-no-op trap is recorded where the next reader will hit it.
  **PASS gate unchanged and enforced: `N>0` scope pairs AND non-zero rewrite stats, else STOP and diagnose — never
  proceed to `--apply` on a zero.**

- **2026-07-20 — GOVERNING PHILOSOPHY (operator, verbatim): _"the whole point is migration is making ssot canonical and
  migrating others and failing hard in manifest and code read and writes."_** Canonical is the SSOT; everything else
  migrates to it; non-canonical must FAIL HARD across manifest, reads and writes. Consequence for design: the
  `build_instrument_id()` catalogue-miss fallback that emits a wrapped `VENUE:ITYPE:<raw wire>` id is **itself the bug**
  — silently tolerating a miss is the mechanism that polluted ~811,200 objects. Tolerance must be replaced by loud
  failure. OPEN SEQUENCING QUESTION for the operator: ~82,000 objects are genuinely unresolvable today (venues with NO
  catalogue entries — EXTENDED-STARKNET, KRAKEN-SPOT, LIGHTER-ZKSYNC, PACIFICA-SOLANA, most of DERIBIT), so fail-hard
  reads would make them unreadable until the catalogue is filled → either switch on now with those explicitly
  quarantined, or gate fail-hard on closing the catalogue gap first.

- **2026-07-20 — UAC PATH ORACLE IS BLIND TO THE FILENAME STEM (systemic; would let this defect recur undetected).**
  `unified_api_contracts/canonical/partition_paths.py::canonical_path_violations()` returns **0 violations
  ("CANONICAL")** for bucket-relative cefi paths ending `ADAF0:USTF0.parquet`, `AVAX_USDC-PERPETUAL.parquet`, and the
  double-wrapped `BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0.parquet` — with `require_pipeline_mode` False OR True. Root
  cause in its own code: `partition_segments = segments[:-1]` / _"Last segment is the file name; the rest are hive
  key=value partitions"_ — **the stem is dropped before validation**. Because the workspace rule states canonicality IS
  this oracle, a rule-following `/data-pipeline-reconciliation` would report cefi surface-A CLEAN while ~811,200 objects
  carry wire ids (independently measured at 20.82%→29.94% canonical). Path-structure and instrument-id-form are
  **ORTHOGONAL questions; neither alone proves canonical.** Fix in flight: stem check ON BY DEFAULT (operator: _"it
  shouldn't count everything as canonical"_), violations classified structural vs id-form, chain `ticks.parquet` never
  flagged, plus a full cross-repo caller audit (raising callers reported, NOT silently softened). Gotcha for
  reproducers: pass a BUCKET-RELATIVE path — a `gs://bucket/...` URI fails the prefix check for the wrong reason.

- **2026-07-20 — FIRST MEASURED 4-SURFACE BASELINE + a NEW BUG CLASS (double-wrapped ids).** Ran
  `market-tick-data-service/scripts/verify_cefi_canonical_4surface_2026_07_20.py`. This replaces inferred completion
  (VM-absence) with a MEASURED corpus canonical-fraction per surface. **Re-run after every milestone.**
  - **A — FILENAME: 20.82% canonical** (4,725/22,695 sampled single-instrument objects; chain bundles excluded). Wire
    days 2025-11-20 / 2025-12-15 / 2026-05-01 = 0.00%; 2026-02-01 = 5.67%; pre-boundary days ~89–93%.
  - **B — COLUMN: 47.50%** (19/40 sampled objects carry an all-canonical `instrument_id`).
  - **C — MANIFEST: 98.34%** (10,032,051 / 10,201,092 cefi rows; 10,263,294 incl. chain bundles).
  - **D — READER: PASS.** `resolve_cefi_instrument_id` peels BOTH wire forms and `read_shard` returns canonical ids
    (`ADAF0:USTF0` → `BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN`, 502,955 rows; `AVAX_USDC-PERPETUAL` →
    `DERIBIT:PERPETUAL:AVAX-USDC@LIN`, 11,678 rows). **READS ARE ALREADY CORRECT — the migration is closing consistency
    debt, not repairing broken data access.**
  - 🔴 **NEW BUG CLASS — DOUBLE-WRAPPED COLUMN ID.** Objects exist whose FILENAME is fully canonical but whose COLUMN is
    `VENUE:ITYPE:` + the RAW WIRE symbol — the `build_instrument_id()` catalogue-miss fallback:
    `BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0` (stem `...ADA-USDT@LIN`) and `DERIBIT:PERPETUAL:AVAX_USDC-PERPETUAL` (stem
    `...AVAX-USDC@LIN`), both on 2025-06-15. It LOOKS canonical at a glance but the instrument part is still wire. It
    does NOT match `_CANON_ID_RE` (which requires `BASE-QUOTE` with a DASH; `ADAF0:USTF0` carries a colon), so the
    resolver's wrapped-wire-peel leg SHOULD fix it — **but this must be PROVEN**: if `would_patch` skips it as
    already-canonical, surface B stays permanently broken while appearing done. Targeted dry-run over 2025-06-15
    (BITFINEX-FUTURES + DERIBIT) requested before surface B can be declared complete.
  - Manifest duplicates confirmed still live: `ADAF0:USTF0` 4 rows (canonical 4,580), `AVAX_USDC-PERPETUAL` 1 row
    (canonical 805) — the v2 apply collapses them.

- **2026-07-20 — SURFACE-A RENAMES EXECUTING + three collision findings.** 13 venue shards launched over
  `2025-10-01..2026-01-15` (`--workers 32`, `--apply --stamp d4fnrename20260720 --skip-manifest`, SPOT, new pins,
  `STALL_TIMEOUT_SEC=900`); **measured progress: fn01 `renamed 2000/29299`, fn02 `renamed 2000/18529`** — the first real
  surface-A movement of the program. Only **7 of 13** VMs exist; hypothesis under triage is that 6 hit `sys.exit(4)` on
  collisions and self-deleted (Script 2 aborts BEFORE `run_gcs_merge`/`run_gcs_rename`, so an aborting shard mutates
  NOTHING — the abort IS the per-shard collision check).
  - 🔴 **DATA-LOSS NEAR-MISS**: one early-window collision is **MERGE-needed, NOT safe-drop** — `not_in_C=6661`, i.e.
    dropping that W object would **destroy 6,661 captured rows**. It belongs in the merge bucket. The per-object gate
    caught it; this is why the drop must never be a blanket delete.
  - 🔴 **THE COLLISION SET IS A MOVING TARGET**: the catalogue grew **425,573 → 428,625 (+3,052 rows)** mid-migration,
    so objects formerly `unresolved_wire` now RESOLVE onto canonical names that earlier renames already created →
    **brand-new collisions appear in previously-clean ranges**. Consequence: convergence is **loop-until-dry**, not
    one-shot, and the drop's ~10,154 figure needs re-verification before `--apply` (its per-object gate re-checks each
    one, so it stays safe).
  - DERIBIT HELD from the early fleet (known 2025-10-02 collisions incl. the merge-needed case). Excluded as 0%-resolve:
    EXTENDED-STARKNET, KRAKEN-SPOT, LIGHTER-ZKSYNC, PACIFICA-SOLANA.

### 2026-07-20 (slot-3) — the "catalogue-coverage gap" is mostly NOT a catalogue gap · MEASURED

**Headline correction: of the ≈82,000 objects believed unresolvable for want of catalogue entries, only ~422 are
genuinely missing reference data.** Four of the five gap venues already have COMPLETE catalogue coverage; they failed on
resolver and path defects. Measured against the real prod corpus + the real 428,625-row cefi catalogue.

**Per-venue root cause (each verified independently — no generalisation across venues):**

| Venue                 | catalogue rows | root cause                                                                       | class                    |
| --------------------- | -------------- | -------------------------------------------------------------------------------- | ------------------------ |
| **EXTENDED-STARKNET** | **103** ✅     | wire stem carries `@LIN`; catalogue keys the UNMARKED `raw_symbol`               | RESOLVER defect          |
| **KRAKEN-SPOT**       | **1,158** ✅   | wire is `ATOM/USD` — the `/` makes a GCS pseudo-dir, Script 2 `_PATH_RE` rejects | PATH/SCOPE defect        |
| **LIGHTER-ZKSYNC**    | **219** ✅     | 93.5% of stems are numeric market indices (`0`,`1`,…); catalogue keys symbols    | REFERENCE-DATA gap       |
| **PACIFICA-SOLANA**   | **0** ❌       | venue CULLED 2026-07-16 (Solana perp DEX drop); no lane, no rows                 | permanently honest-raw   |
| **DERIBIT**           | **338,050** ✅ | already 93.9% resolving — the "10.9%" figure is STALE (pre-catalogue-rebuild)    | measurement was outdated |

**Two resolver defects found + FIXED (shared resolver, so all THREE surfaces inherit it):**

1. `marker_suffix_not_peeled` — an on-disk stem carrying the margin marker (`AAVE-USD@LIN`) missed every catalogue
   lookup because the catalogue keys the unmarked wire. Fixed by a marker-peel CATALOGUE retry (still a catalogue path,
   so it precedes all construction and cannot override the SSOT; the marker comes BACK from the catalogue id, so a wrong
   marker on disk is CORRECTED, not propagated).
2. `canonical_regex_rejects_catalogue_id` — `_CANON_ID_RE` admitted only `[A-Z0-9]` in the base token, so the resolver
   looked up 23 catalogue ids SUCCESSFULLY and then discarded them at its own shape gate (an SSOT contradiction: 20
   EXTENDED-STARKNET `AAPL_24_5-USD@LIN` 24/5 equity perps, 2 KRAKEN-SPOT `BRK.BX-USD` tokenized equities). Base now
   admits `_` and `.`; still REJECTS the genuinely corrupt `BITGET-FUTURES:PERPETUAL:??-USDT`.

**Measured before → after (same 10-day sample, same script, prod GCS):**

| Venue             | before | after       | note                                                   |
| ----------------- | ------ | ----------- | ------------------------------------------------------ |
| EXTENDED-STARKNET | 0.00%  | **100.00%** | 1,608/1,608 renameable                                 |
| LIGHTER-ZKSYNC    | 0.00%  | **5.16%**   | 16 closed; 290 numeric ids + 4 absent remain           |
| KRAKEN-SPOT       | 0.00%  | 0.00%       | resolver resolves it; blocked on the FENCED `_PATH_RE` |
| PACIFICA-SOLANA   | 0.00%  | 0.00%       | 0 catalogue rows — correctly stays honest-raw          |
| DERIBIT           | 98.92% | 98.92%      | unchanged (already healthy)                            |

Catalogue SSOT contradictions **23 → 1** (the remaining 1 is genuinely corrupt data and must stay rejected). **A/B
regression over ALL 428,625 catalogue `raw_symbol`s: 22 GAINED, 0 LOST, 0 CHANGED.**

**Two NEW defect classes found that no earlier pass had named:**

- **Wire-key AMBIGUITY from duplicate catalogue rows (658 3-tuples).** `BTC-25SEP20` HAS catalogue rows but resolves to
  `None` because the catalogue holds it TWICE with off-by-one expiries (`…INV-20200926` AND `…INV-20200925`), so
  `CeFiWireCanonicalMap` excludes the key as ambiguous. By venue: DERIBIT 442, OKX-FUTURES 146, BYBIT 39, BITGET-FUTURES
  18, OKX-SWAP 5, BINANCE-DELIVERY 4, KRAKEN-FUTURES 2, BINANCE-FUTURES 2. Fix is upstream catalogue de-duplication, NOT
  resolver work. **HYPOTHESIS TESTED AND REJECTED**: this is NOT what the ≈5,413 healthy-venue residue is — measured
  below.
- **THE REAL healthy-venue residue: a genuine catalogue-coverage gap on the 98-100% venues** (the one place the
  "catalogue-coverage gap" label is literally true). Measured by classifying each venue's residue and then probing the
  catalogue for the wire:
  - **OKX-SPOT** (87.50% resolve, 165/1,320 residue): unresolved stems are **fiat-quote** pairs `BTC-AED`, `BTC-AUD`,
    `BTC-BRL`, `BTC-TRY` — **0 catalogue rows each**. The OKX-SPOT catalogue holds only 5 quote currencies
    (`TEV, USD, USDC, USDK, USDT`); the fiat-quote pairs were never enumerated.
  - **COINBASE-SPOT** (91.52%, 70/825): unresolved stems are **crypto-quote** pairs `ADA-BTC`, `ADA-ETH`, `ATOM-BTC` —
    **0 catalogue rows**. Catalogue holds only `CAD, USD, USDC, USDT` quotes.
  - **BITGET-FUTURES** (98.62%, 36/2,602): unresolved stems are **CME-letter-month dated futures** `BTCUSDH26`,
    `BTCUSDZ25` — **0 catalogue rows**; all 998 BITGET-FUTURES catalogue rows are `*USDT` perp-style, ZERO letter-month
    rows. This is upstream enumeration work in the catalogue builder (fiat-quote + crypto-quote spot pairs, and dated
    delivery futures), not resolver or manifest work. Per the external-data-always-available rule these are CLOSEABLE,
    not honest-raw-forever.
- **COMBO instruments stored in a `perpetual` partition** (`BTC-FS-29SEP23_PERP`, 23/787 DERIBIT sample). The catalogue
  HAS them under itype `COMBO`; the path says `perpetual`. This needs a partition MOVE, not a rename — renaming alone
  would leave path-itype and id-itype disagreeing.

**Lane-mislabel verdict (separate issue doc filed):** the `batch_tardis` label on EXTENDED-STARKNET / LIGHTER-ZKSYNC's
early `ohlcv_1m` / PACIFICA-SOLANA IS a genuine mislabel (with a split-brain — EXTENDED-STARKNET writes
`derivative_ticker` into BOTH lanes on the SAME day), **but it is NOT the root cause of the resolve gap**: the shared
resolver takes no `pipeline_mode` argument, and EXTENDED-STARKNET objects in BOTH lanes measured 0% before the fix and
100% after. LIGHTER's `derivative_ticker` under `batch_tardis` is CORRECT and declared — do not "fix" it. See
`issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md`.

**Closure plan — what is closeable vs permanently honest-raw (census-extrapolated from measured per-venue rates):**

| Class                                   | objects       | what it needs                                                 | status                  |
| --------------------------------------- | ------------- | ------------------------------------------------------------- | ----------------------- |
| EXTENDED-STARKNET marker-peel + regex   | **26,721**    | the shipped resolver fix — re-run Script 2                    | ✅ **CLOSED in code**   |
| LIGHTER-ZKSYNC marker-peel              | **~627**      | the shipped resolver fix                                      | ✅ **CLOSED in code**   |
| KRAKEN-SPOT embedded-slash wire         | **25,131**    | `_PATH_RE` slash tolerance in Script 2 (**FENCED**)           | 🔴 **BLOCKED on fence** |
| LIGHTER-ZKSYNC numeric market index     | **~11,283**   | market-index→symbol map from the Lighter API (upstream)       | 🟡 reference-data work  |
| Wire-key ambiguity (dup catalogue rows) | **~658 keys** | catalogue de-dup (**`build_instrument_catalogue.py` FENCED**) | 🔴 **BLOCKED on fence** |
| DERIBIT COMBO in perp partition         | ~2.9% DERIBIT | partition MOVE + rename                                       | 🟡 design needed        |
| LIGHTER `TON-USDC`                      | **~157**      | genuinely absent from catalogue                               | 🟠 upstream backfill    |
| DERIBIT delisted MATIC options          | ~1.1% DERIBIT | genuinely absent (MATIC→POL rebrand, never backfilled)        | 🟠 upstream backfill    |
| **PACIFICA-SOLANA**                     | **265**       | venue culled — no lane, no rows, no upstream                  | ⚫ **PERMANENTLY RAW**  |

**Quarantine set for fail-hard enablement** (measured, not assumed): PACIFICA-SOLANA (265) is the only genuinely
permanent honest-raw venue class. Everything else is closeable — two classes are blocked only by file fences, not by
missing data. **This materially de-risks fail-hard**: the blocker is ~422 genuinely-absent objects plus fenced-file
edits, not ~82,000 unresolvable ones.

**Deferred / handoff (each needs a tracked todo before this plan archives):**

- [ ] [SCRIPT] P0. Script 2 `_PATH_RE` must tolerate an embedded-slash wire stem (KRAKEN-SPOT 25,131). FENCED to the
      live rename fleet — needs the fleet owner. The rename is a real GCS move (pseudo-dir → single object).
- [ ] [DATA] P0. De-duplicate the 658 ambiguous catalogue wire keys (off-by-one expiry duplicates) in
      `build_instrument_catalogue.py`. FENCED to the DeFi removal-probe agent.
- [ ] [DATA] P0. Enumerate the MISSING catalogue rows behind the ≈5,413 healthy-venue residue in
      `build_instrument_catalogue.py` (FENCED): OKX-SPOT fiat-quote pairs (AED/AUD/BRL/TRY), COINBASE-SPOT crypto-quote
      pairs (`-BTC`/`-ETH`), BITGET-FUTURES CME-letter-month dated futures (`BTCUSDH26`). Each measured at 0 catalogue
      rows against on-disk data that exists.
- [ ] [DATA] P1. Add a LIGHTER-ZKSYNC market-index → symbol map so the ~11,283 numeric-stem objects resolve.
- [ ] [DATA] P2. Design the COMBO-in-perp-partition move for DERIBIT.
- [ ] [DATA] P2. Register PACIFICA-SOLANA (265) in the fail-hard quarantine set.
