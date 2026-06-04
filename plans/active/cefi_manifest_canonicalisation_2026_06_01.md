---
title: "CeFi legacy gap-fill + manifest canonicalisation (single-walk) — L3 owner for cefi"
created: 2026-06-01
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-cefi
status: active
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by: live-defi-rollout
locked_since: 2026-06-01
source:
  - bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md (L3 ordering — cefi had NO owner)
  - _index comparison 2026-06-01 (cefi canonical ~complete: 838 legacy-only captured cells out of 91,602)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# CeFi legacy gap-fill + manifest canonicalisation (L3 owner for cefi)

> **🔎 CROSS-AG FINDING from defi (2026-06-01) — CHECK THE SAME HERE**: defi's CF data-state audit found the legacy
> `_index` **100% NOT v9** (v4/5/6/8 spread), with **no `source`/`asset_group`/`pipeline_mode` COLUMNS** and glued
> venues (`AERODROMEV3`/`TRADER_JOEV2`) — a FULL re-canonicalisation, not the headline cell-count. **CF-2 gotcha**: the
> migrate tool emitted `asset_group=` to the object PATH but did NOT stamp it as a parquet COLUMN → the rebuilt `_index`
> lacked the column. Fix = stamp `asset_group` (+ `schema_version`/`source`/`pipeline_mode`) as COLUMNS, never rely on
> the consolidator deriving them from the path. **Action**: run a CF data-state audit on cefi's `_index` as pre-flight +
> verify (reusable: `market-tick-data-service/market_tick_data_service/scripts/audit_canonical_form.py` or
> `plans/audit/results/cf_manifest_audit_2026_06_01.py`) — trust the real data-state, never the v9 constant. If the same
> debt shows → fix fully in-walk (scope is a prior, not a ceiling). SSOT:
> `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md`.

> **MASTER**: `defi_manifest_canonicalisation_2026_06_01.md` §MASTER (L3, cefi lane). **Single-walk discipline (HARD
> RULE)**: ONE bundled walk on the cefi `_index` — bundle the **full v8→v9 re-version + `source` column + `asset_group`
> column + `pipeline_mode=` partition** (see the data-state finding below) **AND** the 838-cell gap-fill; do NOT open a
> second walk. `pipeline_mode_partition_migration` + `data_source_provenance` (cefi) ride THIS walk.

> **🔴 DATA-STATE FINDING (2026-06-01, slot-3 audit) — cefi is a FULL re-canonicalisation, NOT an 838-cell gap-fill.**
> Reading the ACTUAL canonical cefi `_index` (not the constant — the manifest-v8 lesson): **100% of rows are v8 (CF-1
> RED, not v9)**, there is **no `source` column (CF-4 RED)**, **no `category`/`asset_group` column (CF-2 RED)**, and
> **`pipeline_mode` is blank (CF-3 RED)**. So the headline "~complete / 838-cell gap" was a coarse PRIOR; the data-state
> is the truth and the scope is the whole corpus. Per the **"Audit scope is a prior, not a ceiling —
> fix-fully-autonomously"** HARD RULE (`canonical_form_cross_service_audit_checklist.md`), this is **fixed FULLY and
> AUTONOMOUSLY in the one bundled walk** — NOT descoped to 838 cells, NOT deferred, NOT blocked-on-operator. Capture the
> remaining schema signal (`error_reason` for CF-5, object paths for CF-2/3/9) into a **reusable audit tool**, then the
> walk lands every CF-1…CF-12 fix.

## Slot-3 CeFi master orchestrator — owned + attached plans/issues

> **Slot↔asset-group split (operator 2026-06-03):** one asset group per slot. **Slot 3 = CeFi end-to-end** across every
> service — instruments-service → MTDS → MDPS → features → downstream → bucket/data/manifest/UI. **THIS plan is the CeFi
> master orchestrator**: every cefi-related plan + issue cross-references here; orphaned cefi issues attach here.
> Sibling AG masters: **defi → slot 2**, **sports → slot 4**, **prediction → slot 5**
> (`prediction_manifest_canonicalisation_2026_06_01.md`), **tradfi → slot 6**
> (`tradfi_manifest_canonicalisation_2026_06_01.md`). Cross-cutting service plans keep their own `assigned_vm` (vm-ml /
> vm-cross-cutting) as PRIMARY owner — slot-3 tracks + drives only their **cefi slice**, not the whole plan.

**Absorbed (cefi-primary — slot-3 owns outright):**

- `issues/cefi_processed_candles_manifest_file_disconnect_2026_05_25.md` — **ABSORBED 2026-06-03** (harsh out for the
  day; was harsh-held). The manifest↔file disconnect (MTDS marks `processed_candles` `captured` for KRAKEN/BITFINEX with
  no file; ~42% phantom on the test date) IS the CF-11 honest-absence reconciliation this plan owns — folded as the
  CF-11 "MTDS processed_candles phantom-`captured` reconcile" todo below. Issue doc archives when that todo is GREEN.

**Cross-referenced cefi slices (primary owner keeps the plan; slot-3 drives the cefi portion):**

| Plan / issue                                                                                                                    | Primary VM         | CeFi slice                                                                            |
| ------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------- |
| `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`                                                                  | vm-cross-cutting   | L3 cefi ordering + L6 legacy `market-data-tick-cefi` delete (this plan's E8 hand-off) |
| `data_source_provenance_all_asset_groups_2026_06_01.md`                                                                         | vm-ml              | cefi `source=tardis` column (this plan's C-source RIDER)                              |
| `pipeline_mode_partition_migration_2026_06_01.md`                                                                               | vm-cross-cutting   | cefi `pipeline_mode=` partition (this plan's C-pipeline_mode RIDER)                   |
| `data_pipeline_acquisition_remediation_2026_06_03.md`                                                                           | orchestrator-agent | cefi audit-finding phase                                                              |
| `issues/gcs_hive_partition_malformed_paths_remediation_2026_06_01.md`                                                           | vm-ml              | cefi 9 root-level real-data files (SUPERSEDED by E2 migrator)                         |
| `features_input_manifest_migration` / `features_service_e2e_pipeline_test` / `features_calc_efficiency_and_correctness`         | vm-ml              | cefi processed_candles read-path + e2e + calc correctness                             |
| `mdps_filter_pushdown_memory_audit_and_fix` / `mdps_pure_polars_migration` / `mdps_long_running_multi_shard_architecture_audit` | vm-ml              | cefi MDPS processing slice                                                            |
| `issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md`                                                                     | vm-ml              | cefi state adapters (derivative / futures / options / book_snapshot)                  |

## 🎬 NEXT-SESSION HANDOFF (slot-3 cefi, paste-ready, 2026-06-03)

**GOAL:** complete CeFi work **up to and including the dry-run VM + bucket creation**. **HARD CONSTRAINT (operator):**
EVERY coding task across ALL repos must be DONE + green-on-LDR **before** you launch the dry-run VM or create any
bucket. Code first; GCS execution only after.

**OUT OF SCOPE this session (deliberate, later):** the IRREVERSIBLE ~1.2M-object orphan delete (old
`day=/asset_group=cefi/` no-`pipeline_mode=` objects + 9 L-flat root files) and the **E8 legacy-bucket delete**. Do NOT
run them — they need the pre-delete idempotent-guarantee + verification + operator awareness.

**STATE — DO NOT RE-DERIVE (verified 2026-06-03):** the `-prd` `pipeline_mode=` migration is **COMPLETE corpus-wide**
(raw_tick + candles + 9 L-flat all have canonical forms; sampled 2020→2026). The migrator WORKS — the "E4-BUG" claim was
**RETRACTED** (`moved=0` = idempotent-skip). Only ADDITIVE data work left = the `--also-legacy` 5,233-cell gap-fill. E5
rebuild DONE (mtds@2c3a479b). features-service residual #1 (933b8747) + conftest fix (d39d154f) SHIPPED; the
features-service full-QG flake is **macOS-local** (Linux `quality-gates-v2` green — don't chase on Linux; ship via
operator exemption if a local macOS gate blocks).

**PHASE 1 — ALL CODING (ship each via quickmerge; flip the checkbox same-turn):**

- [x] ✅ [CODE] instruments-service — CF-11 IS-side write-path: cefi reference-data adapters now **raise on a genuine
      fetch-failure** (→ `_fetch_one` `failed[]` → `attempted_failed`) instead of `return []` (which landed the venue in
      `_non_error_venues` → excluded from `expected_venues` → silent universe shrink, worse than `empty_confirmed`).
      Cross-AG sweep slot-6@e2e008f0 fixed aster/hyperliquid/tardis (RuntimeError); slot-3 completed the one they missed
      — **DeribitCombo** (`get_instruments` tracks per-currency `failures`, re-raises if EVERY currency failed; partial
      success preserved) — instruments-service@f2ca5954 + regression tests (IS QG --no-fix exit 0, 3097 pass). Mirrors
      the tradfi databento CF-11 fix. (cefi CF-11 below)
- [x] ✅ [CODE] market-data-processing-service — CF-11 #3: **VERIFIED no emission bug** (slot-3 grep-then-READ
      2026-06-03). The apparent ohlcv "under-emission" is the **intended WriteGate honest-coverage** behaviour —
      `canonical_writer.py:1318-1322` documents that policy-gated rows write bytes (heartbeat) but deliberately skip the
      manifest `captured` row; the normal path emits exactly one row per published candle; a manifest-write failure
      emits `MANIFEST_WRITE_FAILED` (not silent). So MDPS faithfully reflects published candles. The real `ohlcv` gap
      (8,715 rows; BITGET-heavy files) is a **candle BACKFILL (DATA)**, not a code bug → tracked as the CF-11 #2
      candle-coverage DATA item below. No MDPS code change.
- [ ] [CODE] unified-trading-pm — identity-hook follow-ups (`issues/commit_identity_misconfig_fleet_2026_06_03.md`):
      root-cause the bot-email leak + recurrence-guard in `verify-slot-host-symmetry.sh`; `setup-tab-worktrees.sh`
      provisions `extensions.worktreeConfig` + `--worktree` identity. SSOT:
      `codex/05-infrastructure/per-tab-worktrees.md` § "Commit attribution". (EDITS DONE — leak root-caused
      `rollout-semver-agent.sh:117` shared-config write → one-shot `git -c`; `setup-workspace-from-manifest.sh:345`
      `--global agent@ci.local` → only-seed-if-unset canonical; provisioning + recurrence-guard added. Pending PM QG
      ship.)
- [x] ✅ [CODE] market-tick-data-service — orphan-sweep/gap-fill **VERIFIED needs no code** (slot-3 2026-06-03): the
      migrator `migrate_cefi_flat_to_v9_canonical.py` already handles `--also-legacy` over all 3 layouts, idempotent
      skip-if-exists = copies ONLY the gap. The explicit orphan-DELETE mode is deliberately NEXT session (irreversible).
- [ ] grep this plan for remaining open `[ ] [CODE]` todos.

**GATE:** confirm ALL Phase-1 coding shipped + `quality-gates-v2` green on LDR per repo BEFORE Phase 2.

**PHASE 2 — DRY-RUN VM + BUCKET CREATION (only after Phase-1 green):** create any buckets the plan needs (via
`resolve_bucket_name`, never inline `gs://`); re-run the E4 **dry-run** on a VM to measure the REMAINING scope (the
`--also-legacy` gap-fill + orphan count — NOT the done `-prd` walk), **sharded by year / bigger-mem** (the 1.9M legacy
listing OOM'd an e2-standard-4). `VM_TASK=canonical-migration`,
`VM_MIGRATION_CMD=… migrate_cefi_flat_to_v9_canonical --start-date … --end-date … --also-legacy` (NO `--apply` = dry).
No-fire-and-forget (STARTED + T+10min + read `…/vm-logs/<vm>/run.log`). STOP at dry-run + bucket creation — the
`--apply` gap-fill / orphan delete / E8 are the NEXT session.

## E2E code-readiness audit (slot-3, 2026-06-03) — get the CODE canonical BEFORE the migration runs

> **Operator framing**: "code e2e" = after the migration runs, future backfills + code + data-status summary + drilldown
> all align with the migrated structure. The migration's PATH/SCHEMA/COLUMNS must be IDENTICAL in the writers, readers,
> preflight gates, manifest rebuild, and deployment-api/UI — and empty + partial must be handled the same in code as in
> reality. 5-dimension audit (path / schema-columns / empty-partial / data-status-UI / plan-sweep).

### 🚦 CeFi E2E RUN-READINESS GATE (full IS→execution audit, 2026-06-04, slot-3 + sub-agents)

> **Operator bar (2026-06-04):** before the migration runs, ALL of the below must be DONE + ticked: ① migrator dry-run,
> ② manifest-rebuild dry-run, ③ **pre-flight engrained on EVERY service IS→execution using the canonical post-migration
> paths**, ④ **empty/partial handled honestly** — the zero-volume / NaN / last-price-forward-fill candle taxonomy in
> MDPS
>
> - downstream consuming it correctly (batch AND live), ⑤ **read+write paths match the post-migration shape
>   everywhere.** A full IS→MTDS→MDPS→features→strategy→execution audit (2026-06-04) ran each layer against the
>   canonical `day=/pipeline_mode=batch_*/asset_group=cefi/venue=/instrument_type=/data_type=/` SSOT
>   (`build_cefi_partition_path` / `candidate_parquet_paths` / `resolve_bucket_name`). **VERDICT: NOT-YET-READY — 2×P0 +
>   2×P1 migration-blocking gaps.**

**✅ READY (verified this audit — do not re-litigate):**

- **IS** — reference-store writes go through `resolve_bucket_name`/`get_write_bucket_name` + canonical prefixes
  (`catalogue_builder.py:185`, `orchestrator.py:1859`); manifest `record_*` pass explicit `pipeline_mode=`;
  skip-existing pre-flight (`instruments_handler.py:64`). IS writes its OWN `instruments-store-*`, not `raw_tick_data`,
  so the pipeline_mode raw-tick rule doesn't bind it. PATH-PARITY MATCH.
- **MTDS batch** — cefi batch writer routes `build_cefi_partition_path` + inserts `pipeline_mode=` LEFT of
  `asset_group=` (`engine/orchestrator.py:930-1005`); reader 3-level fallback probes canonical FIRST
  (`reader.py:281-295`); capture pre-flight `_skip_states={CAPTURED,EMPTY_CONFIRMED}`, retries `attempted_failed`,
  bait-sentinel guard (`orchestrator.py:2201-2228`). Migration-safe.
- **MDPS candle-absence taxonomy is HONEST** — `base_adapter._finalize_session_grid` produces a dense session grid:
  no-trade bin in a live session → **forward-filled `o=h=l=c=prev_close`, `volume=0`** (zero-volume + last-price), state
  streams zero-fill flow cols (never NaN), pre-first-obs bins → NaN (honest), fully-empty shard → `record_empty` (the
  banned 1440-NaN-placeholder shape was removed, mtds@d717c59 / per-tf `record_empty_for_shard`). All 5 core cefi
  adapters (trades/book_snapshot/derivative/futures_chain/options_chain) route the session grid. Aggregator
  (`fast_candle_aggregation.py:304`) NaN-guards the rollup. Read+write canonical.
- **features-service** — cefi reads via `candidate_parquet_paths("cefi",…)` + `resolve_bucket_name`
  (`cefi/calculators/perp_funding_rates.py:115`), honest null handling (no `fillna(0)`; emits typed
  `record_empty(EXPECTED_NO_FUNDING_RATE_TICKS)`), 4-state pre-flight (`volatility/core/data_loader.py:43`). This repo
  is the **reference exemplar** — bring strategy + execution cefi reads to parity with it. PATH MATCH / PRE-FLIGHT
  PRESENT / CANDLE SAFE.

**🔴 P0 — migration-BLOCKING (must be DONE + ticked before the real run):**

- [x] ✅ [CODE] P0. **MTDS live cefi writer path divergence — FIXED (mtds@318473eb).** `live_tick_blob_path`
      (websocket_runner.py) now routes cefi through the SAME UAC `build_cefi_partition_path` the batch writer uses
      (byte-identical) with `pipeline_mode=live_websocket` LEFT of `asset_group=`, venue UPPER +
      instrument_type/data_type lower (reader case-parity); `instrument_type=` threaded from the flush call site (was
      discarded); defi/other mirror the reader's generic order (chain before venue). +regression tests asserting
      reader-order + case parity. **MDPS lockstep `default_tick_blob_path` fixed the same way (mdps@b9b3263, QG exit
      0).** MTDS QG exit 0. (Also shipped: P2 `reader.read_from_manifest` lifts pipeline_mode from the captured row —
      canonical path probed first.)
- [x] ✅ [CODE] P0. **execution-service legacy raw_tick paths → UAC SSOT — FIXED (execution@6230c18d0).** Was: ALL raw
      candle/mark/orderbook reads hardcode `raw_tick_data/by_date/day={date}/data_type={dt}` with NO
      `pipeline_mode=`/`asset_group=cefi/` (`data/loaders/base.py:182`, `data/checker.py:155,323`,
      `data/loader_transforms.py:150`, `data/loaders/defi.py:41,77`, `data/loader_local.py:62`,
      `l2_depth_provider.py:34` `_L2_ORDERBOOK_PATH_TEMPLATE`). Relies ENTIRELY on the reader-fallback that Phase 8
      removes (~2026-06-15) ⇒ cefi backtest + live mark reads silently return EMPTY after cutover. **Fix:** route every
      raw read through `candidate_parquet_paths()` (pipeline_mode-aware first, legacy fallback) — mirror
      features-service `perp_funding_rates.py`. **DONE:** new `data/canonical_paths.py` SSOT
      (`build_candidate_raw_tick_paths` canonical-first + legacy fallback, probe both → works pre/post-migration) wired
      into loader_base/loaders.base/ loader_transforms/loader_local/l2_depth_provider; signatures unchanged; +18 tests;
      basedpyright 0; QG exit 0.
- [ ] [CODE] P1. **execution-service — `data/loaders/defi.py:41,77` DeFi raw-tick reads still legacy (slot-2/defi
      owner).** The shared `candidate_parquet_paths` DeFi branch needs a `chain` kwarg
      (`build_defi_partition_path(venue, chain, …)`) + a defi instrument-id→chain mapping that the cefi-scoped fix did
      not supply (calling it as-is raises `KeyError("chain")`). `loader.py` `load_swaps`/`_build_swaps_paths` DeFi paths
      likewise unchanged. Mirror the cefi `canonical_paths.build_candidate_raw_tick_paths` pattern with the defi chain
      axis. Target repo: execution-service (DeFi slice). Provenance: cefi E2E audit 2026-06-04 (the cefi P0 above is
      GREEN; this is the defi sibling).

**🟡 P1 — pre-flight engrained (blocking the "pre-flight on every service" bar):**

- [x] ✅ [CODE] P1. **strategy-service cefi pre-flight — DIAGNOSED over-flagged; the REAL gap was P2 (FIXED).**
      Grep-then-read correction: `service_entry.py:648`'s `market-data-tick-cefi` is the **GAP-5 consolidator-HEALTH
      startup gate** (`assert_consolidator_healthy`), NOT a raw-tick data read — strategy consumes **features**
      (features-delta-one, already in `UPSTREAM_DEPS` + 4-state-gated via `check_allocation_manifest`), not raw cefi
      ticks. So no raw-tick `UPSTREAM_DEPS` entry is warranted (a `required` one would be wrong). Strategy's cefi
      pre-flight already exists (consolidator-health + features 4-state). The actual cefi gap was the allocation guard
      hitting the WRONG features bucket — see P2 (now P0-level), **FIXED**.
- [x] ✅ [CODE] P1. **execution-service manifest 4-state pre-flight — ADDED (execution@6230c18d0).** Was:
      `data/checker.py` (`check_gcs_file_exists` / `check_data_availability` / `blob_exists` `:168,214,335`) is a raw
      path-EXISTENCE probe — never reads `availability_index` / `capture_status`, so it cannot tell zero-volume /
      `empty_confirmed` / `attempted_failed` from genuinely-missing. **DONE:**
      `canonical_paths.resolve_manifest_capture_status()` (4-state, fail-open) gates `checker._gcs_lookup_and_check` —
      empty_confirmed→honest-absence skip, attempted_failed→skip+alert, captured/unknown→proceed.

**⚪ P2/P3 — correctness hardening (not run-blocking but in-scope for "engrained"):**

- [x] ✅ [CODE] P1(↑from P2). **strategy-service allocation guard hit the WRONG features bucket for cefi — FIXED.**
      `cli/handlers/batch_handler.py:_check_manifest_for_category` (called per-category incl. cefi at :480) hardcoded
      `kind="features-sports"` for EVERY category. cefi features live in `features-delta-one` (cloud-providers.yaml:67
      `features-delta-one-cefi-${GCP_PROJECT_ID}`); `features-sports` is the sports-only flat key. ⇒ a cefi allocation
      cycle resolved a sports bucket, found no availability index, and **FAILED OPEN** (`capture_status="unknown"` →
      proceed) — the 4-state allocation gate was a silent **no-op for cefi**. **FIXED:**
      `features_kind = "features-sports"     if asset_group=="sports" else "features-delta-one"` (sports behaviour
      unchanged; cefi/defi/tradfi/prediction now gate on their REAL features index). This was the real "strategy cefi
      pre-flight" gap (P1 above was the red herring). **DONE — strategy@879d1bbd, QG exit 0** (+ regression test).
- [x] ✅ [CODE] P2. **market-tick-data-service** — `reader.read_from_manifest` (`reader.py`) now LIFTS `pipeline_mode`
      from the captured manifest row into `read_shard` so the canonical `pipeline_mode=` path is probed FIRST (caller
      override still wins). +2 regression tests. Was leaving manifest-driven reads on the soon-removed bare fallback.
      **DONE — mtds (shipping with the P0 live-writer fix).**
- [x] ✅ [CODE] P2. **execution-service** — `l2_depth_provider.py` `from google.cloud import storage` / `gcs.Client()` →
      `get_storage_client()` (cloud-agnostic). **DONE — execution@6230c18d0.**
- [ ] [DATA] P3. **market-data-processing-service** — leading-NaN before first observation for state adapters that skip
      the session-grid finalize (already tracked: `issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md`). Confirm
      all cefi adapters route `_finalize_session_grid`; liquidations (no grid) is intentional event-counts — verify.
- [ ] [CODE] P3. **strategy-service** — `gcs_feature_provider.py:99` `merged.ffill()` across sampling frequencies could
      mask a genuine gap; gate with a staleness limit (strategy — still open). **execution-service**
      `benchmark_service.py` stale `gs://` comment refreshed ✅ (execution@6230c18d0).

### 🔎 DIMENSION 6 + 7 AUDIT (IS/UAC instrument guardrails + could-exist denominators, 2026-06-04, slot-3 + sub-agents)

> Operator extended the readiness bar: **⑥** code must GUARDRAIL against using instruments / fixtures /
> (venue×instrument_type×data_type) combos that **cannot exist** per IS+UAC; **⑦** deployment-api/ui coverage must use
> the **universe of what COULD exist** (IS instruments × UAC valid combos × upstream availability) as the DENOMINATOR,
> with the manifest marking could-exist-but-not-yet-backfilled cells as `expected_unattempted` (not invisible / no row).

**✅ VERIFIED (Dim 6 — IS/UAC guardrails, mostly in place):**

- MTDS cefi capture resolves its universe + venue URLs FROM IS, per date: `engine/cefi_catalog_reader.py:62-236`
  (`CeFiCatalogReader.list_instruments` filters status/availability-window per processing-date), wired at
  `orchestrator.py:2148`/`:3436`; `list_not_yet_listed()` emits `EXPECTED_INSTRUMENT_NOT_LISTED`. Per-date existence
  gate `_check_instruments_available` (`orchestrator.py:285`).
- UAC combo guardrail BEFORE fetch: `orchestrator.py:2342-2364` intersects requested data_types with
  `get_expected_data_types_for_venue(venue)` (UAC `market_data_categories.py:440-492`) — drops venue-unsupported types.
- execution-service batch preflight RAISES on missing cefi instrument: `instruments/factory.py:197-236`
  (`INSTRUMENT_NOT_FOUND`, cefi has no config fallback), `engine/validation/{instrument,catalog}_validator.py` read
  `instrument_availability/by_date/day={date}/` per date. Date-correct (no cross-date instrument reuse found).

**✅ VERIFIED (Dim 7 — could-exist denominators, machinery EXISTS + RUN for cefi):**

- `expected_unattempted` universe emission is cefi-wired + has RUN:
  `instruments-service/scripts/enumerate_expected_universe.py` `_enumerate_v2_cefi()` cross-joins IS catalog × dates ×
  `DATA_TYPES_BY_ASSET_GROUP["cefi"]`, diffs vs existing rows, emits `expected_unattempted` for alive-but-absent cells
  (lifecycle reasons EXPECTED_INSTRUMENT_NOT_LISTED/\_DELISTED/ \_PRE_VENUE_LAUNCH). Live cefi `_index` ≈ 11.7% (4.1M
  rows) expected_unattempted — the not-backfilled gap is MATERIALISED as rows, not invisible. UTL
  `manifest_writer.py:2115` `record_expected_unattempted()`.
- Denominator is universe-aware: UAC `honest_coverage.py:575` `compute_honest_coverage()` denom =
  captured+empty_confirmed+known_empty+attempted_failed+**expected_unattempted_pending_fetch** (the could-exist gap is
  IN the denominator). deployment-api `data_status_service.py:25` imports it. UI shows it DISTINCTLY:
  `deployment-ui HonestCoverageCard.tsx:52` + `VenueCoverageTable.tsx` render `expected_unattempted` as its own segment
  (playwright `tests/smoke/venue_year_coverage.spec.ts` mocks cefi).

**🟡 GAPS — Dim 6 (guardrail holes):**

- [ ] [CODE] P2. **market-tick-data-service — hardcoded date-BLIND fallback universe bypasses IS.**
      `engine/orchestrator.py:326-439` `_VENUE_WIRE_SYMBOL_FALLBACK` (static MVP majors per venue) is substituted by
      `_uac_seed_instruments_for_venue` (`:411`) when `_check_instruments_available(venue,date)` is False
      (`:2316-2326`). Bounded to majors + logged + honest-skip when empty (so practical "cannot-exist" risk is low —
      majors exist every operational date), BUT it is date-BLIND (ignores venue-launch/delist per date) + bypasses the
      IS SSOT. **Fix:** gate the fallback behind a batch-bootstrap-only flag (never the live path); in normal operation,
      when IS is missing → honest-skip / `record_failed(EXPECTED_*)` rather than substitute a hardcoded universe.
- [ ] [SCRIPT] P2. **unified-trading-pm QG blind spot** — `scripts/qg/no_hardcoded_venue_universe.sh:22-40` scans only
      `cli/handlers/` for `*_TOKENS/_MARKETS/_PAIRS/_UNIVERSE` names, so the `engine/`-resident
      `_VENUE_WIRE_SYMBOL_FALLBACK` dict above is INVISIBLE to the gate. **Fix:** extend the scan to `engine/` + the
      `*_FALLBACK` / wire-symbol-dict pattern (PM template — rollout to all repos).
- [ ] [CODE] P2. **strategy-service — no IS instrument-existence guardrail.** `preflight.py` (venue auth+balance only) +
      `risk_preflight_gate.py` (risk rules only) do NOT validate a cefi instrument EXISTS in IS for the date before
      emitting an instruction (0 hits for `instrument_availability`/`InstrumentRecord` in non-test source); a strategy
      config naming a delisted/non-existent cefi instrument is only caught later at execution. **Fix:** add an
      IS-catalog existence check to strategy preflight (mirror execution `catalog_validator`).
- [x] ✅ [CODE] P3. **execution-service — Deribit live-order not-found guard FIXED (execution@f111a8e2c, QG exit 0).**
      Was SWALLOWED: `venues/deribit_orders.py:84-90` raises `ValueError("…not found or expired")` but the enclosing
      `except (OSError, ValueError, RuntimeError)` at `:89` catches it → only `logger.warning` → a non-existent/expired
      Deribit instrument does NOT hard-block the live order (and validates against the venue API, not IS). **Fix:**
      re-raise the not-found `ValueError` on the live path.
- [ ] [CODE] P3. **unified-api-contracts — `validate_data_type_for_venue` permissive on unknown venue.**
      `market_data_categories.py:456-457` returns True for an unknown/typo'd venue → escapes the combo guardrail.
      **Fix:** fail-closed (or warn-loud) for unknown venues on the live path.

**🟡 GAPS — Dim 7 (denominator precision):**

- [ ] [CODE] P2. **deployment-api in-process per-instrument denominator uses a capped MVP seed, not the real IS
      universe.** `data_status_service.py:1417` `_per_instrument_shard_denominator` →
      `get_expected_instruments_for_venue(...,     instruments_provider=None)` → falls back to
      `_SPOT_MVP_SEED_INSTRUMENTS` (21) + `_PERP_MVP_SEED_INSTRUMENTS` (10) (`market_data_categories.py:1013-1058`) →
      UNDER-counts the real ~200-perp / full-spot cefi universe → that path's coverage reads optimistically (mitigated
      where the manifest-seeded `expected_unattempted` rows dominate, but the two universes can disagree). **Fix:**
      inject a live IS-catalog `instruments_provider` (or raise the per-instrument cap) for cefi so the in-process
      denominator matches the enumerator's full universe.
- [ ] [INFRA] P3. **`expected_unattempted` is enumerator-run-dependent (not auto per-write).** A not-yet-backfilled cefi
      cell is invisible until the v2 enumerator VM runs (`launch-expected-universe-v2-vm.sh cefi --apply-write`; cadence
      "one-shot then quarterly"). cefi is currently seeded (4.1M rows) but NEW venues/instruments between runs are
      invisible (`honest_coverage.py:623` warns a fresh AG reads a misleading 100%). **Fix:** schedule the cefi v2
      enumerator on a recurring cron (not one-shot/quarterly).

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

**🔴 P0 — E2E-blocking code (OPERATOR-APPROVED to do THIS session before the dry-run):**

- [x] ✅ [CODE] P0. **`rebuild_cefi_manifest.py` CF-11 3-way classifier** — **DONE (mtds@fa2b02c7).** New
      `reemit_cefi_honest_absence_rows` pass (mirrors the proven `rebuild_tradfi_manifest` sibling): reads the prior
      `_index`, filters to the run date-range + cefi, dedups vs freshly-scanned keys, then (a) within-bounds empty
      (blank-reason OR `SOURCE_RETURNED_ZERO` on a guaranteed-when-listed `trades`/`ohlcv*`/`book_snapshot_5` OR
      invalid-reason) → `record_failed(WITHIN_BOUNDS_EMPTY_RECLASSIFIED)`; typed-empty on a sparse data_type
      (funding/options_chain/…) → `record_empty` PRESERVED; (b) prior `attempted_failed` → `record_failed` PRESERVED
      (the ~1.33M survive); phantom captured-no-object → `record_failed(PHANTOM_CAPTURED_NO_OBJECT)`; (c) +24 unit
      tests; `--scan-only` flag restores pure-scan. MTDS QG --no-fix exit 0. Closes the open E5/CF-11 items at §CF-11
      below.
- [x] ✅ [CODE] P0. **Live cefi writer source+pipeline_mode COLUMN parity** — **CONFIRMED gap + FIXED (mtds@4e5fa57f).**
      orchestrator.py finalize per-instrument `add()` stamped source/pipeline_mode ONLY for sports odds (comment:
      "Non-sports shards leave source=None"); cefi/defi/prediction captured rows got blank `pipeline_mode` (`add()`
      doesn't auto-derive it) → Batch≠Live drift. Now every non-sports per-instrument row derives `source` via
      `get_primary_source(asset_group,data_type)` + `pipeline_mode` via `_resolve_pipeline_mode_for_sentinel` (same
      helpers the bundled path + migrator/rebuild use) + stamps both. Sports branch unchanged (no slot-4 collision; the
      `else` branch is additive). source= is crosscutting (all asset_groups). MTDS QG --no-fix exit 0.

**🟡 P1 — data-status / drilldown reflects the migrated structure (DEFERRED to a tracked follow-up unless quick):**

- [ ] [CODE] P1. **deployment-api FLAG-1** — CeFi multi-source UNION coverage + per-source breakdown (dedup via
      `select_primary_available_source`; `groupby("source")` on the `_index` source column). CeFi single-source today,
      but the column/dedup path must exist for swap-resilience. Cross-ref
      `downstream_services_manifest_canonicalisation_2026_06_01.md` FLAG-1.
- [ ] [CODE] P1. **deployment-api FLAG-3** — env-tier the hardcoded `*-store` bucket f-strings → `resolve_bucket_name`
      (`commentary/pipeline_uat.py`, `deployment_api_config.py`). Cross-ref downstream plan FLAG-3.
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

**⚪ P2 / needs-confirm (tracked):**

- [ ] [CODE] P2. **MDPS GAP-7** — `category`→`asset_group` param rename in `dependency_checker` (vocabulary; cross-ref
      downstream plan GAP-7).
- [ ] [DATA] P2. **CONFIRM partial-BUNDLE completeness guard** — bundled cefi data_types (book_snapshot/options_chain).
      **PARTIALLY CONFIRMED (slot-3 read-only 2026-06-03):** the finalize path DOES run cluster validation
      (`record_captured_from_counts(expected_root_clusters, observed_clusters)`; CLAUDE.md 4-pillar "cluster coverage ≥
      expected" — `MissingClusterValidationError` if absent), so the gate is PRESENT (not missing). The audit's worry is
      the `≥ count-threshold` vs `len(observed)==len(expected)` precision (a partial bundle that meets the count but
      misses a cluster root). The cluster-validation internals live in UTL `manifest_writer.py`
      `record_captured_from_counts` — left as a refinement for the cluster-SSOT owner (`mtds_mdps_master`) to tighten if
      `≥` admits incomplete bundles; **NOT a slot-3-solo fix** (UTL + the bundled writer span DeFi/sports too). The live
      writer's per-instrument path is unaffected (no clusters). Repo: UTL/MTDS — owning VM.
- [x] ✅ [CODE] P2. **CONFIRM reader empty-vs-failed differentiation — NOT A GAP (slot-3 read-only 2026-06-03).** The
      MTDS reader (`reader.py:583-639`) fetches `capture_status == "captured"` data + raises `ShardNotFoundError` for
      any non-captured cell — it does NOT (and should not) differentiate empty-vs-failed at the raw-read layer. The
      `attempted_failed` (retry) vs `empty_confirmed` (accept) differentiation is correctly handled ONE layer up at the
      **manifest-query / pre-flight** consumer (the backfill pre-flight reads `capture_status` and retries
      `attempted_failed`, skips `captured`/`empty_confirmed` — the honest-absence consumer policy). No reader fix
      needed.

## Phase 2 — dry-run + sharding/performance scope (slot-3, 2026-06-03)

> **✅ DRY-RUN COMPLETE — `mtds-migrate-cefi-v9dry-2024`** (n2-highmem-4, asia-northeast1-c, **NO `--apply`**;
> exit_code=0, self-deleted; ~3 min wall).
> `migrate_cefi_flat_to_v9_canonical --start-date 2024-01-01 --end-date 2024-12-31 --also-legacy --workers 32`.
> **Result: `TOTAL planned=914,624 written/moved=0 (DRY-RUN)`** for the 2024 shard (candles `planned=45,585`; 9 L-flat
> orphans fan-out shown with correct canonical dests). **`moved=0` = idempotent-skip** (the `-prd` already holds the
> migrated `pipeline_mode=` forms — consistent with the verified corpus-complete state). **No OOM at 32 GB** for a dense
> ~914k-object year (vs the 16 GB e2-standard-4 OOM on the all-years 1.9M listing). PLAN paths verified canonical
> (`day=/pipeline_mode=batch_tardis/asset_group=cefi/venue=/instrument_type=/data_type=/…`). Banner removed (VM
> self-deleted). Coding gate MET first: IS@f2ca5954 + MTDS@fa2b02c7/4e5fa57f + PM@878dd9553 all QG-green + on LDR.

**Per-year object distribution (measured 2026-06-03, delimited day-dir listing on the legacy bucket):**

| year  | day-dirs  | notes                          |
| ----- | --------- | ------------------------------ |
| 2019  | 277       | partial (from 2019-03-30)      |
| 2020  | 366       |                                |
| 2021  | 365       |                                |
| 2022  | 365       |                                |
| 2023  | 365       |                                |
| 2024  | 366       |                                |
| 2025  | 365       |                                |
| 2026  | 144       | partial (to 2026-05-24)        |
| **Σ** | **2,613** | == plan L2 count; ~2.377M objs |

≈ **910 objects/day-dir**, ≈ **300k objects/year**. The e2-standard-4 (16 GB) OOM was loading **all 2.377M** legacy
object names at once.

**Sharding + machine-size recommendation (for the NEXT-session `--apply`):** **8 year-shards (2019…2026), one VM each,
`n2-highmem-4` (32 GB)** — a per-year shard (~300k object names) fits comfortably in 32 GB (the OOM was 8× that on half
the RAM). Server-side `gcs_copy_object` at `--workers 32` (GIL-free I/O) → the per-year copy is network-bound, not
CPU-bound, so 4 vCPU suffices. The running 2024 dry-run validates the real per-year listing time + the 32 GB headroom
(result appended here on completion).

### ✅ E5 MANIFEST-REBUILD DRY-RUN — the real `_index`-rebuild step, validated 2026-06-04 (slot-3)

> Operator Q: _"have we dry-run the manifest (`_index`) rebuild to check it works as expected?"_ — **YES, and it caught
> a serious false-phantom bug that would have corrupted the `_index`.** Ran
> `rebuild_cefi_manifest --dry-run --start-date 2024-06-01 --end-date 2024-06-07` against the real `-prd` v8 `_index`
> (laptop ADC, `CLOUD_MOCK_MODE=false`; exit 0, ~100 s/week; reads the v8 index + classifies with NO column-name crash —
> validates the `reason`/`error_reason` fallback + the whole CF-11 re-emit pass on real data).

**Bug the dry-run surfaced (3 covered-key match gaps → FALSE phantom demotes of REAL captured cells):** the first run
flagged **`phantom_to_failed=1187`/week** — prior-`captured` cells the object scan "couldn't find" → it would
`record_failed(PHANTOM_CAPTURED_NO_OBJECT)` them, i.e. **flip real captured → attempted_failed corpus-wide** (the exact
data-corruption the workspace rule forbids). Root-caused to THREE gaps, each fixed + locked with a regression test (mtds
`rebuild_cefi_manifest.py` + `test_rebuild_cefi_manifest_cf11.py`, 5 new tests):

1. **Kraken slash-symbols** (`ADA/USD`, `XBT/USD`) — written as a 2-segment path
   `…/data_type=book_snapshot_5/ADA/USD.parquet`; the parser stem `[^/]+` can't cross the slash → object `unparseable`
   (576/week) → its captured cell looked phantom. Fix: stem `→ [^/=]+(?:/[^/=]+)*` (allows slash-symbols, excludes `=`
   so it can't swallow a bundle path).
2. **`instrument_type` case** — prior v8 `_index` stores `SPOT_PAIR` (UPPERCASE, old-writer anomaly) but the GCS path is
   `spot_pair`; the covered-key compared it case-sensitively (only `venue` was normalised) → EVERY real Kraken/spot
   captured cell missed the dedup. Fix: lowercase `instrument_type` on both sides of the covered-key (canonical form).
3. **Malformed/sentinel junk rows** — blank venue, no cell key (blank instrument_id AND underlying), or the `ticks`
   bundle-filename leaked into `instrument_id`; demoting them mints junk `attempted_failed` rows. Fix: **DROP** them
   (`dropped_malformed_captured`), never demote.

**Result after fixes (same week):** `phantom_to_failed 1187 → 12` (the 12 are genuine — DERIBIT
`futures_chain`/`options_chain` with a real `underlying` but verifiably NO object → honest absence → `attempted_failed`
for retry, CORRECT); `dropped_malformed_captured=399`; `reemit_skipped_covered 2938 → 3714` (+776 Kraken cells now
correctly matched); `reemit_attempted_failed=3763` preserved; `unparseable 576 → 0`. **The rebuild now works as expected
— verified the real v8 `_index` reads + classifies correctly + no real captured cell is demoted.** Before the REAL run,
re-confirm on a wider date range (the dry-run was a 1-week sample; the slash-symbol + case gaps are corpus-wide so
they'll recur identically, but a multi-year `--scan-only`/`--dry-run` spot-check of the phantom count is the cheap final
gate).

- [x] ✅ [CODE] P0. **E5 rebuild false-phantom fixes (3 covered-key gaps)** — slash-symbol parser stem,
      `instrument_type` case-canonical covered-key, malformed-junk drop. mtds `rebuild_cefi_manifest.py` + 5 regression
      tests. Caught by the 2026-06-04 manifest-rebuild dry-run (1187→12 false phantoms/week). **DONE — mtds@60debbfe**
      (tab→LDR; staging deferred behind the UTL/UAC dep-tier dam) | QG --no-fix exit 0 | 29/29 CF-11 tests green.
- [ ] [DATA] P1. **Before the REAL `_index` rebuild — multi-year dry-run phantom spot-check**: re-run
      `rebuild_cefi_manifest --dry-run` over a multi-year span (or the full corpus) and confirm `phantom_to_failed`
      stays small + well-formed (DERIBIT-chain-style true phantoms only), `dropped_malformed_captured` is junk-only, and
      `unparseable=0`. Cheap final gate before the irreversible-adjacent index overwrite.
- [ ] [DATA] P0. **NEXT SESSION — execute the migration** (after the dry-run validates perf): run the 8 year-sharded
      `--also-legacy --apply` gap-fill (5,233 legacy-only cells), then the irreversible orphan-sweep (with the mandatory
      pre-delete idempotent-`--apply`-over-full-range guarantee), then E5 manifest rebuild (now CF-11-canonical +
      false-phantom-safe @mtds#fa2b02c7+this-fix), E7 verify, E8 legacy-bucket delete. NOT this session (irreversible).

## Why this exists — cefi canonical FORM is broken corpus-wide (+ a recent 838-cell data gap)

The 2026-06-01 `_index` comparison (legacy `market-data-tick-cefi-…` vs canonical `market-data-tick-cefi-prd-…`) showed
the cell-coverage gap is small (838) — but the canonical FORM is wrong across the WHOLE corpus (the finding above). Both
are fixed in the one walk. Cell-coverage table:

| metric                                         | value                                                                                                                        |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| captured legacy CELLS `(date,venue,data_type)` | 91,602                                                                                                                       |
| canonical CELLS                                | 142,893 (canonical is AHEAD overall)                                                                                         |
| overlap                                        | 90,764                                                                                                                       |
| legacy-only CELLS (canonical MISSING)          | **838**                                                                                                                      |
| legacy-only examples                           | `(2026-03-21, BINANCE-SPOT, book_snapshot_5)`, `(2026-05-14, UPBIT, book_snapshot_5)`, `(2026-05-20, COINBASE-SPOT, trades)` |
| legacy-only by data_type                       | `book_snapshot_5` 363 · `trades` 336 · `derivative_ticker` 83 · `liquidations` 47 · `ohlcv_15s` 3 · `ohlcv_1m` 2             |

So cefi canonical is overall MORE complete than legacy (142k vs 91k cells), but **838 recent cells (2026-03→05,
BINANCE/UPBIT/COINBASE) exist in legacy only** — likely written to legacy right before the writers were drained
2026-06-01. These must land in canonical before L6 deletes the legacy bucket. Legacy layout (2026-06-01 audit):
`raw_tick_data/` (NO `by_date/` sub-tree — different from tradfi) + `processed_candles/`.

## Sequencing — gate before cefi backfill (inherits master HARD RULE)

No cefi backfill until this walk is C-GREEN. L0 tarball-prune blocker
(`issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md`) must be fixed first if run on a VM. (The drained
`mdps-backfill-cefi-main-test` already self-terminated; no live cefi writer — relaunch is gated on C-GREEN.)

## Canonical target form (cefi)

| Dimension       | Legacy                                     | Canonical                                                                             |
| --------------- | ------------------------------------------ | ------------------------------------------------------------------------------------- |
| Bucket          | `market-data-tick-cefi-{project}` (no env) | `market-data-tick-cefi-prd-{project}`                                                 |
| asset-group key | `category=cefi`                            | `asset_group=cefi`                                                                    |
| pipeline_mode   | absent in path                             | `pipeline_mode=` partition (`batch_tardis`/`batch_hyperliquid_rest`/`live_websocket`) |
| schema_version  | legacy spread                              | v9                                                                                    |
| source          | (per `data_source_provenance` cefi)        | `tardis` / `<venue>` multi-source                                                     |

## Phased execution

### P0 — audit

- [x] ✅ [DATA] P0. Legacy→canonical `(date,venue,data_type)` diff (slot-3 tool, 2026-06-01): **legacy-only CELLS =
      5,233** (NOT 838 — the headline undershot; prior-not-ceiling). Oldest examples are 2020-01
      `OKX-FUTURES     book_snapshot_5` (legacy captured 91,602 · canonical 90,931 · overlap 86,369). These must land in
      canonical before L6 deletes legacy. Exact per-data_type object counts resolved in the C0 walk (idempotent copy of
      the gap).
- [x] ✅ [DATA] P0. Read canonical `cefi-prd` `_index` DATA-STATE (2026-06-01 slot-3): **100% v8** (not v9), **no
      `source` column**, **no `category`/`asset_group` column**, **blank `pipeline_mode`** → the
      FULL-re-canonicalisation finding above. Whole corpus is in scope, not 838 cells.
- [x] ✅ [DATA] P0. Reusable audit tool SHIPPED — `plans/audit/results/cf_manifest_audit_2026_06_01.py` (PM@4be440b6a):
      per-CF GREEN/RED data-state for any AG `_index` (schema_version dist, `source`/`category`/
      `asset_group`/`pipeline_mode` col presence, `error_reason` histogram CF-5, shallow object-path probe CF-2/3/9,
      legacy-only cell diff). DNS-robust (`gcloud cp` retried + time-boxed shallow probe). Run on cefi/tradfi/sports/
      prediction (results in their P0 blocks). Generalises to instruments + downstream. Feeds the audit-instruction
      Canonical-form sections.

### C — single-walk (gap-fill + canonicalisation)

- [x] ✅ [DATA] P0. **Phase 0 — layout audit (MANDATORY, blocking — slot-2 DeFi lesson 2026-06-01)**: before the walk,
      enumerate ALL top-level trees + nested layouts in the cefi source + canonical buckets (`raw_tick_data/by_date/`
      flat-symbol, `processed_candles/by_date/day=/timeframe=/…`, any `day=/category=` or bare `{venue}/{chain}/date=`).
      Per layout: object count + sample schema; classify duplicate (keep freshest) vs complementary (migrate all). The
      walk MUST cover every in-scope layout or it is incomplete (review-blocking). SSOT:
      `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § Cross-AG lesson + grounded recipe Phase 0. DONE
      (slot 10, 2026-06-03): exhaustive enumeration confirmed THREE layouts (not 2 from shallow probe). Legacy: L1=9
      flat orphans, L2=2,613 day=/pipeline_mode=batch_tardis/asset_group=cefi/ (MOST CANONICAL), L3=460 candle day-dirs.
      Canonical: C1=9 flat orphans, C2=2,594 day=/asset_group=cefi/ (MISSING pipeline_mode= — LESS canonical than L2),
      C3=464 candle day-dirs. Key finding: legacy L2 is more canonical than canonical C2. 19-day raw gap (L2−C2). Walk
      implications documented in SSOT §Phase-0 cefi-specific verification. PM@2f315f0fb.

> **Migration-script performance contract (HARD — codified 2026-06-01, defi C0 lesson)**: the walk script MUST be
> parallel (`ThreadPoolExecutor` — GCS I/O releases the GIL → 5–10×; a bare `for obj` loop is review-blocking) + wire
> `--workers`/`--start-date`/`--end-date` (date-shardable across VMs — no dead args) + `gcs_copy_object` for path-only
> moves (server-side ~250×) / download+transform+upload only for content changes + unbuffered progress logging
> (`python -u`, counter every ~1000) + per-object `try/except…continue` isolation + idempotent re-runs. SSOT:
> `codex/05-infrastructure/gcs-object-operations.md` § "Migration-script performance contract".

- [x] ✅ [DATA] P0. C0 ONE bundled **WHOLE-CORPUS** walk (the finding makes this corpus-wide, not 838 cells): (a)
      re-version **every** cefi row+parquet **v8→v9** (CF-1) asserting data-state, not the constant; (b) add the
      **`source` column** = `tardis` on every row (CF-4) + (c) the **`asset_group=cefi` column/key** on rows + paths
      (CF-2) + (d) the **`pipeline_mode=` partition** + non-blank column (CF-3); (e) typed empty-reasons (CF-5); (f) the
      838-cell legacy→canonical gap-fill copy (`raw_tick_data/` + `processed_candles/`, layout-aware — cefi has NO
      `by_date/`). Column adds (b–c) are a CONTENT rewrite → download+transform+upload **parallelised per the perf
      contract** (NOT a server-side path move; NOT "run locally" — this is a VM-scale walk now, gated on L0). The
      838-cell pure-path copies use `gcs_copy_object`. Idempotent. — DONE (slot 10, 2026-06-03):
      market-tick-data-service@53671a0 (Kraken BASE/QUOTE 2-level path fix) + @7cb9947. TOTAL planned=3928281
      written/moved=1863687 (dry-run: 3,916,302). 112 corrupt KRAKEN-SPOT USD.parquet objects from partial apply deleted
      before re-run with fix. Canonical bucket now has pipeline_mode=batch_tardis paths.
- [ ] [DATA] P0. C-pipeline_mode RIDER (folded into C0 (d)): the `pipeline_mode=` partition lands in THIS walk
      (satisfies `pipeline_mode_partition_migration` for cefi).
- [ ] [DATA] P1. C-source RIDER (folded into C0 (b)): the `source` column (`tardis`, swap-resilient) lands in THIS walk
      (closes `data_source_provenance` cefi).

### Verify + handoff

- [ ] [DATA] P0. Post-walk: re-read the canonical `_index` DATA-STATE (re-run the reusable audit tool) → **100% of rows
      v9** (was 100% v8); **`source` populated on every cell** (zero blank; `tardis`, swap-resilient); **`asset_group`
      column/key present** (no `category`/blank); **`pipeline_mode` non-blank + partition present**; typed reasons;
      **legacy-only CELLS = 0** (838-gap closed). Closes `data_source_provenance` cefi + `pipeline_mode_partition` cefi.
      C-GREEN signal for `bucket_name_ssot…` Phase 6/7 cefi legacy bucket decommission.
- [ ] [DATA] P0. **Orphan sweep + bucket-state evidence (slot/Harsh bucket-state verification 2026-06-02).** Measured
      (Cloud Monitoring `storage/v2/total_count`, live-object): `market-data-tick-cefi-prd` 1,545,850 (~65% of legacy
      2,377,168) and **~17 days STALE — `-prd` latest `day=2026-05-07` vs legacy `day=2026-05-24`** (consistent with the
      5,233 legacy-only cells; the C0 gap-fill closes it by reading legacy as source). `-prd` is INTERMEDIATE FORM:
      `asset_group=cefi` is in the PATH but there is **NO `pipeline_mode=` partition** (confirmed at the data level, not
      just the manifest). So the E4 walk writes NEW `pipeline_mode=` paths → the pre-existing legacy-FORM `-prd` objects
      become ORPHANS; E5 rebuild / E7 verify MUST delete the legacy-FORM `-prd` objects too (not only the legacy SOURCE
      bucket), else the rebuild double-counts. Legacy carries 3.81M noncurrent objects → the E8 delete must also purge
      noncurrent versions, and the "canonical ≥ legacy" count gate must use Monitoring `type=live-object` (never a naive
      recursive `ls`, which counts versions + soft-deleted).

## Execution checklist (grounded — next session, finish in full)

> CF debt is in the `_index` MANIFEST + object PATHS, NOT the raw tick parquets (cefi raw = pure market data). See
> `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § MECHANISM + complete layout map. cefi is the HARDEST:
> `raw_tick_data/by_date/{SYMBOL}.parquet` is FULLY FLAT (day/venue/data_type only in cols + epoch-µs ts).
>
> ⚠️ **IRREVERSIBLE — E8 DELETES the legacy bucket permanently.** Do not run E2–E8 until the canonical target (schema =
> v9, paths = `day=/pipeline_mode=/asset_group=cefi/venue=/chain=/instrument_type=/data_type=`, source/available_at
> semantics) is CONFIRMED CORRECT on the verify step. One pass, no confusion — once legacy is deleted it is gone.

- [x] ✅ [DATA] P0. E1 **EXHAUSTIVE** layout + VOCAB audit (slot-3 2026-06-01, operator "3 versions like defi" check).
      ⚠️ **CORRECTION — the earlier shallow probe was WRONG ("FULLY FLAT").** A multi-level count found cefi raw is
      **THREE layouts**: (L-bulk) `raw_tick_data/by_date/day=/asset_group=cefi/venue=/instrument_type=/data_type=/` =
      the DOMINANT layout, **2,613 day-dirs**, near-canonical (instrument_type already lowercase) but MISSING
      `pipeline_mode=`; (L-canon) some days already `day=/pipeline_mode=batch_tardis/asset_group=cefi/`; (L-flat) **only
      9 orphan** root `{SYMBOL}.parquet` (2026-05-04 backfill bug). Same 3 layouts in legacy + prd. **Canonical VOCAB
      (data-state, not assumed)**: venue HYPHENATED (DERIBIT/BITFINEX-SPOT/BINANCE-FUTURES/HYPERLIQUID);
      `instrument_id="{VENUE}:{ITYPE}:{SYMBOL}"`. **CF-7 drift**: instrument_type CASE in \_index column,
      blank/`UNKNOWN` venue (1453+111), blank data_type (9757), COINBASE vs COINBASE-SPOT. — slot-3 2026-06-01.
- [x] ✅ [DATA] P0. E2 Built + FIXED `migrate_cefi_flat_to_v9_canonical.py` (3-layout-aware, perf-contract). **The first
      build handled ONLY the 9 L-flat orphans → would have MISSED the 2,613 L-bulk day-dirs (the exact "we keep missing
      things" trap the operator flagged). FIXED** to cover all three: L-bulk/L-canon = path-only `gcs_copy_object`
      inserting `pipeline_mode=` after `day=` (server-side ~250x; L-canon dest==src → no-op); L-flat =
      read+regroup-by-day+ fan-out. All via the UAC `candidate_parquet_paths` SSOT (byte-exact batch=live; pipeline_mode
      from venue, HYPERLIQUID→ hyperliquid_rest else tardis). Parquet content untouched (v9 cols at E5 rebuild). CF-7
      blank/`UNKNOWN` venue + blank data_type skip+logged for E6. Candles = pipeline_mode insert. Knobs
      `--workers`/`--start-date`/`--end-date`/`--also-legacy` + `python -u` + per-object isolation + idempotent. All 3
      layout transforms unit-validated; lint+typecheck clean. — market-tick-data-service@844124f7, slot-3 2026-06-01.
- [x] ✅ [DATA] P0. E3 Confirm cefi writer drained + snapshot `cefi-prd/_index` — **DONE (slot-3, 2026-06-03).** No live
      cefi writer VM (`gcloud compute instances list --filter="name~cefi OR name~mdps-backfill-cefi"` → empty);
      `_index/per_vm/` holds only the stale `_legacy_seed.parquet` (2026-05-12, no active shard emission). Consolidated
      `availability_index.parquet` (47.58 MiB, last consolidator write 2026-06-03T09:28Z) snapshotted to
      `_index/snapshots/pre_migration_2026-06-03.parquet` (49,893,721 bytes == source; sits beside the prior
      `pre_migration_2026-05-22.parquet`). Pre-migration safety point established; E4 walk can run.
- [x] ✅ [DATA] P0. E4 — **the `-prd` raw_tick + candles PATH migration is ALREADY DONE** (slot-3 calibration + GCS
      verify 2026-06-03). `--apply` calibration slices reported `moved=0` NOT from a bug but because the migrator
      correctly **idempotent-skips** (`_move_day_one:219` `gcs_describe_object(dst) is not None`): the canonical
      `pipeline_mode=` dests already exist. Verified on day=2024-06-03 — `_canon_day_rel` computes
      `day=/asset_group=cefi/…/ADAUSDT.parquet` → `day=/pipeline_mode=batch_tardis/asset_group=cefi/…/ADAUSDT.parquet`
      (dst≠src, `pipeline_mode` inserted — migrator is CORRECT), and GCS shows BOTH forms coexisting:
      `day=2024-06-03/asset_group=cefi/` = **474 OLD/orphan** objects + `pipeline_mode=batch_tardis/` +
      `batch_hyperliquid_rest/` = **482 MIGRATED** objects. So the corpus-wide `pipeline_mode=` insert already ran (a
      prior `--apply`); `gcs_copy_object` copies (not moves) → the old `day=/asset_group=cefi/` objects remain ORPHANS.
- [ ] [DATA] P0. **❌ RETRACTION of the earlier "E4-BUG / we-keep-missing-things" P0 (it was WRONG).** I read
      `moved=0` + a `head -3` listing (which shows `asset_group=` paths — they sort BEFORE `pipeline_mode=`) and wrongly
      concluded "no `pipeline_mode=` sibling / migrator no-ops L-bulk". The FULL listing shows the `pipeline_mode=`
      siblings DO exist (482/day). slot-10's `C2 = day=/asset_group=cefi/` count is exactly these **post-migration
      orphans**, not a pre-migration gap. No migrator fix is needed.
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
      rushed.** Repo: market-tick-data-service.
- [x] ✅ [DATA] P0. E5 Manifest rebuild → v9 — **DONE (mtds@2c3a479b, 2026-06-02)** via the RECOMMENDED fork (A):
      `rebuild_cefi_manifest.py` now (1) parses an OPTIONAL `pipeline_mode=(?P<pipeline_mode>[^/]+)/` segment in all 3
      `_PAT_*` matchers (between `day=` and `asset_group=`); (2) lists at DAY level (`raw_tick_data/by_date/day={d}/`)
      so migrated `pipeline_mode=` objects are enumerated (an `…/asset_group=cefi/` list prefix MISSES them); (3)
      targets the canonical `-prd` bucket; (4) stamps `pipeline_mode` on `add()` — from the path segment when present
      else `derive_pipeline_mode_for_row(venue,"cefi",dt)` (== the migrator + live writer); `source` left "" → add()
      auto-resolves (cefi single-source tardis). 11 parser tests green (3 new pipeline_mode cases). add()'s
      pipeline_mode kwarg landed utl@b872bdf1 (fork A). **REMAINING enhancements (gate G4, tracked via CF-11 todos
      above + Verify below):** `available_at` parquet-col-else-day-EOD; 0-row→empty backstop; legacy-`_index` re-emit of
      `attempted_failed`/typed-`empty_confirmed` rows (CF-11). Original build-spec retained below for reference.
- [ ] [DATA] P2. E5 build-spec reference (superseded by the DONE item above): `rebuild_cefi_manifest.py` encodes the
      per-instrument row key (the LIVE writer key =
      `date,venue,chain,data_type,league_id,instrument_type,underlying,quote_asset,     margin_type,instrument_id`;
      orchestrator.py:2937/2957) + tolerates `raw_tick_data/by_date/`+`asset_group=`. Two changes only: (1) its `_PAT_*`
      regexes + `prefix_templates` do NOT account for the NEW `pipeline_mode=` segment between `day=` and `asset_group=`
      → list per `raw_tick_data/by_date/day={d}/` and extend `parse_hive_path` to capture an optional
      `pipeline_mode=(?P<pipeline_mode>[^/]+)/`; (2) stamp v9 cols: pass `source` (cefi single-source `tardis`;
      HYPERLIQUID→`hyperliquid_rest`) + `pipeline_mode`. **INTERNALS Q — RESOLVED (slot-3 2026-06-01):** `add()`
      persists `source` (auto-resolved via SOURCE_PRIORITY at manifest_writer.py:236) but does **NOT** persist
      `pipeline_mode` (no kwarg; goes to `**kwargs` → dropped) — that is exactly why CF-3 reads blank corpus-wide (the
      live per-instrument cefi `add()` at orchestrator.py:2957 also omits it). `record_captured_from_counts`
      (mw.py:2840) takes `pipeline_mode` but **REQUIRES** `expected_root_clusters` + `observed_clusters` +
      `available_at_envelope` (the BUNDLED path). `record_captured` takes `pipeline_mode` but needs a `df` (read every
      parquet). **DESIGN FORK (pick deliberately — feeds the irreversible delete):** (A) **[RECOMMENDED]** add a
      back-compatible `pipeline_mode: PipelineMode|str = ""` kwarg to `ManifestWriter.add()` that coerces
      (`_coerce_pipeline_mode`) + persists it like `source` (default "" = today's behavior → zero back-compat risk; ALSO
      closes the live-writer CF-3 gap so batch=live). Then rebuild via `add(...,     pipeline_mode=, source=)`. Needs
      UTL QG. (B) use `record_captured_from_counts` with trivial single-cluster maps (`{instrument_id: rows}` as both
      expected+observed) — hacky for per-instrument. (C) `record_captured(df=...)` reading each parquet — correct but
      slow. `available_at`: parquet col if present, else day-EOD-UTC (never migration-time). Same fork applies to
      `rebuild_prediction_manifest.py`. **Do NOT build until the fork is chosen** — wrong choice corrupts the `_index`
      that gates L6 delete.
- [ ] [DATA] P1. E6 CF-7 relabel: `COINBASE`↔`COINBASE-SPOT`, blank venue/data_type → canonical (diagnose, don't bulk).
      Investigate the 50% `attempted_failed` rows (1.33M) — flag to cefi AG owner (separate from canonicalisation).
- [ ] [DATA] P0. E7 Verify: `cf_manifest_audit_2026_06_01.py market-data-tick-cefi-prd-…` → CF-1…CF-12 GREEN on
      data-state; flip CF-coverage rows in `cefi_master_audit_instructions.md`.
- [ ] [DATA] P0. E8 ⚠️ IRREVERSIBLE — only after E7 GREEN: hand C-GREEN to `bucket_name_ssot…` L6 → **delete legacy
      `market-data-tick-cefi` permanently** (single source of truth; legacy data is gone).

### CF-11 completeness — fetch-failure must be `attempted_failed`, NOT `empty_confirmed` (operator directive 2026-06-02)

> Operator: "when there is an API issue somewhere in IS or MTDS, is it correctly doing `attempted_failed` where the
> attempt makes sense by instrument / UAC bounds — RATHER THAN `empty_confirmed` which would not be complete?" CeFi
> twist: cefi is single-source (`tardis`). A Tardis fetch error for a `(venue, instrument, data_type, date)` cell INSIDE
> the expected-attempt set — instrument in the IS CeFi universe, data_type registered in UAC SOURCE_PRIORITY, date
> within the venue/instrument coverage window — is a masked fetch failure → `attempted_failed` (retry/backfill), NOT a
> false `empty_confirmed`/`SOURCE_RETURNED_ZERO` that freezes the gap forever.
>
> **The manifest must EXPLAIN every zero (3-way decision tree — the E5 rebuild contract):** (1) attempt errored on a
> warranted cell → `attempted_failed`; (2) a UAC guard explains the zero → typed `empty_confirmed`
> (`EXPECTED_OUT_OF_COVERAGE_WINDOW` / pre-listing / delisted); (3) only if market open + fetch succeeded + genuinely
> nothing → `SOURCE_RETURNED_ZERO`. A blanket/blank `SOURCE_RETURNED_ZERO` = "we don't know why" masquerading as
> complete.

- [x] ✅ [CODE] P0. **Rebuild classifier (`rebuild_cefi_manifest.py` / E5): within-bounds empty → `attempted_failed`.**
      **DONE (mtds@fa2b02c7)** — see the audit P0 #1 above. `reemit_cefi_honest_absence_rows` reclassifies blank-reason
      OR `SOURCE_RETURNED_ZERO`-on-guaranteed (`trades`/`ohlcv*`/`book_snapshot_5`) OR invalid-reason →
      `record_failed(WITHIN_BOUNDS_EMPTY_RECLASSIFIED)`; keeps typed-empty on sparse data_types (funding/options_chain).
      (Coverage-window / known-gap precision deferred — the conservative data_type-guarantee + reason gate is the
      operator-prioritised core; a per-instrument IS-universe/coverage cross-check is a NICE-TO-HAVE refinement, tracked
      as the P2 below.)
- [x] ✅ [CODE] P0. **Rebuild: re-emit existing `attempted_failed` rows v9, status PRESERVED** — **DONE
      (mtds@fa2b02c7).** The pass re-emits every prior `attempted_failed` row (not superseded by a fresh parquet) via
      `record_failed` with its original `error_reason` (blank→`UNCLASSIFIED_ADAPTER_ERROR`) — the ~1.33M survive as v9
      `attempted_failed`, still flagged for backfill, never collapsed to empty. +unit test asserts preservation.
- [ ] [CODE] P2. **NICE-TO-HAVE — rebuild within-bounds precision**: cross-check the reclassify decision against the IS
      CeFi universe + per-instrument coverage windows + the known-gap registry (today the gate is the conservative
      data_type-guarantee + reason heuristic, which the operator prioritised; the IS-universe cross-check would tighten
      false-positive reclassifications on genuinely-sparse symbol-days). Provenance: slot-3 E2E audit 2026-06-03.
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
        feature*groups' candle
        `ohlcv*\*`data_types via`resolve_data_type_for_feature_group`(mirrors the already-correct    `get_available_instruments`). +regression test (`ohlcv_1m`counted;`trades`/`book_snapshot_5`not). Verified     delta_one 20/20 + basedpyright-clean diff. **Shipped under operator EXEMPTION** (local macOS QG red only on the     foreign non-deterministic flake`features_service_full_qg_test_pollution_flake_2026_06_03.md`; Linux     `quality-gates-v2`
        re-verifies at promotion). Repo: features-service.
  - [ ] [DATA] P1. **Real cefi candle-coverage gap (partial backfill).** `ohlcv_*` manifest rows are sparse (8,715) and
        processed-candle FILES exist only for a partial venue set (BITGET-heavy; e.g. day=2026-05-03 = BITGET-FUTURES
        319 / BITGET-SPOT 151 / BITFINEX-FUTURES 90 / KRAKEN-FUTURES 18). MDPS candle generation for cefi is incomplete
        → track + complete the candle backfill (separate from raw-tick canonicalisation). Repo: MDPS.
  - [ ] [DATA] P1. **VERIFY MDPS candle-manifest faithfulness.** Do the `ohlcv_*` rows faithfully reflect the candle
        files that DO exist, or is MDPS under-emitting `ohlcv` rows for written candle files? Compare `ohlcv` row
        coverage vs candle-file coverage on a sample day. Also reconcile the minor cross-writes (782 MTDS-written
        `ohlcv` rows; 616 MDPS-written `trades` rows) — confirm which service legitimately emits `ohlcv` per venue (MTDS
        REST-poll venues like LIGHTER/PACIFICA vs MDPS-processed). Repo: MDPS (+ MTDS REST-poll path). On all three
        GREEN, archive the absorbed issue doc.
- [ ] [CODE] P0. **Write-path CF-11 audit + fix (IS + MTDS cefi/tardis adapters)**: on a genuine API error
      (timeout/5xx/429/auth) for an in-universe instrument within coverage bounds, the handler MUST `record_failed` (→
      `attempted_failed`) via `classify_venue_error()`/`ADAPTER_FETCH_FAILED`, NOT `record_empty`. Grep the cefi/tardis
      fetch paths in MTDS handlers + instruments-service for `except … record_empty` / bare `return []` swallows; gate
      the empty-vs-failed decision on instrument-in-universe + UAC coverage bounds. Cross-ref the sports CF-11 model
      (`sports_manifest_canonicalisation_2026_06_01.md` § CF-11). **DIAGNOSIS (slot-3 2026-06-02, grep-then-READ — MTDS
      side VERIFIED COMPLIANT, no swallow):** the MTDS write-path already implements the sports CF-11 model for
      cefi/tradfi/prediction. (a) Adapters (tardis/ccxt/databento/massive/ polymarket) classify via
      `classify_venue_error()` + emit `ADAPTER_FETCH_FAILED` + **re-raise** on a genuine API error (do NOT swallow into
      `record_empty`/`return []`). (b) `engine/orchestrator.py` finalize gates the empty-vs-failed decision on a
      recorded fetch-failure at BOTH levels: tier-2 venue-level (`orchestrator.py:3818` —
      `if effective_failure is not None: record_failed(classify_venue_error(code_token)) else: record_empty(SOURCE_RETURNED_ZERO)`,
      with `failed_per_dt_by_venue` precedence for the bundled-Databento partial-success case) and tier-3 per-instrument
      (`orchestrator.py:3766` —
      `if tier3_classified_error is not None: record_failed else record_empty(SOURCE_RETURNED_ZERO)`). So a swallowed
      fetch-failure cannot land as a frozen `SOURCE_RETURNED_ZERO` from the MTDS path. **RESIDUAL (still `- [ ]`):** the
      **instruments-service** fetch paths were NOT exhaustively read this session — focused verify needed that IS
      reference-data fetch errors likewise `record_failed` (not `record_empty`/`return []`). Reclassify this todo as
      "verify IS write-path CF-11 (MTDS already compliant)" — the heavy lift the todo assumed is largely absent.
- [ ] [CODE] P1. **IS-side CF-11 verify (slot/Harsh 2026-06-02, read-only) — cefi IS adapters use the
      classify+emit-event+return-[] shape.** Read the cefi IS reference-data adapters
      (`instruments-service/.../reference_data/adapters/cefi/`): `aster.py` / `hyperliquid.py` /
      `deribit_combo_adapter.py` / `tardis.py` handle transient API errors via `classify_venue_error(...)` + emit
      `ADAPTER_FETCH_FAILED`, then `return []` (consistent with the shard-isolation "no raise in per-venue loops" rule;
      tardis has multiple return-[] sites — L764/872/918/959/968). No ZERO-signal swallow found in the cefi IS adapters
      (unlike tradfi `databento.py:826` — see tradfi plan § CF-11). **OPEN QUESTION (needs the IS
      catalogue/manifest-layer read — deeper context):** whether the IS layer records `attempted_failed` from the
      emitted `ADAPTER_FETCH_FAILED` when an adapter returns [] — if it does NOT, the return-[] universe shrink is
      itself the gap. So cefi IS-side compliance is UNCONFIRMED (the classify+event pattern is right; the event→manifest
      wiring is unverified). Repo: instruments-service. parent_epic: mtds_mdps_master.

## Success criteria

- Canonical `cefi-prd` `_index` DATA-STATE: **v9 on 100% of rows** (was v8) + `asset_group` column + `pipeline_mode=`
  partition (non-blank) + **`source` on every cell (zero blank — HARD)** + typed reasons; **0 legacy-only cells**.
- The full-corpus form fix (not just the 838-cell gap) is landed — per the fix-fully-autonomously HARD RULE.
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy `market-data-tick-cefi-…` deletable.

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — cefi canonical form.
