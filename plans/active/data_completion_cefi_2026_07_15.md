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
last_updated: 2026-07-24 # (was: 2026-07-15 -- folded in the CeFi-lane Progress Log entries from M-1 per plan line-cap remediation)
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

- [ ] [DATA] P0. **⑧ — IS cefi REFERENCE-UNIVERSE gap: catalogue not ⊇ manifest present-set (CF-14, falsely-high
      coverage). 🟢 ROOT-CAUSE CODE FIX SHIPPED `is@a6bc4d48`; operational backfill re-run + CLOB sub-part remain.**
      Real-prod (2026-06-08): IS `instruments-store-cefi-prd` `instrument_availability/by_date/day=2026-05-22/` lists
      only **12 venues** {ASTER, BINANCE-FUTURES/SPOT, BITFINEX-FUTURES, BYBIT, COINBASE-SPOT, DERIBIT, HYPERLIQUID,
      OKX-FUTURES/SPOT/SWAP, UPBIT}; the MTDS manifest captures **45 venues** ⇒ **29 captured venues absent from IS
      reference = 108,556 captured rows (8.3%)**. Headline genuine gaps: **KRAKEN-SPOT (75,714) + KRAKEN-FUTURES
      (31,582)** (KRAKEN-FUTURES verified on disk `day=2026-05-24`), **BITFINEX-SPOT**, **PACIFICA-SOLANA (309)**,
      **LIGHTER-ZKSYNC (319)**. **ROOT CAUSE FOUND (corrects the earlier "dynamic universe" read):** the IS Tardis
      reference adapter (`reference_data/adapters/cefi/tardis.py`) had a **hand-maintained `_DEFAULT_EXCHANGES` of 8
      Tardis exchange-ids** (`binance/binance-futures/bybit/okex/deribit/coinbase/upbit`) that had **silently DRIFTED
      below the canonical SSOT `VenueMapping.all_tardis_exchanges` (20)** — omitting `kraken`, `cryptofacilities`
      (=KRAKEN-FUTURES), `bitfinex`, `bitget`, `lighter-zksync`. (My KRAKEN/DERIBIT grep missed it because the list uses
      lowercase Tardis _exchange-ids_, not canonical venue NAMES — the SSOT already maps `kraken→KRAKEN-SPOT`,
      `cryptofacilities→KRAKEN-FUTURES` with start-dates.) So the IS reference backfill never queried those venues →
      catalogue ⊉ present-set → falsely-high coverage. **(1) ✅ CODE FIX SHIPPED `is@a6bc4d48` (QG --no-fix green):**
      `_DEFAULT_EXCHANGES = list(VenueMapping().all_tardis_exchanges)` (derives from SSOT → no future drift; verified
      ==SSOT, now includes kraken/cryptofacilities/bitfinex/bitget/lighter-zksync) + extended
      `_DERIVATIVES_ONLY_EXCHANGES`
      (cryptofacilities/okex-futures/okex-swap/huobi-dm/bitfinex-derivatives/bitget-futures) so unknown-type instruments
      aren't mis-defaulted to SPOT + 3 regression tests asserting no-drift-from-SSOT. **(2) OPERATIONAL (owner:
      `instruments_backfill_phase3` / vm-cross-cutting) — re-run the IS reference backfill with the fixed universe so
      `instrument_availability/by_date/` ⊇ the MTDS captured present-set (memory-heavy multi-year VM sweep — the adapter
      cache OOM-killed `cefi-instr-deribit` 2026-05-04, run on a VM).** **(3) CLOB venues PACIFICA-SOLANA +
      LIGHTER-ZKSYNC are NOT Tardis exchanges — they ride the CLOB adapter path (hyperliquid.py / aster.py); confirm an
      IS reference adapter enumerates them (only hyperliquid+aster exist today) — separate from the Tardis fix.** **(4)
      diagnose the ~650 `*F0`/`UNKNOWN`-venue manifest-pollution rows (blank instrument_type/instrument_id) — reconcile
      or demote.** Gates honest coverage denominator (⑦/⑧), NOT the G4 data/manifest `--apply`. **Big finding — operator
      notified 2026-06-08.** Provenance: slot-3 pre-apply audit 2026-06-08 (real-prod catalogue vs manifest walk + IS
      adapter `_DEFAULT_EXCHANGES` root-cause). **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

- [ ] [CODE] P1. **execution-service — `data/loaders/defi.py:41,77` DeFi raw-tick reads still legacy (slot-2/defi
      owner).** The shared `candidate_parquet_paths` DeFi branch needs a `chain` kwarg
      (`build_defi_partition_path(venue, chain, …)`) + a defi instrument-id→chain mapping that the cefi-scoped fix did
      not supply (calling it as-is raises `KeyError("chain")`). `loader.py` `load_swaps`/`_build_swaps_paths` DeFi paths
      likewise unchanged. Mirror the cefi `canonical_paths.build_candidate_raw_tick_paths` pattern with the defi chain
      axis. Target repo: execution-service (DeFi slice). Provenance: cefi E2E audit 2026-06-04 (the cefi P0 above is
      GREEN; this is the defi sibling).

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

- [ ] [CODE] P1. **deployment-api CeFi pipeline_mode dedup + drilldown filter** (deployment-api; downstream owner).
      **CONFIRMED read-only (slot-3 2026-06-03):** the dedup MECHANISM exists + is AG-agnostic — the count is
      `len(captured_df.drop_duplicates(subset=_shard_atom_cols))` and `_shard_atom_cols` derives from the UAC
      `SHARD_AXIS_MATRIX`, which for cefi is `(venue, data_type, instrument_type, instrument_id, day)` — pipeline_mode
      is NOT a cefi shard-atom axis, so multiple `pipeline_mode=` rows for one cell collapse to ONE shard (no
      double-count). The existing `test_pipeline_mode_rows_do_not_double_count_shards` guards the DeFi
      **chain**-breakdown builder; REMAINING for the deployment-api/`downstream_services_manifest_canonicalisation`
      owner: (a) a **cefi parity test** (venue-breakdown builder) as a regression guard, (b) the `pipeline_mode`
      drilldown **filter param** (a feature-add; UI label is playwright-gated). NOT a cefi-correctness gap today (dedup
      works); a regression-guard + feature enhancement for the deployment-api owner. (In practice cefi double-count is
      also unlikely — a cefi cell carries ONE pipeline_mode per day, batch OR live, not both.)

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

- [ ] [DATA] P1. **Before the REAL `_index` rebuild — multi-year dry-run phantom spot-check**: re-run
      `rebuild_cefi_manifest --dry-run` over a multi-year span (or the full corpus) and confirm `phantom_to_failed`
      stays small + well-formed (DERIBIT-chain-style true phantoms only), `dropped_malformed_captured` is junk-only, and
      `unparseable=0`. Cheap final gate before the irreversible-adjacent index overwrite. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. **NEXT SESSION — execute the migration** (after the dry-run validates perf): run the 8 year-sharded
      `--also-legacy --apply` gap-fill (5,233 legacy-only cells), then the irreversible orphan-sweep (with the mandatory
      pre-delete idempotent-`--apply`-over-full-range guarantee), then E5 manifest rebuild (now CF-11-canonical +
      false-phantom-safe @mtds#fa2b02c7+this-fix), E7 verify, E8 legacy-bucket delete. NOT this session (irreversible).
      **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. C-pipeline_mode RIDER (folded into C0 (d)): the `pipeline_mode=` partition lands in THIS walk
      (satisfies `pipeline_mode_partition_migration` for cefi). **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. C-source RIDER (folded into C0 (b)): the `source` column (`tardis`, swap-resilient) lands in THIS walk
      (closes `data_source_provenance` cefi). **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. Post-walk: re-read the canonical `_index` DATA-STATE (re-run the reusable audit tool) → **100% of rows
      v9** (was 100% v8); **`source` populated on every cell** (zero blank; `tardis`, swap-resilient); **`asset_group`
      column/key present** (no `category`/blank); **`pipeline_mode` non-blank + partition present**; typed reasons;
      **legacy-only CELLS = 0** (838-gap closed). Closes `data_source_provenance` cefi + `pipeline_mode_partition` cefi.
      C-GREEN signal for `bucket_name_ssot…` Phase 6/7 cefi legacy bucket decommission. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. **Orphan sweep + bucket-state evidence (slot/Harsh bucket-state verification 2026-06-02).** Measured
      (Cloud Monitoring `storage/v2/total_count`, live-object): `market-data-tick-cefi-prd` 1,545,850 (~65% of legacy
      2,377,168) and **~17 days STALE — `-prd` latest `day=2026-05-07` vs legacy `day=2026-05-24`** (consistent with the
      5,233 legacy-only cells; the C0 gap-fill closes it by reading legacy as source). `-prd` is INTERMEDIATE FORM:
      `asset_group=cefi` is in the PATH but there is **NO `pipeline_mode=` partition** (confirmed at the data level, not
      just the manifest). So the E4 walk writes NEW `pipeline_mode=` paths → the pre-existing legacy-FORM `-prd` objects
      become ORPHANS; E5 rebuild / E7 verify MUST delete the legacy-FORM `-prd` objects too (not only the legacy SOURCE
      bucket), else the rebuild double-counts. Legacy carries 3.81M noncurrent objects → the E8 delete must also purge
      noncurrent versions, and the "canonical ≥ legacy" count gate must use Monitoring `type=live-object` (never a naive
      recursive `ls`, which counts versions + soft-deleted). **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. **❌ RETRACTION of the earlier "E4-BUG / we-keep-missing-things" P0 (it was WRONG).** I read
      `moved=0` + a `head -3` listing (which shows `asset_group=` paths — they sort BEFORE `pipeline_mode=`) and wrongly
      concluded "no `pipeline_mode=` sibling / migrator no-ops L-bulk". The FULL listing shows the `pipeline_mode=`
      siblings DO exist (482/day). slot-10's `C2 = day=/asset_group=cefi/` count is exactly these **post-migration
      orphans**, not a pre-migration gap. No migrator fix is needed. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. **E4 remaining work = ORPHAN SWEEP + gap-fill, NOT a path walk.** (slot-3 verify 2026-06-03: the
      `pipeline_mode=` migration is COMPLETE corpus-wide — sampled days 2020→2026 ALL have both forms; the **9 L-flat
      orphans are ALSO migrated** (e.g. `SOL-ETH.parquet` →
      `day=2024-11-07/pipeline_mode=batch_tardis/…/SOL-ETH.parquet` exists; the 9 root files remain only as orphans). So
      the ONLY additive work left is the legacy gap-fill.) (a) **🛑 IRREVERSIBLE — delete the OLD
      `day=/asset_group=cefi/…` (no-`pipeline_mode=`) orphan objects corpus-wide (~474/day × ~2,613 days ≈ 1.2M) + the 9
      root L-flat orphans** now their `pipeline_mode=` forms exist. PRE-DELETE GUARANTEE (mandatory): first run
      `migrate_cefi_flat_to_v9_canonical --apply` over the FULL range once (idempotent — copies any orphan still lacking
      a sibling, skips the rest) so EVERY orphan provably has a migrated dest; THEN delete (count via Monitoring
      live-object, NOT naive recursive `ls`; per-object isolation; idempotent). This IS the E7 orphan-sweep. (b)
      `--also-legacy` 5,233-cell legacy→canonical gap-fill (additive; VM-scale — the 1.9M legacy listing stalled an
      e2-standard-4, so shard/bigger-mem). **Deliberate execution (irreversible deletes + VM-scale) — not to be
      rushed.** Repo: market-tick-data-service. **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

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

- [ ] [DATA] P0. **Absorbed from `cefi_processed_candles_manifest_file_disconnect` (harsh) — ROOT CAUSE CORRECTED by
      direct `_index` query (slot-3 2026-06-03).** The reported "MTDS marks `processed_candles` `captured` with no file"
      is a **category error, NOT manifest corruption.** Reading the live cefi `_index` (2,640,864 rows): the manifest
      **already disambiguates surfaces via `data_type`** — RAW tick (`trades` 1.19M / `book_snapshot_5` /
      `derivative_ticker` / `liquidations` / `futures_chain`, ~all `service_name=market-tick-data-service`) vs CANDLE
      (`ohlcv_1m/5m/15m/1h/4h/1d`, **only 8,715 rows**, mostly `service_name=market-data-processing-service`). The issue
      cross-checked `processed_candles/` FILES against **`trades`-captured** rows; a `trades` `captured` row (MTDS)
      correctly means the **RAW** tick file exists (VERIFIED: day=2026-05-02 BITFINEX/BITGET/KRAKEN raw `trades` files
      present) — the manifest **never marked CANDLES captured** for those venues (on 2026-05-02 KRAKEN/BITFINEX have NO
      `ohlcv` rows at all). So MTDS is NOT writing phantom processed-candle rows; hypothesis (b) is disproved and the
      `reconcile_phantom_manifest_rows_all.py` flip-to-`attempted_failed` would WRONGLY demote correct raw rows (it only
      probes `raw_tick_data/` anyway). Real findings to action (3 sub-items, repos noted):
  - [x] ✅ [CODE] P0. **Read-side contract fix (features-service)** — **DONE (features-service@933b8747, slot-3
        2026-06-03).** `LookbackValidator._build_captured_index` credited ANY captured `data_type` as a candle-available
        lookback date (raw `trades`/`book_snapshot_5` over-counted history off the shared `_index`); now filters to the
        feature*groups' candle `ohlcv*\*`data_types via`resolve_data_type_for_feature_group`(mirrors the
        already-correct`get_available_instruments`). +regression test (`ohlcv_1m`counted;`trades`/`book_snapshot_5`
        not). Verified delta_one 20/20 + basedpyright-clean diff. **Shipped under operator EXEMPTION** (local macOS QG
        red only on the foreign non-deterministic flake `features_service_full_qg_test_pollution_flake_2026_06_03.md`;
        Linux `quality-gates-v2` re-verifies at promotion). Repo: features-service.
  - [ ] [DATA] P1. **Real cefi candle-coverage gap (partial backfill).** `ohlcv_*` manifest rows are sparse (8,715) and
        processed-candle FILES exist only for a partial venue set (BITGET-heavy; e.g. day=2026-05-03 = BITGET-FUTURES
        319 / BITGET-SPOT 151 / BITFINEX-FUTURES 90 / KRAKEN-FUTURES 18). MDPS candle generation for cefi is incomplete
        → track + complete the candle backfill (separate from raw-tick canonicalisation). Repo: MDPS.
  - [ ] [DATA] P1. **VERIFY MDPS candle-manifest faithfulness.** Do the `ohlcv_*` rows faithfully reflect the candle
        files that DO exist, or is MDPS under-emitting `ohlcv` rows for written candle files? Compare `ohlcv` row
        coverage vs candle-file coverage on a sample day. Also reconcile the minor cross-writes (782 MTDS-written
        `ohlcv` rows; 616 MDPS-written `trades` rows) — confirm which service legitimately emits `ohlcv` per venue (MTDS
        REST-poll venues like LIGHTER/PACIFICA vs MDPS-processed). Repo: MDPS (+ MTDS REST-poll path). On all three
        GREEN, archive the absorbed issue doc. **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`,
        2026-07-13 per MTDS consolidation ruling.)**

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
