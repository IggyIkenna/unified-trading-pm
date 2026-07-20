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
