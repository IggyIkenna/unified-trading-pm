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
  ]
created: 2026-07-18
last_updated: "2026-07-24"
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

### Checkpoint cadence — `data-pipeline-check-is` / `data-pipeline-check-mtds` (brackets the Track-2 backfill)

Per `task_template.md` §3 finding K, this plan needs 3 distinct DATED run checkpoints per skill; cefi has zero genuine
RUN todos for either today (the DOCS todo above only upgraded the `-mtds` skill's own test coverage, it never ran it).

- [ ] [DATA] P1. Run `/data-pipeline-check-is` for cefi as the PRE-BACKFILL BASELINE, before the Track-2 coverage
      backfill resumes. Definition of done: cite the report path + run date in this plan's Progress Log.
- [ ] [DATA] P1. Run `/data-pipeline-check-is` for cefi as the MID-BACKFILL SPOT-CHECK, partway through the Track-2
      coverage backfill. Definition of done: cite the report path + run date in this plan's Progress Log.
- [ ] [DATA] P1. Run `/data-pipeline-check-is` for cefi as the POST-BACKFILL FINAL GATE, after the Track-2 coverage
      backfill completes. Definition of done: cite the report path + run date, plus a PASS verdict for every MVP
      (asset_group, venue) shard, in this plan's Progress Log.
- [ ] [DATA] P1. Run `/data-pipeline-check-mtds` for cefi as the PRE-BACKFILL BASELINE, before the Track-2 coverage
      backfill resumes (a real dated run, distinct from the skill-upgrade todo above). Definition of done: cite the
      report path + run date in this plan's Progress Log.
- [ ] [DATA] P1. Run `/data-pipeline-check-mtds` for cefi as the MID-BACKFILL SPOT-CHECK, partway through the Track-2
      coverage backfill. Definition of done: cite the report path + run date in this plan's Progress Log.
- [ ] [DATA] P1. Run `/data-pipeline-check-mtds` for cefi as the POST-BACKFILL FINAL GATE, after the Track-2 coverage
      backfill completes. Definition of done: cite the report path + run date, plus a PASS verdict (0 false
      `attempted_failed`, every MVP shard genuinely captured-vs-skipped), in this plan's Progress Log.

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

- [ ] [BACKEND] P2. **Resolve the `*_ccxt.py`/`*_native.py` parallel-file question for BINANCE/BYBIT/OKX** — audit
      `instruments-service/.../adapters/cefi/tardis/`, MTDS's `.../adapters/cefi/`, and every cefi venue file in
      `execution-service/.../trade_execution/adapters/` for dead code, stale fallback paths, and duplicate logic: is
      each `*_ccxt.py`/`*_native.py` pair genuinely both live-routed by design (e.g. ccxt for one operation, native for
      another), or is one file in the pair dead code nothing calls? Cite
      `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`. Definition of done: a written per-venue
      verdict (both-live-with-reason, or one-dead-then-deleted-no-shim) for binance/bybit/okx, recorded in this plan's
      Progress Log or a new issue doc.

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
- `issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md` —
  `deribit_volatility_index_handler.py` and `book_microstructure_handler.py` stamp `available_at` from BATCH-run
  wall-clock instead of an already-computed deterministic per-row/`as_of` timestamp (same defect class as the resolved
  DeFi `available_at` clobber bug — breaks ε=0 on re-run/replay). Prediction's adapters and cefi's primary
  `ccxt_adapter.py` path already do this correctly, no gap there. Audit-only finding, code fix not yet started.

- [ ] [DATA] P3. Sweep for any non-Tardis cefi VM class with multi-hour+ single-VM runtime that is not already
      cross-machine-sharded (Tardis-consuming VMs are EXEMPT — they carry their own hard concurrency cap of 1, see
      `/codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap). Definition of done: a list of every non-Tardis
      cefi VM class with its measured typical runtime, a PASS/FAIL verdict per class against the "shard across machines
      once multi-hour+" bar, and a follow-up todo filed for each FAIL, recorded in this plan's Progress Log.

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
- [ ] [BACKEND] P1. **AUDIT the UAC per-venue seed fallback's blast radius (surfaced by the fail-loud work; distinct
      from the wholesale absent-catalogue fallback already removed in MTDS)** — restructured 2026-07-24 from an
      open-ended "decide + remove if..." judgment call per `task_template.md` §3's bounded-outcome rule: the actual
      go/no-go call needs a blast-radius fact this file doesn't have, so this todo gathers that fact; the decision
      itself is the separate `[OPERATOR]` todo below.
      `unified_api_contracts.registry.market_data_categories.get_expected_instruments_for_venue` STILL falls back to the
      per-venue MVP seed when `instruments_provider` is None / a PRESENT catalogue lacks a specific venue
      (`market_data_categories.py:2250` + `registry/defi_prediction_instrument_seeds.py`). Enumerate every caller of
      `get_expected_instruments_for_venue` fleet-wide and record, per caller, whether it depends on the fallback firing
      in the present-catalogue-missing-venue case (i.e., would silently regress if the fallback were removed).
      Definition of done: a written caller list with a safe-to-remove/blocks-removal verdict per caller, recorded in
      this plan's Progress Log or a new issue doc. Also register Tardis error codes in `classify_venue_error` + land the
      REQUEST-side vendor-catalogue gating (preflight shouldn't generate cefi `futures_chain` shards →
      `expected_unattempted`) — both belong in the in-flight UAC `coverage_exclusions` work. (repo:
      unified-api-contracts)
- [ ] [OPERATOR] P1. **Decide whether to remove the UAC per-venue seed fallback**, using the audit todo above's
      blast-radius findings. The operator's "catalogues should be the sole source" ruling (already applied to the
      wholesale MTDS fallback removal) points toward removal, but this is a UAC change with fleet-wide blast radius — an
      operator/interactive call on acceptable risk, not a background-dispatchable decision. Definition of done: the
      ruling recorded in this plan's Progress Log, then executed as a follow-up todo if the ruling is "remove". (repo:
      unified-api-contracts)
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
      97.49%). (repo: instruments-service) **✅ CASING FREEZE LIFTED 2026-07-20 (operator ruling D1 — UPPERCASE column
      ratified).** The itype-casing leg of this script is now the ratified direction, so the D1 _casing_ freeze on the
      `--apply` is lifted. **This does NOT mean run it now**: the `--apply` also sits behind the SEPARATE, still-live
      Track-1 operational drain gate (consolidator pause / pre-migration drain). Ruling recorded in
      `plans/active/data_pipeline_reconciliation_skill_2026_07_20.md` § D1.
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

- [ ] [DATA] P1. **Enumeration-audit terminal checkpoint** — re-run
      `scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py` (the distinct-values census tool cited above)
      against the live cefi manifest, once the Track-1 cutover drain-gate lifts and
      `complete_cefi_manifest_canonical_dedup_2026_07_17.py --apply` actually runs. Definition of done: the census
      returns 0 non-canonical rows across instrument_id/instrument_type/venue/data_type, or every remaining non-zero
      count is an explicitly-accepted exception already ruled on in this plan (e.g. the genuinely-unresolvable residual
      under the bare-wire / missing-quote / DATED-contract recovery item above) — record the final counts in this plan's
      Progress Log. (repo: market-tick-data-service)

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
    MVP). Clean the STALE `/codex/02-data/mvp-scope-canonical.md` PACIFICA-as-MVP bolding.
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

| Venue(s)                                                                                                                                                                               | Codex MVP status                                                                                                                                | Wired status (this plan's evidence)                                                                                                                                                                                                                                                                                                           |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BINANCE-SPOT/-FUTURES, BYBIT(/-SPOT), OKX-SPOT/-SWAP/-FUTURES, DERIBIT, HYPERLIQUID, ASTER, KRAKEN-SPOT/-FUTURES, COINBASE-SPOT/-FUTURES, BITFINEX-SPOT/-FUTURES, BITGET-SPOT/-FUTURES | MVP                                                                                                                                             | **PROVEN WIRED** — real captured rows throughout the 11.19M-row cefi manifest (representative ids + row counts cited across this plan, e.g. the Surface-C re-measure's BITFINEX-FUTURES/DERIBIT canonical-vs-duplicate counts); KRAKEN-SPOT independently re-verified fully clean 2026-07-23                                                  |
| EXTENDED-STARKNET                                                                                                                                                                      | MVP                                                                                                                                             | **PROVEN WIRED** — "live MVP" per the CEFI CANONICAL SPEC + Operator dispositions sections                                                                                                                                                                                                                                                    |
| LIGHTER-ZKSYNC                                                                                                                                                                         | MVP                                                                                                                                             | **PARTIAL** — scaffold + real captured data exist (~11,283 raw objects, mostly bare numeric market-index stems); resolver code shipped (`mtds@8835b899`); live capture is BLOCKED-CREDENTIALS (external-data-always-available scaffold rule) and the canonical-rename backfill of the existing objects has not run yet (Deferred-work item 6) |
| UPBIT                                                                                                                                                                                  | MVP                                                                                                                                             | **NOT EVIDENCED anywhere in this plan's audit trail** — see the new todo below                                                                                                                                                                                                                                                                |
| BINANCE-DELIVERY                                                                                                                                                                       | **NOT MVP** (COIN-M inverse/delivery, decision #3)                                                                                              | Registered/kept in UAC (not purged) with real historical captured data, but explicitly descoped from MVP backfill going forward — do not re-add to MVP scope                                                                                                                                                                                  |
| KALSHI-PERP, POLYMARKET-PERP                                                                                                                                                           | **NOT in the codex CeFi MVP table today** — this plan's "roadmap, will be added" framing is a future-scope declaration, not a current MVP grant | **NOT WIRED** — verified 2026-07-18: 100% `empty_confirmed`, `row_count=0`, `instrument_count=0`; kept registered purely for the roadmap                                                                                                                                                                                                      |
| BITSTAMP-SPOT, HUOBI-SPOT/-FUTURES, GEMINI-SPOT, PHEMEX-SPOT (defunct); Solana-perp cull (DRIFT/PACIFICA/MANGO/ZETA/FLASH/SOLAYER/PICASSO/CAMBRIAN)                                    | **NOT MVP**                                                                                                                                     | Being PURGED entirely (snapshot-first) per the Operator dispositions venue-purge ruling — never re-add                                                                                                                                                                                                                                        |

- [ ] [DATA] P2. Confirm UPBIT's live-wiring status (captured row count in the cefi manifest, any open backfill/issue
      doc) — it is codex-MVP but has zero mentions anywhere in this plan's audit trail. Definition of done: a recorded
      row count + PASS/FAIL verdict against the MVP definition, landed in this plan's Progress Log (or a new issue doc
      if a gap is found).

## Track 7 — Candle namespace bundle-collision residual (`processed_candles/`, todo 19; separate bucket prefix/script/defect class from Track 1's raw-tick migration) · P2

- **Source**: `candle_feature_canonical_path_divergence_2026_07_20.md` todo 19, folded in 2026-07-23 (operator
  directive: "put it under cefi_consolidated_closeout_2026_07_18.md"). That doc's P6-P8 candle canonical-**path**
  migration (`market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py --apply`) is COMPLETE and
  independently P8-verified — CEFI's live `processed_candles/` corpus is 99.98%+ clean (405,259/405,408 objects
  `CANONICAL_NOOP`, 0 orphan, 0 unexpected disposition). **The residual is exactly 149 objects**, listed in
  `plans/audit/results/cefi_todo19_149_residual_objects_2026_07_23.csv`.
- **The defect**: NOT id-format non-canonicalization (Track 1's axis) — a bundle-target COLLISION. 93 BYBIT
  `futures_chain` + 56 DERIBIT `options_chain` objects are real, DISTINCT per-contract-leg candle files (e.g. a
  `BTC-20240628` future and an `ETH-20240628` future, same day/venue/timeframe) that all need to land in the SAME shared
  `ticks.parquet` bundle target. The migration script's split-brain-dedup logic assumes siblings racing for one target
  are byte-identical duplicates (true for its normal case: a `pipeline_mode=`-tagged copy vs. a `pipeline_mode`-less
  copy of the SAME shard) — false here, since each leg carries different candle data. Whichever leg's copy lands first
  wins; every other leg's post-copy crc32c/size verification against the now-different-content target legitimately
  fails, so the script correctly KEEPS (never deletes) the loser's source rather than risk data loss. **These 149
  objects are NOT redundant duplicates — deleting them would permanently destroy whichever legs lost the race, with no
  other copy anywhere.** Concentrated on exactly 8 days (2023-06-01, 2023-08-02, 2023-11-02, 2024-02-01, 2024-02-02,
  2024-07-01, 2025-11-01, 2026-01-01).
- **The fix — verified safe 2026-07-23**: raw tick data for BYBIT and DERIBIT is confirmed intact in `raw_tick_data/`
  for the affected days (checked 2 of 8: `day=2023-11-02` and `day=2024-07-01`, both show
  `pipeline_mode=batch_tardis/asset_group=cefi/venue=BYBIT` and `venue=DERIBIT` present). Since candles are DERIVED from
  raw ticks (not primary source data), the clean fix is: delete the 149 stale per-leg objects, then trigger a targeted
  MDPS candle backfill (`--force`) for those exact 8 days/venues — the already-fixed bundling writer (candle issue doc
  todo 8, shipped `mdps@752eaff`) will correctly produce ONE merged `ticks.parquet` per bundle containing every leg's
  data, not just the race winner's. No manual parquet-merge scripting needed, no risk of the data loss a naive delete
  would cause. **This is a much smaller, already-resolved-in-approach problem than TradFi's analogous todo 3 (~7.1M
  objects, raw-tick availability unconfirmed) — do not conflate the two.**
- **Close-out criterion**: the 8 affected `(day, venue)` cells re-derived via MDPS backfill, the regenerated bundle
  verified to contain every leg (row/symbol count check against the pre-delete per-leg object count), the 149 stale
  legacy objects then safely deleted (source data now redundant with the verified-complete bundle), and
  `candle_feature_canonical_path_divergence_2026_07_20.md` todo 19 updated to reference this track's resolution.

- [ ] [DATA] P2. **Verify remaining 6 of 8 affected days** for BYBIT/DERIBIT raw-tick presence in `raw_tick_data/` (only
      2023-11-02 and 2024-07-01 checked so far) before running the backfill, so the fix isn't launched on an unverified
      assumption for the other 6 days.
- [ ] [DATA] P2. **Run the targeted MDPS candle backfill (`--force`)** for the 8 affected (day, venue) cells (BYBIT
      `futures_chain` + DERIBIT `options_chain`, all affected timeframes) against PROD, verify the regenerated
      `ticks.parquet` bundles contain every leg's data (not just the previous race-winner's).
- [ ] [OPERATOR] P2. **Delete the 149 stale legacy per-leg objects** (listed in
      `plans/audit/results/cefi_todo19_149_residual_objects_2026_07_23.csv`) only AFTER the regenerated bundles are
      verified complete — never before; deleting first causes permanent, unrecoverable data loss (no other copy of the
      per-leg data survives). Tagged `[OPERATOR]` per `task_template.md` §3's delete-risk rule and
      `/codex/05-infrastructure/gcs-and-manifest-delete-safety-protocol.md` (2026-07-24 AO-flip-safety audit finding —
      previously untagged, which under AO's same-priority concurrent-dispatch default could have raced this delete
      against the two verify/backfill todos above it instead of strictly following them). Then close todo 19 in the
      source issue doc.

## Codex SSOTs (read before touching a track)

`/codex/02-data/availability-manifest-and-data-status.md`, `…/pipeline-mode-partition.md`,
`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`, `/codex/05-infrastructure/vm-launcher-runbook.md`
(Tardis cap + the throughput-fix ruling), `/codex/06-coding-standards/read-time-filter-pushdown.md`.

## Aggregated source docs

> Moved verbatim to `/plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md` (2026-07-24 line-cap
> trim, 2nd pass — the umbrella:true exemption was removed same-day). Read that doc for the full discoverability index
> of every other cefi-relevant plan/issue with its open-todo digest.

## Progress Log

> **Full day-by-day Progress Log extracted verbatim (2026-07-24 line-cap remediation) to**
> [`cefi_4surface_migration_execution_log_2026_07_24.md`](/plans/active/cefi_4surface_migration_execution_log_2026_07_24.md)
> **— see that file for the complete narrative** (PRE-COMPACT checkpoints, DELTA session updates, deferred-work tables)
> from plan-authoring (2026-07-18) through 2026-07-23 ~08:00Z. Keep appending new session entries to that child file,
> not here, going forward.
>
> **Current status** (as of the child's last entry, 2026-07-23 ~08:00Z, plus the two post-split DELTA updates retained
> below since they were appended here before this remediation and are not yet mirrored into the child): CeFi 4-surface
> migration still IN FLIGHT. KRAKEN-SPOT rename is DONE (Surface A genuinely clean for that venue); the fleet self-drive
> chain (error-recon → re-verify → LATE renames → MID window → colon_wire → loop-until-dry) and the Surface C v2
> manifest-dedup `--apply` are both blocked on transient issues (GCS connectivity blips / a real chain-collision
> data-safety gate) rather than being done. Final 4-surface re-proof (A/B/C/D all PASS) + plan archival has not been
> reached yet — do not assume ALL_DONE without re-measuring.

**Open todos surfaced in the execution log, carried here so they stay tracked in this coordination index (do not
duplicate further — resolve/close via the child's own entries, then tick here):**

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
- [ ] [DATA] P1. DERIBIT combo mispartition — read the design doc
      `plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md` in full before touching this. Two
      DISTINCT actions: (a) **[WRITER] fix the still-open write-path leak** (widen the combo-shape guard in
      `tardis_cefi_shards.py` so new captures stop landing mispartitioned — safe to ship alone, no data motion) — do
      this FIRST, independent of (b); (b) **[DATA] the partition-MOVE for the existing 15,119 mispartitioned rows** —
      needs **explicit operator sign-off on the specific plan** (operator has seen the finding in chat and acknowledged
      it, but has NOT yet signed off on the actual `--apply` — do not execute (b) without a fresh, explicit go-ahead on
      the doc's §7 plan).

> Several of these predate later child-log entries that may have since resolved them (e.g. the wire-key dedup and
> quarantine-registration items) — verify current status against the child's DELTA history before assuming still-open.

The following section was appended to this parent directly (post-split, before this remediation) and has not yet been
mirrored into the execution-log child — reconcile/move it there on the next pass rather than duplicating it further
here.

## Deferred work after 2026-07-22 ~20:15Z (pre-compact checkpoint — supersedes the stale "REVISED REMAINING QUEUE" above; items 1/2/5/6 there are DONE, see this session's DELTAs)

| #   | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Kind                                            | Blocked-on                                                                                                                                                                                                       |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | ~~KRAKEN-SPOT `--apply`~~ — **DONE 2026-07-23 ~15:40Z**. Attempt 3 (with the retry-hardened fix) completed `PYTHON_EXIT=0`: 155,872 auto-renamed + 1,157 stale duplicates deleted; 6 renames hit a transient GCS 503 mid-`copyTo` (never touched by `run_gcs_rename`'s no-retry single attempt) — verified via direct `gsutil stat` that source-untouched/target-absent for all 6, then retried with a tiny script reusing `do_rename()` verbatim; all 6 now confirmed canonical via GCS spot-check. The manifest phase's `honest_unresolved_rows: 3598` figure was investigated and is a NON-ISSUE: confirmed exactly 1 manifest row per (venue, day, instrument_type, data_type) shard atom with `instrument_id=None` — a shard-level completeness marker, not a per-instrument record (per-instrument data lives in the actual GCS files, independently confirmed present + canonical for the sampled shard). **KRAKEN-SPOT Surface A is genuinely, fully clean.** | **DONE**                                        | Nothing outstanding on KRAKEN-SPOT itself — proceed to item 2                                                                                                                                                    |
| 2   | Fleet self-drive chain (taken over directly, `ae18c5ef1b16bc8e8` unreachable from this session): ~~error-recon (348 would_patch errors)~~ **DONE, all genuinely benign** → ~~re-run `verify_cefi_canonical_4surface_2026_07_20.py`~~ **DONE, real fresh measurement, OVERALL FAIL as expected (A=48%/B=95%/C=98%/D=PASS)** → **LATE colliding-venue renames (serialized) — NEXT, scope now precisely pinpointed by the fresh reverify (2025-12-15/2026-02-01/2026-05-01 low-A-fraction dates)** → MID window → colon_wire (1,697) → loop-until-dry (2 clean passes)                                                                                                                                                                                                                                                                                                                                                                                                   | 2/5 links done                                  | LATE colliding-venue renames is the next link — dispatching now                                                                                                                                                  |
| 3   | Surface C: land the v2 manifest dedup apply — 3 attempts blocked on transient GCS connectivity (zero mutation), a 4th got past connectivity and hit a REAL data-safety gate: 3304 `chain`-differing PIN_ATOM groups would lose data if collapsed (the earlier dry-run measured this at 0/0 — corpus moved in the hours between; likely ongoing live capture). Zero mutation this attempt either (script's own validation refused before any write). Consolidator RESUMED again to a safe state                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Blocked on chain-drop investigation             | Investigate the 3304 lossy groups (are they genuinely new captures, or something else) before deciding: re-run a fresh dry-run + apply, or use the script's own offered `--keep-chain` safe alternative          |
| 4   | ~~Residual ~216 ambiguous CeFi wire-keys~~ — **213/216 SHIPPED, DONE**: `instruments-service@bf5322bb9` (BINANCE-DELIVERY 4/4, BINANCE-FUTURES 2/2, KRAKEN-FUTURES 2/2, OKX-FUTURES sub-pattern-A 76/146) + `instruments-service@39e26bfe` (BYBIT FUTURE base-asset-parsing 36/36) + `instruments-service@1c920fab` (OKX-FUTURES sub-pattern-B 70/70 + OKX-SWAP 5/5 + BITGET-FUTURES 18/18 margin_type mislabel, operator-ruled). **3 remain, forever**: BYBIT's 3 PERPETUAL keys — confirmed two genuinely distinct real products (closed 2019-2020 linear + still-active inverse), correctly excluded, not a bug, will never be "fixed"                                                                                                                                                                                                                                                                                                                             | **DONE**                                        | Nothing outstanding — 216→3, and the 3 are a correct terminal state, not a gap                                                                                                                                   |
| 4b  | ~~OKX-FUTURES (70) + OKX-SWAP (5) + BITGET-FUTURES (18) margin_type wire-key collision reclassification~~ — **SHIPPED 2026-07-23** (`instruments-service@1c920fab`): new `_dedup_cefi_margin_type_mislabel()` reuses the live Tardis adapter's own classifier to keep the correct row, drop the stale pre-fix duplicate. Independently re-verified against a fresh prod snapshot (93→0), BYBIT's 3 PERPETUAL confirmed byte-identical untouched                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | **DONE**                                        | Folded into item 4 above, no longer a separate open item                                                                                                                                                         |
| 5   | ~~Build the missing catalogue-enumeration-gap measurement script~~ — **SHIPPED** (`instruments-service@f6f16785`): re-runnable, bounded-read script generalized to 2 case classes (spot-quote-gap, cme-letter-month-gap). Live-measured 211 gap rows today (OKX-SPOT 174, BITGET-FUTURES 33, COINBASE-SPOT 4) — the stale ~422 figure is retired in favor of this number, independently re-verified with real GCS spot-checks                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Done (measurement) / Not done (the fix itself)  | OKX-SPOT/COINBASE-SPOT need an operator decision on widening UAC's `_CEFI_VENUE_QUOTE_EXTENSIONS`; BITGET-FUTURES just needs a catalogue rollup re-run, no code change — neither fix is built yet, just measured |
| 6   | LIGHTER-ZKSYNC market-index → symbol map (~11,283 objects, 93.5% bare numeric stems)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Not done                                        | Greenfield, zero code confirmed                                                                                                                                                                                  |
| 7   | ~~DERIBIT combo PARTITION-MOVE P1 prep~~ — **INVESTIGATED, NO CODE NEEDED**: the guard-widen already shipped this session (`mtds@2ddc6d4a`, landed the day after UAC's DERIBIT-COMBO deregistration `uac@11adf279` — synergistic, not conflicting) and `tardis_cefi_shards.py` already shares the fixed classifier (no duplicate code path to port into). The actual 15,119-row `--apply` data MOVE remains fully unstarted and Operator-owned per §7 — this ruling never covered it                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Prep: DONE (no-op) / Move: still operator-owned | The `--apply` partition-move still needs explicit operator sign-off per `deribit_combo_perpetual_partition_move_2026_07_21.md` §7 — do not start that without a SEPARATE future review                           |
| 7c  | ~~`[INFRA] P2.` MTDS orchestrator hard-coding `DERIBIT-COMBO` as active despite UAC deregistration~~ — **SHIPPED** (`market-tick-data-service@5334bff6`): removed from both call-sites, new test imports the LIVE UAC registry so it stays in sync automatically rather than re-hardcoding an assumption                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | **DONE**                                        | Nothing outstanding                                                                                                                                                                                              |
| 8   | `[INFRA] P1.` Audit `slot-cron-ff-pull.sh` (and any other cron touching shared slot checkouts) for a hard-reset fallback path that silently discards locally-committed-unpushed work — make it fail loud instead                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Operator-owned                                  | This session's hard-reset near-miss (documented above) is evidence, not a fix; needs an operator/infra owner to investigate the actual cron script                                                               |
| 9   | Final 4-surface done-state re-proof (all of A/B/C/D = PASS on both probe instruments) + plan archival                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Cannot be done yet                              | Gated on items 1-3 landing — do NOT assume ALL_DONE without re-measuring; the 44.65%→FAIL baseline was a real corpus-wide measurement                                                                            |

**Recommended next (STALE — see DELTA below for current state)**: ~~keep watching item 1 (KRAKEN-SPOT v4)~~ — item 1 is
DONE. Current blocking chain: item 2 (fleet self-drive chain) + item 3 (Surface C v2 apply), both retrying after a
transient GCS connectivity issue; item 9 (final re-proof + archival) is next once those land.

### DELTA — 2026-07-24 ~01:30Z (`/autonomous` invoked, operator away 6h — driving to completion, no further check-ins)

**Operator invoked `/autonomous` explicitly**, stating they are away for 6 hours and to "complete everything." Per
`cursor-configs/AUTONOMOUS_AGENT_RULES.md` (read in full this tick), decisions the operator could make are now mine to
make using the documented record of intent — logging the one scope decision made under that authority:

**DERIBIT combo partition-move `--apply` (item 7, the actual 15,119-row data MOVE) remains OUT OF SCOPE for this
autonomous drive, NOT reinterpreted as newly-authorized.** Reasoning: earlier THIS SAME session, the operator gave an
explicit, specific ruling on this exact item — "Proceed with P1 prep now" — deliberately answering a question that
distinguished the P1 prep work (approved) from the actual `--apply` data move (explicitly NOT covered, "a SEPARATE
future review required"). That is a recent, specific, documented decision from this operator about this exact action,
not a vague old plan note — the autonomous rules direct using "the documented record of intent" to decide, and the most
faithful reading of that record is that this carve-out stands: "complete everything" naturally refers to the currently
in-flight work threads (Surface C, fleet chain, LIGHTER backfill, MTDS fix, final re-proof, archival), not a dormant,
explicitly-deferred, hard-to-reverse production data migration on live-served financial data that wasn't even part of
the in-flight list reported to the operator. If this reasoning is wrong, it is the conservative direction to be wrong in
(leaving a real migration deferred, not launching an under-scrutinized one while unsupervised).

Also leaving item 8 (`slot-cron-ff-pull.sh` hard-reset audit) untouched — it is shared cross-slot infra affecting OTHER
concurrent agents' sessions, outside this plan's actual scope (flagged Operator-owned for a different reason: needs an
infra owner, not a data-migration sign-off) — modifying it unsupervised carries real risk of breaking sibling sessions
mid-task with no one able to notice quickly.

**Everything else in this plan**: driving to actual completion per rule 1 (no `DEFERRED`/`BLOCKED-OPERATOR` end states),
looping per rule 12 (self-paced `ScheduleWakeup`, journaling every tick to this Progress Log, terminating when items
2/3/9 all reach DONE).

### DELTA — 2026-07-24 ~01:20Z (item 7c SHIPPED; fresh 4-surface re-measure is REAL and FAIL as expected; Surface C hit a genuine data-safety gate)

**Item 7c DONE**: `market-tick-data-service@5334bff6` removes `DERIBIT-COMBO` from both active-venue-enumeration
call-sites (`engine/orchestrator/__init__.py::get_venues_for_asset_groups`, `adapters/umi_tick_provider.py`'s
`_TARDIS_CEFI_VENUES`), adds a live-UAC-registry-backed regression test (imports the real
`unified_api_contracts.registry.market_data_categories.VENUES_BY_ASSET_GROUP` and asserts non-membership, so it stays in
sync automatically rather than hardcoding an assumption), confirmed shipped
(`git rev-list --count origin/live-defi-rollout..HEAD` = 0).

**Fresh `verify_cefi_canonical_4surface_2026_07_20.py` re-measure — a REAL, complete run** (prior 2 attempts crashed on
GCS connectivity before reaching any surface; this one got all the way through): **OVERALL: FAIL [A=FAIL B=FAIL C=FAIL
D=PASS]**. Corpus-level fractions: **A (filename) 48.04%** — but this hides a sharp day-by-day gradient: 94-95%
canonical on 2025-06/08/10/11-12, then 67.04% (2025-12-15), 33.02% (2026-02-01), 23.99% (2026-05-01) — the "LATE window"
the plan already flagged (23-28%), now re-confirmed fresh and post-KRAKEN-SPOT. **B (column) 95.00%** (38/40 sampled
objects). **C (manifest) 98.22%** (excl. chain bundles) — 2 concrete FAIL examples shown (BITFINEX- FUTURES ADA: 7
duplicate wire-form manifest rows alongside 4628 canonical; DERIBIT AVAX-USDC: 2 duplicates alongside 814 canonical) —
exactly the shape the Surface C v2 apply is designed to collapse. **D (reader) PASS** — resolver correctly handles both
wire and canonical forms either way. This is genuinely useful, not just a re-confirmation: it pinpoints the LATE-renames
scope precisely (the 3 low-fraction dates/pattern) rather than relying on a stale 2026-07-20 histogram.

**Surface C v2 manifest apply — 4th attempt got PAST the earlier connectivity failures, hit a REAL data-safety gate
instead**:
`STOP (DATA LOSS): dropping 'chain' would merge 3304 PIN_ATOM group(s) holding >1 CAPTURED row with DIFFERING non-zero row_count`.
Critically, **the dry-run run a few hours earlier (2026-07-23 ~18:58Z) measured this EXACT invariant at 0/0**
("`[v2 CHAIN-DROP=True] rows merging on chain-differing PIN_ATOM groups=0 LOSSY (captured w/ differing count)=0 [MUST be 0]`")
— the underlying manifest data genuinely changed in the few hours between the dry-run and this apply attempt (very
plausibly ongoing live capture continuing to write new cefi rows in that window — the whole corpus grew by other,
unrelated measurements around the same time). Zero mutation occurred (the script's own validation stage refused before
any write — confirmed no "Backed up original index"/"Wrote canonicalised index" log lines appear). Consolidator cron
RESUMED again to a safe state. **Next: investigate the 3304 lossy groups before deciding whether to re-run the dry-run
fresh (the corpus has moved since 18:58Z) + apply, or use the script's own offered `--keep-chain` escape hatch** — the
script's error message explicitly names `--keep-chain` as the safe alternative to a forced collapse, which is a stronger
safety property than the "operator directive 2026-07-20: derive chain from UAC on demand" preference for cleanup; do NOT
force past this check without understanding it first.

### DELTA — 2026-07-24 ~05:55Z (`/pre-compact` mid-autonomous-loop; genuine connectivity degradation confirmed, 3 workflows lost to it, 1 real commit recovered before it could be lost)

**Item 7c's LIGHTER-ZKSYNC follow-up SHIPPED**: `market-tick-data-service@8835b899` ("fix(cefi): LIGHTER-ZKSYNC numeric
market_id stem resolution for Script 2") — threads the shipped `resolve_market_index()` resolver through Script 2's
shared `_cefi_canonical_resolver_migration_2026_07_18.py` as an optional, default-empty
`ResolverMaps.lighter_market_index` field; substitutes a bare-numeric LIGHTER-ZKSYNC stem for its resolved symbol before
the ordinary catalogue lookup. This commit existed locally (made by the LIGHTER-backfill workflow before it stalled) but
was NEVER PUSHED — found by this exact pre-compact audit's Step 1 git-status check, independently re-verified green
(`quality-gates.sh --no-fix` exit 0, fresh re-run, not trusting the stalled workflow's own claim) before pushing. **This
is exactly the kind of loss this ritual exists to catch — a real, valuable, QG-green commit that would have been
invisible to any future session had it stayed local.**

**All 3 dispatched workflows this tick failed identically**: `LATE colliding-venue renames` (Measure phase),
`LIGHTER- ZKSYNC backfill` (DryRun phase, already had the above commit banked from an earlier resumed attempt), and
`Surface C chain-drop investigation` (Investigate phase) — every one "agent stalled on all 6 attempts (no progress for
180000ms each)", burning 208/244/221 minutes respectively before giving up. **Root-caused, not assumed**: directly timed
`gsutil stat` against the same object checked earlier tonight — took ~19-25s just now vs ~3-7s a few hours ago (same
command, same object, same host). Host load (3.13/2.51/2.29) and free memory are unremarkable; only 1 heavy process was
running at measurement time — this is NOT local resource contention, it is a genuine, currently-ongoing GCS connectivity
degradation, most likely the same condition that caused 3 separate transient failures on the Surface C apply earlier
tonight. **The LATE-renames/LIGHTER-backfill/Surface-C-investigation items are reclassified from "in progress" to
"cannot be done yet — blocked on connectivity, not on any decision or code issue.**

**LESSON (new, real cost tonight)**: when GCS connectivity is degraded, a Workflow-dispatched sub-agent running a long
GCS-heavy script can silently stall for 180s x 6 retries (~200+ minutes wall-clock, real token spend) before the harness
gives up and reports failure — a MUCH more expensive failure mode than a direct `Bash run_in_background` command hitting
a clean, fast exception (the same connectivity issue crashed the direct Surface C `--apply` attempts in under a minute
each, with a clear traceback, captured cheaply). **Going forward: during any SUSPECTED connectivity degradation, prefer
direct `Bash run_in_background` execution over Workflow-dispatched agents for long-running, GCS-heavy scripts** — it
fails fast and cheaply instead of stalling expensively. Confirm suspected degradation with a cheap, timed `gsutil stat`
check before deciding which path to use.

**Cross-check consolidator cron state (safety-critical, mid-audit)**: confirmed `PAUSED` at this exact moment — the
failed `Surface C chain-drop investigation` workflow's `Investigate` phase never reached the point of pausing it
(read-only phase, per its own design), so this PAUSED state must be a leftover from the last DIRECT apply attempt this
session (~01:14Z) that I resumed after — re-verified and RESUMED again now, confirmed ENABLED, so it is not left paused
through this connectivity-degraded window.

**`/autonomous` loop continues** — per rule 12(e) (stall-safety: a flat progress metric = STOP and diagnose, never burn
ticks blindly repeating a failing action), NOT re-dispatching another heavy workflow into the same degraded connectivity
immediately. Backing off for a longer interval, will re-check connectivity health (cheap `gsutil stat` timing) before
resuming LATE renames / LIGHTER backfill / Surface C investigation.

### DELTA — 2026-07-24 ~13:35Z (connectivity recovered, resumed briefly, operator returned and called a stop — `/pre-compact` run interactively, nothing local to quickmerge)

**Connectivity re-check**: `time gsutil stat` on the small (9MB) catalog object came back ~3.0s — matches the healthy
baseline, not the ~19-25s degraded reading from the prior tick. Pulled in 17 commits (`unified-trading-pm`) + 5 commits
(`market-tick-data-service`, across 2 pulls) that landed from other concurrent sessions while this loop was backed off;
`instruments-service` was already current. All 3 repos fast-forwarded cleanly, no conflicts.

**Surface C chain-drop investigation — STARTED, INTERRUPTED before conclusion, but already overturns the ~01:20Z DELTA's
working hypothesis.** Read `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py` + its imported v1 module directly
(not via Workflow, per the standing lesson). Found, by reading the code rather than assuming: `_chain_merge_safety()`
early-returns `(0, 0)` whenever `"chain" not in df.columns`; `main()`'s dry-run path calls
`v1._load(..., columns=v1._DRYRUN_COLS)`, and confirmed directly (`'chain' in v1._DRYRUN_COLS` → `False`) that
`_DRYRUN_COLS` does **not** include `"chain"`; `_ensure_cols` only re-materialises `pipeline_mode`/`row_count`, never
`chain`. **This means every dry-run reports the chain-drop invariant as 0/0 UNCONDITIONALLY, regardless of the real
data** — `--apply` is the ONLY code path that loads the full schema (`columns=None`) and therefore the only path that
can ever see a nonzero `chain_lossy`. **This is a plausible alternate/additional root cause to the ~01:20Z DELTA's
"corpus moved between dry-run and apply" hypothesis — quite possibly the ENTIRE explanation, not just a contributing
factor**, since a dry-run showing 0/0 provides zero actual evidence either way; it was never measuring anything. **NOT
YET FULLY CONFIRMED**: a follow-up script (`investigate_chain_lossy_20260724.py`, written to the session scratchpad) was
mid-run — it had proven the `_DRYRUN_COLS` fact above, then hit a transient `ChunkedEncodingError` on the 187MB
full-index download (connectivity had recovered per the cheap `gsutil stat` check on the small object, but a large-blob
download can still hit a one-off reset independent of general degradation), was retried, and was killed mid-flight when
the operator called this stop — so the actual current `chain`-column presence and live lossy-group count in the FULL
schema were never re-measured this tick. **Nothing was mutated**: this was a pure read/diagnostic investigation, zero
`--apply` calls made.

**New tracked todo (do not lose this finding)**:

- [ ] [SCRIPT] P0. Fix (or explicitly justify) `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py`'s dry-run
      chain-drop blind spot: `_DRYRUN_COLS` excludes `"chain"`, so `_chain_merge_safety()` always reports `(0, 0)` in
      dry-run mode regardless of the real data — the STOP-ON-SURPRISE gate for this invariant only ever fires at
      `--apply` time. Either add `"chain"` to `_DRYRUN_COLS` (small perf cost, real safety value: a dry-run would then
      give an honest early warning) or add an explicit log line when the check is structurally skipped, so a clean
      dry-run is never mistaken for a proven-safe one. Re-run `investigate_chain_lossy_20260724.py` (scratchpad, this
      session — promote it to `scripts/` first per the one-off lifecycle rule if it earns its keep) against the FULL
      schema to get the actual current lossy-group count and inspect a sample before deciding `--keep-chain` vs. a
      repair vs. a fixed dry-run + clean `--apply`.

**Operator returned and said stop** (not the 6-hour window elapsing — an explicit interrupt). Per the autonomous skill's
own instruction ("On operator 'stop': kill the loop/sleeper PID immediately and don't re-arm"), this session is ending
the `/autonomous` loop now. **No `ScheduleWakeup` will be re-armed.**

**Consolidator cron state**: re-verified `ENABLED` (not paused) — the interrupted investigation never reached the pause
step (it's a read-only diagnostic phase by design), and no apply attempt happened this tick, so there was nothing to
resume.

**Nothing local to quickmerge**: `git status --porcelain` + `git diff --stat HEAD` came back empty across all 3 repos
before this doc edit — every change from this entire `/autonomous` window was already committed and pushed (confirmed
`ahead=0` repeatedly, most recently by the ~05:55Z pre-compact tick before this one). This plan-doc edit itself is the
only uncommitted change at stop time, shipped via the standard `docs(plans):` direct-push carve-out.

## Deferred work after 2026-07-24 ~13:35Z (supersedes all earlier Deferred-work sections in this file — items 1/4/4b/5/6/7/7c below are DONE, see DELTAs above)

| #    | Item                                                                                                   | Kind                                                          | Blocked-on                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ---- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | ~~KRAKEN-SPOT Surface A~~                                                                              | **DONE**                                                      | —                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 2a   | Fleet chain: error-recon + fresh 4-surface reverify                                                    | **DONE**                                                      | —                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 2b   | LATE colliding-venue renames (fresh scope measurement, then per-venue dry-run+apply)                   | Not done                                                      | Connectivity confirmed healthy now — no longer blocked; operator called a stop before this was started this tick                                                                                                                                                                                                                                                                                                                                            |
| 2c   | MID window (KRAKEN-SPOT `ADA/USD.parquet` spurious hive-segment) + colon_wire (1,697) + loop-until-dry | Not done                                                      | Next link after 2b; not yet started                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 3    | Surface C v2 manifest apply                                                                            | Code-level UNBLOCKED (2026-07-24 later tick)                  | `instruments-service@654d694f` folds `underlying`+`chain` into the manifest dedup key — chain-drop invariant now fully understood (0 DERIBIT/ASTER residual; 28 groups BITFINEX-SPOT/BYBIT-SPOT accepted as a small, logged, tracked tolerance). Full detail: `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` Finding 5. The apply itself (pause cron → fresh dry-run → `--apply` → verify → resume) has NOT run yet — do that next. |
| 4/4b | ~~Residual ambiguous wire-keys + margin_type mislabel~~                                                | **DONE**                                                      | —                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 5    | ~~Catalogue-enumeration-gap script~~                                                                   | **DONE**                                                      | —                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 6    | LIGHTER-ZKSYNC numeric-stem GCS rename backfill (~11,283 objects)                                      | Not done                                                      | Resolver code SHIPPED (`mtds@8835b899`); the actual dry-run + apply of the GCS rename itself never attempted this tick — operator stop landed first                                                                                                                                                                                                                                                                                                         |
| 7    | DERIBIT combo PARTITION-MOVE (15,119 rows, actual data move)                                           | **Operator-owned, explicitly out of scope for `/autonomous`** | Per the `/autonomous` DELTA above — a specific, recent operator ruling this session already deferred this, not reinterpreted as newly authorized                                                                                                                                                                                                                                                                                                            |
| 7c   | ~~MTDS DERIBIT-COMBO venue staleness~~                                                                 | **DONE**                                                      | —                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 8    | `slot-cron-ff-pull.sh` hard-reset audit                                                                | **Operator-owned, explicitly out of scope for `/autonomous`** | Shared cross-slot infra affecting other concurrent sessions — per the `/autonomous` DELTA above                                                                                                                                                                                                                                                                                                                                                             |
| 9    | Final 4-surface done-state re-proof + plan archival                                                    | Cannot be done yet                                            | Gated on 2b/2c/3/6 all landing — do not assume done without re-measuring                                                                                                                                                                                                                                                                                                                                                                                    |

**Recommended next (on resume)**: fix or explicitly accept the dry-run chain-drop blind spot (the new P0 todo) first —
it changes whether ANY future dry-run reading of that invariant can be trusted — then re-run the chain-drop
investigation against the full schema for real numbers, decide `--keep-chain` vs. repair vs. clean apply, then proceed
to 2b (LATE renames) and 6 (LIGHTER backfill) via direct Bash, then 2c, then 9.

## Step 8 verdict (`/pre-compact` run interactively — operator present, called the stop; this closes out the `/autonomous` window)

**Safe to compact/stop: YES.** All 3 repos (`unified-trading-pm`, `market-tick-data-service`, `instruments-service`)
confirmed clean (`git status --porcelain` empty) and `ahead=0` against `origin/live-defi-rollout` immediately before
this doc edit; this edit itself is the only pending change, about to be pushed via the `docs(plans):` direct-push
carve-out. **Nothing to quickmerge**: no code changes were made this tick (pure investigation/reading), so there is no
`--files`-scoped quickmerge to run — the operator's "quickmerging everything local" instruction found nothing local.
**What was at risk and is now saved**: the chain-drop dry-run blind-spot finding — a genuine, non-obvious discovery that
would otherwise have lived only in this turn's transcript — is now a tracked P0 todo, not a chat-only fact. **What was
killed, not lost**: two background diagnostic Python processes (`investigate_chain_lossy_20260724.py` attempts) — both
pure read-only GCS downloads, zero mutation, safe to kill; the script itself remains in the session scratchpad for the
next session to resume from rather than rewrite. **Where to resume**: read this DELTA + the new P0 todo, promote/re-run
`investigate_chain_lossy_20260724.py` against the full schema first, then continue down the Deferred-work table above.
The `/autonomous` loop is now OFF — resuming requires a fresh explicit invocation.
