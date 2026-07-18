---
doc_type: plan
title: TradFi consolidated close-out — track + close every remaining tradfi canonicalisation workstream once and for all
summary:
  Single coordination plan that references (does NOT duplicate) every still-open tradfi plan/issue so they can be closed
  off together — the TradFi analog of cefi_consolidated_closeout_2026_07_18.md, documenting the canonicalisation across
  the same four surfaces (GCS filename/path, parquet instrument_id column, manifest key/status, reader). Authored
  2026-07-18 from a 3-agent audit of ~24 active tradfi/IS/MTDS docs + direct code verification. VERDICT — for the
  INSTRUMENT-ID CANONICALISATION axis, TradFi is FURTHER along than it looks on the deployed data-status page — the MTDS
  tick surfaces (single-leg @LIN-YYYYMMDD, CME options-chain bundled layout, combo-leg decomposition) and the v9
  manifest-schema migration are largely DONE and VM-applied. The one remaining id-format gap is the instruments-service
  reference-data CATALOGUE surface (the "Upcoming expiries" widget's source), whose primary instrument_key is still the
  raw exchange symbol (CME:FUTURE:GCQ26) plus a non-matching third-shape canonical_instrument_id — the TradFi analog of
  the CeFi Deribit missing-quote finding, and the pre-migration CODE disposition that gates the catalogue rebuild.
  Beyond the id axis, ~5 genuinely separate tracks remain (v9 finish residuals, coverage/sourcing reconciliation, a live
  T+1 forward-fill gap, denominator correctness, adapter re-drift prevention).
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
    features-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [tradfi, close-out, consolidation, canonicalisation, instrument-id, manifest, coverage, backfill, adapter-retrofit]
related:
  [
    cefi_consolidated_closeout_2026_07_18.md,
    canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
    tradfi_v9_stage1_finish_2026_07_06.md,
    data_completion_tradfi_2026_07_15.md,
    tradfi_massive_dual_source_2026_05_28.md,
    tradfi_multisource_backfill_2026_06_22.md,
    tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md,
    instrument_id_format_canonicalization_2026_07_08.md,
    master_data_canonicalisation_migration_catalogue_2026_06_07.md,
  ]
created: 2026-07-18
last_updated: 2026-07-18
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  Operator, 2026-07-18 — reviewing the deployment-api data-status page (DERIBIT:FUTURE:AVAX@LIN-20260718 missing its
  quote) asked why TradFi canonical ids differ from CeFi and directed a consolidated TradFi close-out plan mirroring the
  cefi one — "tradfi canonicalisation migrations of GCS paths, instrument ID columns, manifest status, and data should
  all be documented the same way as for CeFi ... consolidated plan, and all the code-related stuff beforehand needs to
  be done that's relevant to tradfi, same process as another agent is tackling for CeFi right now." Authored from a
  3-agent tradfi doc/code audit (slot-3, 2026-07-18).
---

# TradFi consolidated close-out

> **Purpose.** One place to see + close ALL remaining tradfi canonicalisation work, documented the same way as
> `cefi_consolidated_closeout_2026_07_18.md`. This plan **references** the source docs; it does not duplicate their
> content. Close a track by closing its source doc(s), then tick it here. Authored from a 3-agent audit (2026-07-18) of
> every active tradfi/IS/MTDS plan+issue plus direct code verification of the adapter/builder state.

## Why TradFi looked "different from CeFi" on the deployed page (the operator's question)

There is **one** canonical target for every asset group — `VENUE:INSTRUMENT_TYPE:SYMBOL` via the single
`build_canonical_instrument_id` dispatcher (operator decision 2026-07-08); TradFi is NOT a separate scheme. TradFi
looked like raw exchange codes on the data-status page for two reasons, both narrow and now scoped here:

1. **The "Upcoming expiries" widget reads the IS reference-data CATALOGUE**, whose primary `instrument_key` for
   Databento TradFi is still the raw sanitized exchange symbol (`CME:FUTURE:GCQ26`) — the MTDS **tick-data** surfaces
   were migrated to `@LIN`-`YYYYMMDD`, but the **catalogue writer** was not. See Track 1 + the pre-migration disposition
   below. (Direct verification 2026-07-18: `instruments-service/.../tradfi/databento/adapter.py:880`.)
2. **The same catalogue row carries THREE non-aligned id shapes**: `instrument_key=CME:FUTURE:GCQ26` (raw),
   `canonical_instrument_id=CME:FUTURE:SP500:2030-06` (product-root, `YYYY-MM`, colon strike, NO margin marker —
   `adapter.py:974-999`), and the operator-decided target the MTDS side already writes,
   `CME:FUTURE:SP500@LIN-20300621[-STRIKE-C|P]`. None match. Converging them is the pre-migration code work.

## Headline verdict — "is the migration final?"

- **Instrument-ID canonicalisation (4 surfaces: GCS filename / parquet `instrument_id` column / manifest key / reader):
  NEARLY — MTDS tick surfaces are DONE & VM-applied; the IS CATALOGUE surface is the one remaining id-format gap.**
  - Single-leg FUTURE/OPTION `@LIN`-`YYYYMMDD` product-root migration: **DONE, VM-applied**
    (`canonical-migration-tradfi-20260709-160919`; forward-write live in
    `market-tick-data-service/.../tradfi/tradfi_shared.py::derive_tradfi_row_instrument_id`).
  - CME/ICE options-chain legacy flat layout → canonical bundled `underlying=`/`venue=` layout: **DONE, VM-applied**
    (`canonical-migration-tradfi-cme-options-20260714-150207`, 210,589,799 rows, 0 unclassified;
    `tradfi_cme_options_chain_legacy_layout_2026_07_10.md` — **archivable**).
  - Combo-leg decomposition + per-leg canonical key (venue-prefix dropped), IBKR `_SEC_TYPE_MAP`, Databento
    `_resolve_product_root()`, whitespace-delimiter purge at key-construction sites: **DONE in code**
    (`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` — 3 residual todos, one stale).
  - **REMAINING (the pre-migration disposition below)**: the IS catalogue adapter still emits the raw `instrument_key` +
    a non-matching third-shape `canonical_instrument_id` for TradFi — must be converged to the MTDS `@LIN`-`YYYYMMDD`
    target and the catalogue rebuilt BEFORE any "TradFi id migration is final" claim.
- **v9 manifest-schema / `pipeline_mode` partition axis (SEPARATE from id-format, mirrors CeFi Track 3): substantially
  DONE, VM-applied** (`tradfi_v9_stage1_finish_2026_07_06.md`: 2020-2026 `--apply`, orphan-sweep E=0, 100%
  `schema_version=9` re-stamped 2026-07-16); residuals = a CF-audit all-GREEN re-run + operator-gated legacy-twin bucket
  deletes.
- **TradFi OVERALL: NOT done.** Beyond the id + schema axes, separate open tracks remain (Tracks 3–6): coverage/sourcing
  reconciliation, a live T+1 forward-fill gap, denominator correctness, and adapter re-drift prevention.

## Track 1 — TradFi instrument-ID canonicalisation (THE id migration) · SUBSUMES the id-format family

- **Vehicles**: `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` (combo + single-leg id-format) + the
  TradFi slice of `instrument_id_format_canonicalization_2026_07_08.md` (design-origin SSOT, TradFi findings 1 & 7
  closed) + `tradfi_cme_options_chain_legacy_layout_2026_07_10.md` (options-chain layout, **done**).
- **Status**: MTDS tick surfaces migrated + VM-applied; forward-write path live. The **catalogue** surface is the gap →
  Pre-migration disposition P0.1 below.
- **Close-out criterion**: a real TradFi FUTURE/OPTION (e.g. the operator's `CME:FUTURE:…` sample) is
  `PRODUCT_ROOT[-QUOTE]@LIN-YYYYMMDD[-STRIKE-C|P]` on ALL FOUR surfaces — GCS filename, parquet `instrument_id`,
  manifest key, AND the IS catalogue `instrument_key` (with `canonical_instrument_id` either dropped or made byte-equal)
  — verified live; the widget shows the canonical form, not `CME:FUTURE:GCQ26`.
- **Residual adapter-retrofit carve-out → Track 5.**

- [ ] [PM] P0. Land the pre-migration code dispositions (below), rebuild `prod/catalog.parquet`, then flip Track 1 +
      `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`'s 3 residual todos (one is stale — single-leg
      `@LIN` is already VM-applied; flip citing `canonical-migration-tradfi-20260709-160919`).

## Track 2 — TradFi v9 schema / manifest-status migration (SEPARATE from id-format) · P1

- **Vehicle**: `tradfi_v9_stage1_finish_2026_07_06.md` (the TradFi analog of CeFi's Track 3 manifest axis). 10/13 done.
- **Open**: (1) **E7 CF-audit all-GREEN re-run** — the last 2-3 CF REDs traced to the 13,971-row v4 tail that was closed
  2026-07-16; needs a fresh `cf_manifest_audit.py` CF-1…CF-12 run to actually flip. (2) **Legacy-twin bucket DELETEs
  (defi/tradfi/pred)** — HARD-STOP, `BLOCKED-OPERATOR-DECISION`, correctly never run autonomously. (3) **Certify TradFi
  Layer-1 %** once the above closes.
- **Also verify (manifest-axis blocker-candidate, from the audit)**: confirm the live tradfi `_index.schema_version` is
  `int64`, not string `'9'` — `cross_cutting_manifest_canonicalisation_findings_2026_07_11.md` confirms the in-place
  normalisation landed for **prediction** but does NOT confirm it for tradfi; a mixed-dtype `schema_version` on the
  manifest-key/reader surface can silently misbehave under an int comparison (this is a Track-1 cutover pre-check).
- **Close-out criterion**: fresh CF-1…CF-12 all-GREEN + `schema_version` dtype confirmed int64 + operator sign-off on
  legacy-twin deletes + Layer-1 % recorded. Do NOT fold into Track 1 (parallel axis).

## Track 3 — TradFi coverage / sourcing reconciliation + the live T+1 gap · P1 (one P0 inside)

- **`data_completion_tradfi_2026_07_15.md` is a STALE FORK** — 28 unflipped todos split verbatim from the archived
  `tradfi_manifest_canonicalisation_2026_06_01.md`, most already executed by `tradfi_v9_stage1_finish_2026_07_06.md`; it
  also contains a literal duplicate paragraph (the "PRE-EXISTING UAC QG RED" finding, twice). **Reconcile every todo
  against `tradfi_v9_stage1_finish`'s Progress Log before trusting it as backlog** (flip what's done, re-scope the
  genuinely-open equities/ETF re-verify + macro/altdata scaffolds, delete the dup paragraph).
- **P0 data-correctness (surface to operator): TradFi has NO working T+1 forward-fill job.**
  `tradfi_t1_no_working_mtds_job_2026_07_17.md` — the only job nominally scoped to TradFi T+1 (`fast-t1-recon`)
  structurally can't collect TradFi (an OHLCV download needs an explicit one-per-invocation
  `--source databento|massive`), and T6.10 dropped TradFi from it rather than fix it. Nothing source-scoped for TradFi
  T+1 exists in the Cloud Run job inventory → live coverage drifts stale on a rolling basis; only the backfill
  wave-launcher fleet fills history. Fix = add `…-tradfi-databento-t1-recon` (+ massive) Cloud Run jobs to terraform,
  verified with a real exit-0 row-writing run.
- **Genuinely-open sourcing gaps** (each in its own doc, independent of the id migration):
  `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` (CME
  `VENUE_DATA_TYPE_CAPABILITIES` `mbp_10` restoration still needed to actually flow data; no `ohlcv_15m/24h` aggregation
  writer exists despite 3 docs assuming one, leaving `vix_features` unfed); `tradfi_multisource_backfill_2026_06_22.md`
  (FX-yahoo drain to completion); `tradfi_massive_dual_source_2026_05_28.md` (Phase-4b Massive connector shape-parity —
  operator-downgraded P0→P2 2026-07-12; **but the manifest-consolidator dedup-key still omits `source`** — a real
  silent-loss risk the moment any tradfi cell genuinely goes dual-source, carry it as P1).
- **Close-out criterion**: `data_completion_tradfi` reconciled or archived; a TradFi T+1 job runs green; the sourcing
  gaps closed or explicitly accepted.

## Track 4 — Denominator / catalogue-completeness correctness + new findings · P1

- **New findings from the audit (no tracking doc yet — file issue docs)**: from
  `tradfi_instrument_type_migration_read_stale_legacy_object_2026_07_17.md` (headline bug RESOLVED,
  `instruments-service@bd115230`) — 875 tradfi atoms with narrowed historical objects + 153 duplicate KRX row_keys
  surfaced but untracked.
- **Close-out criterion**: the 875-atom + 153-KRX findings triaged (own issue docs or folded here); catalogue
  denominator confirmed against the post-migration `instrument_key` shape.

## Track 5 — Adapter canonical-ID-builder retrofit (RE-DRIFT prevention, post-migration) · P2

- **Why separate**: Track 1's fixes converge the CURRENT catalogue/tick writers; a QG gate (or shared-builder routing)
  is what stops NEW writes re-drifting. TradFi's forward-write already routes single-leg + combo through
  `build_instrument_id`; the catalogue adapter is the retrofit target (see disposition P0.1). Cross-reference the shared
  `canonical_id_builder_retrofit_checklist_2026_07_08.md` (its TradFi slice is a no-op pointer — the real work lives in
  the combo-leg vehicle).
- **Close-out criterion**: the IS catalogue TradFi writer routes through the shared builder (or a QG asserts canonical
  `instrument_key` shape on catalogue write), so `CME:FUTURE:GCQ26`-shaped keys cannot be re-minted.

## Track 6 — Independent tradfi data-correctness / hygiene items · P2

Real but non-blocking, each in its own doc; listed so nothing is orphaned:

- `tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` — dead `mvp_mode` param (never set True); operator DECISION
  wire-vs-delete.
- `tradfi_backfill_oom_remediation_2026_06_24.md` — OOM crash-loop RESOLVED + verified live (e2-highmem-4 baked
  default); 2 P2 tail items (confirm stale env override gone; optional memray of the ~15GB decode footprint).
- `phantom_captures_tradfi_2026_06_28.md` — 171 ICE + 1,083 blank-`data_type` phantom-capture diagnose todo (0.25%);
  close directly or by citing CF-7's later related finding.
- `tradfi_eu_not_draining_source_axis_drift_2026_06_24.md` — mostly executed; residual 4,655-row `barchart` (retired VIX
  source) keep-vs-purge is `BLOCKED-OPERATOR-DECISION`. Its 2026-07-15 note also flags a **procedural rule for Track
  1**: direct-canonical-index mutation must pause the consolidator (or use CAS / additive per-VM-shard writes) — the EU
  floor-clip "got lucky on timing," it did not eliminate the race.
- `tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md` — core fix + write-guard shipped; 2 P3
  follow-ups (EXPECTED_* taxonomy enum decision; writer-provenance archaeology).
- `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` — `BLOCKED-OPERATOR-DECISION` 3+ weeks: Option A (features
  read raw MTDS ohlcv directly) vs Option B (build the MDPS processed-candle layer). Downstream ML/backtest gated on it;
  orthogonal to the migration.

## Pre-migration code dispositions (2026-07-18) — do these BEFORE the catalogue rebuild / Track-1 "final" claim

> Mirrors the CeFi plan's pre-migration section. Track 1's "final" claim is GATED on P0.1–P0.3. Each maps to a source;
> archive/annotate the source when its item lands.

- [ ] [BACKEND] P0.1 **IS catalogue adapter still emits raw + third-shape TradFi ids — the TradFi analog of the CeFi
      DERIBIT missing-quote finding.** `instruments-service/.../reference_data/adapters/tradfi/databento/adapter.py:880`
      builds the primary `instrument_key=f"{venue}:{TYPE}:{sanitized_symbol}"` → `CME:FUTURE:GCQ26` (raw exchange code),
      and `:974-999` (`_build_canonical_instrument_id`) emits a THIRD shape
      `VENUE:TYPE:PRODUCT_ROOT:YYYY-MM[:STRIKE{C|P}]` (no `@LIN`, month-only, colon strike). Neither matches the
      operator-decided target the MTDS side already writes (`CME:FUTURE:SP500@LIN-20300621[-STRIKE-C|P]`). Fix: make the
      catalogue writer emit the SAME `PRODUCT_ROOT[-QUOTE]@LIN-YYYYMMDD[-STRIKE-C|P]` shape as
      `tradfi_shared.py::derive_tradfi_row_instrument_id` (converge or drop the additive `canonical_instrument_id`) →
      **rebuild `prod/catalog.parquet`** → **extend the Track-1 verify gate** to assert ZERO raw-exchange-code /
      third-shape TradFi `instrument_key`s. GATES Track 1 (else the widget + catalogue stay raw while the tick data is
      canonical). (repo: instruments-service)
- [ ] [OPERATOR] P0.2 **TradFi quote/margin ruling — the direct answer to the original question.** TradFi `@LIN` ids are
      currently bare product roots (`CME:FUTURE:GOLD@LIN-20260821`, no quote). Unlike DERIBIT this is likely
      non-ambiguous — every real TradFi future/option here is USD-settled, no inverse-margined TradFi product exists
      (per the single-leg migration's own docstring), so `@LIN` is invariant. **DECIDE**: does the canonical TradFi
      symbol stay `PRODUCT_ROOT@LIN-YYYYMMDD` (bare — recommended for TradFi since margin is invariant), OR carry an
      explicit `-USD` to match the uniform cross-AG `BASE-QUOTE@MARGIN_TYPE-YYYYMMDD` pattern
      (`CME:FUTURE:GOLD-USD@LIN-20260821`)? Recommendation: **explicit `-USD`** — it makes the quote non-ambiguous
      (consistent with the 2026-07-18 DERIBIT ruling) and makes "same pattern regardless of asset class" literally true.
      Whichever is chosen, P0.1 emits that exact shape. (decision only)
- [ ] [BACKEND] P0.3 **Confirm live tradfi `_index.schema_version` is int64 (not string `'9'`) before the Track-1
      cutover** — the in-place normalisation is confirmed only for prediction
      (`cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`); a mixed-dtype column on the
      manifest-key/reader surface risks silent reader misbehaviour during the migration. Direct dtype check; if string,
      run the targeted `to_numeric().astype("int64")` pass with a pre-write snapshot. (repo: market-tick-data-service)
- [ ] [PM] P0.4 **Reconcile `data_completion_tradfi_2026_07_15.md` against `tradfi_v9_stage1_finish_2026_07_06.md`** —
      flip the already-done todos, re-scope the genuinely-open ones (equities/ETF re-verify + macro/altdata scaffolds),
      delete the duplicate paragraph, so the consolidated backlog is honest before cutover. (repo: unified-trading-pm)
- [ ] [BACKEND] P1. **manifest-consolidator dedup-key omits `source`** (`tradfi_massive_dual_source_2026_05_28.md`
      Phase-4b) — land the `source` addition before any tradfi cell genuinely goes dual-source (databento+massive), else
      two-source cells collapse last-write-wins. (repo: unified-trading-library)
- [ ] [INFRA] P1. **File + fix the TradFi T+1 forward-fill gap** (`tradfi_t1_no_working_mtds_job_2026_07_17.md`) — add
      source-scoped Cloud Run T+1 jobs; independent of the migration but eroding live coverage now. (repos:
      deployment-service, market-tick-data-service)
- [ ] [PM] P1. **Consolidate + archive the done docs.** Archive `tradfi_cme_options_chain_legacy_layout_2026_07_10.md`,
      `tradfi_manifest_row_loss_regression_2026_07_12.md`,
      `tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md`,
      `tradfi_manifest_consolidator_row_count_varchar_crash_2026_07_12.md`,
      `tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md`, `tradfi_ice_ohlcv_1m_no_working_fetch_path_2026_07_13.md`
      per the archival ritual (the last two have a 1-line residual live-capture verification each). (repo:
      unified-trading-pm)

## Codex SSOTs (read before touching a track)

`codex/02-data/tradfi-databento-sourcing-ssot.md` (Databento 3-dataset billing, `SOURCE_PRIORITY`, VIX=VX-futures,
Barchart RETIRED), `codex/02-data/availability-manifest-and-data-status.md`, `codex/02-data/pipeline-mode-partition.md`,
`codex/04-architecture/instruments-service-as-ssot-for-mtds.md`,
`codex/05-infrastructure/manifest-consolidator-ssot.md`, `codex/05-infrastructure/vm-launcher-runbook.md`.

## Progress Log

- **2026-07-18 (slot-3) — Plan authored from a 3-agent audit of ~24 active tradfi/IS/MTDS docs + direct code
  verification**, at operator request to mirror `cefi_consolidated_closeout_2026_07_18.md` after spotting
  `DERIBIT:FUTURE:AVAX@LIN-20260718` missing its quote on the data-status page. Verdict: TradFi's MTDS tick surfaces +
  v9 manifest schema are largely DONE & VM-applied; the one remaining id-format gap is the IS catalogue writer
  (`databento/adapter.py:880` raw `instrument_key` + `:974-999` non-matching third-shape `canonical_instrument_id`) —
  the TradFi analog of the CeFi DERIBIT finding, and the pre-migration P0.1 code disposition that gates the catalogue
  rebuild. Five separate tracks remain (v9 finish residuals, coverage/sourcing reconciliation, the live T+1 gap,
  denominator + 2 new untracked findings, adapter re-drift prevention). The CeFi-side DERIBIT missing-quote finding is
  already captured in `cefi_consolidated_closeout_2026_07_18.md` (line 183, `unified-trading-pm@bacd35981`) — not
  duplicated here. All source docs referenced above; none duplicated.
