---
doc_type: plan
title: Data completion to 100% — CeFi manifest canonicalisation + backfill (split from M-1)
summary: >-
  CeFi slice of the data-completion-to-100% program, split out of data_completion_to_100_all_ag_2026_06_21 (M-1) on
  2026-07-15 per operator ruling (plan-reconcile §8) when M-1 breached the absolute 5000-line ceiling. Carries the cefi
  scope M-1 absorbed in the 2026-07-13 consolidation, migrated VERBATIM — no scope added, dropped or reworded. M-1
  remains the coordinator hub for cross-cutting work (bucket naming, source provenance, bar-edge) and owns the shared
  Progress Log.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [backfill, manifest, honest-coverage, data-completion, cefi, data-correctness]
related: [/plans/active/data_completion_to_100_all_ag_2026_06_21.md]
created: 2026-07-15
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2
last_updated: 2026-07-28 # (was: 2026-07-28 deployment-api pipeline_mode dedup+drilldown-filter verified already-shipped, slot-16 -- consolidated 3 overlapping E4-E8 todos into cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md, slot-4)
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
source: [data_completion_to_100_all_ag_2026_06_21 (M-1) — split 2026-07-15, plan-reconcile §8 operator ruling A]
drift_direction: advance-code
---

# Data completion to 100% — CeFi

> **Split from M-1 on 2026-07-15** (`data_completion_to_100_all_ag_2026_06_21.md`, plan-reconcile §8, operator ruling
> A). M-1 had reached 5,366 lines — the only file in the corpus over the absolute 5,000-line ceiling — after absorbing
> 130 folded-in todos in the 2026-07-13 consolidation. This plan carries M-1's **cefi** scope **verbatim**; M-1 stays
> the coordinator hub (measured snapshot, per-AG launch matrix, cross-cutting scope, shared Progress Log).
>
> **Read M-1 first** for the program-level snapshot + launch matrix. Cross-cutting items (bucket-name SSOT, data-source
> provenance, bar-edge) deliberately stayed there — they are not cefi-specific.

### From `cefi_manifest_canonicalisation_2026_06_01.md` (archived 2026-07-13 -- CeFi legacy gap-fill + manifest canonicalisation (single-walk, L3 owner for cefi))

- [x] ✅ [DATA] P0. **⑧ — IS cefi REFERENCE-UNIVERSE gap: catalogue not ⊇ manifest present-set (CF-14, falsely-high
      coverage). ALL 4 sub-parts VERIFIED CLOSED 2026-07-27.** Original finding (2026-06-08): IS
      `instruments-store-cefi-prd` listed only 12 venues vs MTDS manifest's 45, headline gaps KRAKEN-SPOT/FUTURES,
      BITFINEX-SPOT, PACIFICA-SOLANA, LIGHTER-ZKSYNC — root cause was `reference_data/adapters/cefi/tardis.py`'s
      hand-maintained `_DEFAULT_EXCHANGES` drifting below the canonical SSOT `VenueMapping.all_tardis_exchanges`. **(1)
      code fix**: SHIPPED `is@a6bc4d48` (unchanged from prior verification). **(2) operational backfill re-run —
      CONFIRMED DONE**: live `gcloud storage ls -r` on
      `gs://instruments-store-cefi-prd-central-element-323112/instrument_availability/by_date/` shows
      KRAKEN-SPOT/KRAKEN-FUTURES/BITFINEX-SPOT/BITFINEX-FUTURES/BITGET-SPOT/BITGET-FUTURES present as far back as
      `day=2021-06-01` and through the latest `day=2026-07-26` (22 venues total, up from 12). **(3) CLOB venues —
      CONFIRMED**: `instruments_service/reference_data/adapters/cefi/lighter.py` + `.../adapters/cefi/extended.py` now
      exist and LIGHTER-ZKSYNC + EXTENDED-STARKNET both appear in the live `day=2026-07-26` by_date listing;
      PACIFICA-SOLANA was removed from scope entirely by a later operator ruling
      (`instruments_service/engine/orchestrator/defi.py` comment: "all Solana perp DEXes dropped except Jupiter, not
      integrated", 2026-07-16) so its CLOB-enumeration sub-part is now moot. **(4) ~650 UNKNOWN/blank-venue pollution
      rows — RESOLVED**: read `market-data-tick-cefi-prd`'s `_index/availability_index.parquet` directly (8,764,263
      rows) — 0 blank-venue rows, 0 `UNKNOWN`-venue rows, 0 `*F0`-suffixed instrument_ids today (was ~650).
      Corroborating evidence: the first-ever complete `cf_manifest_audit.py` rollup
      (`plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`, 2026-07-26) reports
      `instruments-store-cefi-prd` as CF-14 **"(clean)"**. Gates honest coverage denominator (⑦/⑧); does not touch the
      G4 data/manifest `--apply`. **NEW, separate, minor finding surfaced during this verification** (NOT part of this
      item — filed as its own follow-up, see `cefi_coinbase_futures_blank_instrument_type_2026_07_27.md`): 354
      `market-data-tick-cefi-prd` rows on `date=2026-07-25` for venue `COINBASE-FUTURES` carry a null `instrument_type`
      despite well-formed `instrument_id`s (301 `empty_confirmed` + 53 `attempted_failed`) — a distinct, single-day
      writer gap, not the venue-pollution class this item tracked. Provenance: slot-3 pre-apply audit 2026-06-08
      (original finding); slot-4 live-verification 2026-07-27 (this closure). **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [CODE] P1. **DONE 2026-07-27 (slot-15)** — **execution-service — `data/loaders/defi.py:41,77` DeFi raw-tick
      reads still legacy.** Found `data/loaders/defi.py`'s `DeFiDataLoader._defi_read_candidates` ALREADY has the chain
      kwarg + derivation (already shipped by someone else before this dispatch) — the genuinely-unfixed gap was the
      SEPARATE legacy `UCSDataLoader` in `data/loader.py` (still reachable: `engine/backtest/data_loader.py:386`
      instantiates it with `domain="defi"`), whose `_build_swaps_paths`/`load_swaps` never got the canonical-first +
      chain-axis treatment at all. Fixed both `_build_swaps_paths` AND the identical adjacent bug in
      `_build_liquidity_paths` (same file, same root cause) by mirroring `DeFiDataLoader._defi_read_candidates` exactly:
      derive chain via `to_canonical_venue`, route through `build_candidate_raw_tick_paths` (`canonical_paths` SSOT),
      legacy path appended as fallback. 2 new regression tests pin the chain derivation + confirm the canonical builder
      is called (not silently skipped) even with no derivable venue. `quality-gates.sh` green (204s, 2nd attempt — 1st
      was silently killed mid-run by the same shared-host RAM contention tracked in
      `issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`, but its 7888/7888 test pass before the kill
      already confirmed the fix correct). Shipped: `execution-service@0788b1f0`.

**🟡 P1 — pre-flight engrained (blocking the "pre-flight on every service" bar):** **(MIGRATED FROM:
`cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P3. **market-data-processing-service** — leading-NaN before first observation for state adapters that skip
      the session-grid finalize (already tracked: `issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md`). Confirm
      all cefi adapters route `_finalize_session_grid`; liquidations (no grid) is intentional event-counts — verify.
      **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [INFRA] P3. **`expected_unattempted` is enumerator-run-dependent (not auto per-write) — BLOCKED-OPERATOR-DECISION
      on a missing prerequisite (slot-3 2026-06-04).** A not-yet-backfilled cefi cell is invisible until the v2
      enumerator VM runs (`launch-expected-universe-v2-vm.sh cefi --apply-write`; cadence "one-shot then quarterly").
      cefi is currently seeded (4.1M rows) but NEW venues/instruments between runs are invisible
      (`honest_coverage.py:623` warns a fresh AG reads a misleading 100%). **Why a naive recurring cron is NOT
      shippable:** the v2 enumerator REQUIRES `--catalog-path` = a pre-built IS catalog parquet
      (`gs://instruments-store-cefi-{env_short}-{project}/{env}/catalog.parquet`; the launcher defaults to it,
      `enumerate_expected_universe.py:1410` hard-fails `missing_catalog_path` without it). **NO automated/recurring
      producer of that `catalog.parquet` exists** (workspace grep 2026-06-04: only the launcher + its test reference the
      path; nothing writes it) — it is operator-supplied. So a recurring enumerator scheduler would read a stale/absent
      catalog (fire-and-forget failure, banned). A correct fix needs a PREREQUISITE: either (a) add a recurring
      catalog-build step that writes `{env}/catalog.parquet` from the IS store, or (b) refactor the v2 enumerator to
      build its catalog from the IS availability index at runtime (the exact `read_availability_index`→`{venue:[ids]}`
      pattern deployment-api now uses in `_build_cefi_is_instruments_provider`, eliminating the `--catalog-path`
      dependency). A drafted `expected_universe_cefi_scheduler.tf` (Cloud Run Job + weekly Scheduler, env-tiered buckets
      per `manifest_consolidator_scheduler.tf`) was NOT committed pending this decision. **RESOLVED 2026-06-04 →
      SUPERSEDED-BY `plans/active/proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md`** (operator decision: the
      real fix is a proper, self-refreshing instrument catalogue rolled up from the per-date `by_date/` definitions —
      foundation-level, all asset groups, gates the MTDS migration `--apply`). This cefi cron becomes a thin wrapper
      once that plan's Phase 3 lands; tracked there, no longer a cefi-solo item. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [CODE] P3. **deployment-api per-date denominator refinement (separate follow-up, NOT migration-blocking).** The
      cefi coverage denominator (deployment-api@d55bcb6) reads ONE current IS availability snapshot
      (`read_availability_index`), not the per-date `instrument_availability/by_date/` definitions — so it is the
      latest-known universe, NOT per-date point-in-time-correct (the universe as-of each historical date). Acceptable
      for a coverage denominator (and a big improvement over the 21/10 MVP seed), but if data-status should be
      time-sliced per historical date, switch the provider to read the per-date `by_date/` definitions. Repo:
      deployment-api. Depends on the proper catalogue plan above for the per-date source contract.

**VERDICT:** ⑥ **PARTIAL** — IS-derived per-date capture + UAC combo gate + execution preflight are real + date-correct;
the residual holes (date-blind MTDS fallback un-caught by its QG, no strategy IS-existence check, swallowed Deribit live
guard, permissive unknown-venue) are tracked above. ⑦ **STRONG** — the could-exist universe drives
`expected_unattempted` (run for cefi, 4.1M rows) + the canonical denominator includes it + the UI shows it distinctly;
residual is the in-process MVP-seed denominator under-count + the enumerator cadence (both tracked).

**UAC/UTL helpers (the absence "explainer"):** `build_cefi_partition_path` / `candidate_parquet_paths`
(`canonical/partition_paths.py:392`) are the path SSOT; the `empty_confirmed` closed-set taxonomy lives in
`canonical/crosscutting/honest_coverage.py` (the `EXPECTED_NO_*` / `SOURCE_RETURNED_ZERO` reasons features uses). The
candle-level zero-volume/LOCF/NaN contract is documented in MDPS `base_adapter.py:36-624` (`_finalize_session_grid`) —
**this MDPS docstring is the de-facto SSOT for the candle-absence semantics; the P0/P1 downstream fixes must consume it
(distinguish volume=0 vs NaN vs forward-filled), not re-derive.**

**✅ GREEN (verified consistent — do not touch):**

- **Path correctness**: migration, live+batch writers, MTDS reader, features reader, `rebuild_cefi_manifest.py` ALL go
  through the UAC `candidate_parquet_paths()` SSOT and insert `pipeline_mode=` left of `asset_group=cefi`;
  reader-fallback probes both shapes until ~06-15 (PREP3 writer pipeline_mode= PRIMARY landed mtds@f50116ca). The path
  the migration reads/writes == the writers'/readers'/preflight's path.
- **Data-status infra**: deployment-api reads canonical `market-data-tick-cefi-prd` via `resolve_bucket_name`, uses UTL
  `read_availability_index` (v9 columns), renders 4-state status, derives drilldown axis order from the UAC registry.

**🔴 P0 — E2E-blocking code (OPERATOR-APPROVED to do THIS session before the dry-run):** **(MIGRATED FROM:
`cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [CODE] P1. **deployment-api FLAG-3 — RE-SCOPED (slot-3 evaluation 2026-06-05): NOT a mechanical
      f-string→`resolve_bucket_name` swap; a blind swap would BREAK working code.** The `commentary/pipeline_uat.py`
      reads (`instruments-store-{pid}/instruments/latest/manifest.json`, `features-store-{pid}/health/latest.json`,
      `ml-store-{pid}/training/latest/metrics.json`, `execution-store-{pid}/t1_recon/latest/summary.json`) are NON-AG
      **pipeline-health summary** buckets carrying `# CORRECT-LOCAL` markers (a deliberate QG STEP-5.69 allowlist), NOT
      the AG-scoped market-data stores. The canonical `resolve_bucket_name(kind="instruments-store", asset_group=…)`
      everywhere else resolves a PER-AG bucket (`instruments-store-cefi-…`) with a different path shape — there is no
      single non-AG `instruments-store-{pid}` in that registry, so swapping these would point the health reads at
      wrong/nonexistent buckets (they already `try/except`→None-degrade gracefully today). REMAINING for the
      deployment-api/downstream owner: decide the UAT health-summary bucket MODEL (keep the `# CORRECT-LOCAL` aggregate
      form, or migrate the health summaries into per-AG/env-tiered buckets) — a model decision, not a slot-3 mechanical
      edit. `deployment_api_config.py` store buckets already use typed `effective_*` config (FLAG-3-compliant).
      Cross-ref downstream plan FLAG-3. **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per
      MTDS consolidation ruling.)**

- [x] ✅ [CODE] P1. **deployment-api CeFi pipeline_mode dedup + drilldown filter — VERIFIED ALREADY SHIPPED 2026-07-28
      (slot-16).** Both remaining sub-parts from the 2026-06-03 read-only confirmation were found already landed by
      prior, unrelated commits — no new code required, verified live: **(a) cefi parity test** —
      `tests/unit/test_venue_breakdown_shards_cefi_dedup.py` (`deployment-api@51890b3`, 2026-07-26) mirrors
      `test_pipeline_mode_rows_do_not_double_count_shards` for cefi: 2 instruments × 5 dates × 2 pipeline_modes = 20 raw
      rows must collapse to 10 distinct `(instrument_id, date)` shard atoms via `_per_instrument_coverage`'s set-based
      numerator (`found_pairs`) — the cefi shard-atom dedup is structurally immune to the DeFi builder's raw-`len()` bug
      by construction (no `drop_duplicates` fix needed there), and this test is the regression guard proving it. **(b)
      `pipeline_mode` drilldown filter param** — already fully wired end-to-end:
      `GET     /api/data-status/drilldown/{service}/{asset_group}` accepts `pipeline_mode: str | None` Query
      (`deployment_api/routes/data_status/_deploy_turbo.py`, shipped `deployment-api@4dd2575` "v9 manifest UNION read
      path + pipeline_mode/source drilldown (G3/M5)") and `GET /api/data-status/turbo` accepts
      `pipeline_mode: list[str]     | None` (OR-semantics, shipped `deployment-api@0ae5230` "add pipeline_mode filter to
      /turbo endpoint"); the TS client (`deployment-ui/src/api/client.ts` `_DRILLDOWN_FILTER_KEYS`) already threads
      `pipeline_mode` through. Re-ran both regression suites live 2026-07-28:
      `test_venue_breakdown_shards_cefi_dedup.py` + `test_chain_breakdown_shards_vs_dates.py` = 5/5 passed;
      `test_data_status_hierarchical.py` + `test_data_status_drilldown_provenance.py` = 69/69 passed. No dirty tree, no
      new commit needed. **Residual, NOT part of this item** (noted for a future UI todo, not blocking):
      `HierarchicalShardDrilldown.tsx` renders `pipeline_mode` as a display-only per-cell badge — there is no
      operator-facing filter dropdown wired to the already-existing API param, so the "UI label is playwright-gated"
      clause never triggered (no new UI surface was added). (MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)

**⚪ P2 / needs-confirm (tracked):** **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per
MTDS consolidation ruling.)**

- [ ] [DATA] P2. **CONFIRM partial-BUNDLE completeness guard** — bundled cefi data_types (book_snapshot/options_chain).
      **PARTIALLY CONFIRMED (slot-3 read-only 2026-06-03):** the finalize path DOES run cluster validation
      (`record_captured_from_counts(expected_root_clusters, observed_clusters)`; CLAUDE.md 4-pillar "cluster coverage ≥
      expected" — `MissingClusterValidationError` if absent), so the gate is PRESENT (not missing). The audit's worry is
      the `≥ count-threshold` vs `len(observed)==len(expected)` precision (a partial bundle that meets the count but
      misses a cluster root). The cluster-validation internals live in UTL `manifest_writer.py`
      `record_captured_from_counts` — left as a refinement for the cluster-SSOT owner (`mtds_mdps_master`) to tighten if
      `≥` admits incomplete bundles; **NOT a slot-3-solo fix** (UTL + the bundled writer span DeFi/sports too). The live
      writer's per-instrument path is unaffected (no clusters). Repo: UTL/MTDS — owning VM. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P1. **Before the REAL `_index` rebuild — multi-year dry-run phantom spot-check — RE-RUN 2026-07-28
      (slot-12), GATE FAILED — real finding, NOT a clean pass.** Ran `rebuild_cefi_manifest --dry-run` over the FULL
      corpus (`--start-date 2019-01-01 --end-date 2026-07-28`, `GCP_PROJECT_ID=central-element-323112` exported — the
      CF-11 pass silently no-ops without it, a first attempt without the env var falsely read "prior _index is
      empty/missing"). `unparseable=0` ✅ and `dropped_malformed_captured=25,413` (~0.45% of the 5,677,228-row prior
      index, junk-only per its predicate) ✅ — but **`phantom_to_failed=490,639` (~8.6% of the entire prior index) FAILS
      the "stays small + DERIBIT-chain-style only" criterion** — per-venue spread is broad (OKX-FUTURES, HYPERLIQUID,
      ASTER, BYBIT-SPOT, OKX-SWAP, BINANCE-FUTURES, COINBASE-FUTURES, BITFINEX-FUTURES, BITGET-FUTURES, KRAKEN-FUTURES
      all show large counts; DERIBIT is a small minority of the total, not the dominant class). **Root cause CONFIRMED
      live** (3 independent GCS spot-checks, 100% false-phantom hit rate — not real absences): the CF-11 covered-keys
      dedup compares the prior manifest's stored `instrument_type`/`underlying` COLUMNS against the live object scan's
      parsed path, and multiple venues' actual GCS folder structure (`instrument_type=perpetual` for OKX-FUTURES dated
      futures / BYBIT-SPOT spot pairs; blank `underlying` for ASTER per-instrument shards) no longer matches what the
      prior manifest recorded historically — the object is genuinely present, but the exact-tuple key match fails, so
      it's falsely reclassified `PHANTOM_CAPTURED_NO_OBJECT`. Same bug class as the already-fixed `spot`→`spot_pair`
      synonym (2026-06-11) and the slash-symbol stem fix (2026-06-04), but NOT covered by either. Full evidence + root
      cause + recommended fix + follow-up todos:
      `plans/active/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`. **This BLOCKS the "NEXT
      SESSION — execute the migration" P0 todo immediately below** — see its updated note. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. **SUPERSEDED-BY `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md`
      (2026-07-28, slot-4, main ruling BLK-650261be) — checkbox left UNCHECKED, no sweep has run.** **NEXT SESSION —
      execute the migration** (after the dry-run validates perf) — **🔴 BLOCKED 2026-07-28 (slot-12): the dry-run did
      NOT validate cleanly** — `phantom_to_failed=490,639` (~8.6% of the prior index) is a confirmed false-phantom bug
      (itype/underlying column drift), not real orphans; see
      `plans/active/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`. Running this todo's
      `--apply` migration as-is would `record_failed` ~490K genuinely-present rows for real — do NOT run until that
      issue's fix lands + a clean re-run confirms `phantom_to_failed` drops to a small DERIBIT-chain-style residual.
      Original scope once unblocked: run the 8 year-sharded `--also-legacy --apply` gap-fill (5,233 legacy-only cells),
      then the irreversible orphan-sweep (with the mandatory pre-delete idempotent-`--apply`-over-full-range guarantee),
      then E5 manifest rebuild (now CF-11-canonical + false-phantom-safe @mtds#fa2b02c7+this-fix), E7 verify, E8
      legacy-bucket delete. NOT this session (irreversible) — this exact reasoning is why the successor plan phases the
      chain instead of bundling it into one dispatch. **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P0. C-pipeline_mode RIDER (folded into C0 (d)): the `pipeline_mode=` partition lands in THIS walk
      (satisfies `pipeline_mode_partition_migration` for cefi) — **VERIFIED ALREADY SHIPPED 2026-07-28 (slot-10), +
      regression coverage added.** `rebuild_cefi_manifest.py`'s object-scan walk (`scan_and_rebuild`) has stamped
      `pipeline_mode` on every emitted row since utl@b872bdf1 / PREP2-E5 (2026-06-02, code comments confirm): the
      `_PM_RE` regex captures the canonical `pipeline_mode=` path segment when present
      (`rebuild_cefi_manifest.py:179-182`), and for legacy pre-migration objects with no such segment the walk falls
      back to `derive_pipeline_mode_for_row` (same derivation the live writer + migrator use) rather than stamping blank
      (`rebuild_cefi_manifest.py:442-461`). `ManifestWriter.add()` has persisted `pipeline_mode` since utl@b872bdf1
      (`unified_trading_library/manifest_writer/_writer_ingest.py:148`). Path-parsing was already unit-tested
      (`tests/unit/scripts/test_rebuild_cefi_manifest.py`), but the `scan_and_rebuild`-level stamping (both the
      from-path and derive-fallback branches) had NO regression coverage — added
      `test_scan_and_rebuild_stamps_pipeline_mode_from_canonical_path_segment` +
      `test_scan_and_rebuild_derives_pipeline_mode_for_legacy_path_without_segment` to
      `tests/unit/test_rebuild_cefi_manifest_cf11.py`, both green, full `quality-gates.sh` green (7265 passed / 17
      skipped). This confirms the rebuild-walk CODE is ready for when the actual migration runs (still gated on the
      separate, blocked "NEXT SESSION — execute the migration" P0 todo above — the false-phantom bug at
      `plans/active/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`); no code change was needed
      for this rider itself. `market-tick-data-service@cf8a6817`. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. C-source RIDER (folded into C0 (b)): the `source` column (`tardis`, swap-resilient) lands in THIS walk
      (closes `data_source_provenance` cefi). **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. **🔴 BLOCKED 2026-07-28 (slot-8, confirmed by main) — real predecessor is
      `plans/active/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`, not this todo's own
      action.** Post-walk: re-read the canonical `_index` DATA-STATE (re-run the reusable audit tool) → **100% of rows
      v9** (was 100% v8); **`source` populated on every cell** (zero blank; `tardis`, swap-resilient); **`asset_group`
      column/key present** (no `category`/blank); **`pipeline_mode` non-blank + partition present**; typed reasons;
      **legacy-only CELLS = 0** (838-gap closed). Closes `data_source_provenance` cefi + `pipeline_mode_partition` cefi.
      C-GREEN signal for `bucket_name_ssot…` Phase 6/7 cefi legacy bucket decommission — **this is a GATE, do not flip
      it on a RED audit (data-pipeline-correctness HARD RULE + foundation-completion-gate).** **RE-RUN 2026-07-28
      (slot-8, live, `mode=changed`, no `--apply`) — STILL RED, criteria NOT met**: v9=97.4% (not 100%), source
      blank=24.0% (not 0%), pipeline_mode blank=1.4% (not 0%), Era-B chain-dtype rows=490,332 (not 0) — expected, since
      the underlying walk this todo is post- has not executed yet and remains blocked on the false-phantom itype/
      underlying-drift fix (see the 2026-07-28 slot-12 entry above + the issue doc linked at the top of this item). **Do
      not flip until the walk executes AND a fresh audit reads GREEN on all four criteria** (v9=100% / source blank=0% /
      pipeline_mode blank=0% / Era-B chain rows=0). See the 2026-07-28 (slot-8) Progress Log entry for the full per-CF
      readout. **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation
      ruling.)**

- [ ] [DATA] P0. **SUPERSEDED-BY `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md`
      (2026-07-28, slot-4, main ruling BLK-650261be) — checkbox left UNCHECKED, this measured evidence is folded into
      that plan's Phase B.** **Orphan sweep + bucket-state evidence (slot/Harsh bucket-state verification 2026-06-02).**
      Measured (Cloud Monitoring `storage/v2/total_count`, live-object): `market-data-tick-cefi-prd` 1,545,850 (~65% of
      legacy 2,377,168) and **~17 days STALE — `-prd` latest `day=2026-05-07` vs legacy `day=2026-05-24`** (consistent
      with the 5,233 legacy-only cells; the C0 gap-fill closes it by reading legacy as source). `-prd` is INTERMEDIATE
      FORM: `asset_group=cefi` is in the PATH but there is **NO `pipeline_mode=` partition** (confirmed at the data
      level, not just the manifest). So the E4 walk writes NEW `pipeline_mode=` paths → the pre-existing legacy-FORM
      `-prd` objects become ORPHANS; E5 rebuild / E7 verify MUST delete the legacy-FORM `-prd` objects too (not only the
      legacy SOURCE bucket), else the rebuild double-counts. Legacy carries 3.81M noncurrent objects → the E8 delete
      must also purge noncurrent versions, and the "canonical ≥ legacy" count gate must use Monitoring
      `type=live-object` (never a naive recursive `ls`, which counts versions + soft-deleted). **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P0. **RE-VERIFIED 2026-07-27 (slot-9)**: this todo is itself a diagnostic conclusion ("no migrator fix
      is needed"), not an action item — flipping now that its core technical claim has been spot-checked live rather
      than just trusted. Confirmed `pipeline_mode=` siblings genuinely exist for a sampled day
      (`gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2024-11-07/` lists
      `pipeline_mode={batch_aster,batch_hyperliquid,batch_tardis}/` prefixes, directly contradicting the retracted "no
      `pipeline_mode=` sibling" claim). The retraction's own conclusion stands: no migrator code change is required
      here. The follow-on ORPHAN SWEEP + gap-fill (irreversible deletes, VM-scale) is explicitly a SEPARATE, still-open
      todo immediately below — not folded into this one, not executed by this session. **❌ RETRACTION of the earlier
      "E4-BUG / we-keep-missing-things" P0 (it was WRONG).** I read `moved=0` + a `head -3` listing (which shows
      `asset_group=` paths — they sort BEFORE `pipeline_mode=`) and wrongly concluded "no `pipeline_mode=` sibling /
      migrator no-ops L-bulk". The FULL listing shows the `pipeline_mode=` siblings DO exist (482/day). slot-10's
      `C2 = day=/asset_group=cefi/` count is exactly these **post-migration orphans**, not a pre-migration gap. No
      migrator fix is needed. **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [ ] [DATA] P0. **SUPERSEDED-BY `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md`
      (2026-07-28, slot-4, main ruling BLK-650261be) — checkbox left UNCHECKED, the sweep has not run against prod.**
      **E4 remaining work = ORPHAN SWEEP + gap-fill, NOT a path walk.** (slot-3 verify 2026-06-03: the `pipeline_mode=`
      migration is COMPLETE corpus-wide — sampled days 2020→2026 ALL have both forms; the **9 L-flat orphans are ALSO
      migrated** (e.g. `SOL-ETH.parquet` → `day=2024-11-07/pipeline_mode=batch_tardis/…/SOL-ETH.parquet` exists; the 9
      root files remain only as orphans). So the ONLY additive work left is the legacy gap-fill.) (a) **🛑 IRREVERSIBLE
      — delete the OLD `day=/asset_group=cefi/…` (no-`pipeline_mode=`) orphan objects corpus-wide (~474/day × ~2,613
      days ≈ 1.2M) + the 9 root L-flat orphans** now their `pipeline_mode=` forms exist. PRE-DELETE GUARANTEE
      (mandatory): first run `migrate_cefi_flat_to_v9_canonical --apply` over the FULL range once (idempotent — copies
      any orphan still lacking a sibling, skips the rest) so EVERY orphan provably has a migrated dest; THEN delete
      (count via Monitoring live-object, NOT naive recursive `ls`; per-object isolation; idempotent). This IS the E7
      orphan-sweep. (b) `--also-legacy` 5,233-cell legacy→canonical gap-fill (additive; VM-scale — the 1.9M legacy
      listing stalled an e2-standard-4, so shard/bigger-mem). **Deliberate execution (irreversible deletes + VM-scale) —
      not to be rushed.** Repo: market-tick-data-service. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P2. E5 build-spec reference (superseded by the DONE item above): `rebuild_cefi_manifest.py` encodes the
      per-instrument row key (the LIVE writer key =
      `date,venue,chain,data_type,league_id,instrument_type,underlying,quote_asset,margin_type,instrument_id`;
      orchestrator.py:2937/2957) + tolerates `raw_tick_data/by_date/`+`asset_group=`. Two changes only: (1) its `_PAT_*`
      regexes + `prefix_templates` do NOT account for the NEW `pipeline_mode=` segment between `day=` and `asset_group=`
      → list per `raw_tick_data/by_date/day={d}/` and extend `parse_hive_path` to capture an optional
      `pipeline_mode=(?P<pipeline_mode>[^/]+)/`; (2) stamp v9 cols: pass `source` (cefi single-source `tardis`;
      HYPERLIQUID→`hyperliquid_rest` — _retired pre-R4 token; now `hyperliquid` + transport=rest column_) +
      `pipeline_mode`. **INTERNALS Q — RESOLVED (slot-3 2026-06-01):** `add()` persists `source` (auto-resolved via
      SOURCE_PRIORITY at manifest_writer.py:236) but does **NOT** persist `pipeline_mode` (no kwarg; goes to `**kwargs`
      → dropped) — that is exactly why CF-3 reads blank corpus-wide (the live per-instrument cefi `add()` at
      orchestrator.py:2957 also omits it). `record_captured_from_counts` (mw.py:2840) takes `pipeline_mode` but
      **REQUIRES** `expected_root_clusters` + `observed_clusters` + `available_at_envelope` (the BUNDLED path).
      `record_captured` takes `pipeline_mode` but needs a `df` (read every parquet). **DESIGN FORK (pick deliberately —
      feeds the irreversible delete):** (A) **[RECOMMENDED]** add a back-compatible
      `pipeline_mode: PipelineMode|str = ""` kwarg to `ManifestWriter.add()` that coerces (`_coerce_pipeline_mode`) +
      persists it like `source` (default "" = today's behavior → zero back-compat risk; ALSO closes the live-writer CF-3
      gap so batch=live). Then rebuild via `add(..., pipeline_mode=, source=)`. Needs UTL QG. (B) use
      `record_captured_from_counts` with trivial single-cluster maps (`{instrument_id: rows}` as both expected+observed)
      — hacky for per-instrument. (C) `record_captured(df=...)` reading each parquet — correct but slow. `available_at`:
      parquet col if present, else day-EOD-UTC (never migration-time). Same fork applies to
      `rebuild_prediction_manifest.py`. **Do NOT build until the fork is chosen** — wrong choice corrupts the `_index`
      that gates L6 delete. **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [x] ✅ [DATA] P1. E6 CF-7 relabel: `COINBASE`↔`COINBASE-SPOT`, blank venue/data_type → canonical (diagnose, don't
      bulk). Investigate the 50% `attempted_failed` rows (1.33M) — flag to cefi AG owner (separate from
      canonicalisation). **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)** — **DONE 2026-07-26 (`cefi_satellite_ao_dispatch_batch2_2026_07_26.md` item -002, slot-7,
      data_engineering)**: diagnosed via a single live read of
      `market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` (9,138,791 rows, no
      `--apply`, no corpus walk). `COINBASE` bare-venue = 0 rows (already fully canonical) — no relabel needed.
      Blank-venue = 6 rows (negligible). Blank-`data_type` = 9,750 rows (new finding, filed as its own P3 follow-up).
      The 1.33M/50% `attempted_failed` figure is **STALE** — current measurement is 11.61% (1,060,613 of 9,138,791),
      75.2% of which is the already-tracked Tardis-403/DERIBIT population (no new mechanism). Full write-up:
      `plans/active/issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md`.

- [ ] [DATA] P0. E7 Verify: `cf_manifest_audit_2026_06_01.py market-data-tick-cefi-prd-…` → CF-1…CF-12 GREEN on
      data-state; flip CF-coverage rows in `cefi_master_audit_instructions.md`. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. E8 ⚠️ IRREVERSIBLE — only after E7 GREEN: hand C-GREEN to `bucket_name_ssot…` L6 → **delete legacy
      `market-data-tick-cefi` permanently** (single source of truth; legacy data is gone). **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [CODE] P2. **NICE-TO-HAVE — rebuild within-bounds precision**: cross-check the reclassify decision against the IS
      CeFi universe + per-instrument coverage windows + the known-gap registry (today the gate is the conservative
      data_type-guarantee + reason heuristic, which the operator prioritised; the IS-universe cross-check would tighten
      false-positive reclassifications on genuinely-sparse symbol-days). Provenance: slot-3 E2E audit 2026-06-03.
      **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- **[DATA] P0.** **Absorbed from `cefi_processed_candles_manifest_file_disconnect` (harsh) — ROOT CAUSE CORRECTED by
  direct `_index` query (slot-3 2026-06-03).** Non-checkbox rollup header — **restructured 2026-07-27 (slot-14) so its 3
  findings dispatch/gate independently** (the original single-checkbox-with-3-nested-sub-items shape let a dispatched
  worker complete 1 of 3 sub-items with real evidence yet have nothing to honestly flip, since the parent's own checkbox
  correctly requires all 3 green — see the 3 promoted todos immediately below, plus the archival todo that gates on
  them). The reported "MTDS marks `processed_candles` `captured` with no file" is a **category error, NOT manifest
  corruption.** Reading the live cefi `_index` (2,640,864 rows, 2026-06-03): the manifest **already disambiguates
  surfaces via `data_type`** — RAW tick (`trades` 1.19M / `book_snapshot_5` / `derivative_ticker` / `liquidations` /
  `futures_chain`, ~all `service_name=market-tick-data-service`) vs CANDLE (`ohlcv_1m/5m/15m/1h/4h/1d` as understood at
  the time, **only 8,715 rows**, mostly `service_name=market-data-processing-service`). The issue cross-checked
  `processed_candles/` FILES against **`trades`-captured** rows; a `trades` `captured` row (MTDS) correctly means the
  **RAW** tick file exists (VERIFIED: day=2026-05-02 BITFINEX/BITGET/KRAKEN raw `trades` files present) — the manifest
  **never marked CANDLES captured** for those venues. So MTDS is NOT writing phantom processed-candle rows; hypothesis
  (b) is disproved and the `reconcile_phantom_manifest_rows_all.py` flip-to- `attempted_failed` would WRONGLY demote
  correct raw rows (it only probes `raw_tick_data/` anyway).
- [x] ✅ [CODE] P0. **Read-side contract fix (features-service)** — **DONE (features-service@933b8747, slot-3
      2026-06-03).** `LookbackValidator._build_captured_index` credited ANY captured `data_type` as a candle-available
      lookback date (raw `trades`/`book_snapshot_5` over-counted history off the shared `_index`); now filters to the
      feature*groups' candle `ohlcv*\*`data_types via`resolve_data_type_for_feature_group`(mirrors the
      already-correct`get_available_instruments`). +regression test (`ohlcv_1m`counted;`trades`/`book_snapshot_5` not).
      Verified delta_one 20/20 + basedpyright-clean diff. **Shipped under operator EXEMPTION** (local macOS QG red only
      on the foreign non-deterministic flake `features_service_full_qg_test_pollution_flake_2026_06_03.md`; Linux
      `quality-gates-v2` re-verifies at promotion). Repo: features-service. **(Promoted 2026-07-27 from the Absorbed
      rollup's sub-item 1 — no content change.)**
- [ ] [DATA] P1. **Real cefi candle-coverage gap (partial backfill) — RE-SCOPED 2026-07-27 (slot-14), now a manifest
      gap, not (only) a data gap.** The `ohlcv_*` manifest-row sparsity this item's original text cites is a STALE
      symptom of the wrong query vocabulary (see the VERIFY todo below) — the REAL candle files themselves are growing,
      not stuck: a fresh live listing of `processed_candles/by_date/day=2026-05-03/` today shows **1,238 files**
      (BITGET-FUTURES 664 / BITGET-SPOT 340 / BITFINEX-FUTURES 199 / KRAKEN-FUTURES 35) — roughly **2x** this item's
      original 2026-06-03 count (578: 319/151/90/18 same venues, same day) — so candle GENERATION for this venue set is
      active and growing. What's now confirmed missing is the MANIFEST recording of those writes (see the VERIFY todo
      below) — track + complete BOTH: (a) the manifest backfill/repair for already-written candle files, (b) whether
      candle generation is missing entirely for OTHER major cefi venues (BYBIT/OKX/COINBASE/DERIBIT/HYPERLIQUID etc. —
      not checked this session, still open). Repo: MDPS. Likely VM-scale given the breadth of (b); needs its own scoped
      follow-up, not a quick fix. **(Promoted 2026-07-27 from the Absorbed rollup's sub-item 2 to a first-class,
      independently-dispatchable todo.)**
- [x] ✅ [DATA] P1. **VERIFY MDPS candle-manifest faithfulness — DONE 2026-07-27 (slot-14).** Verdict: **YES, MDPS is
      dramatically under-emitting manifest rows relative to real candle files it writes** — confirmed by direct
      comparison, not assumption. _\*Root cause of the original "8,715 sparse ohlcv_* rows" premise_*: STALE query
      vocabulary — a 2026-07-21 operator ruling (`market-data-processing-service/app/core/canonical_writer.py:519-527`,
      `canonical_writer_streaming.py:478-483`, `output_path_helpers.py:120-124`) changed the manifest's `data_type` AXIS
      for MDPS-derived candle rows to the SOURCE type (e.g. `trades`), never `ohlcv_*` — both the manifest row and the
      GCS object path's `data_type=` segment now carry the source value. A fresh corrected live query
      (`service_name=market-data-processing-service`, any data_type, cefi manifest, 8,734,804 total rows) finds only
      **75 rows ever** (72 `captured` + 3 `attempted_failed`, 2024-01-01..2026-07-20, 70 HYPERLIQUID + 2 BITGET-FUTURES)
      — none for `day=2026-05-03`'s BITGET-FUTURES/BITGET-SPOT/BITFINEX-FUTURES/KRAKEN-FUTURES at all, despite the 1,238
      real files confirmed above. **Cross-write reconciliation**: not re-measured this session (the old 782/616 figures
      are themselves now suspect given the same axis change); the codebase's own `tests/unit/test_phantom_prevention.py`
      confirms an emission-policy gate (`should_publish_row=False`, the "heartbeat-only" path) intentionally uploads GCS
      bytes while skipping `record_captured` — a second, BY-DESIGN source of files-without-manifest-rows, plus a broad
      `except Exception` around the manifest call itself (`canonical_writer.py:514-585`) that logs-and-swallows rather
      than retrying/alerting. **NEW finding, filed separately below (not this todo's scope)**: the real candle files
      inspected all carry `pipeline_mode=batch_databento`, a value whose only SSOT
      (`unified-api-contracts/canonical/crosscutting/pipeline_mode.py:85`,
      `/codex/02-data/tradfi-databento-sourcing-ssot.md`) documents it as TRADFI/VIX-only — its presence on genuine cefi
      venues looks like a mislabeling bug, not a legitimate value. Repo: MDPS (+ MTDS REST-poll path). Evidence: live
      reads against `market-data-tick-cefi-prd-central-element-323112` (manifest + GCS listing), read-only, no
      `--apply`. `unified-trading-pm@c987b3eed`. **(Promoted 2026-07-27 from the Absorbed rollup's sub-item 3 to a
      first-class todo — same completed work, now cleanly flippable.)**
- [ ] [DATA] P2. **Archive the absorbed issue doc, gated on the backfill todo above landing.** Once the "Real cefi
      candle-coverage gap (partial backfill)" todo above completes (both its (a) manifest-repair and (b) other-venues
      sub-parts), all 3 original findings from `cefi_processed_candles_manifest_file_disconnect` are GREEN — archive
      that issue doc, citing this plan's rollup header + all 3 promoted todos' evidence. Gated on the backfill todo
      above (do not dispatch before it lands). Repo: unified-trading-pm (doc-only). **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling — restructured 2026-07-27
      per BLK-e002d3cb resolution.)**

- [ ] [DIAG] P1. **NEW (2026-07-27, slot-14) — cefi processed-candle files carry `pipeline_mode=batch_databento`, a
      value whose only documented SSOT is tradfi/VIX-only.** Live GCS listing of
      `processed_candles/by_date/day=2026-05-03/` in the `market-data-tick-cefi-prd-central-element-323112` bucket shows
      1,238 real candle files for BITGET-FUTURES/BITGET-SPOT/BITFINEX-FUTURES/KRAKEN-FUTURES all stamped
      `pipeline_mode=batch_databento` in their object path. `batch_databento` is defined in
      `unified-api-contracts/canonical/crosscutting/pipeline_mode.py:85` and documented exclusively for tradfi/VIX
      sourcing (`/codex/02-data/tradfi-databento-sourcing-ssot.md`) — cefi's own pipeline_mode is `batch_tardis` /
      `live_<venue>` everywhere else in this corpus. This is diagnosis-only: determine whether (a) MDPS's candle
      pipeline_mode-derivation for cefi has a real bug (e.g. `derive_pipeline_mode_for_row` falling through to a
      databento default for an unrecognized/edge-case source), or (b) these are legacy/stale files from a past
      migration/test that never got cleaned up, or (c) something else. Do NOT implement a fix in this todo — mirrors the
      diagnosis-only pattern used elsewhere in this doc family. Repo: market-data-processing-service. **Done when**: a
      written finding states which cause applies, citing the exact code path or file provenance, and recommends (without
      implementing) the fix or cleanup.

- [ ] [CODE] P1. ⑦ cefi could-exist denominator seed — build the `--catalog-path` parquet from the cefi IS catalog
      (per-instrument lifecycle: `instrument_id`/`instrument_type`/`venue`/`available_from`/`available_to`) and run
      `enumerate_expected_universe.py --asset-group cefi --catalog-path <catalog> --apply-write` against the canonical
      `_index` so the raw-tick denominator == could-exist universe (active-but-uncaptured instruments seeded
      `expected_unattempted`). Verify on a VM (GCS flaky locally); confirm `_enumerate_v2_cefi` row-key/data_types match
      the cefi captured atom; add a regression (IS-universe ⊃ manifest ⇒ denominator doesn't shrink). The mechanism +
      bucket fix are done; this is the per-AG catalog build + run + verify. parent_epic: mtds_mdps_master. **(MIGRATED
      FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. **cefi `instruments-store` `_index` v8→v9 single-walk** (CF-1/3/4/8 RED + 40% null `capture_status` +
      blank `data_type` + ~~23 legacy-only cells~~; cf-audit ① above). **[2026-07-13 CORRECTION — stale number, real
      audit run]**: the "23 legacy-only cells" figure above is STALE/WRONG. The first-ever post-apply CF-1..CF-14
      manifest audit for cefi (real execution of `unified-trading-library/unified_trading_library/cf_manifest_audit.py`
      against live data, this session) found `instruments-store-cefi-prd` L6-legacy-only **RED at 18,076 cells** —
      not 23. See the 2026-07-13 (cefi lane) Progress Log entry at the end of this doc for the full audit readout
      (instruments-store + market-data-tick both surfaces). Owner = the **cefi slice** of
      `instruments_manifest_canonicalisation_2026_06_01.md` (was: cited as live owner — **[2026-07-12 correction]**:
      that doc is ✅ ARCHIVED 2026-06-26, folded into `instruments_mtds_subset_consistency_remediation_2026_06_17.md`
      survivor I-2 — retarget the owner pointer there. That successor doc reports cefi's instruments-store v9 migration
      as "fully migrated" / legacy-delete DONE at a fleet level (its lines ~185/452/608/1524), but does NOT visibly
      re-confirm the specific CF-1/3/4/8 + null `capture_status` + blank `data_type` residuals this todo names —
      checkbox NOT flipped without that direct re-verification; re-audit against the successor before treating this as
      done. Corrected per plan-reconciliation finding 150,
      `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 B-queue ruling.); `--apply` **GATED
      on coordinator G0** (source-aware pipeline_mode). Re-run `cf_manifest_audit instruments-store-cefi-prd-…`
      post-walk → all-CF GREEN. Provenance: slot-3 G1 cf-audit 2026-06-07. parent_epic: mtds_mdps_master. **(MIGRATED
      FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

## Progress Log

> **Folded in 2026-07-24** from the M-1 coordinator's (`data_completion_to_100_all_ag_2026_06_21.md`) shared Progress
> Log (plan line-cap remediation, `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` bucket-(d) split,
> operator-approved) — every CeFi-lane-tagged dated entry, moved verbatim, in original chronological order. M-1 retains
> the cross-cutting/multi-AG entries; read M-1's Progress Log too for the full program-level narrative.

### 2026-06-21 — CEFI lane: live producer unblocked (missing lifecycle topic — fleet-wide finding)

First-ever operational live MTDS launch crashed: `NotFound: 404 … market-tick-data-service-events`. UTL
`_sink_factory.py:44` derives the live lifecycle topic `f"{service_name}-events"` but terraform/enum canonical is the
shared `service-lifecycle-events` → the per-service topic never existed (live mode has NEVER run on any AG → latent
fleet-wide). **Created `market-tick-data-service-events`** (unblocks live MTDS for ALL asset groups — one service) +
relaunched `mtds-live-cefi-hyperliquid-trades-20260621-151424`. Systemic fix (UTL sink → `service-lifecycle-events`, or
terraform per-service topics; also hits MDPS/features/strategy/execution live) filed:
`plans/active/issues/live_mode_event_sink_topic_missing_2026_06_21.md`. Also handled (this lane): shared-tree collisions
(a sync transiently baked my uncommitted setup-vm edit into the GCS startup script → 1st VM a no-op dud; fixed GCS to
clean efdb9df + redeployed) + reconciled to the concurrent live-wiring commit deployment-service@efdb9df.

Coverage snapshot above (measured, not memory). Kalshi seed VM re-launched (runner set-u fix mtds@74e228c). Fleet
launch + monitoring loop starting (this plan is the path-to-100% plan-of-record).

### 2026-06-21 — CEFI lane (/autonomous, Opus): triage measured + live-path diagnosed

Measured cefi from consolidated v9 `_index` (3.87M rows; cov 33.9% = 1.31M cap / 1.28M empty / 802k failed / 482k
unatt). **802k failed triage (measured):** source=tardis 753,341 + 22,519 `batch_tardis` phantoms = **775,860
Tardis-gated (96.7%)** → historical re-fetch is billing-gated (operator EXCLUDED) → BLOCKED-CREDENTIALS. Free-venue
re-fetchable = hyperliquid 30,835 + aster 17,675 = **48,510** (native, no Tardis). Top `error_reasons`:
`UNCLASSIFIED_ADAPTER_ERROR` 689,899 / `VENUE_FETCH_FAILED` 83,923 / `phantom_no_parquet` 22,700 / `HTTP_429` 3,652.
**IS cefi VERIFIED 99.9% (36,062/36,084, all v9) — done.**

**BIG FINDING — live path:** operator named `launch-cefi-forward-poll.sh`/`launch-cefi-onchain-forward-poll.sh` for the
live stream, but BOTH run `--mode batch` → BILLED Tardis replay + `batch_<source>` rows (would violate the
Tardis-billing exclusion AND not produce `live_<source>`). The genuine FREE live path =
`launch-mtds-live.sh --asset-group cefi` (`--operation websocket-streaming --mode live`, real-time exchange-WS proxy; 18
cefi connectors registered since the 2026-05-17 Phase 3.5 rollout — the handler's "registry empty at Phase 3.1"
docstring is STALE).

Gap: `setup-data-pipeline-vm.sh` has NO `live_websocket` branch (generic fall-through hardcodes `--mode batch`), and the
handler needs `--shard-spec` + `--instrument-ids` + `streaming_redis_url`. **Plan: wire the live branch + local redis
into setup-data-pipeline-vm.sh → launch mtds-live cefi → verify ≥1 live row** (reusable for all AGs — live=0
fleet-wide). Then year-shard the 48.5k free-venue failed re-fetch + file the BLOCKED-CREDENTIALS ask for the 775.9k
Tardis-gated.

### 2026-07-27 (slot-14, `data_engineering`) — dispatched the "NEXT SESSION — execute the migration" todo (line 195): STOPPED before executing, standing down

Dispatched task `data_completion_cefi-009` targets the todo bundling: (1) an 8 year-sharded `--also-legacy --apply`
gap-fill (5,233 legacy-only cells), (2) an irreversible corpus-wide orphan-sweep-delete, (3) E5 manifest rebuild, (4) E7
verify, (5) E8 **permanent legacy-bucket delete** — as ONE dispatched unit (`est_hours: 1.0`). Did not execute any part
of it. Reasons:

1. **The todo's own text already says not to**: title is literally "NEXT SESSION — execute the migration", body ends
   "NOT this session (irreversible)" — this is stale prose carried verbatim from
   `cefi_manifest_canonicalisation_2026_06_01.md` (2026-06-01 era, migrated 2026-07-13) and was never meant to be picked
   up as a single atomic dispatch.
2. **A discovered, pre-existing, unambiguous cross-plan HARD RULE forbids step 5 (E8) right now**:
   `plans/active/legacy_bucket_dual_write_decommission_2026_07_24.md` line 134: "**Do NOT delete an AG's legacy bucket
   while its L3 plan is open** — prediction/cefi hold legacy-only history." THIS plan (cefi's L3 plan) is
   `status: active` with many other open P0 items beyond this one todo (⑦ catalog-path denominator build, the v8→v9
   single-walk, E7 verify itself is its own separate unchecked item, several MDPS candle-coverage gaps) — it is not
   C-GREEN, so E8 is structurally not permitted yet regardless of how steps 1-4 go.
3. **Steps 1-4 are each independently VM-scale and irreversible-adjacent**: the doc's own text elsewhere describes the
   legacy listing alone as having "stalled an e2-standard-4, so shard/bigger-mem" and explicitly calls this class of
   work "**Deliberate execution (irreversible deletes + VM-scale) — not to be rushed**" (same doc, E4 item). An
   8-year-sharded VM launch fleet + a full-corpus orphan-sweep delete + a manifest rebuild is not something to originate
   and monitor to completion inside a single ~1-hour interactive dispatch, independent of the E8 gate.

**Recommendation for whoever picks this up next**: this whole todo needs to be split into a properly-scoped, phased,
VM-launched execution plan (matching the pattern used for the cefi Track-1/Track-2 migrations elsewhere this week), with
the E8 delete as its own final, separately-gated step confirmed against
`legacy_bucket_dual_write_decommission_2026_07_24.md`'s L3-open rule at execution time, not bundled into one dispatch.
Did not flip this todo's checkbox. Filed the same finding via `/blocked` for operator awareness given the scale/stakes.

### 2026-07-28 (slot-8, `data_engineering`) — "Post-walk" audit todo (line 247): re-ran the reusable audit tool live — RED, checkbox correctly NOT flipped (walk still hasn't run)

Dispatched task `data_completion_cefi-012` = the "Post-walk: re-read the canonical `_index` DATA-STATE (re-run the
reusable audit tool)" todo. Ran `unified_trading_library.cf_manifest_audit.audit()` (the reusable tool named by the
todo) read-only, `mode=changed` (index-only, no GCS bulk walk — single-walk discipline), directly against both live cefi
buckets, no `--apply`:

- **`instruments-store-cefi-prd-central-element-323112`** (84,507 rows): CF-1/CF-3/CF-4/CF-5/CF-6/CF-8/CF-13/Era-B all
  **GREEN** (v9=100%, source blank=0%, pipeline_mode populated=100%). Only CF-2-paths/CF-3-partition RED — the
  `entity=fixtures` non-hive path already documented as a pre-existing, accepted schema characteristic (2026-07-12
  finding-144 waiver, quoted above in this same file), not this todo's raw-tick concern.
- **`market-data-tick-cefi-prd-central-element-323112`** (9,177,562 rows) — the bucket this todo's criteria actually
  gate — is **still RED on exactly the criteria this checkbox names**: CF-1 v9=**97.4%** (8,943,353/9,177,562; not
  100%), CF-4 source blank=**24.0%** (2,206,913/9,177,562; not "populated on every cell"), CF-3 pipeline_mode
  populated=**98.6%** (126,228 blank; CF-3-partition segment itself IS present=GREEN), CF-8 available_at RED (a
  pre-existing schema-evolution artifact per the same finding-144 waiver, not a fresh defect), Era-B RED (**490,332**
  rows still carry legacy-form `data_type=options_chain/futures_chain` instead of the post-Era-B `trades` scheme, so not
  yet 0). CF-13 (source-aware pipeline_mode form) is GREEN on the populated subset.

**Verdict: the "100% of rows v9 / source populated on every cell / pipeline_mode non-blank" acceptance bar is NOT met.**
This is not a new problem — it reconfirms, with fresh live numbers, the already-tracked fact (2026-07-27/28 entries
above) that the actual walk this checkbox is "post-" (the C0(b)/(d) source+pipeline_mode riders, the E4 gap-fill/orphan
sweep, the E5 rebuild) has **not executed yet** and remains blocked on the false-phantom itype/underlying-drift bug
(`plans/active/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`). Did **not** flip this todo's
checkbox — doing so on a RED audit would be fabricated progress. No new issue doc filed (these findings corroborate, not
introduce, the already-open blocker). Whoever unblocks the walk should re-run this exact audit command afterward; if
CF-1/CF-3/CF-4 all read GREEN and Era-B reads 0, that todo can then honestly flip.

### 2026-07-28 (slot-6, `data_engineering`) — E7 Verify todo (line 359): re-ran the audit live — still RED, checkbox correctly NOT flipped

Dispatched task `data_completion_cefi-017` = "E7 Verify: `cf_manifest_audit_2026_06_01.py market-data-tick-cefi-prd-…` →
CF-1…CF-12 GREEN on data-state; flip CF-coverage rows in `cefi_master_audit_instructions.md`". Ran
`unified_trading_library.cf_manifest_audit.audit()` (the same reusable tool as the prior entry) directly in Python,
read-only, `mode="changed"` (index-only, no GCS bulk walk — single-walk discipline preserved), against
`market-data-tick-cefi-prd-central-element-323112` only (this todo's named target; `instruments-store-cefi-prd` was
already confirmed GREEN on the relevant CFs in the entry immediately above and was not re-walked).

Fresh live result (9,195,191 rows, up from 9,177,562 a few hours earlier — corpus still growing):

- **CF-1** schema_version RED: v9=8,960,982/9,195,191 (97.5%; dist also carries 108,367 null + 63,226 `v6` + 924 `v5`).
- **CF-3** pipeline_mode-populated RED: 9,068,963/9,195,191 (98.6%; 126,228 blank).
- **CF-4** source RED: blank=2,206,880/9,195,191 (24.0%).
- **CF-8** available_at RED: non-null=1,230,144/9,195,191 (pre-existing schema-evolution artifact per the finding-144
  waiver already cited above, not a fresh defect).
- **Era-B** RED: 490,470 rows still carry legacy-form `data_type=options_chain/futures_chain` (up slightly from
  490,332).
- **CF-2-paths** RED: no `asset_group=`/`category=` hive segment on the object path scheme (path uses
  `pipeline_mode=`/`timeframe=`/`data_type=` segments only, no bucket-level asset_group/category prefix segment) — same
  characteristic as the prior entries' path-scheme finding, not previously called out per-CF in this doc but not a new
  defect either.
- **GREEN**: CF-2 (asset_group column present, no `category` column), CF-5 (typed reasons), CF-6 (4-state), CF-13
  (source-aware pipeline_mode, 100% of populated rows), CF-3-partition (pipeline_mode= path segment present), CF-9 (env
  bucket naming).
- **SKIP**: CF-10 (phantom — honest SKIP under `mode=changed`, needs `--mode full`), CF-14 (catalogue not materialised —
  G1 pending).

**Verdict: identical root cause, identical conclusion as the entry immediately above — CF-1…CF-12 is NOT GREEN on
`market-data-tick-cefi-prd-…`.** Did **not** flip this todo's checkbox, and did **not** flip any CF-coverage rows in
`cefi_master_audit_instructions.md` (its own "Canonical-form coverage (CF-1…CF-12)" section, lines 140-154) — both
actions are explicitly conditioned on GREEN by this todo's own text, and flipping on a RED result would be fabricated
progress. No new issue doc filed: this corroborates, not introduces, the already-open
`cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md` blocker that the entry above already names. This todo
stays open pending that blocker's resolution + the E4 gap-fill/orphan sweep + E5 rebuild; whoever unblocks those should
re-run this exact audit and flip both this checkbox and the `cefi_master_audit_instructions.md` CF-coverage rows only
once CF-1/CF-3/CF-4/CF-8/Era-B/CF-2-paths all read GREEN (CF-8 and CF-2-paths pending a decision on whether the
finding-144-waived characteristics count against this specific acceptance bar or are out of scope for it — flagged for
whoever picks this up next, not resolved here).

### 2026-07-28 (slot-3, `data_engineering`) — E4 orphan-sweep todo (line ~307): built the missing `--drop-stale` tool, did NOT run it against prod

Dispatched task `data_completion_cefi-015` = "E4 remaining work = ORPHAN SWEEP + gap-fill, NOT a path walk" — the todo's
own text already flags it as "**Deliberate execution (irreversible deletes + VM-scale) — not to be rushed**", matching
the same bundled-irreversible-VM-scale shape the 2026-07-27 (slot-14) entry above correctly declined to rush for the
sibling "NEXT SESSION — execute the migration" todo. Before rushing the same class of mistake here, checked what tooling
this todo's part (a) (the irreversible orphan-delete, gated on the PRE-DELETE GUARANTEE) actually requires: **no delete
mechanism existed for cefi at all** — `migrate_cefi_flat_to_v9_canonical.py` (market-tick-data-service) only ever COPIES
(day-tree pipeline_mode= insert + L-flat fan-out), it has no `--drop-stale`/delete path, unlike its sibling
`migrate_sports_canonical_v9.py`, which already has a proven, twin-verified, backup-then-delete E8 sweep
(`_migrate_drop_stale.py`: snapshot-first → per-object twin-verify → backup-copy → parity-check → delete → verify gone →
HARD-ABORT on any mismatch, never a naive delete).

**What shipped this session** (`market-tick-data-service@e663d72f`, QG green — 7335/7335 tests incl. 3 new tests I fixed
after an initial mock-ordering bug in my own test, 238s): added a `--drop-stale` mode to
`migrate_cefi_flat_to_v9_canonical.py` reusing the SAME shared `_migrate_drop_stale.py` helper (generalised its
docstring — the module was already bucket/prefix-agnostic, sports was just its only caller until now; zero behavior
change to the sports E8 sweep). New code: `_cefi_dispatch_day_rel` (adapter matching the shared helper's
`dispatch_fn(full, bucket, surface=)` signature, delegating to the existing `_canon_day_rel`),
`_drop_stale_flat_orphans` (the 9 L-flat root orphans need a DIFFERENT check than the day-tree — a flat file fans out
1-to-many, so this verifies EVERY row's canonical destination exists before allowing the source file's delete, never a
partial-coverage delete), and `run_drop_stale` (orchestrates: manifest `_index` snapshot → day-tree raw+candle sweep →
flat-orphan sweep). Wired behind `--drop-stale` (dry-run safe by default, same convention as `--apply`). 3 new unit test
files/additions covering the adapter, the flat-orphan coverage-gate logic (fully-covered deletes, partial-coverage
never-deletes, dry-run reports-only, empty/unreadable files skipped), and the orchestration wiring — all mocked at the
`unified_trading_library.cloud_interface` boundary, no live GCS.

**What did NOT run**: the actual `--drop-stale --apply` sweep against production, and the separate `--also-legacy`
5,233-cell gap-fill. Both remain genuinely VM-scale (this same doc's E4 text: the legacy listing alone "stalled an
e2-standard-4"; the `--drop-stale` corpus-wide day-tree walk is ~2,613 days × ~474 objects/day ≈ 1.2M candidate objects)
and the delete leg is irreversible — running it start-to-finish inside one ~1h interactive dispatch would be exactly the
same mistake the slot-14 entry above already called out, not a fix for it. The existing
`launch-canonical-migration-vm.sh cefi <start> <end> {dry|full}` launcher already wires the base migrate-copy pass
(registered `canonical-migration-cefi-` VM prefix confirmed); it does NOT yet pass `--drop-stale` through — that's the
next concrete step (either a small launcher change to thread `--drop-stale` for a `cefi-drop-stale` category, or an env
override), followed by: (1) a fresh `--apply` copy pass over the FULL corpus range (the mandatory PRE-DELETE GUARANTEE —
confirms every orphan has a migrated dest), (2) `--drop-stale --apply` on a dedicated SPOT VM (per the heavy-I/O +
backfill-SPOT-default rules), monitored properly (no fire-and-forget), then (3) the `--also-legacy` gap-fill as its own
separately-launched, sharded VM pass. Did **not** flip this todo's checkbox — the sweep itself hasn't executed against
prod; flipping now would be the exact false-completion class `check_evidence_backed_completion.py` exists to catch. No
new issue doc filed (this is in-scope, bounded follow-up already named by the todo's own text, not an out-of-plan
finding).

### 2026-07-28 (slot-4, `data_engineering`) — consolidated 3 overlapping E4→E8 todos into one phased plan (main ruling BLK-650261be)

Dispatched task `data_completion_cefi-015` (the "E4 remaining work" todo immediately above) — before executing,
main-agent coordination flagged this todo, its sibling `data_completion_cefi-013` ("Orphan sweep + bucket-state
evidence"), and the older "NEXT SESSION — execute the migration" todo as THE SAME underlying E4→E8 irreversible/VM-scale
chain, already independently declined-for-execution by a 2026-07-27 slot-14 session for exactly this reason. Ruling: do
not execute; author one consolidated, phased LOCAL plan instead. Shipped this session: (1) a `cefi-drop-stale`
VM-launcher category in `deployment-service` (`scripts/vm/launch-canonical-migration-vm.sh` + 4 new regression tests in
`tests/unit/test_vm_launcher_scripts.py`, mocked-GCS only — wires slot-3's already-shipped `--drop-stale` tool into the
launcher fleet, DRY-BY-DEFAULT + `--apply` for full, `--also-legacy` via `MIGRATION_EXTRA_ARGS`, no prod invocation;
quality-gates.sh green, shipped `deployment-service@9dd27ff`); (2) the new plan
`plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` — 6 phases (A: pre-delete-guarantee copy
pass, B: the irreversible orphan-sweep delete, C: legacy gap-fill, D: E5 rebuild gated on the false-phantom fix, E: E7
verify, F: E8 legacy-bucket delete triple-gated) all `[OPERATOR]`/human-supervised. All three source todos above
annotated `SUPERSEDED-BY` inline (checkboxes left UNCHECKED — no sweep has run against prod). Did **not** flip any of
the three todos' checkboxes.
