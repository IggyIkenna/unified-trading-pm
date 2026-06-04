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

## Slot-6 TradFi master orchestrator — owned + attached plans/issues

> **Slot↔asset-group split (operator 2026-06-03):** one asset group per slot (five slots). **Slot 6 = TradFi
> end-to-end** across every service — instruments-service → MTDS → MDPS → features → downstream → strategy/execution →
> bucket/data/manifest/UI. **THIS plan is the TradFi master orchestrator**: every tradfi-related plan + issue
> cross-references here; orphaned tradfi issues attach here. Sibling AG masters: **defi → slot 2**
> (`defi_manifest_canonicalisation_2026_06_01.md`), **cefi → slot 3** (`cefi_manifest_canonicalisation_2026_06_01.md`),
> **sports → slot 4** (`sports_manifest_canonicalisation_2026_06_01.md`), **prediction → slot 5**
> (`prediction_manifest_canonicalisation_2026_06_01.md`). Cross-cutting per-service plans keep their own `assigned_vm`
> (vm-ml / vm-cross-cutting) as PRIMARY owner — slot-6 tracks + drives only their **tradfi slice**, not the whole plan.

**Cross-referenced tradfi slices (primary owner keeps the plan; slot-6 drives the tradfi portion):**

| Plan / issue                                                   | Primary VM       | TradFi slice                                                                                       |
| -------------------------------------------------------------- | ---------------- | -------------------------------------------------------------------------------------------------- |
| `tradfi_massive_dual_source_2026_05_28.md`                     | vm-tradfi        | Massive ingest + `source=databento\|massive` write-path (this plan's C-source RIDER; absorbs -031) |
| `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` | vm-cross-cutting | L3 tradfi ordering + L6 legacy `market-data-tick-tradfi` delete                                    |
| `pipeline_mode_partition_migration_2026_06_01.md`              | vm-cross-cutting | tradfi `pipeline_mode=` partition (this plan's C-pipeline_mode RIDER)                              |
| `instruments_manifest_canonicalisation_2026_06_01.md`          | vm-cross-cutting | `instruments-store-tradfi` reference slice                                                         |
| `downstream_services_manifest_canonicalisation_2026_06_01.md`  | vm-ml            | tradfi MDPS/features/execution canonical-form slice                                                |
| tradfi phase-3 backfill + VIX/Massive continuity work          | vm-tradfi        | tradfi data acquisition slice                                                                      |

> **🤝 HANDOFF (slot-5 → slot-6, 2026-06-03) — E5 carry-forward + CF-11 + IS databento, code-complete, BLOCKED
> dep-tier.** Slot-5 (pre-reassignment) built + verified the following TradFi work; handing to slot-6 (TradFi owner) per
> the one-AG-per-slot reassignment. **Nothing is lost — code is on `origin/handoff/tradfi-e5-cf11-slot6` in both
> repos:**
>
> 1. **mtds E5 rebuild CF-11 carry-forward — DONE, QG-green** (`handoff/tradfi-e5-cf11-slot6`@2746cf1a). The rebuild now
>    re-emits the ~43k non-captured legacy `_index` rows (was silently dropping them = false-complete coverage), with
>    the CF-11 3-way trading-day classifier (blank/`SOURCE_RETURNED_ZERO` on a trading day → `attempted_failed` via
>    `record_zero_rows`). 11 unit tests green. See E5 STATUS todo below.
> 2. **IS databento parse-failure event — DONE (un-QG'd)** (`handoff/tradfi-e5-cf11-slot6`@b4a43093). Observability fix
>    only — see the CONFIRMED databento:820 SILENT-SHRINK finding + the **P0 [CODE] state-threading fix todo** below
>    (the real data-correctness fix, not yet built).
> 3. **`available_at` reclassified** to an E4 parquet-layer verify (not a rebuild/manifest concern) — see E5 STATUS
>    todo.
>
> **BLOCKER (both repos): dep-tier gate** — mtds needs UTL's `record_zero_rows`, which is on LDR but **NOT on staging**
> (verified 0/staging). Skipping the gate would break mtds on staging. **Slot-6 next step**: once the LDR→staging
> automation drains UTL+UAC (semver-agent on quality-gates-v2), `git merge`/cherry-pick the handoff branch + ship via
> `quickmerge --agent` (mtds is QG-green; run the IS QG for the databento branch). Then flip the E5 + CF-11 todos.

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
      (`EXPECTED_WEEKEND` 35,050 / `EXPECTED_HOLIDAY` 2,427 / `EXPECTED_OUT_OF_COVERAGE_WINDOW` 8 /
      `SOURCE_RETURNED_ZERO` 5). capture_status: captured 100,536 / empty 37,490 / attempted_failed 6,036.
- [x] ✅ [DATA] P0. Legacy-only diff: **71 legacy-only cells** (NOT 4 — headline undershot; NYSE `tbbo` 2023-05 spread;
      legacy 12,948 · canonical 17,941 · overlap 12,877). All 71 copied + re-versioned in the C0 walk.
- [x] ✅ [DATA] P0. **`available_at` FINDING — there is NO `available_at` column in the canonical tradfi `_index`**
      (only `written_at`), contradicting the plan's "tradfi_massive shipped per-row available_at" assumption (CF-8 RED).
      The C0 walk MUST add a per-row `available_at` (preserve from parquet where present; backfill missing from day EOD
      UTC — never migration-time). Captured as expanded scope (prior-not-ceiling).
- [ ] [DATA] P1. Verify the corpus venue / data_type strings are underscore-canonical: data-state shows venues
      `BARCHART/CBOE/CME/FX/ICE/NASDAQ/NYSE/YAHOO_FINANCE` (canonical) BUT also `UNKNOWN` + blank `''` (drift to
      diagnose); data_types `ohlcv_15m/ohlcv_1m/ohlcv_24h/options_chain/tbbo/trades` + blank `''`. Relabel/diagnose the
      `UNKNOWN`/blank rows in the walk (do NOT bulk-rename ambiguous strings).

### C — single-walk (v9 + partition + canonical verify + source re-consolidate)

- [ ] [DATA] P0. **Phase 0 — layout audit (MANDATORY, blocking — slot-2 DeFi lesson 2026-06-01)**: enumerate ALL
      top-level trees + nested layouts in the tradfi source + canonical buckets before the walk; classify duplicate
      (keep freshest schema) vs complementary (migrate all → canonical v9). Cover every in-scope layout or the walk is
      incomplete (review-blocking). SSOT: `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § grounded
      recipe Phase 0.

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
- [ ] [DATA] P0. **Orphan sweep + bucket-state evidence (slot/Harsh bucket-state verification 2026-06-02).** Measured
      (Cloud Monitoring `storage/v2/total_count`, live-object): `market-data-tick-tradfi-prd` 5,299,037 (~93% of legacy
      5,696,400), current to `day=2026-05-18` (= legacy). Sample `-prd` parquet
      `day=2026-05-18/asset_group=tradfi/venue=CME/instrument_type=combo/data_type=ohlcv_1m/underlying=SP500/ticks.parquet`
      (244 rows): columns LACK `schema_version`/`source`/`pipeline_mode`/`asset_group` (it has `available_at`) → `-prd`
      is INTERMEDIATE FORM (`asset_group=` in PATH only, NO `pipeline_mode=`). So the E4 walk writes NEW
      `pipeline_mode=` paths → the pre-existing legacy-FORM `-prd` objects become ORPHANS; E5/E7 MUST delete the
      legacy-FORM `-prd` objects too (not only the legacy SOURCE bucket). Legacy carries 3.52M noncurrent objects → E7's
      bulk-delete (incl. the 12 hyphen 0-row-placeholder prefixes) must also purge noncurrent versions; count
      comparisons use Monitoring `type=live-object`.
- [ ] [DATA] P1. Notify `tradfi_massive_dual_source` to flip its Task -031 (manifest re-consolidation) — executed here
      as the C-source rider; cross-link both ways.

## Execution checklist (grounded — next session, finish in full)

> CF debt is in the `_index` MANIFEST + object PATHS, NOT the raw tick parquets. See
> `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § MECHANISM + layout map. tradfi raw = HYPHEN
> pseudo-hive (`day-2025-11-02/data_type-ohlcv_1m/equities/NYSE/`) — parse `-`-delim, not `=`.
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
> - **L-hive (DOMINANT, 1,996 `day=` dirs, 2020+)**:
>   `day={D}/asset_group=tradfi/venue={V}/instrument_type={IT}/data_type={DT}/[underlying={U}/]{file}`. Near-canonical —
>   has `asset_group=`, MISSING only `pipeline_mode=`. Bundled types (`combo`/`futures_chain`/`options_chain`) carry an
>   `underlying=` bundle segment (like cefi chain bundles). venue set observed = CME (futures/options/combo). **Fix =
>   path-only `pipeline_mode=` insert after `day=` (server-side `gcs_copy_object`), preserve `underlying=` bundle, CF-7
>   relabel in place** — identical to the cefi L-bulk branch.
> - **L-hyphen (12 `day-` dirs ONLY, recent databento batches Nov-2025…Feb-2026)** — TWO sub-shapes:
>   - ohlcv_1m:
>     `day-{D}/data_type-ohlcv_1m/{itype_bare∈equities|etf|futures_chain}/{VENUE∈NYSE|NASDAQ|CME}/{instrument_id}.parquet`
>   - trades|tbbo: `day-{D}/data_type-{trades|tbbo}/{VENUE}/{file}` — **NO instrument_type segment** (derive itype from
>     the `{VENUE}:{ITYPE}:{SYMBOL}` instrument-id filename). Bare itype `equities`→canonical `equity`; `etf`→`etf`;
>     `futures_chain`→`futures_chain`. **Fix = parse hyphen pseudo-hive → build canonical path manually + server-side
>     copy** (content already classified). Placeholder files `…:MARKET_CLOSED:PLACEHOLDER.parquet` = empty-day markers →
>     do NOT migrate as data.
> - **⚠️ CORRECTION (slot-3 2026-06-02, operator cross-check vs `gcs_hive_partition_malformed_paths_remediation`): the
>   ENTIRE hyphen tree is 0-ROW PLACEHOLDERS, NOT real data.** Row-count inspection of the hyphen parquets (ohlcv_1m
>   equities AAPL = 0 rows / futures_chain AUD = 0 rows / trades CME-option = 0 rows; uniform 3070/4251-byte
>   header-only) confirms these are the issue-doc **Pattern 1** Massive **dry-run placeholders** (written 2026-02-09;
>   `MASSIVE_API_KEY` created 2026-05-29 — 3.5 months later; **0 BATCH_MASSIVE rows in the manifest** — never a real
>   ingest). An earlier path-only `ls` enumeration mis-read them as "complementary equities/etf real data" — a row-count
>   check disproved it. **So**: the migrator does NOT migrate the hyphen tree (a 0-row guard skips every placeholder —
>   banned to migrate empties that look populated); the hyphen prefixes are **DELETED at E7** (this IS the issue-doc
>   Pattern-1 cleanup, now owned here). The 12 hyphen dates' REAL data is the `day=` hive (CME databento, verified
>   224/66-row files) — handled by L-hive. **NYSE/NASDAQ equities/etf were NEVER genuinely ingested** (0-row dry run
>   only) → a REAL tradfi coverage gap (backfill todo below), NOT data to migrate.
> - **`databento-batch-registry/`** = job-dedup registry (not market data) → NOT migrated, NOT deleted by E7.
> - pipeline_mode per object = `derive_pipeline_mode_for_row(venue, "tradfi", data_type)` (UTL `pipeline_mode_resolver`)
>   — venue-override (BARCHART→batch_barchart / YAHOO→batch_yahoo / EIA→batch_eia) else SOURCE_PRIORITY-primary
>   (CME/NYSE/NASDAQ ohlcv_1m/trades/tbbo → `batch_databento`). **Identical derivation to the live writer
>   `resolve_pipeline_mode` → batch=live correct.** `source` (E5) = `source_string_for(pipeline_mode)`.

- [x] ✅ [DATA] P0. E2 BUILT `migrate_tradfi_to_v9_canonical.py` (NEW v9 path canonicaliser — NOT the old
      content-reclassification `migrate_tradfi_canonical.py`) — mtds@ae9e1b31 + launcher deployment-service@4cbb2e2.
      Handles all 3 layouts (E1 RESULTS): L-hive `pipeline_mode=` insert (preserve `underlying=` bundle), L-hyphen 2
      sub-shapes parse → canonical, candles insert; overlap dedup (L-hive wins CME, hyphen fills equities/etf); chain
      types built manually (UAC builder rejects futures_chain/options_chain); pipeline_mode via
      `derive_pipeline_mode_for_row` (batch=live identical). 12 unit tests green (ruff+basedpyright clean). The 71
      legacy-only cells ride `--also-legacy`. DRY-BY-DEFAULT + `--apply`. Source/v9 columns added by E5 rebuild (next).
- [ ] [DATA] P0. E3 Confirm tradfi writer drained; snapshot `tradfi-prd/_index` (pre-migration drain per tradfi_massive
      -029).
- [ ] [DATA] P0. E4 Dry-VM → timing → optimise → full-VM run (144k index rows — modest; no fire-and-forget).
  - **DRY-RUN SCOPING DONE (slot-6 2026-06-03 — sharding/perf scoped, NO apply; full-VM run stays operator-gated):**
    - **Migrator** `migrate_tradfi_to_v9_canonical.py --dry-run` (real GCS `tradfi-prd`): **5,305,520 objects** planned,
      **moved=0 (dry)**, **100,698 L-hyphen placeholders correctly skipped** (0-row guard), **0 errors** → clean,
      date-shardable corpus; placeholder-skip is honest-absence-safe.
    - **Rebuild** `rebuild_tradfi_manifest.py --dry-run`: **704,641 shards / 6 venues**, distribution **CME 486,189
      (69%)** · NYSE 162,519 · NASDAQ 44,203 · ICE 9,452 · CBOE 1,607 · FX 671; **1,984 distinct dates**; CF-11 re-emit
      path exercised (no-op in mock = no local `_index`, works against real GCS).
    - **Sharding/perf recommendation**: shard the full run **by `day=`** (1,984 dates) across VMs; **CME is the heavy
      partition** (69%) → give it dedicated shards; use **workers=32 REST-API** (GCS-object-ops rule, ~250× vs CLI).
      Migrator is `--apply`-gated + dry-by-default; E3 drain + snapshot still precede the real run.
- [x] ✅ [DATA] P0. E5 Manifest rebuild → v9 — **DONE: NEW `rebuild_tradfi_manifest.py` (mtds@e6250b99, 2026-06-02, 20
      tests)**. Scans canonical
      `day=/pipeline_mode=/asset_group=tradfi/venue=/instrument_type=/data_type=/[underlying=/]{file}` (per-instrument →
      instrument_id=stem; chain bundle → underlying=; optional pipeline_mode= segment + legacy tolerance); day-level
      list; `-prd` bucket; stamps `pipeline_mode` (path-or-`derive_pipeline_mode_for_row`) + `source` (REQUIRED,
      `source_string_for(pm)`); SKIPS the `day-` hyphen 0-row placeholder tree (E7 deletes those). Modeled on the cefi
      E5. **REMAINING (gate G4) — STATUS (slot-5 2026-06-03):** (a) **legacy-`_index` carry-forward of
      `attempted_failed`/typed-`empty_confirmed` rows + the CF-11 3-way trading-day classifier = DONE** (mtds handoff
      branch `handoff/tradfi-e5-cf11-slot6`@2746cf1a (QG-green; ship via quickmerge once UTL+UAC on staging — dep-tier:
      needs UTL record_zero_rows)): `rebuild_tradfi_manifest.py` now reads the legacy `_index`, re-emits non-captured
      rows v9 (date-windowed for shard-idempotency), routes blank/`SOURCE_RETURNED_ZERO` empties on a TRADING day (via
      UAC `non_trading_day_reason`) → `attempted_failed` (`record_zero_rows(was_expected=True)`), preserves typed
      weekend/holiday empties + the 6,036 existing `attempted_failed` verbatim, dedups against captured cells; 11 unit
      tests. The 5 `SOURCE_RETURNED_ZERO` rows are auto-re-evaluated by the classifier at rebuild time. (b)
      **`available_at` = NOT a rebuild/manifest concern** — it is a per-row column INSIDE the data tick parquets (UTL
      `AvailabilityRecord` manifest schema has NO `available_at` field; CF-8 conflated the two). The data parquets
      already carry it (orphan-sweep sample, E7-evidence todo below); the migrator's whole-object server-side copy
      preserves it. → reclassified as an **E4 parquet-layer VERIFY** (confirm all legacy parquets carry `available_at`;
      backfill only any that don't), removed from the rebuild's scope. Executes `tradfi_massive` Task -031 (source
      re-consolidation). Original recipe retained below for reference.
- [ ] [DATA] P2. E5 build-spec reference (superseded by the DONE item above): NEW `rebuild_tradfi_manifest.py`.
      REFERENCE: cefi E5 DONE (mtds@2c3a479b) — copy its structure (optional `pipeline_mode=` regex segment, DAY-level
      list prefix, canonical `-prd` bucket, stamp `pipeline_mode` via
      path-or-`derive_pipeline_mode_for_row(venue,"tradfi",dt)`). The post-migrator tradfi canonical form (the L-hive
      shape + inserted pipeline_mode) is
      `raw_tick_data/by_date/day={D}/pipeline_mode={mode}/asset_group=tradfi/venue={V}/instrument_type={IT}/data_type={DT}/[underlying={U}/]{file}`
      (chain bundles keep `underlying=`). Stamp `source` via `source_string_for(pipeline_mode)`
      (databento/massive/yahoo/ barchart/eia — REQUIRED for tradfi v9 per `MissingSourceError`) + `available_at`
      (parquet col else day-EOD-UTC). NO hyphen-tree rows (those are 0-row placeholders excluded by the migrator +
      deleted at E7). Executes `tradfi_massive` Task -031 (source re-consolidation) — cross-link + flip there.
- [ ] [DATA] P1. E6 CF-7 relabel: `UNKNOWN`/blank venue + blank data_type → canonical (diagnose, don't bulk-rename).
- [ ] [DATA] P0. E7 Verify: `cf_manifest_audit_2026_06_01.py market-data-tick-tradfi-prd-…` → CF-1…CF-12 GREEN
      data-state (esp. v9 confirmed on real rows — CONFLICT-2); flip CF-coverage in
      `tradfi_master_audit_instructions.md`. ⚠️ IRREVERSIBLE — only after GREEN: hand C-GREEN to L6 → **delete legacy
      `market-data-tick-tradfi` permanently** + **bulk-delete the 12 `day-*` hyphen 0-row-placeholder prefixes** in
      `tradfi-prd` (~110k objects — the issue-doc **Pattern-1 cleanup, now executed here**; pre-delete guard: re-assert
      0-row per object before deleting, abort the prefix on any non-empty object). This SUPERSEDES the
      `gcs_hive_partition_malformed_paths_remediation` Pattern-1 todo.
- [ ] [DATA] P1. **COVERAGE GAP (surfaced by the 0-row-placeholder finding, 2026-06-02)**: tradfi **equities/ETF
      (NYSE/NASDAQ)** were NEVER genuinely ingested — only the 0-row Massive dry-run placeholders exist; the real `day=`
      hive corpus is **CME databento only**. This is a real gap (Data-Pipeline-Correctness HARD RULE — every cell in
      scope; data exists via databento/massive paid tiers). Backfill equities/ETF ohlcv/trades/tbbo via the
      databento/massive ingest path (NOT a canonicalisation blocker — the migrator + E5 ship on the CME-real corpus;
      track the equities/etf backfill as its own ingest item under `tradfi_massive_dual_source` / tradfi epic). Until
      backfilled, the manifest must show these cells as MISSING/`attempted_unattempted`, never empty_confirmed (CF-11).

### CF-11 completeness — fetch-failure must be `attempted_failed`, NOT `empty_confirmed` (operator directive 2026-06-02)

> Operator: "when there is an API issue somewhere in IS or MTDS, is it correctly doing `attempted_failed` where the
> attempt makes sense by instrument / UAC bounds — RATHER THAN `empty_confirmed` which would not be complete?" TradFi
> twist: tradfi has LEGITIMATE typed empties on non-trading days (`EXPECTED_WEEKEND` 35,050 / `EXPECTED_HOLIDAY` 2,427 /
> `EXPECTED_OUT_OF_COVERAGE_WINDOW` 8) — those stay `empty_confirmed`. The risk is a databento/massive API error on a
> TRADING day for an in-universe ticker within UAC coverage being mislabeled `SOURCE_RETURNED_ZERO` (only 5 such today —
> verify each) instead of `attempted_failed`. The expected-attempt set = TRADFI_TICKER_UNIVERSE / databento universe ×
> trading-calendar (weekday, non-holiday) × UAC SOURCE_PRIORITY data_type registration × coverage window.
>
> **The manifest must EXPLAIN every zero (3-way decision tree — the E5 rebuild contract):** (1) attempt errored on a
> trading-day in-universe cell → `attempted_failed`; (2) a UAC guard explains the zero → typed `empty_confirmed`
> (`EXPECTED_WEEKEND` / `EXPECTED_HOLIDAY` / `EXPECTED_OUT_OF_COVERAGE_WINDOW` / pre-listing "not started yet"); (3)
> only if a trading session was open + fetch succeeded + genuinely nothing → `SOURCE_RETURNED_ZERO`. A blanket/blank
> `SOURCE_RETURNED_ZERO` = "we don't know why" masquerading as complete.

- [x] ✅ [DATA] P0. **E5 rebuild classifier: within-bounds trading-day empty → `attempted_failed` — DONE (mtds@90aeb7dd,
      slot-6 2026-06-03).** rebuild_tradfi_manifest reclassifies via UAC `is_non_trading_day(venue,day)` (the SAME
      helper the orchestrator uses → batch=live): a `SOURCE_RETURNED_ZERO` on a TRADING day →
      `record_failed(WithinBoundsTradfiSourceZero)` (attempted_failed);
      weekend/holiday/out-of-coverage/calendar-exception preserved as typed empty. The 5 existing SOURCE_RETURNED_ZERO
      are audited by this path. Tests: trading-day-reclassified / weekend-preserved / holiday-preserved /
      calendar-exception-preserved. ORIGINAL: For every empty cell: if it is a trading day (NOT weekend/holiday) +
      ticker in universe + data_type guaranteed-when-listed (trades / tbbo / ohlcv on an active venue+ticker) + within
      coverage window → `attempted_failed` (`record_failed`), NOT `SOURCE_RETURNED_ZERO`/`empty_confirmed`. Audit the 5
      existing `SOURCE_RETURNED_ZERO` rows specifically — confirm genuine source-zero vs masked fetch failure. Preserve
      the legit weekend/holiday/out-of-coverage typed empties.
- [x] ✅ [DATA] P0. **E5 rebuild: re-emit existing `attempted_failed` rows (6,036) v9, status PRESERVED — DONE
      (mtds@90aeb7dd, slot-6 2026-06-03).** `reemit_honest_absence_rows` reads the existing tradfi `_index` (robust:
      `read_availability_index` → direct `_index/availability_index.parquet` fallback on gcsfs DNS flakiness) + re-emits
      every `attempted_failed`/`empty_confirmed` row not covered by the object-scan (dedup by row_key, `record_failed`
      error / `record_empty` reason preserved + validated vs EMPTY_CONFIRMED_REASONS), fixing the pure-object-scan
      false-complete. 11 tests; QG --no-fix exit 0. ORIGINAL: never silently relabel a failure to `empty_confirmed`;
      they stay flagged for backfill.
- [x] ✅ [CODE] P0. **Write-path CF-11 audit + fix (IS + MTDS tradfi databento/massive) — DONE
      (instruments-service@bd1456aa, slot-6 2026-06-03).** MTDS side was VERIFIED COMPLIANT (below); IS-side residual is
      now fixed — Databento fetch-failure threads state → attempted_failed (see the STATE-threading item). on a genuine
      API error (timeout/5xx/429/auth) for an in-universe ticker on a trading day within coverage bounds, the handler
      MUST `record_failed` (→ `attempted_failed`) via `classify_venue_error()`/`ADAPTER_FETCH_FAILED`, NOT
      `record_empty`. Grep the tradfi databento/massive fetch paths for `except … record_empty` / bare `return []`
      swallows; gate empty-vs-failed on trading-calendar + ticker-in-universe + UAC coverage. Cross-ref the sports CF-11
      model (`sports_manifest_canonicalisation_2026_06_01.md` § CF-11). **DIAGNOSIS (slot-3 2026-06-02): MTDS side
      VERIFIED COMPLIANT** — same finding as the cefi CF-11 todo (the MTDS orchestrator finalize is shared across AGs):
      tradfi databento/massive adapters classify+emit+re-raise (no swallow), and `orchestrator.py:3818`/`:3766` gate
      `record_failed` vs `record_empty(SOURCE_RETURNED_ZERO)` on a recorded fetch-failure (incl.
      `failed_per_dt_by_venue` for bundled-Databento partial-success). RESIDUAL = focused instruments-service write-path
      verify. See cefi plan § CF-11 for the full diagnosis.
- [x] ✅ [CODE] P1. **IS-side CF-11 verify — DONE (superseded by the STATE-threading fix below,
      instruments-service@bd1456aa).** The observability-only event-emission (handoff branch) is now subsumed: the
      parse-failure branch emits `ADAPTER_FETCH_FAILED` AND the real state-threading fix lands the `attempted_failed`
      row. (slot/Harsh 2026-06-02, read-only) — partial result + 1 concrete zero-signal gap.** Read the IS tradfi
      universe-discovery adapter `instruments-service/.../reference_data/adapters/tradfi/     databento.py`:
      `_fetch_symbols` handles a `BentoError` (L820) by `classify_venue_error("DATABENTO",…)` + emit
      `ADAPTER_FETCH_FAILED` + **`return []`**, and `get_instruments` (L537-547) does `results.extend(batch)` with NO
      raise/record — the classify+emit-event+return-[] shape (consistent with the shard-isolation "no raise in per-venue
      loops" rule). **CONCRETE GAP**: the SECOND site `databento.py:826` (`data.to_df()` parse failure) does
      `logger.warning` + `return []` with **NO `ADAPTER_FETCH_FAILED` event + NO classify** → on a transient parse
      failure those symbols vanish from the discovered universe with ZERO failure signal (silent universe truncation =
      A8-class false-complete coverage). Fix = mirror the L820 branch (classify + emit `ADAPTER_FETCH_FAILED`) on the
      parse-failure branch — **DONE (slot-5 2026-06-03, instruments-service handoff branch
      `handoff/tradfi-e5-cf11-slot6`@b4a43093 (un-QG'd; run IS QG before ship))**: the `data.to_df()` parse branch now
      classifies (`VALIDATION_ERROR`) + emits `ADAPTER_FETCH_FAILED` like the L820 branch. **OPEN QUESTION NOW RESOLVED
      → CONFIRMED (B) SILENT-SHRINK GAP (slot-5 2026-06-03 trace, verified file:line):** the emitted
      `ADAPTER_FETCH_FAILED` is **fire-and-forget — the manifest layer never reads it\*\*, so neither L820 NOR L826
      produces an `attempted_failed` row. Trace: `databento.py:820` SWALLOWS the `BentoError` (`return []`, no re-raise)
      → `base_adapter.py:240` caches the `[]` as a legit result → `urdi_reference_provider.py:_fetch_one` only
      classifies failures from RAISED exceptions (its `except Timeout/Connection/RuntimeError/ValueError` → `failed[]`),
      so an empty return is a CLEAN success → the venue lands in `orchestrator.py` `_non_error_venues` (NOT
      `failed_venues`) → on a trading-day zero the orchestrator does NOT `record_failed`; the cell has NO honest
      `attempted_failed` row (A8-class false-complete coverage). The event-emission fix above is OBSERVABILITY-ONLY — it
      does not close the data gap. Repo: instruments-service. parent_epic: mtds_mdps_master.
- [x] ✅ [CODE] P0. **IS Databento fetch-failure threads STATE — DONE (instruments-service@bd1456aa, slot-6
      2026-06-03).** databento.py `_fetch_symbols` BentoError + `data.to_df()` parse-failure branches now RE-RAISE
      `RuntimeError` (after classify+emit) → caught by `urdi_reference_provider._fetch_one`'s per-venue
      `except RuntimeError` (shard-isolation boundary) → venue in `failed[]` → excluded from `_non_error_venues` →
      orchestrator `record_failed` → honest `attempted_failed` row. Genuine empty still returns `[]` cleanly;
      `base_adapter` cache skips write on raise (no failed-fetch memoization). 4 tests (raise-on-fail /
      genuine-empty-clean / cache-not-memoized) + 40/40 file; IS QG --no-fix exit 0. Caveat: same swallow likely in
      cefi/defi/sports IS adapters → separate audit. Closes the CONFIRMED silent-shrink gap above).\*\* The real fix:
      the `databento.py` `BentoError` branch (L820) + parse-failure branch (L826) must SIGNAL the failure to URDI as
      state so it reaches `_non_error_venues`-vs-`failed_venues` accounting — either re-raise a
      `urdi_reference_provider._fetch_one`-classifiable exception (RuntimeError/ConnectionError/… per its `except`
      ladder) so the venue lands in `failed[]`, OR thread a per-venue failure flag through `get_instruments_cached` →
      URDI → orchestrator. Blast radius (own unit, NOT a same-commit hack): (1) must NOT cache `[]` from a failed fetch
      (`base_adapter.py:240`); (2) audit every other `get_instruments()` caller that relies on the graceful
      `[]`-on-failure contract; (3) ensure orchestrator records `attempted_failed` (not raise-and-abort) on a
      trading-day fetch-fail so it's a retryable honest-absence row, not a shard crash; (4) unit test: fetch-fail on a
      trading-day in-universe venue → `attempted_failed` row, genuine-empty → `empty_confirmed`. Cross-ref the same
      adapter-swallow pattern likely affects cefi/other IS adapters (verify). Repo: instruments-service. parent_epic:
      mtds_mdps_master.

- [x] ✅ [CODE] P1. **Cross-AG IS adapter fetch-failure swallow — AUDITED + FIXED (instruments-service@e2e008f0, slot-6
      2026-06-03).** Audited all 3 AGs vs `_fetch_one` consumption: **cefi** hyperliquid/aster/tardis(×2) + **sports**
      betfair + **defi** lighter(×2) had the return-[]-on-fetch-error swallow → now RE-RAISE (→ failed[] →
      attempted*failed). **defi family otherwise CLEAN** (raises ConnectionError already); sports
      footystats/understat/etc. correctly excluded (not URDI-consumed); tardis preserves per-exchange partial-success
      isolation (raises only if all-fail-empty). +12 regression tests + 7 old-contract tests updated to assert raise; IS
      QG exit 0. ORIGINAL: (slot-6 discovery 2026-06-03, surfaced by the tradfi Databento state-threading fix
      instruments-service@bd1456aa). The `\_fetch*_`→     classify+emit`ADAPTER_FETCH_FAILED`+`return
      []`(no re-raise) pattern that silently shrank the tradfi universe     almost certainly exists in other IS reference-data adapters (cefi tardis/exchange, defi, sports) → same A8     false-complete on a fetch error. Audit each`reference_data/adapters/_/`fetch path; apply the same fix (re-raise     a`\_fetch_one`-classifiable exception so the venue lands in `failed[]`→`attempted_failed`); don't cache `[]`
      from a failed fetch. Repo: instruments-service. parent_epic: mtds_mdps_master.

- [x] ✅ [CODE] P2. **SSOT-cleanliness — SHIPPED slot-6 2026-06-03 (UAC@0abbdf86 + mtds@ce0a7d7a).** fold
      `pipeline_mode` into UAC `build_tradfi_partition_path` (remove the MTDS mirror divergence)** (slot-6
      path-correctness audit 2026-06-03 — latent footgun, NOT a live bug). The UAC base builder
      `unified-api-contracts/.../canonical/partition_paths.py::build_tradfi_partition_path` produces the path WITHOUT
      `pipeline_mode=`; `candidate_parquet_paths(pipeline_mode=...)` layers it, the live writer
      (`tradfi_shared.build_tradfi_partition_path`) inserts it inline ("mirrors UAC byte-for-byte but accepts
      pipeline_mode"), and the orchestrator inserts it via `.replace`. All ACTUAL write/migrate/read/rebuild paths are
      consistent + pipeline_mode-aware TODAY (audit-verified GREEN), but the UAC base builder + the MTDS mirror have
      drifted apart — a future caller using the bare UAC builder would write the pre-migration path. Fix: add optional
      `pipeline_mode` to UAC `build_tradfi_partition_path` (insert LEFT of asset_group=, matching
      `candidate_parquet_paths`) so the MTDS mirror can delegate instead of diverging; update orchestrator to pass it
      rather than `.replace`. Cross-repo (UAC + mtds), so a coordinated pass. Repos: unified-api-contracts +
      market-tick-data-service. parent_epic: mtds_mdps_master. **DONE (slot-6 2026-06-03):** UAC
      `build_tradfi_partition_path` now accepts optional `pipeline_mode=` (inserted LEFT of `asset_group=`, matching
      `candidate_parquet_paths`) @0abbdf86. **Full delegation deferred** — the UAC typed builder requires an
      `InstrumentType` enum that does NOT model TradFi series-class tokens (`rates`/`etf_flows`), so the MTDS mirror
      keeps its inline build; instead a **byte-identity guard test\*\*
      (`tests/market_interface/unit/test_tradfi_shared_path_byte_identity.py`, mtds@ce0a7d7a) asserts mirror == UAC
      builder for overlapping types → any drift is now a test failure (the footgun the item targeted is closed).
      Residual nice-to-have: extend the UAC `InstrumentType` enum to cover TradFi series-class tokens, then delete the
      mirror + delegate — tracked here, P3.

## Readiness gate — 4 ready-to-run criteria (slot-5 audit 2026-06-04, handed to slot-6/vm-tradfi to MARK)

> Operator 2026-06-04 named 4 criteria that must be **completed + marked done in this plan** before the TradFi full run.
> Slot-5 ran a read-only cross-repo audit (2 fan-out agents + self-verification — one agent's "NOT READY" verdict was
> grep-then-conclude noise: it reported `rebuild_tradfi_manifest.py`/features-preflight/batch-live-parity-test as "not
> found" when they exist, just in different repos). **The infrastructure for all 4 is in place + verified.** Slot-6 (the
> owner) should confirm + tick these — slot-5 is NOT marking them (cross-slot ownership). The actual full migration
> run + E8 legacy-delete stay operator-gated regardless.

- [ ] [DATA] P0. **Criterion 1+2 — migrator + rebuild DRY-RUNS done → mark them.** Both already executed (slot-6
      2026-06-03, see E4 item above): `migrate_tradfi_to_v9_canonical.py --dry-run` = 5,305,520 objects / 0 err /
      100,698 placeholders skipped; `rebuild_tradfi_manifest.py --dry-run` = 704,641 shards / 6 venues. ACTION: split
      the E4 checkbox so the dry-run half can tick `- [x]` (full-VM run stays gated).
- [ ] [DATA] P0. **Criterion 4 — read/write paths MATCH post-migration everywhere → CONFIRMED, mark it.** slot-5 audit
      verified all surfaces use the identical `derive_pipeline_mode_for_row` →
      `pipeline_mode=batch_*/asset_group=tradfi/` (path==manifest invariant): UAC `build_tradfi_partition_path`, live
      MTDS writer (`orchestrator.py:991-1005`), MDPS candle writer (`get_processed_path` pipeline_mode= — the cross-AG
      fix mdps@5e7f075 is on LDR), migrator `_canon_rel`, and `rebuild_tradfi_manifest`; readers dual-probe via
      `candidate_parquet_paths`; the MTDS-mirror vs UAC-builder divergence is closed by the byte-identity test
      (mtds@ce0a7d7a). ACTION: tick the path-correctness rows.
- [ ] [CODE] P0. **Criterion 3 — pre-flight + empty/partial (zero-vol/NaN/last-price candles) batch+live → CONFIRMED
      wired, mark it.** slot-5 audit verified: MDPS finalize-session represents an empty bin as **NaN-volume + prior-day
      last-price carry-forward**, deterministic + **batch==live** (`tests/unit/test_batch_live_mode_parity.py` +
      `test_finalize_session_grid_seed.py`); off-session via `market_state`; CF-11 honest-absence in
      `rebuild_tradfi_manifest.py:241` (`reemit_honest_absence_rows`, trading-day empties → `attempted_failed`);
      features-service delta_one `dependency_checker` reads the v9 `_index` (`read_availability_index` +
      `UPSTREAM_DEPS` + `validate_can_run(asset_group=…)` incl. TRADFI); strategy-service `manifest_allocation_guard`.
      ACTION: tick the preflight/honest-absence rows.
- [ ] [TEST] P1. **Criterion 3 — the ONE genuine residual: a single END-TO-END batch+live confirmation** that a
      zero-volume / NaN / off-session TradFi candle flows IS→MTDS→MDPS→features→strategy→execution correctly in BOTH
      modes (the per-layer pieces are verified individually; what's not pinned is one e2e pass proving they compose — no
      silent NaN-propagation / phantom-candle / divide-by-zero downstream). Add an e2e/integration test (or a documented
      manual run) asserting the honest-absence row is consumed as absence (not data) end-to-end. Repos: e2e-testing (+
      features/strategy if a consumer gap surfaces). parent_epic: mtds_mdps_master.

## Pre-run 7-criteria readiness — VERIFIED slot-6 2026-06-04 (operator readiness bar)

> Audit (3-agent fan-out, every flag operator-verified — both agent "P0 blockers" were false positives). **6/7 met; ②
> real-GCS rebuild running; ⑦ the lone open item.**

- [x] ✅ **① Migrator dry-run** — real-GCS `migrate_tradfi_to_v9_canonical.py --dry-run`: **5,305,520 objects** planned,
      0 moved, 100,698 L-hyphen placeholders skipped, 0 err (plan E4).
- [ ] **② Manifest-rebuild dry-run** — REAL-GCS dry running (`rebuild_tradfi_manifest.py`, bounded 2026 range to
      validate mechanism on real data; flags pre-migration `category=` blobs as unparseable = expected). Full-corpus
      (5.3M / ~2,700 dates, ~11h single-thread) is a **VM job** (plan's "VM-only whole-corpus walks" gate). Mock-704k
      done earlier.
- [x] ✅ **③ 4-state preflight every service IS→execution** — MTDS/MDPS/features 4-state-aware (`dependency_checker`,
      `manifest_window_guard`+GAP-4 drift-WARN); strategy `manifest_allocation_guard`. execution = N/A (consumes
      strategy signals, not tradfi candles).
- [x] ✅ **④ Empty/partial honest (zero-vol/NaN/last-price + data-type-dependent equiv) batch+live** — MDPS
      `ohlcv_passthrough` (empty→zero-row→`record_empty` typed; open-no-trade→`o=h=l=c=prev_close, vol=0`; NO NaN OHLC;
      1440-NaN bug deleted 2026-05-26) + `tbbo_adapter` (empty→`_make_empty_candle_output`; OHLCV=NaN by-design for
      quote data; spread/mid via honest LOCF) + `trades_adapter`; `supports_prior_day_seed` (batch=live single path).
- [x] ✅ **⑤ Read/write paths match post-migration** — UAC SSOT `build_tradfi_partition_path(pipeline_mode)` +
      `candidate_parquet_paths`; features `gcs_reader` pipeline_mode-aware; mtds byte-identity guard; canonical migrator
      (all shipped this session).
- [x] ✅ **⑥ IS+UAC guardrail vs instruments that cannot exist** — `engine/tradfi_catalog_reader.py` reads IS
      `instruments-store-tradfi` (CatalogueBuilder) per-date; `_INACTIVE_STATUSES={expired,delisted}` +
      availability-window EXCLUDED; feeds orchestrator Tier-3 override (universe=IS, not a seed); missing catalog →
      UAC-seed fallback.
- [ ] [CODE] P2. **⑦ deployment-api/UI pending-backfill (expected_unattempted) surfacing** — denominator ALREADY = UAC
      could-exist universe (FLAG-1/FLAG-4, all 6 tradfi venues incl CBOE/FX) ✅; the `ln`-pending modeling exists
      (`unified_trading_library/manifest_freshness.py`: `ln`+non-EXPECTED = pending-fetch gap). **Open**: surface
      `expected_unattempted` ("instruments exist, backfill not yet run") as a DISTINCT pending-backfill bucket in the
      deployment-api `ln`-metric coverage response
      (`deployment-api/deployment_api/services/data_status_{service,drilldown,hierarchical}.py`) + the deployment-UI
      data-status view (PLAYWRIGHT-GATED — needs `pw:L2 ✓` + regression spec). Repos: **deployment-api +
      unified-trading-system-ui**. Needs a focused UI-capable session.

## Success criteria

- Canonical `tradfi-prd` `_index` = **v9** (data-state verified) + `pipeline_mode=` partition + `source` populated +
  `available_at` non-null; venue/data_type canonical only.
- 0 legacy-only tradfi cells; `tradfi_massive` Task -031 closed (re-consolidation done here).
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy `market-data-tick-tradfi-…` deletable; tradfi writer relaunch
  unblocked (writes canonical-only).

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — tradfi canonical form (v9 + pipeline_mode partition).
