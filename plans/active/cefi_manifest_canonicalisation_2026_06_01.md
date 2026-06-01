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

- [ ] [DATA] P0. **Phase 0 — layout audit (MANDATORY, blocking — slot-2 DeFi lesson 2026-06-01)**: before the walk,
      enumerate ALL top-level trees + nested layouts in the cefi source + canonical buckets (`raw_tick_data/by_date/`
      flat-symbol, `processed_candles/by_date/day=/timeframe=/…`, any `day=/category=` or bare `{venue}/{chain}/date=`).
      Per layout: object count + sample schema; classify duplicate (keep freshest) vs complementary (migrate all). The
      walk MUST cover every in-scope layout or it is incomplete (review-blocking). SSOT:
      `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § Cross-AG lesson + grounded recipe Phase 0.

> **Migration-script performance contract (HARD — codified 2026-06-01, defi C0 lesson)**: the walk script MUST be
> parallel (`ThreadPoolExecutor` — GCS I/O releases the GIL → 5–10×; a bare `for obj` loop is review-blocking) + wire
> `--workers`/`--start-date`/`--end-date` (date-shardable across VMs — no dead args) + `gcs_copy_object` for path-only
> moves (server-side ~250×) / download+transform+upload only for content changes + unbuffered progress logging
> (`python -u`, counter every ~1000) + per-object `try/except…continue` isolation + idempotent re-runs. SSOT:
> `codex/05-infrastructure/gcs-object-operations.md` § "Migration-script performance contract".

- [ ] [DATA] P0. C0 ONE bundled **WHOLE-CORPUS** walk (the finding makes this corpus-wide, not 838 cells): (a)
      re-version **every** cefi row+parquet **v8→v9** (CF-1) asserting data-state, not the constant; (b) add the
      **`source` column** = `tardis` on every row (CF-4) + (c) the **`asset_group=cefi` column/key** on rows + paths
      (CF-2) + (d) the **`pipeline_mode=` partition** + non-blank column (CF-3); (e) typed empty-reasons (CF-5); (f) the
      838-cell legacy→canonical gap-fill copy (`raw_tick_data/` + `processed_candles/`, layout-aware — cefi has NO
      `by_date/`). Column adds (b–c) are a CONTENT rewrite → download+transform+upload **parallelised per the perf
      contract** (NOT a server-side path move; NOT "run locally" — this is a VM-scale walk now, gated on L0). The
      838-cell pure-path copies use `gcs_copy_object`. Idempotent.
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
- [ ] [DATA] P0. E3 Confirm cefi writer drained (mdps-backfill-cefi already self-terminated); snapshot
      `cefi-prd/_index`.
- [ ] [DATA] P0. E4 Dry-VM → review timing (cefi is 2.6M index rows / largest; date-shard across VMs if >1h) → optimise
      → full-VM run (no fire-and-forget verification).
- [ ] [DATA] P0. E5 Manifest rebuild → v9. **BUILD SPEC (refined slot-3 2026-06-01 — ADAPT the existing tool, don't
      rebuild):** `market_tick_data_service/scripts/rebuild_cefi_manifest.py` ALREADY encodes the correct per-instrument
      row key (the LIVE writer key =
      `date,venue,chain,data_type,league_id,instrument_type,underlying,quote_asset,     margin_type,instrument_id`;
      orchestrator.py:2937/2957) + tolerates `raw_tick_data/by_date/`+`asset_group=`. Two changes only: (1) its `_PAT_*`
      regexes + `prefix_templates` do NOT account for the NEW `pipeline_mode=` segment between `day=` and `asset_group=`
      → list per `raw_tick_data/by_date/day={d}/` and extend `parse_hive_path` to capture an optional
      `pipeline_mode=(?P<pipeline_mode>[^/]+)/`; (2) stamp v9 cols: pass `source` (cefi single-source `tardis`;
      HYPERLIQUID→`hyperliquid_rest`) + `pipeline_mode` to the writer. **OPEN INTERNALS Q (resolve first):** confirm
      `ManifestWriter.add()` PERSISTS `pipeline_mode` (the live cefi `add()` at orchestrator.py:2957 does NOT pass it →
      that's why CF-3 is blank); the manifest row schema HAS `pipeline_mode`/`source`/`available_at` cols
      (manifest_writer.py:1129/1138/74) + `_coerce_pipeline_mode`. If `add()` drops pipeline_mode (→ \*\*kwargs), use
      `record_captured`/`record_captured_from_counts` (which take `pipeline_mode=` explicitly) instead. `available_at`:
      prefer the parquet's column; else day-EOD-UTC (never migration-time). Then consolidator merge → v9 `_index`. Same
      adaptation applies to `rebuild_prediction_manifest.py` for prediction E5.
- [ ] [DATA] P1. E6 CF-7 relabel: `COINBASE`↔`COINBASE-SPOT`, blank venue/data_type → canonical (diagnose, don't bulk).
      Investigate the 50% `attempted_failed` rows (1.33M) — flag to cefi AG owner (separate from canonicalisation).
- [ ] [DATA] P0. E7 Verify: `cf_manifest_audit_2026_06_01.py market-data-tick-cefi-prd-…` → CF-1…CF-12 GREEN on
      data-state; flip CF-coverage rows in `cefi_master_audit_instructions.md`.
- [ ] [DATA] P0. E8 ⚠️ IRREVERSIBLE — only after E7 GREEN: hand C-GREEN to `bucket_name_ssot…` L6 → **delete legacy
      `market-data-tick-cefi` permanently** (single source of truth; legacy data is gone).

## Success criteria

- Canonical `cefi-prd` `_index` DATA-STATE: **v9 on 100% of rows** (was v8) + `asset_group` column + `pipeline_mode=`
  partition (non-blank) + **`source` on every cell (zero blank — HARD)** + typed reasons; **0 legacy-only cells**.
- The full-corpus form fix (not just the 838-cell gap) is landed — per the fix-fully-autonomously HARD RULE.
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy `market-data-tick-cefi-…` deletable.

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — cefi canonical form.
