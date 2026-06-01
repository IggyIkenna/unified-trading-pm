---
title: "TradFi manifest + data canonicalisation (v9 + pipeline_mode partition single-walk) — L3 owner for tradfi"
created: 2026-06-01
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-tradfi
status: active
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by: live-defi-rollout
locked_since: 2026-06-01
source:
  - defi_manifest_canonicalisation_2026_06_01.md §MASTER CONFLICT-2 (tradfi NOT L3-green: v9 + partition owe a walk)
  - tradfi_massive_dual_source_2026_05_28.md (source col + v8→v9 constant shipped; re-consolidation BLOCKED on drain)
  - _index comparison 2026-06-01 (tradfi DATA ~complete: overlap 12,944/12,948 → only 4 legacy-only cells)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# TradFi manifest + data canonicalisation (L3 owner for tradfi)

> **🔎 CROSS-AG FINDING from defi (2026-06-01) — CHECK THE SAME HERE**: defi's CF data-state audit found the legacy
> `_index` **100% NOT v9** (v4/5/6/8 spread), with **no `source`/`asset_group`/`pipeline_mode` COLUMNS** and glued
> venues — a FULL re-canonicalisation, not the headline cell-count. (Tradfi already reads v8 per CONFLICT-2 — confirm
> whether it's actually v9 on real rows, not the constant.) **CF-2 gotcha**: the migrate tool emitted `asset_group=` to
> the object PATH but did NOT stamp it as a parquet COLUMN → the rebuilt `_index` lacked the column. Fix = stamp
> `asset_group` (+ `schema_version`/`source`/`pipeline_mode`) as COLUMNS, never rely on the consolidator deriving them
> from the path. **Action**: run a CF data-state audit on tradfi's `_index` as pre-flight + verify (reusable:
> `market-tick-data-service/market_tick_data_service/scripts/audit_canonical_form.py` or
> `plans/audit/results/cf_manifest_audit_2026_06_01.py`) — trust the real data-state, never the v9 constant. If the same
> debt shows → fix fully in-walk (scope is a prior, not a ceiling). SSOT:
> `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md`.

> **MASTER**: `defi_manifest_canonicalisation_2026_06_01.md` §MASTER (L3, tradfi lane — resolves **CONFLICT-2**). This
> plan is the tradfi analogue of `defi_manifest`'s §C single-walk. **Single-walk discipline (HARD RULE)**: ONE bundled
> walk on the tradfi `_index` — bundle v8→v9 + `pipeline_mode=` partition + venue/data_type canonical verify +
> `available_at` preserve/backfill, AND absorb the still-owed `source`-field manifest re-consolidation
> (`tradfi_massive_dual_source` Task -031) into THIS same walk. Do NOT open a second walk;
> `pipeline_mode_partition_migration` rides THIS walk.

## Why this exists — tradfi DATA is ~complete but the canonical FORM is NOT landed (CONFLICT-2)

The 2026-06-01 `_index` comparison (legacy `market-data-tick-tradfi-central-element-323112` vs canonical
`market-data-tick-tradfi-prd-…`): legacy `(date,venue,data_type)` cells are ~fully a subset of canonical (overlap
**12,944 / 12,948** → only **4 legacy-only cells**). So at the data-copy level tradfi is **verify-only** — no legacy→
canonical data-loss migration is needed.

**But tradfi is NOT L3-green** (master CONFLICT-2):

- `tradfi_massive_dual_source` reports `source` column + the UTL `MANIFEST_SCHEMA_VERSION=9` **constant** done, but its
  **manifest re-consolidation was `BLOCKED-DEPENDENCY deferred`** (Task -031, blocked on the operator pre-migration
  drain Task -029) — so the LIVE canonical tradfi `_index` still reads **v8** (the manifest-v8 lesson: a constant bump ≠
  data state; read the actual rows).
- The **`pipeline_mode=` on-disk partition** is NOT on the tradfi object paths (`pipeline_mode_partition_migration` is a
  RIDER that must bundle into this walk per master CONFLICT-1).
- Venue / data_type canonical names need a verify pass (the canonical set is already underscore — `trades` / `tbbo` /
  `ohlcv_1m` / `ohlcv_15m` / `options_chain` / `futures_chain` — but the corpus must be confirmed clean of any legacy
  drift before decommission, same discipline as defi C2/C3/C12).
- `available_at` must be preserved where present / backfilled (never regenerated to migration-time) — the lookahead-bias
  invariant.

The hard-to-find-ness IS the bug (master rationale): one bundled walk makes data + manifest + `_index` + data-status all
canonical so the next audit is one pass.

## Scope boundary — what this plan does NOT own (no overlap)

- **`source` write-path + parquet-column backfill** is owned by `tradfi_massive_dual_source_2026_05_28.md` (Phase 5) +
  `data_source_provenance_all_asset_groups_2026_06_01.md` (Phase 7). Per **master CONFLICT-4**, `data_source_provenance`
  **SKIPS tradfi** (source already shipped). This plan only **re-consolidates the already-stamped `source` into the
  `_index`** as a RIDER of the same walk (so the v9 re-consolidation and the owed `source` re-consolidation are ONE
  walk, never two — that is exactly `tradfi_massive` Task -031, executed here).
- **Massive REST connector / dual-source backfill ingestion** stays in `tradfi_massive` (its Phase 5 + Phase 7).
- **Live / WebSocket Massive connector** stays deferred (`tradfi_massive` named successor `tradfi_massive_live_ws_…`).

## Sequencing — canonical migration is a GATE before any tradfi backfill (inherits master HARD RULE)

No tradfi backfill / writer relaunch until this walk is C-GREEN (master L3-gates-L5 + `bucket_name_ssot…` Phase 4). The
walk runs **behind / folded into** the tradfi pre-migration drain (`tradfi_massive` Task -029: drain GCP+AWS writers →
consolidate → snapshot `_index/snapshots/pre_migration_2026_06_01.parquet` → walk → re-consolidate → resume). L0
tarball-prune blocker (`issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md`) must be fixed first if run on a
VM.

## Canonical target form (tradfi)

| Dimension       | Legacy / now                                           | Canonical (target)                                                                                 |
| --------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| Bucket          | `market-data-tick-tradfi-{project}` (no env)           | `market-data-tick-tradfi-prd-{project}`                                                            |
| asset-group key | `category=tradfi`                                      | `asset_group=tradfi`                                                                               |
| pipeline_mode   | absent in path                                         | `pipeline_mode=` hive partition (`batch_databento`/`batch_massive`/`batch_yahoo`/`batch_barchart`) |
| schema_version  | live `_index` reads **v8** (constant says 9)           | v9 (re-consolidated — data-state verified, not constant)                                           |
| data_type name  | underscore-canonical (verify clean)                    | `trades`/`tbbo`/`ohlcv_1m`/`ohlcv_15m`/`options_chain`/`futures_chain`                             |
| venue           | ticker / exchange symbol (verify canonical)            | canonical ticker/symbol — flat `venue`                                                             |
| source          | column shipped (`tradfi_massive`); `_index` field owed | `source` re-consolidated into `_index` (RIDER; multi-source = two rows)                            |
| available_at    | per-row exists                                         | preserve where present; backfill only missing from day EOD UTC                                     |

## Phased execution

### P0 — pre-walk audit + scope

> **Scope is a prior, not a ceiling — fix-fully-autonomously (HARD RULE)**: the headline ("4 legacy-only / DATA
> ~complete") is a coarse prior. Read DATA-STATE. If the audit finds MORE form debt than implied (e.g. cefi turned out
> 100% v8 / no source / no asset_group / blank pipeline_mode — a full re-canonicalisation, not the framed gap), fix ALL
> of it in this one walk — NOT descoped, deferred, post-cutover, or `BLOCKED-OPERATOR-DECISION` (a data-state gap is not
> a design fork). SSOT: `canonical_form_cross_service_audit_checklist.md` § "Audit scope is a PRIOR, not a ceiling".

- [x] ✅ [DATA] P0. LIVE canonical `tradfi-prd` `_index` DATA-STATE (slot-3 tool, 2026-06-01 — confirms CONFLICT-2):
      **100% v8** (0/144,062 rows v9 — the constant lied, the data is v8); `asset_group` col present (CF-2 rows GREEN);
      **`pipeline_mode` blank (0/144,062 — CF-3 RED)**; **no `source` column (CF-4 RED)**; CF-5 typed GREEN
      (`EXPECTED_WEEKEND` 35,050 / `EXPECTED_HOLIDAY` 2,427 / `EXPECTED_OUT_OF_COVERAGE_WINDOW` 8 / `SOURCE_RETURNED_ZERO`
      5). capture_status: captured 100,536 / empty 37,490 / attempted_failed 6,036.
- [x] ✅ [DATA] P0. Legacy-only diff: **71 legacy-only cells** (NOT 4 — headline undershot; NYSE `tbbo` 2023-05 spread;
      legacy 12,948 · canonical 17,941 · overlap 12,877). All 71 copied + re-versioned in the C0 walk.
- [x] ✅ [DATA] P0. **`available_at` FINDING — there is NO `available_at` column in the canonical tradfi `_index`** (only
      `written_at`), contradicting the plan's "tradfi_massive shipped per-row available_at" assumption (CF-8 RED). The C0
      walk MUST add a per-row `available_at` (preserve from parquet where present; backfill missing from day EOD UTC —
      never migration-time). Captured as expanded scope (prior-not-ceiling).
- [ ] [DATA] P1. Verify the corpus venue / data_type strings are underscore-canonical: data-state shows venues
      `BARCHART/CBOE/CME/FX/ICE/NASDAQ/NYSE/YAHOO_FINANCE` (canonical) BUT also `UNKNOWN` + blank `''` (drift to
      diagnose); data_types `ohlcv_15m/ohlcv_1m/ohlcv_24h/options_chain/tbbo/trades` + blank `''`. Relabel/diagnose the
      `UNKNOWN`/blank rows in the walk (do NOT bulk-rename ambiguous strings).

### C — single-walk (v9 + partition + canonical verify + source re-consolidate)

- [ ] [DATA] P0. **Phase 0 — layout audit (MANDATORY, blocking — slot-2 DeFi lesson 2026-06-01)**: enumerate ALL
      top-level trees + nested layouts in the tradfi source + canonical buckets before the walk; classify duplicate
      (keep freshest schema) vs complementary (migrate all → canonical v9). Cover every in-scope layout or the walk is
      incomplete (review-blocking). SSOT: `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § grounded recipe Phase 0.

> **Migration-script performance contract (HARD — codified 2026-06-01, defi C0 lesson)**: the walk script MUST be
> parallel (`ThreadPoolExecutor` — GCS I/O releases the GIL → 5–10×; a bare `for obj` loop is review-blocking) + wire
> `--workers`/`--start-date`/`--end-date` (date-shardable across VMs — no dead args) + `gcs_copy_object` for path-only
> moves (server-side ~250×) / download+transform+upload only for content changes + unbuffered progress logging
> (`python -u`, counter every ~1000) + per-object `try/except…continue` isolation + idempotent re-runs. SSOT:
> `codex/05-infrastructure/gcs-object-operations.md` § "Migration-script performance contract".

- [ ] [DATA] P0. C0 ONE bundled walk on the tradfi `_index` + objects: (a) `pipeline_mode=` hive partition added to
      object paths (`pipeline_mode_partition_migration` RIDER — satisfied here, do NOT run separately); (b) re-version
      manifest rows to **v9** (data-state — assert the rewritten rows actually carry 9, not just the constant); (c)
      **`category=`→`asset_group=` across BOTH object PATHS and manifest `_index` ROWS** + env-split bucket for any
      legacy-form rows that remain (CODE side — writers emit `asset_group=` — already shipped via archived
      `venue_axis_asset_group_vocabulary_2026_04_25`; this is historical data+manifest only); (d) venue/data_type
      canonical relabel for any drift found in P0; (e) `available_at` preserve-or-backfill (never migration-time). RUN
      ON A VM via the canonical-migration launcher (gated on L0 tarball-prune fix) — small data scope (≈12,948 cells)
      may run locally if P0 confirms.
- [ ] [DATA] P0. C-source RIDER (absorbs `tradfi_massive` Task -031): re-consolidate the already-stamped parquet
      `source` into the `_index` in THIS walk — every tradfi `_index` row carries `source`; multi-source cells (the 6
      databento+massive/yahoo/barchart cells) emit two rows. Coordinate so `tradfi_massive`'s deferred re-consolidation
      is NOT run as a separate walk.
- [ ] [DATA] P0. C-pipeline_mode RIDER: confirm the `pipeline_mode=` partition for tradfi lands in THIS walk (satisfies
      `pipeline_mode_partition_migration_2026_06_01.md` for tradfi).

### Verify + handoff to decommission

- [ ] [DATA] P0. Post-walk: fresh `_index` read — `schema_version=9` for 100% of rows (data-state), `pipeline_mode=`
      partition present + non-null, venue/data_type canonical only, `source` populated (multi-source = two rows),
      `available_at` non-null. **0 legacy-only cells** (re-run the `(date,venue,data_type)` comparison). This is the
      C-GREEN signal `bucket_name_ssot…` Phase 6/7 waits on for the legacy `market-data-tick-tradfi-…` decommission.
- [ ] [DATA] P1. Notify `tradfi_massive_dual_source` to flip its Task -031 (manifest re-consolidation) — executed here
      as the C-source rider; cross-link both ways.

## Execution checklist (grounded — next session, finish in full)

> CF debt is in the `_index` MANIFEST + object PATHS, NOT the raw tick parquets. See
> `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § MECHANISM + layout map. tradfi raw =
> HYPHEN pseudo-hive (`day-2025-11-02/data_type-ohlcv_1m/equities/NYSE/`) — parse `-`-delim, not `=`.
>
> ⚠️ **IRREVERSIBLE — E7 DELETES legacy `market-data-tick-tradfi` permanently.** Do not run E2–E7 until the canonical
> target (v9 data-state, `day=/pipeline_mode=/asset_group=tradfi/…`, source re-consolidated, available_at added) is
> CONFIRMED CORRECT at verify. One pass, no confusion — once legacy is deleted it is gone.

- [x] ✅ [DATA] P0. E1 Phase-0 layout audit on `tradfi-prd` raw (slot-3 2026-06-02, `gcloud storage ls` enumeration —
      see **E1 RESULTS** below). Confirmed THREE raw layouts (NOT one) + candle + `databento-batch-registry/`. The 0-row
      sample concern is the `*:MARKET_CLOSED:PLACEHOLDER.parquet` placeholder files in the hyphen tbbo/trades trees (a
      real empty-day marker, not systemic corruption — handle as empty, do not migrate as captured data).

> **E1 RESULTS — tradfi raw layout reality (slot-3 2026-06-02, exhaustive `ls`, lesson #0)**. Bucket
> `market-data-tick-tradfi-prd-central-element-323112/raw_tick_data/by_date/`:
>
> - **L-hive (DOMINANT, 1,996 `day=` dirs, 2020+)**: `day={D}/asset_group=tradfi/venue={V}/instrument_type={IT}/data_type={DT}/[underlying={U}/]{file}`.
>   Near-canonical — has `asset_group=`, MISSING only `pipeline_mode=`. Bundled types (`combo`/`futures_chain`/`options_chain`)
>   carry an `underlying=` bundle segment (like cefi chain bundles). venue set observed = CME (futures/options/combo).
>   **Fix = path-only `pipeline_mode=` insert after `day=` (server-side `gcs_copy_object`), preserve `underlying=` bundle, CF-7 relabel in place** — identical to the cefi L-bulk branch.
> - **L-hyphen (12 `day-` dirs ONLY, recent databento batches Nov-2025…Feb-2026)** — TWO sub-shapes:
>   - ohlcv_1m: `day-{D}/data_type-ohlcv_1m/{itype_bare∈equities|etf|futures_chain}/{VENUE∈NYSE|NASDAQ|CME}/{instrument_id}.parquet`
>   - trades|tbbo: `day-{D}/data_type-{trades|tbbo}/{VENUE}/{file}` — **NO instrument_type segment** (derive itype from the `{VENUE}:{ITYPE}:{SYMBOL}` instrument-id filename).
>   Bare itype `equities`→canonical `equity`; `etf`→`etf`; `futures_chain`→`futures_chain`. **Fix = parse hyphen pseudo-hive → build canonical path manually + server-side copy** (content already classified).
>   Placeholder files `…:MARKET_CLOSED:PLACEHOLDER.parquet` = empty-day markers → do NOT migrate as data.
> - **⚠️ OVERLAP/DEDUP HAZARD (lesson #2/#5/#6)**: the 12 hyphen dates **ALSO exist as `day=` hive** (verified 2025-11-02, 2026-01-01, 2026-02-01 in BOTH). On those dates: equals-hive has ONLY `venue=CME` (futures_chain/options_chain/combo); hyphen has `venue=CME futures_chain` (OVERLAP) **PLUS** `NYSE/NASDAQ equities/etf` (COMPLEMENTARY — equities/etf exist ONLY in hyphen). So the migrator MUST: (1) migrate the complementary equities/etf from hyphen (would be lost otherwise); (2) for the CME-futures_chain overlap, **sample object content per lesson #5 before choosing a winner** — default winner = L-hive (the established classified canonical structure) via cell-level skip-if-equals-hive-already-has-(date,venue,itype,data_type); only fall to hyphen where hive lacks the cell. Dedup at the CELL key, not the object path (file granularity differs).
> - **`databento-batch-registry/`** = job-dedup registry (not market data) → NOT migrated, NOT deleted by E7.
> - pipeline_mode per object = `derive_pipeline_mode_for_row(venue, "tradfi", data_type)` (UTL `pipeline_mode_resolver`) — venue-override (BARCHART→batch_barchart / YAHOO→batch_yahoo / EIA→batch_eia) else SOURCE_PRIORITY-primary (CME/NYSE/NASDAQ ohlcv_1m/trades/tbbo → `batch_databento`). **Identical derivation to the live writer `resolve_pipeline_mode` → batch=live correct.** `source` (E5) = `source_string_for(pipeline_mode)`.
- [ ] [DATA] P0. E2 Build/extend `migrate_tradfi_canonical.py` to the v9-canonical target (perf-contract): parse the
      hyphen pseudo-hive → canonical `day=/pipeline_mode=batch_{databento,massive,yahoo,barchart}/asset_group=tradfi/
      venue=/…/data_type=`; copy the 71 legacy-only cells (NYSE tbbo 2023-05 …).
- [ ] [DATA] P0. E3 Confirm tradfi writer drained; snapshot `tradfi-prd/_index` (pre-migration drain per tradfi_massive -029).
- [ ] [DATA] P0. E4 Dry-VM → timing → optimise → full-VM run (144k index rows — modest; no fire-and-forget).
- [ ] [DATA] P0. E5 Manifest rebuild: scan canonical paths → `ManifestWriter` stamping `source` (per UAC SOURCE_PRIORITY /
      BARCHART·YAHOO_FINANCE·DATABENTO·MASSIVE venue→source) + `pipeline_mode` + `available_at` → consolidator → v9. This
      executes `tradfi_massive` Task -031 (source re-consolidation) — cross-link + flip there.
- [ ] [DATA] P1. E6 CF-7 relabel: `UNKNOWN`/blank venue + blank data_type → canonical (diagnose, don't bulk-rename).
- [ ] [DATA] P0. E7 Verify: `cf_manifest_audit_2026_06_01.py market-data-tick-tradfi-prd-…` → CF-1…CF-12 GREEN
      data-state (esp. v9 confirmed on real rows — CONFLICT-2); flip CF-coverage in `tradfi_master_audit_instructions.md`.
      ⚠️ IRREVERSIBLE — only after GREEN: hand C-GREEN to L6 → **delete legacy `market-data-tick-tradfi` permanently**.

## Success criteria

- Canonical `tradfi-prd` `_index` = **v9** (data-state verified) + `pipeline_mode=` partition + `source` populated +
  `available_at` non-null; venue/data_type canonical only.
- 0 legacy-only tradfi cells; `tradfi_massive` Task -031 closed (re-consolidation done here).
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy `market-data-tick-tradfi-…` deletable; tradfi writer relaunch
  unblocked (writes canonical-only).

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — tradfi canonical form (v9 + pipeline_mode partition).
