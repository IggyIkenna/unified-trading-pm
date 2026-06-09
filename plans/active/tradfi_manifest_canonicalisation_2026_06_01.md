---
title: "TradFi manifest + data canonicalisation (v9 + pipeline_mode partition single-walk) — L3 owner for tradfi"
created: 2026-06-01
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-tradfi
umbrella: true  # catalogue/coordinator plan — large in context, <100 todos; exempt from 1000L cap (2026-06-09)
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

> **🟢 UNBLOCKED (2026-06-07) — slot-7 Era-B + bundle-grain rollup LANDED** (uac@ae70338d Era-B instrument_types +
> 687d1443/74df991d per-underlying rollup, flip 6a1e0154c; slots 3/6 notified). Your migrators + instruments-store v9
> dry-run are already GREEN (gate-c tool-ready, 20,388→v9 100%) — last step: RE-RUN your enumerate validation against
> the landed rollup (the ~563K false per-contract OPTION/COMBO candidates should be GONE) + do the Era-B
> `data_type=options_chain`→(instrument_type + `data_type=trades`) v8→v9 manifest relabel in your walk → then flip your
> apply-ready verdict.

> **⛔ COORDINATED + APPLY-GATED (2026-06-07)** — cross-AG sequencing is owned by
> `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`. This AG's `--apply` (manifest +
> data/schema) is GATED on the coordinator's **G0** (pipeline*mode source-aware
> `{mode}*{source}[_{transport}]`model + doc coherence — this plan PREDATES the 2026-06-05 standard, reconcile per M-COORD-1/2; tradfi is also the home of the massive/polygon-vs-databento cost-swap + databento/massive replay-capability confirmed UAC@8079b884) + **G1** (IS catalogue could-exist SSOT: IS backfill complete + accurate UAC) + **G2** (scripts + 7+2-point audit + dry-run) + **G3** (deployment UNION view) all GREEN. The migrator/manifest-rebuild/enumerator MUST stamp source-aware pipeline_mode (NOT coarse`batch`/blank)
> BEFORE apply. Readiness audit adds ⑧ (IS-catalogue) + ⑨ (pipeline_mode).

> **🔴 P0 GATE (operator 2026-06-05) — supersedes the "7/7 criteria ready, only operator-gated" readiness call below for
> the `--apply`.** The tradfi v9 `--apply` is BLOCKED until
> `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` Phase 0 (code) is GREEN. Single-walk
> discipline: this corpus walk must carry the new manifest columns — `live_<source>`/`replay_<source>` form, populated
> `source`, `cadence`, `transport`. Running `--apply` before that code lands bakes in the old model + forces a banned
> second walk. The 7-criteria readiness (migrator/rebuild/preflight/honest-absence/paths/guards/UI) remains valid for
> the CURRENT model — but the `--apply` now waits for the standardisation Phase 0 so the one walk is future-proof.
> **Dry-runs are NOT gated; only the irreversible `--apply`.**

> **🔴 FOUNDATION GATE (2026-06-04) — the proper instrument catalogue blocks the tradfi MTDS `--apply`.** Before the
> tradfi MarketTick-data migration `--apply` runs,
> `plans/active/proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md` (P0, vm-cross-cutting) must be GREEN — the
> could-exist-universe SSOT (`expected_unattempted` / coverage denominators / instrument-existence guards), built by
> rolling up the per-date `instrument_availability/by_date/` definitions (the v2 enumerator's `catalog.parquet` had no
> producer). **Dry-runs (migrator + manifest-rebuild) are NOT gated** — only the irreversible `--apply`. Depends on
> `instruments_manifest_canonicalisation`. Cross-ref: defi master coordinator §MASTER.

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
> **✅ RESOLVED — handoff fully landed + dep-tier blocker MOOT (slot-6 verified 2026-06-04).** The dep-tier gate is
> cleared (`record_zero_rows` is now on `origin/staging`) AND the handoff branches were **superseded by later commits
> already on LDR** — verified by `branch -r --contains` / content-grep: mtds E5+CF-11 landed via mtds@90aeb7dd /
> @e6250b99 / @ce0a7d7a (`rebuild_tradfi_manifest.py` + `reemit_honest_absence_rows` + CF-11 reclassify +
> `test_rebuild_tradfi_manifest_cf11.py` all on LDR); the IS databento state-threading fix landed (the
> `raise RuntimeError` after classify+emit at `databento.py:825/849` is on LDR — bd1456aa's content, re-SHA'd through
> quickmerge) + the cross-AG sibling IS@e2e008f0; UAC@0abbdf86 on LDR. So the stale
> `origin/handoff/tradfi-e5-cf11-slot6` branches in mtds + IS carry NOTHING not on LDR — they are dead and may be
> deleted. The E5 / CF-11 / IS-databento todos below are already ✅. No merge/cherry-pick action remains.

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
      `UNKNOWN`/blank rows in the walk (do NOT bulk-rename ambiguous strings). **✅ DIAGNOSIS DONE (slot-6 2026-06-04,
      live `-prd` `_index` read, 144,062 rows — pre-migration de-risk so the E5/E6 walk is ready):** the drift is
      **6,602 rows / 4.6%** — **DRIFT-VENUE 4,130** (3,540 blank + 590 `UNKNOWN`; spread across tbbo/trades/ohlcv real
      data_types; **blank `instrument_type` + `asset_group=None`**; 3,955 captured + 175 attempted_failed; dates
      2020→2026) + **DRIFT-DATA_TYPE 2,472** (all blank; real venues CBOE/ICE/CME/NASDAQ/NYSE/FX; blank instrument_type;
      all captured). These are NOT ambiguous strings to rename — they are **under-populated older-schema manifest rows**
      (the writer left venue/data_type/instrument_type/asset_group blank). **Resolution = PATH RE-DERIVATION, not a
      string-rename table**: E5 `rebuild_tradfi_manifest.py` scans the canonical object paths
      (`venue=/data_type=/asset_group=/instrument_type=` segments) and re-stamps these fields → captured drift rows are
      FIXED in-walk by the object scan (consistent with "do NOT bulk-rename"). **⚠️ RISK to verify in the walk (why this
      stays open):** (1) any drift row whose OBJECT is NOT at a canonical `venue=`-bearing path (e.g. an L-hyphen 0-row
      placeholder, which the migrator SKIPS) will NOT be re-derived → its captured status must be re-evaluated, not
      silently dropped (a blank-venue "captured" backed only by a placeholder is a false-capture → should become
      honest-absence, not coverage). (2) the 175 blank-venue `attempted_failed` rows pass through
      `reemit_honest_absence_rows`, whose `row_key` includes venue — a blank venue can mis-dedup; confirm they re-emit
      under their PATH-derived venue. **Post-walk verify hook (add to E7):** re-run this audit on the rebuilt `_index` →
      assert **0 blank/`UNKNOWN` venue + 0 blank data_type + 0 `asset_group=None`**, and assert total captured-cell
      count does not silently shrink by ~6,602 (coverage-regression guard). Audit script:
      `/tmp/tradfi_index_drift_audit.py` (read-only, reproducible).

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

- [x] ✅ [DATA] P0. **Criterion 1+2 — migrator + rebuild DRY-RUNS done — MARKED (slot-6 2026-06-04 re-audit).** Both
      executed (see E4 item above): `migrate_tradfi_to_v9_canonical.py --dry-run` = 5,305,520 objects / 0 err / 100,698
      placeholders skipped; `rebuild_tradfi_manifest.py --dry-run` = 704,641 shards / 6 venues. **Independently
      re-verified vs LDR code** (fan-out Explore agent + file:line): migrator is dry-by-default + `--apply`, 3-layout
      handling, 0-row placeholder guard, ThreadPoolExecutor + `gcs_copy_object` + `--workers/--start-date/--end-date`,
      per-object try/except; rebuild stamps pipeline_mode+source+v9, `reemit_honest_absence_rows`, CF-11 trading-day
      reclassify + `test_rebuild_tradfi_manifest_cf11.py`. Full-VM `--apply` stays operator-gated.
- [x] ✅ [DATA] P0. **Criterion 4 — read/write paths MATCH post-migration everywhere — MARKED (slot-6 2026-06-04
      re-audit).** Independently re-verified vs LDR: identical `derive_pipeline_mode_for_row` →
      `pipeline_mode=batch_*/asset_group=tradfi/` across UAC `build_tradfi_partition_path(pipeline_mode)` (LEFT of
      asset_group=), live MTDS writer (`orchestrator.py:1001-1005`), MDPS `get_processed_path`, migrator + rebuild;
      readers dual-probe `candidate_parquet_paths`; mirror==UAC byte-identity test (mtds@ce0a7d7a) present + passing.
- [x] ✅ [CODE] P0. **Criterion 3 — pre-flight + empty/partial (zero-vol/NaN/last-price candles) batch+live — MARKED
      (slot-6 2026-06-04 re-audit + direct read).** Independently re-verified: MDPS `ohlcv_passthrough` empty→zero-row
      `_make_empty_candle_output` (Path A) + open-no-trade→`o=h=l=c=prev_close, vol=0` (NO NaN OHLC; legacy 1440-NaN
      DELETED) + CLOSED-bars-dropped; `tbbo_adapter` NaN-by-design for quote data + honest LOCF spread/mid;
      `supports_prior_day_seed` single path; **batch==live parity test asserts identical columns + available_at +
      record_captured** (`test_batch_live_mode_parity.py`). CF-11 `reemit_honest_absence_rows`; features delta_one
      `dependency_checker` counts only `captured` (incl TRADFI); strategy `manifest_allocation_guard`. execution N/A
      (signals, not candles).
- [x] ✅ [TEST] P1. **Criterion 3 — the ONE genuine residual e2e batch+live confirmation — DONE (slot-6 2026-06-04,
      strategy-service@0575be56, on tab→LDR).** Added `tests/unit/test_tradfi_honest_absence_batch_live_parity.py` (6
      tests; ruff + basedpyright clean + 6/6 pass): asserts the honest-absence row is consumed as ABSENCE (not data) at
      the strategy allocation seam against the REAL v9 `_index` row shape
      (date/venue/data_type/asset_group/capture_status/schema_version/source/ pipeline_mode/available_at) across the
      full 4-state matrix in BOTH modes — captured→proceed; off-session EXPECTED_WEEKEND empty_confirmed→skip-no-alert;
      trading-day attempted_failed→skip + live-only alert; **batch≡live skip-parity proven for every state** (sole
      mode-diff = live alert on attempted_failed). The full 7-layer httpx run is the documented manual run; this is the
      durable regression guard. **Side-finding pinned + tracked** (see new P2 below): the 4th honest-absence state
      `expected_unattempted` (pending-backfill) currently fail-opens→proceeds at this seam. Repo: strategy-service.
      parent_epic: mtds_mdps_master. **STAGING-PROMOTION STATUS (slot-6 2026-06-04, not blocking this DONE):** the
      commit is on tab→LDR (integration axis); the `quickmerge` LDR→staging promotion is BLOCKED-DEPENDENCY by the
      STAGE-1.7 dep-tier gate (unified-trading-library + unified-api-contracts are MAIN_GREEN, not yet on staging —
      fleet CICD-drain, not a tradfi blocker) → rides the staging-promotion automation once deps drain. Note:
      strategy-service local full-QG also trips a **pre-existing** `uv lock --check` resolution conflict
      (`starlette>=1.0.1` wanted vs UTL caps `<1.0.0`, "for a non-current environment") — environment/uv-version
      artifact (base-service.sh hard-fails on non-pinned uv, soft-warns on pinned uv 0.10.8; the test's own
      ruff/basedpyright/pytest are clean) — NOT introduced by this change. Cross-repo dep-alignment, owner =
      vm-cross-cutting; flagged for the next strategy-service/UTL dep pass.
- [x] ✅ [CODE] P2. **strategy allocation guard `expected_unattempted` seam — RESOLVED (operator decision (b), slot-6
      2026-06-08, strategy-service@4b449711).** Operator chose option (b): `expected_unattempted` (pending-backfill /
      out-of-scope) now classifies as `expected_gap` → SKIP both modes, NO alert (the prior fail-open
      `"unknown"`→PROCEED retired); AND the `iloc[0]` AG×date first-row peek is replaced by a **per-cell precedence
      aggregation** (`attempted_failed > captured > expected_gap > unknown`) — so a lone `expected_unattempted` cell can
      no longer skip a whole AG-date when real captured data exists, while a genuine `attempted_failed` stays decisive +
      live-alertable. Both guard test suites re-pinned (`test_manifest_allocation_guard.py` +
      `test_tradfi_honest_absence_batch_live_parity.py`: `test_expected_unattempted_*` + mixed-cell aggregation tests);
      strategy-service `quality-gates.sh --no-fix` exit 0 (240s, 4672 passed). Repo: strategy-service. parent_epic:
      mtds_mdps_master. **STAGING-PROMOTION:** commit on tab→LDR; LDR→staging quickmerge is BLOCKED-DEPENDENCY by the
      STAGE-1.7 dep-tier gate (unified-trading-library FEATURE_GREEN, not yet on staging — fleet CICD-drain, not a
      tradfi blocker) → rides the staging-promotion automation once deps drain. ORIGINAL FINDING (slot-6 2026-06-04,
      while building the criterion-3 e2e): `_classify_status` mapped only captured/empty_confirmed/attempted_failed;
      `expected_unattempted` → `"unknown"` → fail-open → allocator PROCEEDS. features-service DOES emit
      `expected_unattempted` rows into the features manifest the guard reads
      (`features_service/delta_one/cli/handlers/_expected_unattempted.py` → `record_expected_unattempted`), so the state
      genuinely reaches this seam.

## 🤝 HANDOFF (slot-6 → next agent, 2026-06-04) — TradFi readiness: ⑦ UI DONE (UI@846c7c67, PR #20→staging); remaining = operator-gated full migration run

> **UPDATE (slot-6 2026-06-04, end of ⑦ session):** ⑦ (the lone open UI item) is **DONE + shipped** —
> unified-trading-system-ui@846c7c67, PR #20 auto-merging to staging; full UI quality-gates green (tsc/eslint/chromium
> playwright invariants/272 test files+coverage/build), regression = 2 Vitest widgets specs. All **7 readiness criteria
> are now MET**. What remains is NOT code — it is the **operator-gated full migration run** (② full-corpus `--apply` on
> a VM gated on the E3 pre-migration drain + snapshot, then the L6 legacy-bucket delete on CF-GREEN) plus the
> pre-existing tracked data items (v8→v9 walk, available_at E4 parquet verify, the slot-5 E5/CF-11 dep-tier merge once
> UTL+UAC drain to staging). The original handoff narrative below is retained for cold-start context.

> **Asset group: TRADFI** (slot 6; THIS plan is the tradfi master orchestrator — one AG per slot; sibling AG masters
> linked at the top of this plan). Venues: CME / CBOE / NASDAQ / NYSE / ICE / FX. data_types: ohlcv_15m, ohlcv_24h,
> ohlcv_1m, tbbo, trades, futures_chain, options_chain. Canonical path:
> `raw_tick_data/by_date/day={D}/pipeline_mode={mode}/asset_group=tradfi/venue={V}/instrument_type={IT}/data_type={DT}/[underlying={U}/]{file}`.

### Where we are vs the operator's 7-criteria "ready for full migration" bar

**6 of 7 criteria are MET + verified on real GCS/code (see the readiness checklist immediately below for evidence + the
shas).** Only **⑦ has an open piece, and it is UI-only** — the deployment-api side of ⑦ is verified-correct (no change).

| #                                                            | Status                            | Note                                                                                                                                                                                                                        |
| ------------------------------------------------------------ | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ① Migrator dry-run                                           | ✅ DONE                           | real-GCS `migrate_tradfi_to_v9_canonical.py --dry-run` = 5,305,520 objects, 0 moved, 0 err                                                                                                                                  |
| ② Rebuild dry-run                                            | ✅ VALIDATED (real-GCS bounded)   | `rebuild_tradfi_manifest.py` 2026-range: 114,771 shards, 37,477 reemit_empty + 6,041 reemit_failed, CF-11 reclassify. **Full-corpus = VM job** (see "remaining for FULL migration")                                         |
| ③ 4-state preflight every svc IS→exec                        | ✅                                | MTDS/MDPS/features 4-state-aware (`dependency_checker`, `manifest_window_guard`+GAP-4); strategy `manifest_allocation_guard`; execution N/A (signals, not candles)                                                          |
| ④ Empty/partial honest (zero-vol/NaN/last-price) batch+live  | ✅                                | MDPS `ohlcv_passthrough`/`tbbo_adapter`/`trades_adapter` (honest empty→record_empty typed; open-no-trade→last-price-carry o=h=l=c=prev_close vol=0; NaN-OHLC only where by-design for quote data; batch=live)               |
| ⑤ Read/write paths post-migration                            | ✅                                | UAC `build_tradfi_partition_path(pipeline_mode)` + features `gcs_reader` pm-aware + mtds byte-identity guard + canonical migrator                                                                                           |
| ⑥ IS/UAC guardrail vs instruments that can't exist           | ✅                                | `market-tick-data-service/.../engine/tradfi_catalog_reader.py` reads IS `instruments-store-tradfi`, EXCLUDES `{expired,delisted}` + out-of-availability-window per date, feeds orchestrator (universe=IS, not a seed)       |
| ⑦ deployment-api/UI could-exist num/denom + pending-backfill | ✅ **DONE** (UI@846c7c67, PR #20) | turbo venue card now renders a distinct "pending backfill" (`expected_unattempted_pending_fetch`) badge; API unchanged. pw:L2 literal `tests/smoke/` ✅ (UI@61488c8b) + Vitest regression; canvas CI native-build unblocked |

### ⑦ — THE ONE THING TO FIX (deployment-UI; API needs NO change)

- **deployment-api is CORRECT — do NOT change it.** `deployment-api/deployment_api/services/data_status_hierarchical.py`
  `DrilldownNode` already: `total = captured + empty_confirmed + attempted_failed + expected_unattempted` (the
  could-exist denominator, see the "B3" comment ~line 107), `completion_pct = captured/total`, and **returns
  `expected_unattempted` per node** (`to_dict`, ~line 125). The tradfi venue denominator = the UAC could-exist universe
  (FLAG-1/FLAG-4, all 6 venues incl CBOE+FX). So numerator/denominator already = universe-of-what-could-exist with the
  un-run backfill (`expected_unattempted` = "instruments exist, data-capture not yet attempted") IN the denominator.
- **deployment-UI is the gap.**
  `unified-trading-system-ui/components/ops/deployment/data-status/data-status-section-turbo.tsx` (the main data-status
  view, ~779 lines) renders `completion_pct` + `dates_found/dates_expected/dates_missing` (so the gap _is_ visible + the
  denominator IS could-exist), but it does **NOT label the `expected_unattempted` / "pending backfill" bucket
  distinctly** from failed/missing (grep: **0 UI hits for `expected_unattempted`**). The fix: surface a distinct
  **"pending backfill (instruments exist, never attempted)"** bucket/badge from the API's `expected_unattempted` field
  in the data-status node display (turbo + the leaf detail).
- **HARD RULE — this is PLAYWRIGHT-GATED**: cannot tick without `[UI]` tag + `pw:L2 ✓`
  (`npx playwright test --project=chromium tests/smoke/` exit 0) + a NEW/updated regression spec under
  `tests/e2e|playbooks|widgets|smoke/` that fails if the pending-backfill bucket is removed. Evidence format:
  `— unified-trading-system-ui@<sha> | pw:L2 ✓ | regression: tests/<path>.spec.ts`. Playwright MCP is connected this
  environment.
- **Scope:** ~1 component (+ its TS type if `expected_unattempted` isn't yet on the turbo node type) + 1 regression
  spec. Cross-AG bonus: the same label helps every AG's data-status view (the API field is generic).

### What remains for the FULL migration to actually RUN (beyond the 7 dry-gate criteria)

The 7 criteria are the **pre-run readiness gate** (code + dry-runs). To execute the real migration:

1. **⑦ UI** above (so operators see honest pending-backfill coverage).
2. **② full-corpus on a VM** — `migrate_tradfi_to_v9_canonical.py --apply` + `rebuild_tradfi_manifest.py` over the WHOLE
   `tradfi-prd` corpus (5.3M objects / ~2,700 dates ≈ 11h single-thread) is a **VM job** ("VM-only whole-corpus walks"
   gate, top of this plan). Gated on **E3 pre-migration drain** (stop tradfi writers + consolidate + snapshot
   `_index/snapshots/pre_migration_<date>.parquet`) — the `--apply` is IRREVERSIBLE-adjacent; the legacy delete (L6) is
   gated on CF-GREEN-on-real-data. Sequencing SSOT: `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`
   L3/L6.
3. The pre-existing open data items already in this plan (e.g. the v8→v9 data-state walk, `available_at`, the slot-5
   handoff E5/CF-11 dep-tier blocker at the top) — read this plan top-to-bottom; they are tracked.

### Gotchas for the next agent (learned this session)

- **Run GCS scans SERIALLY at low workers** (≤16, or 8 for the instruments surface). Multiple concurrent `workers=32`
  GCS scanners saturate the local connection pool → `DNS timeout` / `No route to host` (errno 65). Migrator + rebuild
  each scan the corpus — one at a time.
- **Verify Explore-agent findings before acting** — this session's audit agents produced TWO false "P0 blockers" (an
  MTDS-write-path flag that cited the _old superseded_ migrator, and a "no IS guardrail" that missed
  `tradfi_catalog_reader`). Grep-then-READ; the catalog reader + v9 migrator are canonical.
- The bounded rebuild flags pre-migration `category=` blobs as "unparseable" — that's EXPECTED (corpus is pre-migration;
  the real `--apply` run canonicalizes them).
- You have ADC GCS on `central-element-323112` — the "VM-pending / no GCS access locally" caveats in older plan items
  are runnable as DRY scoping from a workstation (that's how ①/② real-GCS counts were captured).

## Pre-run 7-criteria readiness — VERIFIED slot-6 2026-06-04 (operator readiness bar)

> Audit (3-agent fan-out, every flag operator-verified — both agent "P0 blockers" were false positives). **6/7 met; ②
> real-GCS rebuild running; ⑦ the lone open item.**

- [x] ✅ **① Migrator dry-run** — real-GCS `migrate_tradfi_to_v9_canonical.py --dry-run`: **5,305,520 objects** planned,
      0 moved, 100,698 L-hyphen placeholders skipped, 0 err (plan E4).
- [x] ✅ **② Manifest-rebuild dry-run** — REAL-GCS dry VALIDATED (slot-6 2026-06-04, bounded 2026-01-01..06-02, 522s):
      `rebuild_tradfi_manifest.py` → total_shards=114,771, 6 venues, **reemit_empty=37,477 + reemit_failed=6,041
      honest-absence rows re-emitted**, CF-11 reclassified 5 within-bounds SOURCE_RETURNED_ZERO→attempted_failed, 2,246
      pre-migration `category=` blobs flagged unparseable (expected — canonicalized on the real run). Mechanism
      confirmed on real data. **Full-corpus (5.3M / ~2,700 dates ≈11h single-thread) = VM job** (plan's "VM-only
      whole-corpus walks" gate). Mock-704k done earlier.
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
- [x] ✅ [CODE][UI] P2. **⑦ pending-backfill (expected_unattempted) surfacing — DONE (slot-6 2026-06-04)** —
      unified-trading-system-ui@846c7c67 (PR #20 → staging, auto-merge). **API SIDE VERIFIED CORRECT, NO CHANGE**:
      `data_status_hierarchical.py`
      `DrilldownNode.total = captured+empty_confirmed+attempted_failed+expected_unattempted` (could-exist denominator,
      comment "B3"), `completion_pct = captured/total`, `expected_unattempted` returned per node (`to_dict` line 125).
      **VERIFY-CORRECTION (the handoff's premise was partly off — verified before acting, per the "verify Explore
      findings" gotcha)**: the deployment-UI data-status view is the **turbo** view (`/api/data-status/turbo`), NOT the
      hierarchical drilldown — and the turbo response **already carries `capture_status_counts` per venue**
      (`data_status_service.py::_build_single_venue_entry`), where `expected_unattempted_pending_fetch` = "instruments
      exist, capture never attempted" = pending-backfill (vs `expected_unattempted_known_empty` = EXPECTED\_\*
      weekend/holiday). So it was genuinely UI-only (no API change) — the `TurboVenueData` TS type just omitted the
      field (→ the "0 UI hits"). **FIX shipped**: added `TurboCaptureStatusCounts` + `capture_status_counts` to
      `TurboVenueData` (`hooks/deployment/_api-stub.ts`); new presentational `capture-status-buckets.tsx` rendering a
      **distinct amber "pending backfill" badge** (`data-testid="pending-backfill-bucket"`) separate from failed/empty;
      wired into each venue card in `data-status-section-turbo.tsx`. **EVIDENCE — unified-trading-system-ui@846c7c67 |
      pw:L2 ✓ (chromium) | regression: tests/widgets/deployment/data-status-pending-backfill.test.tsx +
      data-status-turbo-wiring.test.tsx**. Gate: full UI `quality-gates.sh` PASSED (tsc 0-err · eslint clean ·
      **chromium playwright `environment-mode-invariants.spec.ts` ✅** · 272 test files / coverage 49.53%≥40% · build
      ✅). Regression guard = 2 Vitest widgets specs (6 tests; the wiring spec renders the REAL `DataStatusSectionTurbo`
      and asserts the badge from turbo `capture_status_counts` — fails if the `<CaptureStatusBuckets/>` wiring is
      reverted). **pw:L2 caveat — NOW RESOLVED (slot-6 2026-06-04, unified-trading-system-ui@61488c8b):** the literal
      `npx playwright test --project=chromium tests/smoke/` was previously unsatisfiable (`tests/smoke/` empty + outside
      `testDir`); fixed by (a) widening the chromium project to `testDir: ./tests` + `testMatch: [e2e, smoke]` (collects
      0 vitest files), (b) fixing the baseURL/webServer 3000→3100 mismatch + self-starting the mock server, (c)
      enriching the mock-handler `/api/data-status/turbo` with `capture_status_counts` so the bucket renders in mock
      mode, (d) excluding `tests/smoke/**` from vitest. **`tests/smoke/data-status-pending-backfill.smoke.spec.ts` now
      passes (`playwright test --project=chromium tests/smoke/` → 1 passed)** — a real chromium e2e asserting the badge
      in the live devops turbo view. So pw:L2 is satisfied by BOTH the gate's `environment-mode-invariants` AND this
      dedicated smoke. (Separately fixed the pre-existing CI `pnpm install` failure: removed the vestigial
      `canvas@2.11.2` dep — never imported, vitest uses happy-dom not jsdom — which was failing the runner's native
      build (`pkg-config     pixman-1 not found`); repo-wide unblock, no workflow edits.)
- [x] ✅ [TEST][UI] P3. **⑦ follow-up — dedicated live-turbo-view playwright e2e — DONE (slot-6 2026-06-04,
      unified-trading-system-ui@61488c8b).** `tests/smoke/data-status-pending-backfill.smoke.spec.ts` drives the devops
      → Data Status turbo view (`serviceName="market-tick-data-service"` at `app/(ops)/devops/page.tsx`) and asserts
      `[data-testid="pending-backfill-bucket"]` renders end-to-end; `playwright test --project=chromium tests/smoke/` →
      1 passed. The turbo-empty-in-mock-mode problem was fixed at the SOURCE (mock-handler now serves
      `capture_status_counts`) rather than via per-test route-mocks, so the bucket also shows in mock-mode dev. Repo:
      **unified-trading-system-ui**. parent_epic: mtds_mdps_master. Provenance: slot-6 2026-06-04 ⑦ session.

## Success criteria

- Canonical `tradfi-prd` `_index` = **v9** (data-state verified) + `pipeline_mode=` partition + `source` populated +
  `available_at` non-null; venue/data_type canonical only.
- 0 legacy-only tradfi cells; `tradfi_massive` Task -031 closed (re-consolidation done here).
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy `market-data-tick-tradfi-…` deletable; tradfi writer relaunch
  unblocked (writes canonical-only).

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — tradfi canonical form (v9 + pipeline_mode partition).

## ⑦ Coverage-denominator could-exist seed — cross-AG note (filed by slot-5 2026-06-04)

> Operator 2026-06-04 (point ⑦): the deployment-api/ui coverage **denominator** must reflect the **could-exist
> universe** (instruments/fixtures that exist in IS but whose backfill has NOT run), not just rows that exist in the
> manifest. **The seeding mechanism already exists** — `instruments-service/scripts/enumerate_expected_universe.py` (v2
> expected-universe enumerator) cross-joins the IS catalog × dates × data_types, subtracts existing manifest rows, and
> seeds `record_expected_unattempted` for the residual; deployment-api `data_status_hierarchical` already counts
> `expected_unattempted` in the 4-state denominator. Slot-5 fixed the cross-cutting blocker: the enumerator's default
> bucket map was stale for ALL 5 AGs (missing the `-prd-` env tier) → now resolves via `resolve_bucket_name`
> (instruments-service, ⑦ in `prediction_manifest_canonicalisation_2026_06_01.md`). **Remaining for tradfi:**

- [ ] [CODE] P1. ⑦ tradfi could-exist denominator seed — build the `--catalog-path` parquet from the tradfi IS catalog
      (per-instrument lifecycle: `instrument_id`/`instrument_type`/`venue`/`available_from`/`available_to`) and run
      `enumerate_expected_universe.py --asset-group tradfi --catalog-path <catalog> --apply-write` against the canonical
      `_index` so the raw-tick denominator == could-exist universe (active-but-uncaptured instruments seeded
      `expected_unattempted`). Verify on a VM (GCS flaky locally); confirm `_enumerate_v2_tradfi` row-key/data_types
      match the tradfi captured atom; add a regression (IS-universe ⊃ manifest ⇒ denominator doesn't shrink). The
      mechanism + bucket fix are done; this is the per-AG catalog build + run + verify. parent_epic: mtds_mdps_master.
      **SLOT-6 G1 DRY-RUN PROVEN (2026-06-07) — see the `## G1` section below for full evidence; `--apply-write` stays
      GATED (gate-b catalogue liveness + gate-c v9 indices).** **SLOT-6 NOTE (2026-06-04, atom-alignment VERIFIED):**
      read `instruments-service/scripts/enumerate_expected_universe.py::_enumerate_v2_tradfi` — it respects
      available_from/available_to lifecycle (date<af → EXPECTED_INSTRUMENT_NOT_LISTED; date>at →
      EXPECTED_INSTRUMENT_DELISTED; alive + no manifest row → `expected_unattempted`) and builds the row_key from
      `(venue, chain="", data_type, instrument_type, instrument_id, league_id="", date)` = the tradfi per-instrument
      captured atom. Logic CONFIRMED correct. **Remaining is genuinely VM + POST-MIGRATION gated**: `--apply-write`
      hard-requires `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<tag>` (per-VM shard isolation, refuses locally) AND must
      seed the v9 `_index` AFTER the canonical `--apply` migration (seeding the pre-migration v8 corpus would be
      rewritten by the walk). So this rides post-migration on a VM — not a local task. Open work = catalog-parquet
      build + VM `--apply-write` run + the IS-universe⊃manifest regression test. **✅ CODE PIECE DONE (slot-6
      2026-06-08, is@7ac22635):** the IS-universe⊇manifest regression
      `test_tradfi_v2_denominator_is_could_exist_universe_not_just_manifest` is shipped (mixed captured/uncaptured
      tradfi catalog → enumerator seeds `expected_unattempted` for the un-captured instrument + SKIPS (does not drop)
      the captured one → seeded universe ∪ manifest ⊇ manifest, denominator never shrinks; the tradfi mirror of the
      proven defi `test_defi_v2_denominator_is_could_exist_universe_not_just_manifest`). IS `quality-gates.sh --no-fix`
      exit 0 (268s, sentinel 7ac22635). **Item stays `- [ ]` — the catalog-parquet build + the gated VM `--apply-write`
      seed are OPERATIONAL/apply-time (bucket-B), not code.**

## G1 — IS catalogue could-exist universe (slot-6 dry-run + gate assessment, 2026-06-07)

> Owner: slot-6 (tradfi). Coordinator: `master_data_canonicalisation_migration_catalogue_2026_06_07.md` G1. This section
> records the read-only G1 dry-run for tradfi + the per-gate readiness for the irreversible `--apply-write` seed. Sync:
> instruments-service tab ⊇ LDR (pulled the `enumerate_expected_universe` pipeline_mode+source+transport
> provenance-stamp @03a93e10 + prediction CF-11 @e674768f). **The `--apply-write` seed is GATED → only dry-runs ran.**

### Step 1 — instruments-store-tradfi `_index` v9-canonical: AUDIT RUN → RED (gate-c UNMET)

- [x] ✅ [DATA] P0. **`cf_manifest_audit_2026_06_01.py instruments-store-tradfi-prd --legacy instruments-store-tradfi`
      RE-RUN (slot-6 2026-06-07).** Data-state of the **instruments-store** reference `_index` (20,388 rows): **CF-1
      RED** v9=170/20,388 (0.8% — the constant lied, 20,218 rows still v8) · **CF-3 RED** `pipeline_mode` blank
      (0/20,388) · **CF-4 RED** `source` column ABSENT · **CF-8 RED** `available_at` absent (only `written_at`) ·
      **CF-7** `data_type` blank `''` (keyed date+venue) · CF-5 GREEN (EXPECTED_WEEKEND 58 / EXPECTED_HOLIDAY 4) · CF-9
      GREEN env bucket; paths flat (no `asset_group=`/`pipeline_mode=`). Legacy diff: **60 legacy-only cells** (2026-03
      NASDAQ/NYSE/CME/ICE, blank data_type) — data-loss-on-delete gate. Identical systemic debt to the MTDS `_index`
      (CONFLICT-2). **The FIX = the gated single-walk in `instruments_manifest_canonicalisation_2026_06_01.md` §C/E**
      (vm-cross-cutting PRIMARY; E2 "build/extend the instruments migrator" is still `[ ]` — **no non-sports
      instruments-store v9 migrator exists yet**) — a **G4-class `--apply`** gated on G0 (standardisation Phase-0
      code) + pre-migration drain. **OUT OF SCOPE for this G1 wave (gated apply); flagged as gate-c below.** - **UPDATE
      (slot-6 2026-06-07 session-2) — the E2 v9 migrator NOW EXISTS + tradfi DRY-RUN GREEN.** The AG-parametric
      `instruments-service/scripts/migrate_instruments_store_v9.py` (is@febb899e) is built;
      `--asset-group tradfi --skip-objects` (read-only) projects the 20,388-row `_index` **v8→v9 100%** (v8_before
      20,218 + v9_before 170 → v9_after 20,388): CF-1 `schema_version={9:20388}` · CF-2 `asset_group=tradfi` · CF-3
      `pipeline_mode=batch_instruments_service` · CF-4 `source=instruments_service` · CF-TRANSPORT `transport=rest` ·
      CF-7 `data_type=instruments` · CF-8 `available_at` filled 20,388 · CF-10 honest 4-state (19,247 captured / 1,141
      empty_confirmed; 10,647 null→captured, 654 null→empty, 425 captured-but-empty→empty, 1,079 typed reasons). So
      **gate-c is now TOOL-READY** — the transform is correct; only the gated `--apply` RUN (the v9 WRITE, on a VM after
      G0 + drain) remains. The Step-1 "no migrator exists yet" text above is SUPERSEDED.

### Step 2 — catalogue + enumerate DRY-RUN (read-only) → mechanism GREEN

- [x] ✅ [DATA] P0. **`build_instrument_catalogue.py --asset-group tradfi --dry-run` (slot-6 2026-06-07, real prod
      GCS).** Found **11,579 `by_date` parquet(s)** under
      `instruments-store-tradfi-prd/instrument_availability/by_date/` (workers=16). The full local rollup is a **VM
      job** (timed out at ~10 min on the 11,579-parquet concat/groupby — consistent with the producer plan "the full
      unbounded run belongs on the Phase-2 VM trigger, not a laptop"). The producer is **already PROVEN for tradfi**
      (slot-7 applied `prod/catalog.parquet` 2026-06-05). Current `prod/catalog.parquet` = **684,372 instruments** (CME
      637,084 mostly OPTION/COMBO · CBOE 31,283 · ICE 15,513 · NYSE 363 · NASDAQ 128 · FX 1); **651,661 delisted (95%,
      `available_to ≤ 2026-05-04`) / 32,711 alive** — the capture-freeze signature (gate-b).
- [x] ✅ [DATA] P0.
      **`enumerate_expected_universe.py --asset-group tradfi --enumerator-version v2 --catalog-path     <prod/catalog.parquet> --start-date 2026-06-04 --end-date 2026-06-05`
      (SCAN-ONLY, slot-6 2026-06-07): exit 0.** catalog 684,372 instruments → manifest present-set **73,352** (of
      144,062 `market-data-tick-tradfi-prd` `_index` rows) → **588,798 candidate rows** (per-instrument grain) = 32,711
      alive × 9 data_types × 2 days. capture_status: **`expected_unattempted` 588,780** + `empty_confirmed` 18
      (`EXPECTED_INSTRUMENT_NOT_LISTED`); **0 DELISTED** (delisted-before-window correctly skipped by the lifecycle
      guard). Report sample-inspected (10 canonical cols; well-formed rows e.g.
      `CBOE:INDEX:VIX × {trades,ohlcv_1m,ohlcv_15m}` → `expected_unattempted`). **Mechanism GREEN.** Note:
      `--catalog-path gs://…` fails locally on gcsfs ADC ("Invalid gcloud credentials") → download the catalog with
      `gcloud storage cp` + pass a local path (the manifest scan uses the working `get_storage_client()`); a VM run
      reads `gs://` directly. > **⚠️ COUNT IS PROVISIONAL — this ran on the OLD over-fanning producer (PREDATES the
      G1-ENUM shape-aware fix, > operator 2026-06-07).** The dry-run cross-joins every alive instrument × ALL 9 tradfi
      data_types with **no > `(instrument_type × data_type)` validity filter** → it over-counts impossible cells (e.g.
      the sample > `CBOE:INDEX:VIX` emits `tbbo`/`mbp_10`/`futures_chain` rows an INDEX cannot have). So **588,798 is an
      UPPER > BOUND**, not the true could-exist denominator. tradfi is per-contract (less bundle-grain-affected than
      cefi), but > the validity slice still trims INDEX/EQUITY/ETF/FUTURE/OPTION × invalid-data_type combos. **RE-RUN
      gated** on > slot-7's shape-aware v2 producer (G1-ENUM: validity-matrix + bundle-grain) — see the HOLD todo below.
      Until then > gate-(a) is PROVISIONAL, not green.

- [x] ✅ [DATA] P0. **RE-RAN the tradfi enumerate dry-run on slot-7's SHAPE-AWARE v2 producer (G1-ENUM @6ea46565) — DONE
      (slot-6 2026-06-07). Count BARELY dropped (588,798 → 587,990, −808 only) → surfaced the REAL blocker (below).**
      `enumerate_expected_universe v2 --asset-group tradfi --catalog-path <prod/catalog.parquet>` (scan-only,
      2026-06-04..05) = 587,990 candidates. The validity filter (`valid_data_types_for_instrument_type`) trimmed ONLY
      INDEX (9→3), EQUITY (9→8), ETF (9→6) — the small per-contract types. The G1-ENUM log shows the dominant types
      **fall back to NO filter (unmapped → all 9 data_types)**: `OPTION` 31,282 instruments, `FUTURE` 1,163, `SPOT_PAIR`
      1 (99.2% of the alive set). So the over-fan persists for the types that matter.
- [x] ✅ [DATA] P0. **RESOLVED 2026-06-08 (slot-6) — gate-(a) GREEN. Era-B bundle rollup (slot-7 uac@ae70338d +
      is@74df991d/687d1443) + my tradfi `future`/`spot_pair` matrix rows (uac, see below) collapsed the enumerate
      587,990 → 24,914 → 17,928 (−570,062): the ~563K false per-contract OPTION/COMBO candidates are GONE (rolled to
      `options_chain`/`futures_chain` bundles, data_type=trades) and the residual FUTURE/SPOT_PAIR over-fan is fixed
      (FUTURE now 6 data_types, NO impossible macro/corp/earnings). Verified on the report: 0 per-contract OPTION/COMBO,
      0 data_type=options_chain, 0 impossible pairs; 17,928 = exact Σ(alive × valid-dts × 2 days). Original finding ↓
      retained for context.** 🔴 ROOT-CAUSE FINDING (slot-6 2026-06-07) — gate-(a) is BLOCKED on G1-ENUM BUNDLE-GRAIN
      for tradfi options/combos, NOT just the validity matrix. The 587,990 is still inflated by ~563K false candidates.
      Verified against the live `market-data-tick-tradfi-prd` `_index` (144,062 rows / 100,536 captured): **captured
      `OPTION` rows = 0**; tradfi captures options at **BUNDLE grain** — `options_chain` 3,262 + `combo` 58,292 +
      `futures_chain` 15,600 (per-underlying), plus per-contract `future` 7,224 / `equity` 4,449 / `spot_pair` 1,967 /
      `index` 22. BUT the IS catalogue + `_enumerate_v2_tradfi` treat OPTION (622,740) + COMBO (56,841) **per-contract**
      → the 31,282 alive per-contract OPTIONs × 9 dts × 2 days = **~563K candidates that can NEVER match the
      bundle-grain manifest** → false `expected_unattempted` (grain mismatch, exactly the cefi
      `option`→`frozenset()`+`options_chain` bundle pattern, which tradfi is MISSING). **THE FIX (mirror cefi,
      mtds_mdps_master):** (1) tradfi catalogue producer (`build_instrument_catalogue` / its tradfi grain) must emit
      `options_chain` / `futures_chain` BUNDLE-grain rows (roll per-contract leaves → one per underlying), matching the
      manifest capture atom — co-owned slot-6 + slot-7 (G1-ENUM bundle-grain mechanism). (2) UAC
      `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`: add `("tradfi","option")     → frozenset()`,
      `("tradfi","combo") → frozenset()` (leaf → no per-contract rows),
      `("tradfi","options_chain") →     {"options_chain"}`, `("tradfi","futures_chain") → {"futures_chain"}`, and the
      per-contract `("tradfi","future") →     {trades,ohlcv_1m,ohlcv_15m,ohlcv_24h,tbbo,mbp_10}` +
      `("tradfi","spot_pair") →     {trades,ohlcv_1m,ohlcv_15m,ohlcv_24h,tbbo}` (manifest confirms `future`/`spot_pair`
      are per-contract). EQUITY/ETF/ INDEX entries already correct. (3) re-run enumerate → confirm the ~563K drop
      (expect a few-×10K count, not ~588K). **NOT authored this session** — a partial validity entry
      (`option→frozenset()`) WITHOUT the catalogue bundle-grain rollup would make options vanish entirely
      (false-absence), so the catalogue + matrix land together. Until then gate-(a) is 🔴 RED. Repos:
      unified-api-contracts (matrix) + instruments-service (catalogue bundle grain). parent_epic: mtds_mdps_master.
      Cross-ref: master coordinator WAVE-1 slot-7 G1-ENUM row + cefi bundle precedent (`market_data_categories.py` cefi
      option/combo→frozenset()).

### Step 3 — `--apply-write` seed: GATED → DRY-RUN ONLY (do NOT run the irreversible seed yet)

- [ ] [DATA] P0. **G1.run `--apply-write` for tradfi — GATED, NOT runnable this wave.** Per-gate readiness:
  - **(a) Slot-7 PART C G1-foundation code: 🟢 GREEN (RESOLVED 2026-06-08, slot-6).** Era-B bundle rollup LANDED
    (uac@ae70338d options_chain/futures_chain are instrument_types→{trades} + is@74df991d/687d1443 per-underlying
    rollup) + my tradfi `future`/`spot_pair` validity rows (uac@576f8fa8). Enumerate re-run (scan-only, 2026-06-04..05):
    **587,990 → 24,914 (Era-B bundle) → 17,928 (matrix fix)** — the ~563K false per-contract OPTION/COMBO candidates are
    GONE; report verified 0 per-contract OPTION/COMBO, 0 data_type=options_chain (Era-B trades model), 0 impossible
    pairs, FUTURE now 6 data_types; 17,928 = exact Σ(alive × valid-dts × 2 days). Original RED ↓ retained for context.
  - **(a-orig) Slot-7 PART C G1-foundation code: 🔴 RED (re-validated 2026-06-07)** — the G1-ENUM shape-aware producer
    LANDED (@6ea46565) and I RE-RAN tradfi enumerate on it, but the count barely moved (588,798→587,990) because
    tradfi's dominant types (OPTION/COMBO/FUTURE/SPOT_PAIR) are UNMAPPED in the validity matrix AND — the real blocker —
    **tradfi options/combos are captured at BUNDLE grain (options_chain/combo/futures_chain) while the catalogue +
    enumerate are per-contract → ~563K false candidates (grain mismatch).** Gate-(a) needs the **G1-ENUM bundle-grain
    rollup for tradfi** (catalogue emits options_chain/futures_chain bundles + the matrix entries) — see the 🔴
    ROOT-CAUSE FINDING todo above. Not green until that lands and the re-run drops to a sane count.
    - **RE-VERIFIED slot-6 2026-06-07 session-2 — gate-(a) STILL RED, PART A still the blocker.** (1) Live UAC accessor
      confirms the matrix gap: `valid_data_types_for_instrument_type("tradfi", X)` returns **None** for `option` /
      `combo` / `options_chain` / `futures_chain` / `future`
      (equity/etf/index/bond/cds/event_contract/commodity/currency ARE mapped). (2) The catalogue instrument_type
      distribution (sampled day=2026-06-07, 33,258 rows) is **OPTION 31,282 (94%)** · FUTURE 1,163 · EQUITY 197 · ETF 67
      · INDEX 1 · SPOT_PAIR 1 → the over-fan is per-contract OPTION. (3) `build_instrument_catalogue.py` STILL emits NO
      `options_chain`/`futures_chain` bundle rows (only prediction multi-grain) and the master coordinator confirms
      "PART A NOT shipped" — slot-7's `dd7fa100 grain_for_instrument_type SSOT` is progress, not the catalogue emission.
      The matrix fix (above) MUST co-land with PART A (a lone `option→frozenset()` makes options vanish =
      false-absence). **Per the operator gate, the enumerate re-validation stays HELD until slot-7 confirms PART A
      green.** The MTDS migrator + instruments-store v9 prep are GREEN (below).
  - **(b) tradfi IS instrument backfill complete: ❌ UNMET** — IS `by_date` capture **degraded 16-18K→~2/day after
    2026-05-04, stopped after 2026-05-22** (freeze FINDING in
    `proper_instrument_catalogue_lifecycle_rollup_2026_06_04`); the catalogue marks **651,661/684,372 (95%) delisted** →
    liveness PROVISIONAL. Seeding `expected_unattempted` against a frozen catalogue would write a WRONG could-exist
    denominator. **Unblock = the Massive IS reference adapter (gate-b remediation, shipped this session — see below) →
    re-feed `by_date/` → regenerate the catalogue → THEN seed.**
  - **(c) accurate UAC + v9 indices: ⏳ TOOL-READY (UPDATED slot-6 2026-06-07 session-2) — the G1-V8 migrator is now
    BUILT (is@febb899e) + tradfi dry-run GREEN (20,388 `_index` rows → v9 100%, all CF stamps; see Step-1 UPDATE).** The
    `instruments-store-tradfi` `_index` is still v8 ON DISK (the dry-run only PROJECTS v9) AND the
    `market-data-tick-tradfi-prd` `_index` the seed writes is still v8 (CONFLICT-2). So gate-c is no longer "blocked on
    a migrator that doesn't exist" — the tool is ready; what remains is the gated `--apply` RUN. Once G0 is green, run
    `migrate_instruments_store_v9 --asset-group tradfi --apply` on `instruments-store-tradfi-prd` (pre-migration drain +
    snapshot first). `--apply-write` must seed the **post-migration v9 `_index`** (seeding the v8 corpus would be
    rewritten by the walk) — so G1.run rides AFTER that v9 walk. It also hard-requires a VM
    (`MANIFEST_PER_VM_SHARDS=true` + `VM_NAME`).
  - **Disposition**: dry-run PROVEN (Step 2); the irreversible seed waits on (b)+(c). NOT `DEFERRED` — gated with named
    unblocks (Massive capture-restore + the v9 walks). parent_epic: mtds_mdps_master.

### Step 4 — daily catalogue scheduler for tradfi: MISSING → gated todo

- [ ] [INFRA] P1. **Wire the tradfi `build_instrument_catalogue.py` daily rollup scheduler (GATED on gate-b capture
      restore).** FINDING (slot-6 2026-06-07): the G1 lifecycle producer `build_instrument_catalogue.py` has **NO
      terraform scheduler for ANY asset group** (`proper_instrument_catalogue_lifecycle_rollup_2026_06_04` [INFRA] P1
      "Trigger on every instruments update" is still `[ ]`, owner vm-cross-cutting). The two TFs that DO exist —
      `deployment-service/terraform/gcp/{catalogue_regen_scheduler,instrument_catalogue_scheduler}.tf` — run a DIFFERENT
      artefact (`generate_instrument_catalogue.py`, the availability-matrix), and their instruments-store `for_each`
      **OMITS tradfi** (only cefi/defi/sports/prediction) AND uses legacy no-env bucket names (`-central-element-…` not
      `-prd-`). So even the matrix regen never reads tradfi. **Gated** behind gate-b (a scheduler over a frozen
      `by_date/` self-perpetuates a stale catalogue) — wire once Massive capture restores `by_date/`. Owner:
      vm-cross-cutting (shared producer scheduler) + slot-6 (confirm tradfi inclusion). Repo: deployment-service
      (terraform). parent_epic: mtds_mdps_master.

### G2 prep status (slot-6 2026-06-07 session-2) — unblocked prep DONE; apply-ready HELD on PART A

> Operator GATE: "do NOT start the enumerate dry-run re-validation until slot-7 confirms the bundle-grain rollup is
> GREEN." PART A is **not** green (above) → the enumerate re-run + the full bundle-aware audit stay HELD. The non-gated
> prep is COMPLETE + re-verified on current LDR:
>
> - **② MTDS migrator dry-run GREEN** — `migrate_tradfi_to_v9_canonical --start-date 2021-08-16 --end-date 2021-08-17`
>   (dry, read-only): **planned=1088 L-hive objects, moved=0, 0 errors, exit 0** (path-only `pipeline_mode=` insert; the
>   v9 COLUMNS are `rebuild_tradfi_manifest`'s, not this script's). Source-aware `pipeline_mode` derivation verified per
>   venue: CME/NYSE/NASDAQ/CBOE/ICE → `batch_databento`, BARCHART → `batch_barchart`, YAHOO → `batch_yahoo`, EIA →
>   `batch_eia` (NOT coarse `batch`/blank). The migrator walks `day=` (date-bounded — no defi-style full-bucket-scan
>   timeout).
> - **③ instruments-store v9 dry-run GREEN** — 20,388-row `_index` → v9 100%, all CF stamps (see Step-1 UPDATE +
>   gate-(c)).
> - **① matrix/grain slice REVIEWED** — the exact missing tradfi rows are grounded (see the ROOT-CAUSE FINDING +
>   gate-(a) re-verify); the fix is authored-but-HELD (must co-land with PART A to avoid false-absence).
>
> **Apply-ready blockers (precise):** gate-(a) bundle-grain = **slot-7 PART A** (catalogue emits options_chain/
> futures_chain bundles) **+ the co-landing tradfi matrix rows** · gate-(b) capture-freeze = Massive `by_date` re-feed +
> catalogue regen (adapter SHIPPED, below) · gate-(c) v9 `_index` = the gated `migrate_instruments_store_v9 --apply` RUN
> (TOOL-READY) · plus G3 (UNION view — SHIPPED pm@822393880) and the operational pre-migration drain. When PART A lands,
> the remaining tradfi work is: co-land the matrix rows → re-run enumerate (expect the ~563K false-candidate drop) →
> finish the bundle-aware 7+2 audit → apply-ready verdict.

### 🟠 TradFi PRE-APPLY 12-POINT AUDIT — ①–⑫ on REAL-PROD data-state (slot-6, 2026-06-08 session-2)

> **🔴 VERDICT SUPERSEDED (slot-6 2026-06-08 session-3, operator pushback on `options_chain`):** the "REGRESSION RISK:
> NONE" claim below was **based on recent-day (Era-B) sampling + a migrator dry-run window (day=2021-08-16) that did NOT
> exercise the OLD `category=` / Era-A `data_type=options_chain` tail**. Probing the OLD tail (day=2023-05-01) surfaced
> **two real G4 orphan/loss risks** → the corrected verdict is **🟠 NOT apply-clean until the old-data tail is handled**
> (see the "🔴 OLD-DATA TAIL — ORPHAN/LOSS RISKS" block appended to the orphan drill-down). The ①–⑫ table below stands
> for the DOMINANT (asset_group=, Era-B) corpus; it does NOT cover the legacy `category=`/Era-A tail. **Headline**: (1)
> the migrator has **NO `category=`→`asset_group=` rename** — old `category=tradfi` paths (1,627/1,680 on
> day=2023-05-01, incl. NASDAQ/NYSE/ICE/FX with **no `asset_group=` twin**) migrate to a non-canonical `category=` path
> that canonical readers ignore → orphan; (2) **`options_chain` is a real schema-backed DATA_TYPE** (UAC
> `(ag, options_chain, options_chain)` `CEFI/TRADFI_OPTIONS_CHAIN_SNAPSHOT` with `mark_iv`/greeks/`underlying_price`),
> present on disk (tradfi day=2023-05-01: 14; cefi day=2024-06-03 BYBIT futures_chain shard 12,525 rows) — and the
> migrator **SKIPS** the Era-A `data_type=options_chain` paths that lack an `instrument_type=` segment
> (`_canon_hive_rel` returns None) → orphan. So the operator was right: we DO have a `data_type=options_chain` and the
> current migrator does not safely carry it. **🟢 MIGRATOR FIXED this session (mtds@51c604a4)** — `_canon_hive_rel`
> rebuilds canonical from parsed dims (renames `category=`→`asset_group=`, derives `instrument_type=options_chain` from
> the chain data_type + KEEPS `data_type=options_chain`, routes un-attributable legacy objects to `_needs_attribution/`
> never skip-then-delete); real-prod dry-run day=2023-05-01 = **1,680/1,680 planned, 0 skipped** (was orphaning the
> `category=`/Era-A tail); 17/17 unit tests (4 new). **Remaining (not migrator-code): T-OLD-2b validity-matrix widening
> (slot-7) + T-OLD-2c content-aware attribution of the holding + T-OLD-3 full-range dry-run as the apply gate.** ↓
> original session-2 verdict retained for context.

> **VERDICT (session-2, SUPERSEDED): tradfi DATA/MANIFEST `--apply` (G4) is APPLY-READY — REGRESSION RISK: NONE.** This
> pass re-verified the full operator ①–⑫ readiness audit against real-prod GCS (`central-element-323112`), not code
> constants — adding the on-disk Era-B byte-probe (⑩), the batch=live symmetry proof (⑪), and rollback-readiness (⑫)
> that the prior 5/5 dry-gate verdict did not formally cover. One code gap was FOUND + FIXED in my AG (⑫ phantom
> prefix_tpls). One cross-AG denominator finding (⑥/⑦) was filed to the coordinator for slot-7 — it affects the **gated
> G1.run could-exist SEED only, NOT the G4 data migration**. **Multi-source confirmed (operator 2026-06-08): tradfi =
> Databento (primary) + MASSIVE (polygon.io-compatible backfill for series Databento credits no longer cover, IDENTICAL
> schema, `pipeline_mode` is the differentiator) + Barchart /Yahoo (VIX 15m) + EIA.** The batch=live symmetry IS the
> databento↔massive symmetry.

| #   | Check                                                 | Verdict                        | Evidence (real-prod; sampled-vs-walked)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| --- | ----------------------------------------------------- | ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ①   | Migrator dry-run                                      | 🟢                             | `migrate_tradfi_to_v9_canonical` is 3-layout-aware (L-hive 1,996 `day=` / L-hyphen 12 `day-` / candles); inserts source-aware `pipeline_mode=batch_<source>` LEFT of `asset_group=`, preserves `underlying=` bundles, CF-7 venue skip. SAMPLED day=2021-08-16..17 + on-disk path WALK.                                                                                                                                                                                                                                                         |
| ②   | Manifest-rebuild dry-run                              | 🟢                             | `rebuild_tradfi_manifest.py` derives `derive_pipeline_mode_for_row(venue,"tradfi",dt)` (source-aware), re-derives from the Era-B disk so the 291 stale Era-A `('',options_chain)` manifest rows are NOT reproduced; `migrate_instruments_store_v9 --asset-group tradfi` → `_index` 20,388 rows 100% v9 (WALKED).                                                                                                                                                                                                                               |
| ③   | 4-state pre-flight (IS→…→execution)                   | 🟢                             | Real `_index` carries the 4-state honestly (captured 100,536 / empty_confirmed 37,490 / attempted_failed 6,036); `expected_unattempted` is the gated G1.run seed (writer-materialised, not pre-apply). G3 UNION consumer shipped (deployment-api@4dd2575).                                                                                                                                                                                                                                                                                     |
| ④   | Empty/partial honest + downstream                     | 🟢                             | TYPED reasons WALKED: empty*confirmed→`EXPECTED_WEEKEND`(35,050)/`EXPECTED_HOLIDAY`(2,427)/`EXPECTED_OUT_OF_COVERAGE_WINDOW`/`SOURCE_RETURNED_ZERO`; attempted_failed→`DATABENTO_FETCH_FAILED`/`SCHEMA_VALIDATION_FAILED`/`phantom*\*`/`403`. No silent placeholders. **Residual**: 5,159 `attempted_failed`/`LegacyBlankErrorReasonError` (legacy-blank marker, honest as failed — not a placeholder).                                                                                                                                        |
| ⑤   | Read/write paths prefix-match post-migration          | 🟢                             | `rg 'pipeline_mode=(batch\|live)([/"\`]\|$)'` across mtds/mdps/features/strategy/execution/deployment-api/UTL → 0 coarse-exact READER probes; the only 2 hits are explanatory comments describing the legacy form the readers prefix-match.                                                                                                                                                                                                                                                                                                    |
| ⑥   | IS+UAC guardrails vs impossible cells                 | 🟢 (matrix) / 🟡 (present-set) | Validity matrix + grain slice CORRECT for every tradfi itype (`option/combo→frozenset()`, `options_chain/futures_chain→{trades}` grain=bundle_by_underlying, `future`=leaf no `FUTURE_BUNDLE_VENUES[tradfi]`, no PERPETUAL, no equity×perp/index×options_chain). **🟡 FILED (coordinator, slot-7):** the seed-vs-present-set rollup asymmetry → phantom `(options_chain,trades)` seeds for combo-captured underlyings (G1.run-seed-only).                                                                                                      |
| ⑦   | deployment-api/UI numerator/denominator = could-exist | 🟢 (consumer) / 🟡 (seed)      | G3 UNION view SHIPPED (pm@822393880); reads 4-state, coverage % over could-exist denominator (never re-derived). 🟡 the denominator-inflation is the same ⑥ G1.run-seed finding (filed) — NOT a consumer bug.                                                                                                                                                                                                                                                                                                                                  |
| ⑧   | IS-catalogue completeness (CF-14) + scheduler         | 🟢                             | `build_instrument_catalogue` rolls up the prd `instrument_availability/by_date/` (64,724 parquets); tradfi NOW in all 3 catalogue schedulers (lifecycle_catalogue_scheduler.tf / catalogue_regen_scheduler.tf / instrument_catalogue_scheduler.tf) — prior "MISSING" finding RESOLVED. terraform apply is the gated infra step.                                                                                                                                                                                                                |
| ⑨   | pipeline_mode source-aware (CF-13)                    | 🟢                             | migrator + rebuild stamp `batch_<source>` (databento/massive/barchart/yahoo/eia) via `derive_pipeline_mode_for_row` (path+column), NOT coarse `batch`/blank; `source_string_for(pm)==source` holds; `transport` separate column.                                                                                                                                                                                                                                                                                                               |
| ⑩   | Era-B ON-DISK byte-probe                              | 🟢                             | **MY probe** `market-data-tick-tradfi-prd day=2025-12-31`: instrument_type ∈ {combo·equity·future·futures_chain·index·options_chain·spot_pair}; data_type ∈ {ohlcv_1m·ohlcv_15m·ohlcv_24h·tbbo·trades}; **`data_type=(options_chain\|futures_chain)` count = 0** → uniformly Era-B, zero Era-A residue.                                                                                                                                                                                                                                        |
| ⑪   | ★ BATCH=LIVE SYMMETRY                                 | 🟢                             | Live writer (`tradfi_shared.py:334`/`databento_adapter.py`) + migrator share `derive_pipeline_mode_for_row`, the same chain-bundle path (`underlying=…/ticks.parquet`), the same `_MERGED_DATA_TYPE_MAP`, per-row `available_at` (no read-time); migrator is content-preserving server-side copy → bit-identical canonical v9 shape. No live-only data_type. Massive backfill uses the IDENTICAL schema (pipeline_mode differentiates). 5-axis sub-agent proof.                                                                                |
| ⑫   | ROLLBACK READY                                        | 🟢 (FIXED)                     | `_index/snapshots/pre_migration_2026_06_08.parquet` PRESENT in both `market-data-tick-tradfi-prd` + `instruments-store-tradfi-prd`. **🟢 FIXED this session (is@5e8d192d)**: tradfi phantom-audit `prefix_tpls` was missing `batch_massive`/`batch_barchart`/`batch_yahoo`/`batch_eia` (comment falsely said "Databento exclusively") — venues BARCHART(4,655)+YAHOO_FINANCE(6,174) are real on `_index` → without the prefixes a post-apply phantom `--apply` would flip their real captured rows→attempted_failed. Added all 5 source modes. |

**Sampled-vs-walked**: WALKED — full 20,388-row instruments-store `_index` v9 transform; full 144,062-row
`market-data-tick-tradfi-prd/_index` profile
(schema_version/capture_status/pipeline_mode/instrument_type×data_type/venue); the 1,996 `day=` vs 12 `day-` partition
split; 4 parquet-footer row-count probes (hyphen tree = 0-row placeholders, canonical combo = 300 rows). SAMPLED —
migrator dry-run day=2021-08-16..17; on-disk leaf paths day=2025-12-31 + day-2026-01-04; CF-5/9/11/12 by code grep + the
25/25 unit suite. **Residual gaps**: the full-horizon enumerate candidate count (gated G1.run VM run) + the ⑥/⑦
present-set-rollup quantification (filed to slot-7) — both downstream of the gated SEED, not the G4 data migration.

**REGRESSION RISK: NONE** for the tradfi DATA + MANIFEST `--apply` (G4). The migrator/rebuild produce the identical
canonical v9 form the live writer produces (⑪), on-disk is uniformly Era-B (⑩), rollback snapshot + corrected phantom
prefixes are in place (⑫). **Remaining gates are OPERATIONAL** (the gated WRITE runs + IS Massive backfill + the Era-B
legacy-row relabel that rides the G4 migrator + pre-migration drain). The one open quality item is the cross-AG
G1.run-SEED denominator finding (⑥/⑦), owned by slot-7, which does **not** gate G4.

- [ ] [SCRIPT] P2. **⑫ FOLLOW — re-run `reconcile_phantom_manifest_rows_all.py --asset-group tradfi --dry-run` AFTER the
      tradfi v9 object `--apply`** to confirm 0 false phantoms across all 5 source pipeline_modes
      (batch_databento/massive/barchart/yahoo/eia). The prefix_tpls fix (is@5e8d192d) is verified by inspection +
      `batch_massive` presence; the live re-run is gated on the apply. Repo: instruments-service. parent_epic:
      manifest_master.

### 🗂️ ORPHAN-COVERAGE DRILL-DOWN (slot-6, 2026-06-08) — every tradfi GCS prefix: covered / not-migrated / DELETE-AFTER

> **Operator ask 2026-06-08: prove the dry-run + apply leave NO orphaned data — enumerate every old-format prefix
> already in the tradfi buckets, what the migrator copies to canonical, and what we expect to DELETE afterward, so
> nothing lingers orphaned (storage waste + reader confusion) and nothing is deleted prematurely (data loss).** The
> migrator is **COPY-only** (server-side `gcs_copy_object`, idempotent) — it writes canonical paths but does NOT delete
> the old ones. Deletion of the old-format source paths is a **separate, gated step** (MTDS E7/G7 verify-then-delete;
> instruments-store E6) — so the "delete-after" set below is what must be tracked + swept post-verify. **VERDICT: with
> the two runbook requirements honoured (R1 `--also-legacy`, R2 the gated delete), tradfi has NO orphan path.**

**Buckets in scope** (`-central-element-323112`): `market-data-tick-tradfi-prd` (canonical dest) ·
`market-data-tick-tradfi` (NO-ENV LEGACY source) · `instruments-store-tradfi-prd`.

| Prefix (real-prod)                                                                                        | Shape on disk TODAY                                                             | Scale                                | Migrator coverage                                                                                                          | Canonical dest                                                            | DELETE-AFTER?                                                                                                                                                                                                     |
| --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `…-prd/raw_tick_data/by_date/day=*/asset_group=tradfi/venue=/instrument_type=/data_type=/[underlying=]/…` | L-hive (asset_group=, **MISSING pipeline_mode=**)                               | **1,996** `day=` dirs                | ✅ `_process_hive` inserts `pipeline_mode=batch_<source>/` after `day=` (path-only)                                        | `…/day=D/pipeline_mode=batch_<source>/asset_group=tradfi/…`               | **YES** — the bare `day=D/asset_group=` paths (old) deleted at the gated G7 sweep once the canonical copy is verified                                                                                             |
| `…-prd/raw_tick_data/by_date/day-*/data_type-*/{equities\|etf\|futures_chain}/{VENUE}/…`                  | L-hyphen (non-hive, per-contract)                                               | **12** `day-` dirs (~110K objs)      | ✅ `_process_hyphen` → canonical rebuild, dedup vs L-hive (L-hive wins overlap); **0-row guard skips placeholders**        | canonical hive (complementary equities/etf migrated; CME overlap deduped) | **YES** — all 12 `day-*` dirs (verified **0-row Massive dry-run placeholders** → footer-skipped, then E7 Pattern-1 deletes them; the equities/etf "data" is the REAL never-ingested gap, NOT migrated as empties) |
| `…-prd/processed_candles/by_date/day=*/…`                                                                 | MDPS candles (day=, no pipeline_mode)                                           | 2020-01-01→                          | ✅ `_process_candles` inserts `pipeline_mode=`                                                                             | `…/processed_candles/by_date/day=D/pipeline_mode=…/`                      | **YES** — old bare-candle paths swept at G7                                                                                                                                                                       |
| **`market-data-tick-tradfi/` (NO `-prd`) `raw_tick_data` + `processed_candles`**                          | legacy pre-prd corpus                                                           | **2,008** `day*` dirs                | ⚠️ **ONLY with `--also-legacy`** — main() loops `sources=[canon]+([legacy] if also_legacy)`, full 3-layout walk per source | dedup-copied into `…-prd` canonical                                       | **YES — DECOMMISSION the whole legacy bucket** after the copy is verified (this is the largest delete-after set)                                                                                                  |
| `…-prd/databento-batch-registry/`                                                                         | databento job-dedup registry                                                    | —                                    | 🚫 **NOT migrated, NOT deleted** (job registry, not market data — migrator docstring explicit)                             | n/a                                                                       | NO (keep)                                                                                                                                                                                                         |
| `…-prd/_vm_staging/` (`migrate_tradfi_to_hive.py`, `logs/`, `mtds_backfill/`)                             | transient staging                                                               | `mtds_backfill/` = **0 parquet**     | 🚫 not data                                                                                                                | n/a                                                                       | optional cleanup (no canonical data; safe to leave or sweep)                                                                                                                                                      |
| `…-prd/backfill-logs/`, `…-prd/configs/`                                                                  | logs + config                                                                   | —                                    | 🚫 not data                                                                                                                | n/a                                                                       | NO (keep)                                                                                                                                                                                                         |
| `…-prd/_index/availability_index.parquet` + `_index/per_vm/`                                              | v8 manifest + per-VM shards                                                     | 144,062 rows                         | ✅ REBUILT by `rebuild_tradfi_manifest` (re-derives v9 from the canonical disk)                                            | v9 `_index`                                                               | per_vm shards consolidated→cleaned by the consolidator (not the migrator)                                                                                                                                         |
| `…-prd/_index/snapshots/`                                                                                 | rollback snapshots                                                              | `pre_migration_2026_06_08.parquet` ✓ | 🚫 keep (rollback)                                                                                                         | n/a                                                                       | NO (keep — ⑫)                                                                                                                                                                                                     |
| `instruments-store-tradfi-prd/_index/availability_index.parquet`                                          | v8 (20,388 rows, 0.8% v9)                                                       | —                                    | ✅ `migrate_instruments_store_v9` rewrites v9                                                                              | v9 `_index`                                                               | n/a (in-place rewrite)                                                                                                                                                                                            |
| `instruments-store-tradfi-prd/instrument_availability/by_date/day=*/venue=*/instruments.parquet`          | reference defns (single `day=`, **clean — no doubled-`day=` bug**, unlike defi) | 11,579+ parquets                     | ✅ `canonical_object_rel` inserts `pipeline_mode=/asset_group=`                                                            | canonical                                                                 | **YES** — old bare paths deleted at the gated **E6** step                                                                                                                                                         |
| `instruments-store-tradfi-prd/prod/catalog.parquet`, `_catalogue/`                                        | GENERATED rollup artifacts                                                      | —                                    | 🚫 not migrated — **REGENERATED** by `build_instrument_catalogue` post-migration                                           | n/a                                                                       | NO (regenerate, don't migrate)                                                                                                                                                                                    |

**Orphan verdict + 2 runbook requirements (HARD):**

- **R1 — `--apply` MUST pass `--also-legacy`** (or the **2,008-day** no-env `market-data-tick-tradfi` corpus orphans —
  the canonical readers prefix-match only the `-prd` bucket). Then **decommission the legacy bucket** after verify.
- **R2 — the old-format source paths are deleted by a SEPARATE gated step, NOT the migrator** (MTDS G7
  verify-then-delete · instruments-store E6). The migrator's only auto-delete is the E7 0-row-placeholder cleanup. So
  the "delete-after" set (every **YES** row above) must be swept post-verify — tracked here so it is neither forgotten
  (orphan) nor run early (data loss). **Do NOT blanket-delete `day=*/asset_group=tradfi/` without `pipeline_mode=` until
  the canonical copy of that exact cell is byte-verified** (G7 cross-shard sample).
- **No uncovered shape**: every prefix holding market/reference DATA maps to a migrator branch; the un-migrated prefixes
  are registries/logs/configs/generated-artifacts (correctly excluded) or rollback snapshots (kept). SAMPLED top-level +
  the 3 raw-tick layouts WALKED-by-count; the legacy bucket's per-layout split + the full delete-set enumeration run on
  the in-region VM at apply time (the migrator's dry-run prints planned-copy counts per source/branch — capture them in
  the G7 ledger).

- [ ] [DATA] P1. **R1 RUNBOOK — the tradfi `migrate_tradfi_to_v9_canonical --apply` MUST include `--also-legacy`** to
      cover the 2,008-day no-env `market-data-tick-tradfi` corpus, then decommission that legacy bucket after the
      canonical copy is G7-verified. Without the flag, 2,008 legacy days orphan. Repo: market-tick-data-service.
      parent_epic: mtds_mdps_master. Provenance: orphan-coverage drill-down, slot-6 2026-06-08.
- [ ] [DATA] P1. **R2 DELETE-AFTER sweep — after the tradfi v9 `--apply` + G7 byte-verify, run the gated delete of the
      old-format source paths** (every **DELETE-AFTER=YES** row in the drill-down: bare `day=*/asset_group=tradfi/`
      without `pipeline_mode=`, the 12 `day-*` hyphen dirs, old processed_candles, the whole legacy bucket, the
      instruments-store E6 bare paths). Capture the migrator dry-run's planned-copy counts per source/branch into a G7
      ledger so the delete set == the verified copy set (no orphan, no premature delete). Repos:
      market-tick-data-service + instruments-service. parent_epic: mtds_mdps_master. Provenance: orphan-coverage
      drill-down, slot-6 2026-06-08.

**Chain data_types beyond `trades` (operator's tardis/implied-vol question, 2026-06-08):** the migrator is **path-only —
it copies EVERY object under a day regardless of `data_type`** (`_list_day` lists all `.parquet`; `_canon_rel` preserves
`instrument_type`+`data_type`), so **NO `data_type` is ever dropped by the migration** — whatever a chain bundle carries
survives byte-for-byte. **tradfi (Databento) chains carry only `{trades, ohlcv_1m}`** (probed
`instrument_type=options_chain` → trades 19 / ohlcv_1m 3; `futures_chain` → trades 9 / ohlcv_1m 13; Databento does NOT
compute implied vols) — so there is no IV data at risk in tradfi. The ONLY place a chain's non-`trades` data_types
matter is the **validity matrix could-exist SEED** (`options_chain/futures_chain → {trades}`), which is exactly the ⑥/⑦
G1.run-seed finding (the matrix is too narrow for chain bundles that also hold `ohlcv_1m`/`tbbo`) — a denominator
concern, NOT data loss. **Tardis/cefi caveat flagged to slot-3 + the matrix owner**: if tardis options_chain bundles
carry `derivative_ticker` (mark IV / greeks) or `book_snapshot_5` as distinct data_types, the SAME matrix-too-narrow gap
applies there with first-class IV data — folded into the coordinator ⑥/⑦ finding for cefi verification (migration still
preserves it; the seed must admit it).

#### 🔴 OLD-DATA TAIL — ORPHAN/LOSS RISKS the migrator does NOT handle (slot-6 2026-06-08 session-3) — G4 BLOCKERS

> Surfaced by the operator's `options_chain` pushback. The session-2 drill-down audited the **`asset_group=` / Era-B**
> corpus; this block audits the **OLD legacy tail** (probed day=2023-05-01: 1,680 parquets). **Both risks are real
> orphan/data-loss at `--apply`** — they REVISE the verdict to 🟠.

| #       | Finding (real-prod)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Migrator behaviour                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Orphan/loss                                                                                                                                                                                             | Severity                                                                                                                                                 |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T-OLD-1 | **Legacy `category=tradfi` path key** — 1,627 of 1,680 paths on day=2023-05-01 (only 53 `asset_group=`). Cells under `category=` include venues **FX/ICE/NASDAQ/NYSE with NO `asset_group=` twin** (live un-migrated equities/futures).                                                                                                                                                                                                                                                                                                                                                                                                           | `migrate_tradfi_to_v9_canonical` has **ZERO `category=`→`asset_group=` rename** (grep `category` in the script = 0 hits). `_canon_hive_rel` only string-inserts `pipeline_mode=` after `day=` → a `category=` source migrates to `day=/pipeline_mode=/category=tradfi/…` — **still non-canonical** (canonical readers prefix-match `asset_group=`). The migrator docstring lists only `asset_group=` as L-hive → it ASSUMES a prior category→hive migration that is **incomplete for the old tail**.                            | NASDAQ/NYSE/ICE/FX old equities/futures → migrated to a non-canonical `category=` path readers ignore → **ORPHAN** (+ if the G7 delete removes the source, **lost**)                                    | 🔴 P0                                                                                                                                                    |
| T-OLD-2 | **`data_type=options_chain` (+ `futures_chain`) is a real schema-backed DATA_TYPE**, not just an instrument*type — UAC `(ag, options_chain, options_chain)` `TRADFI/CEFI_OPTIONS_CHAIN_SNAPSHOT` carry `mark_iv`/`greeks*\*`/`underlying_price`(the tardis timer chain-snapshot). On disk: tradfi day=2023-05-01 = **14**`data_type=options_chain`(category=, **no`instrument_type=`**, real rows e.g. `6AK3.parquet`=17); cefi day=2024-06-03 = a `batch_tardis/.../instrument_type=futures_chain/data_type=options_chain/ticks.parquet`(12,525 rows). 291 tradfi manifest rows`data_type∈{options_chain,futures_chain}` (CME, 2023-05→2026-01). | `_canon_hive_rel` **SKIPS** any path with no `instrument_type=` segment (`if not (day and venue and data_type and instrument_type): return None`, line 174 "CF-7 drift → E6 diagnosis"). The Era-A `data_type=options_chain` paths (no `instrument_type=`) → **None → not copied → orphan**. The migrator also does NOT collapse `data_type=options_chain`→`trades` (it merges `futures_chain`→`options_chain`, the other direction) — so the coordinator-plan's assumed Era-B relabel of these rows is NOT what the code does. | Era-A `data_type=options_chain` objects (the IV/chain-snapshot type) → **ORPHAN/lost**; the Era-B model's "`options_chain` = instrument_type, data_type=trades only" **conflates a distinct data_type** | 🔴 P0 + **BLOCKED-OPERATOR-DECISION** (is `data_type=options_chain` a distinct snapshot to PRESERVE, or superseded by per-contract `derivative_ticker`?) |

**Why the session-2 audit missed it (honest sampled-vs-walked correction):** ⑩/① sampled day=2025-12-31 + day=2021-08-16
(both `asset_group=`/Era-B clean) — neither exercised the `category=`/Era-A-`options_chain` old tail. The migrator
dry-run's day-window likewise. **The fix:** the migrator dry-run must be run over an OLD-TAIL day-range (2023-05) and
assert 0 skipped/non-canonical paths before `--apply`.

- [x] ✅ [SCRIPT] P0. **T-OLD-1 — `category=`→`asset_group=` canonicalisation FIXED (mtds@51c604a4)**: `_canon_hive_rel`
      now REBUILDS the canonical path from parsed dims, renaming legacy `category=tradfi`→ `asset_group=tradfi` (the old
      string-insert kept `category=` → NASDAQ/NYSE/ICE/FX old paths with no `asset_group=` twin orphaned). Verified:
      real-prod dry-run day=2023-05-01 → **1,680/1,680 L-hive objects planned, 0 skipped** (was mishandling 1,627
      `category=` + skipping 20 no-instrument_type); 17/17 unit tests green (4 new). Repo: market-tick-data-service.
      parent_epic: mtds_mdps_master.
- [x] ✅ [MTDS] P0. **T-OLD-2 (migrator part) — `data_type=options_chain` carry-through FIXED (mtds@51c604a4)** per the
      operator PRESERVE decision: `_canon_hive_rel` derives `instrument_type=options_chain` from a chain `data_type`
      with no `instrument_type=` segment and **KEEPS `data_type=options_chain`** (the schema-backed mark_iv/greeks
      snapshot, NOT collapsed to trades). Un-path-attributable legacy objects (no instrument_type, non-chain bare-symbol
      files) route to a **`_needs_attribution/`** holding (preserved, counted, never skip-then-delete — defi pattern),
      NOT a guess. `_ONDISK_DATA_TYPE_MERGE` left as-is (no-op for tradfi — no on-disk `data_type=futures_chain`; the
      option/future distinction lives in `instrument_type`). Unit + real-prod dry-run green. **REMAINING (NOT this
      commit):** ↓ T-OLD-2b matrix widening (slot-7) + T-OLD-2c content-aware attribution of the holding.
- [x] ✅ [UAC] P1. **T-OLD-2b — validity matrix widened for tradfi chains DONE (uac@df0acd06)**: probed the real
      present-set (slot-6) → admitted EXACTLY the captured data_types (no over-fan):
      `("tradfi","options_chain")={trades, ohlcv_1m, options_chain}` (the snapshot data_type included — the 291 Era-A
      rows migrate to instrument_type=options_chain/data_type=options_chain) ·
      `("tradfi","futures_chain")={trades, ohlcv_1m, tbbo}` (no snapshot data_type observed for futures_chain on tradfi
      disk → not admitted). Was `{trades}` only → marked ~12K real captured chain cells "impossible". `option`/`combo`
      leaves stay `frozenset()` (Era-B rollup; the combo present-set reconciliation is the broader ⑥/⑦, slot-7). Test
      `test_tradfi_options_futures_chain_bundle_data_types` updated; matrix(59)/era_b_purge(6)/source_priority(42) green
      — closed-set round-trips hold. Repo: unified-api-contracts. parent_epic: manifest_master.
- [x] ✅ [SCRIPT] P2. **T-OLD-2c — content-aware attribution pass BUILT (mtds@b56da26a)**:
      `attribute_tradfi_needs_attribution.py` reads each held parquet's `instrument_key` (verified format
      `{VENUE}:{ITYPE}:{SYMBOL}`, e.g. `NASDAQ:EQUITY:AAPL-USD`) → maps the ITYPE token via the migrator's
      `_INSTRID_ITYPE_MAP` → rebuilds canonical via the migrator's `_canon_rel` SSOT → server-side copies into the
      canonical tree; un-resolvable (no instrument_key / unknown ITYPE) → LEFT in holding (counted+logged, never
      guessed, never deleted). Idempotent + dry-run default; runs post-`--apply` (the holding only exists then). 5/5
      unit tests on the pure logic (`canonical_for_held`/`_instrument_type_from_key`). Repo: market-tick-data-service.
      parent_epic: mtds_mdps_master.
- [x] ✅ [DATA] P1. **T-OLD-3 — old-tail dry-run SAMPLE PROVEN; full-range VM run is the apply gate**: ran the migrator
      dry-run over 6 representative old-tail days — **day=2023-05-01 1,680/1,680 planned 0 skipped** + 2023-06-01
      (1,272), 2023-12-01 (757), 2024-03-01, 2024-09-02, 2025-03-03 all plan every listed object (0 silent skips;
      candles included in TOTAL). The full 2023-05→2026 whole-corpus dry-run (asserting 0 skipped + the options_chain
      count carried) runs on the in-region VM as the hard `--apply` gate (the `launch-canonical-migration-vm.sh`
      launcher runs the full range). Repo: market-tick-data-service. parent_epic: mtds_mdps_master. Provenance: slot-6
      2026-06-08.

### 🟢 TradFi APPLY-READY VERDICT (slot-6, 2026-06-08) — 5/5 dry-gate criteria GREEN; remaining gates OPERATIONAL only

> **VERDICT: tradfi is APPLY-READY on LDR.** PART A (Era-B bundle rollup) landed and my last matrix slice fix shipped;
> every G1+G2 dry-run is green and the 7+2 audit passes. **No code change remains before `--apply`** — the only blockers
> are operational (the gated WRITE runs + IS backfill + the Era-B relabel that rides G4 + the pre-migration drain).

**The 5 dry-gate criteria (all GREEN):**

1. **① MTDS migrator dry-run** — `migrate_tradfi_to_v9_canonical` (dry): planned=1088 / 0 errors; source-aware
   `pipeline_mode` (CME/NYSE/NASDAQ/CBOE/ICE→`batch_databento`, BARCHART→`batch_barchart`, YAHOO→`batch_yahoo`,
   EIA→`batch_eia`); path-only insert — the v9 columns ride `rebuild_tradfi_manifest`.
2. **② Manifest-rebuild / instruments-store v9** — `migrate_instruments_store_v9 --asset-group tradfi` (is@febb899e):
   `_index` 20,388 rows → **v9 100%**, all CF stamps (`schema_version=9` · `asset_group=tradfi` ·
   `pipeline_mode=batch_instruments_service` · `source=instruments_service` · `transport=rest` · `data_type=instruments`
   · per-row `available_at` · honest 4-state 19,247 captured/1,141 empty_confirmed). cf_manifest_audit projection
   CF-GREEN (v8→v9).
3. **③ Enumerate re-validated GREEN on the Era-B bundle producer** (uac@ae70338d + is@74df991d/687d1443 + my
   uac@576f8fa8): **587,990 → 24,914 (bundle rollup) → 17,928 (future/spot_pair matrix rows)**. Report verified: **0
   per-contract OPTION/COMBO** (rolled to options_chain/futures_chain bundles, one per underlying, data_type=trades),
   **0 data_type=options_chain** candidates (Era-B trades model), **0 impossible pairs** (tradfi has no
   PERPETUAL×chain), FUTURE trimmed to its 6 real data_types (no macro/corp-action/earnings over-fan); 17,928 = exact
   Σ(alive × valid-dts × 2 days). The ~563K false per-contract candidates are GONE.
4. **④–⑦ honest-absence / read-write paths / IS+UAC guardrails / numerator-denominator** — ride the WAVE-1 code (rebuild
   typed reasons + `record_zero_rows`, A7/CF-11 fetch-failure→`attempted_failed`, batch=live single path, env-tier
   `resolve_bucket_name`); G3 UNION view SHIPPED (pm@822393880); the could-exist denominator is now accurate (enumerate
   17,928).
5. **⑧/⑨ catalogue-completeness + source-aware pipeline_mode** — `-prd-` `instrument_availability/by_date/` POPULATED
   (64,724 parquets), shape-aware + bundle-grain producer GREEN, validity+grain slice CORRECT for every tradfi
   instrument*type (option/combo→frozenset; options_chain/futures_chain→{trades}, grain=bundle_by_underlying;
   future/spot_pair→per-contract leaves); migrators stamp source-aware `batch*<source>` (NOT coarse).

**Sampled-vs-walked**: WALKED — the full 20,388-row instruments-store `_index` transform + the full 684,372-instrument
catalog + 144,062-row manifest scan in enumerate (present-set 73,352). SAMPLED — the MTDS migrator dry-run on
day=2021-08-16..17 (path+derivation; the whole-corpus walk runs on the in-region VM) + the catalogue instrument_type
distribution. **Remaining gaps**: none code-side; the candidate-count is for a 2-day window (the full-horizon seed is
the gated G1.run VM run).

**The ONLY remaining gates — ALL OPERATIONAL (no code owed):** G0 ✓ · G3 UNION view ✓ (pm@822393880) · the v9
instruments-store walk `migrate_instruments_store_v9 --asset-group tradfi --apply` RUN (TOOL-READY; dry-run proved 100%
v9) · IS backfill complete (Massive `by_date` re-feed → catalogue regen; adapter SHIPPED) · the **Era-B legacy-row
relabel rides the G4 migrator as its final atomic step** (operator decision slot-7 edca81b57 — NOT a dry-run blocker) ·
pre-migration drain. **`tradfi APPLY-READY — 5/5`.**

- [ ] [INFRA] P2. **PRE-EXISTING UAC QG RED (not tradfi; flagged slot-6 2026-06-08) — blocks the UAC `--no-fix` sentinel
      → no clean UAC quickmerge fleet-wide.** `tests/unit/test_schema_version_matrix.py` 3 failing
      (`test_green_status_when_versions_match` / `test_na_schema_version_does_not_trigger_red` /
      `test_load_providers_green_when_versions_match`): assert `binance.computed_status == "green"` but it is `"yellow"`
      (schema_version provider-status drift). **Proven PRE-EXISTING** (stash-test: fails identically on clean LDR
      without my matrix change) + **unrelated** to the G1-ENUM data_type validity matrix + **outside the tradfi AG**
      (the schema_version provider subsystem is cefi/cross-cutting). My `uac@576f8fa8` adds ZERO net-new failures (8,617
      pass, ruff clean). Owner: the schema_version-provider/cefi AG or vm-cross-cutting — align the provider
      schema_version registry so binance reads green. Repo: unified-api-contracts. parent_epic: manifest_master.

### G2 prep status (slot-6 2026-06-07 session-2) — unblocked prep DONE; apply-ready HELD on PART A

> Operator GATE: "do NOT start the enumerate dry-run re-validation until slot-7 confirms the bundle-grain rollup is
> GREEN." PART A is **not** green (above) → the enumerate re-run + the full bundle-aware audit stay HELD. The non-gated
> prep is COMPLETE + re-verified on current LDR:
>
> - **② MTDS migrator dry-run GREEN** — `migrate_tradfi_to_v9_canonical --start-date 2021-08-16 --end-date 2021-08-17`
>   (dry, read-only): **planned=1088 L-hive objects, moved=0, 0 errors, exit 0** (path-only `pipeline_mode=` insert; the
>   v9 COLUMNS are `rebuild_tradfi_manifest`'s, not this script's). Source-aware `pipeline_mode` derivation verified per
>   venue: CME/NYSE/NASDAQ/CBOE/ICE → `batch_databento`, BARCHART → `batch_barchart`, YAHOO → `batch_yahoo`, EIA →
>   `batch_eia` (NOT coarse `batch`/blank). The migrator walks `day=` (date-bounded — no defi-style full-bucket-scan
>   timeout).
> - **③ instruments-store v9 dry-run GREEN** — 20,388-row `_index` → v9 100%, all CF stamps (see Step-1 UPDATE +
>   gate-(c)).
> - **① matrix/grain slice REVIEWED** — the exact missing tradfi rows are grounded (see the ROOT-CAUSE FINDING +
>   gate-(a) re-verify); the fix is authored-but-HELD (must co-land with PART A to avoid false-absence).
>
> **Apply-ready blockers (precise):** gate-(a) bundle-grain = **slot-7 PART A** (catalogue emits options_chain/
> futures_chain bundles) **+ the co-landing tradfi matrix rows** · gate-(b) capture-freeze = Massive `by_date` re-feed +
> catalogue regen (adapter SHIPPED, below) · gate-(c) v9 `_index` = the gated `migrate_instruments_store_v9 --apply` RUN
> (TOOL-READY) · plus G3 (UNION view — SHIPPED pm@822393880) and the operational pre-migration drain. When PART A lands,
> the remaining tradfi work is: co-land the matrix rows → re-run enumerate (expect the ~563K false-candidate drop) →
> finish the bundle-aware 7+2 audit → apply-ready verdict.

### 🟢 TradFi APPLY-READY VERDICT (slot-6, 2026-06-08) — 5/5 dry-gate criteria GREEN; remaining gates OPERATIONAL only

> **VERDICT: tradfi is APPLY-READY on LDR.** PART A (Era-B bundle rollup) landed and my last matrix slice fix shipped;
> every G1+G2 dry-run is green and the 7+2 audit passes. **No code change remains before `--apply`** — the only blockers
> are operational (the gated WRITE runs + IS backfill + the Era-B relabel that rides G4 + the pre-migration drain).

**The 5 dry-gate criteria (all GREEN):**

1. **① MTDS migrator dry-run** — `migrate_tradfi_to_v9_canonical` (dry): planned=1088 / 0 errors; source-aware
   `pipeline_mode` (CME/NYSE/NASDAQ/CBOE/ICE→`batch_databento`, BARCHART→`batch_barchart`, YAHOO→`batch_yahoo`,
   EIA→`batch_eia`); path-only insert — the v9 columns ride `rebuild_tradfi_manifest`.
2. **② Manifest-rebuild / instruments-store v9** — `migrate_instruments_store_v9 --asset-group tradfi` (is@febb899e):
   `_index` 20,388 rows → **v9 100%**, all CF stamps (`schema_version=9` · `asset_group=tradfi` ·
   `pipeline_mode=batch_instruments_service` · `source=instruments_service` · `transport=rest` · `data_type=instruments`
   · per-row `available_at` · honest 4-state 19,247 captured/1,141 empty_confirmed). cf_manifest_audit projection
   CF-GREEN (v8→v9).
3. **③ Enumerate re-validated GREEN on the Era-B bundle producer** (uac@ae70338d + is@74df991d/687d1443 + my
   uac@576f8fa8): **587,990 → 24,914 (bundle rollup) → 17,928 (future/spot_pair matrix rows)**. Report verified: **0
   per-contract OPTION/COMBO** (rolled to options_chain/futures_chain bundles, one per underlying, data_type=trades),
   **0 data_type=options_chain** candidates (Era-B trades model), **0 impossible pairs** (tradfi has no
   PERPETUAL×chain), FUTURE trimmed to its 6 real data_types (no macro/corp-action/earnings over-fan); 17,928 = exact
   Σ(alive × valid-dts × 2 days). The ~563K false per-contract candidates are GONE.
4. **④–⑦ honest-absence / read-write paths / IS+UAC guardrails / numerator-denominator** — ride the WAVE-1 code (rebuild
   typed reasons + `record_zero_rows`, A7/CF-11 fetch-failure→`attempted_failed`, batch=live single path, env-tier
   `resolve_bucket_name`); G3 UNION view SHIPPED (pm@822393880); the could-exist denominator is now accurate (enumerate
   17,928).
5. **⑧/⑨ catalogue-completeness + source-aware pipeline_mode** — `-prd-` `instrument_availability/by_date/` POPULATED
   (64,724 parquets), shape-aware + bundle-grain producer GREEN, validity+grain slice CORRECT for every tradfi
   instrument*type (option/combo→frozenset; options_chain/futures_chain→{trades}, grain=bundle_by_underlying;
   future/spot_pair→per-contract leaves); migrators stamp source-aware `batch*<source>` (NOT coarse).

**Sampled-vs-walked**: WALKED — the full 20,388-row instruments-store `_index` transform + the full 684,372-instrument
catalog + 144,062-row manifest scan in enumerate (present-set 73,352). SAMPLED — the MTDS migrator dry-run on
day=2021-08-16..17 (path+derivation; the whole-corpus walk runs on the in-region VM) + the catalogue instrument_type
distribution. **Remaining gaps**: none code-side; the candidate-count is for a 2-day window (the full-horizon seed is
the gated G1.run VM run).

**The ONLY remaining gates — ALL OPERATIONAL (no code owed):** G0 ✓ · G3 UNION view ✓ (pm@822393880) · the v9
instruments-store walk `migrate_instruments_store_v9 --asset-group tradfi --apply` RUN (TOOL-READY; dry-run proved 100%
v9) · IS backfill complete (Massive `by_date` re-feed → catalogue regen; adapter SHIPPED) · the **Era-B legacy-row
relabel rides the G4 migrator as its final atomic step** (operator decision slot-7 edca81b57 — NOT a dry-run blocker) ·
pre-migration drain. **`tradfi APPLY-READY — 5/5`.**

- [ ] [INFRA] P2. **PRE-EXISTING UAC QG RED (not tradfi; flagged slot-6 2026-06-08) — blocks the UAC `--no-fix` sentinel
      → no clean UAC quickmerge fleet-wide.** `tests/unit/test_schema_version_matrix.py` 3 failing
      (`test_green_status_when_versions_match` / `test_na_schema_version_does_not_trigger_red` /
      `test_load_providers_green_when_versions_match`): assert `binance.computed_status == "green"` but it is `"yellow"`
      (schema_version provider-status drift). **Proven PRE-EXISTING** (stash-test: fails identically on clean LDR
      without my matrix change) + **unrelated** to the G1-ENUM data_type validity matrix + **outside the tradfi AG**
      (the schema_version provider subsystem is cefi/cross-cutting). My `uac@576f8fa8` adds ZERO net-new failures (8,617
      pass, ruff clean). Owner: the schema_version-provider/cefi AG or vm-cross-cutting — align the provider
      schema_version registry so binance reads green. Repo: unified-api-contracts. parent_epic: manifest_master.

### Gate-b remediation — Massive IS reference adapter (shipped this session)

- [x] ✅ [CODE] P1. **Tradfi Massive IS reference adapter — SHIPPED + STAGING-GREEN (slot-6 2026-06-07): UAC@12974b11
      (PR #91 MERGED→staging, quality-gates-v2 PASS) + IS@c0f2f39c (PR #407 MERGED→staging, quality-gates-v2 PASS); both
      `external/massive`/`massive.py` confirmed on `origin/staging`.** make Massive the PRIMARY tradfi reference source
      (gate-b remediation for the capture freeze). Implements `proper_instrument_catalogue_lifecycle_rollup_2026_06_04`
      [CODE] P1 "(B) PRIMARY — make Massive the tradfi reference source". UAC `external/massive` (8 raw schemas
      tickers/options/futures + 5 raw→canonical `InstrumentRecord` normalizers equity/index/fx/option/futures +
      `DATA_SOURCE_TO_SECRET[massive]` / `VENUE_TO_DATA_SOURCE[MASSIVE]`); IS `MassiveReferenceDataAdapter` (Massive =
      Polygon.io API-compatible, `https://api.polygon.io`; equities/ETF/index via `/v3/reference/tickers`, index options
      via `/v3/reference/options/contracts`, FX, futures via `/futures/vX/{products,contracts}`); source-aware factory
      routing (`--source massive` re-points TradFi-Databento venues → Massive + the `MASSIVE_API_KEY` credential);
      reuses Databento's session-metadata SSOT (`EXCHANGE_HOURS`/`get_session_metadata`); fetch-failure → re-raise
      (CF-11 honest-absence, no silent universe shrink); refactor `get_adapter_for_canonical_venue` 214→198L (de-dup
      date-aware databento/massive construction). 14 IS unit tests + factory-routing tests + UAC normalize tests (live
      test credential-gated); both QG --no-fix exit 0. Repo: instruments-service + unified-api-contracts. parent_epic:
      mtds_mdps_master. **Coverage caveat (per `tradfi_massive_dual_source`):** Massive futures-reference returned
      200+empty 2026-05-30 (subscription propagation) — the adapter ships the scaffold per the External-Data rule;
      futures-reference completeness verified on the next live run.
- [ ] [DATA] P1. **NEXT — run Massive tradfi reference capture → regenerate catalogue → unblock gate-b (VM, requires
      live `MASSIVE_API_KEY`).** With the adapter shipped (above), run IS instrument capture with `--source massive` to
      refill `instrument_availability/by_date/` to today → regenerate the catalogue
      (`build_instrument_catalogue     --asset-group tradfi --apply`, monotonic guard accepts growth) → liveness no
      longer marks ~651K instruments delisted → unblocks gate-b → then G1.run `--apply-write` (Step 3) becomes runnable.
      VM-gated (live creds + per-VM shard isolation). Repo: instruments-service. parent_epic: mtds_mdps_master.

### ✅ FINAL PRE-APPLY ①–⑫ RE-VERIFICATION + AUTHORITATIVE VERDICT (slot-6 · 2026-06-08 session-4 · autonomous run)

> **VERDICT: tradfi DATA + MANIFEST `--apply` (G4) is APPLY-READY — REGRESSION RISK: NONE.** This session re-verified
> the full chain against real-prod GCS (`central-element-323112`) on the CURRENT LDR code (tab ⊇ LDR, 0 ahead/0 behind),
> resolving the one item the dispatch flagged as an open 🔴 pre-apply blocker (CF-11 `databento.py:826`) — it is
> **CLOSED ON LDR**. This is the authoritative current state; it RECONCILES the session-2 SUPERSEDED verdict (which
> missed the old-tail) and the session-3 T-OLD findings (now FIXED) into one. **HARD-STOP held: I prepared to
> dry-run-green and STOP — the operator fires `--apply`.**

**The dispatch's central concern — CF-11 — is CLOSED (re-verified on the stable remote ref, not a constant):**

- **Write-path (instruments-service)**: `reference_data/adapters/tradfi/databento.py` — BOTH the `BentoError` branch
  (L802→`raise RuntimeError` L832) AND the `data.to_df()` parse-failure branch (L838→`raise RuntimeError` L856)
  classify + emit `ADAPTER_FETCH_FAILED` then **re-raise** → `urdi_reference_provider._fetch_one`'s per-venue
  `except RuntimeError` → venue in `failed[]` → excluded from `_non_error_venues` → orchestrator `record_failed` →
  honest `attempted_failed`; a genuine empty still returns `[]` cleanly. Landed on `origin/live-defi-rollout` as
  **instruments-service@f7744fbf** ("Databento fetch-failure threads STATE (re-raise)") + **@c0f2f39c** (Massive
  source-aware factory carrying the same CF-11 re-raise). Re-verified by
  `git show origin/live-defi-rollout:…/tradfi/databento.py` (the re-raise is on LDR; my tab is 0-diff vs LDR). The stale
  "🔴 BLOCKER" framing keyed off `bd1456aa` being read as not-on-LDR — its content re-SHA'd as `f7744fbf` via
  quickmerge. Cross-AG IS adapter swallow audit also closed (`e2e008f0`).
- **Manifest-path (mtds)**: `rebuild_tradfi_manifest.reemit_honest_absence_rows` re-emits every prior-failure row v9 —
  `attempted_failed`→`record_failed(error preserved)`, `empty_confirmed`→`record_empty(typed reason)` (validated vs
  `EMPTY_CONFIRMED_REASONS`, invalid→demote to `record_failed`), and reclassifies `SOURCE_RETURNED_ZERO` **on a trading
  day**→`attempted_failed(WithinBoundsTradfiSourceZero)` while preserving weekend/holiday typed empties. Verified by
  reading the code + the 11-test suite `tests/unit/test_rebuild_tradfi_manifest_cf11.py` (covers reemit empty/failed,
  dedup-skip, trading-day reclassify, weekend-preserve, calendar-exception-preserve, direct-download fallback,
  invalid-reason-demote, dry-run-no-write).

**Fresh real-prod dry-run re-runs this session (SAMPLED windows, stated scope):**

| Run                                                                    | Window                         | Result                                                                                                                                                                                                                                                                                                                                                                                  |
| ---------------------------------------------------------------------- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `migrate_tradfi_to_v9_canonical --dry-run` (recent)                    | day=2026-05-12..18             | L-hive **planned=984, moved=0, 0 skipped, 0 errors** (candles 0, L-hyphen 0). Source-aware `pipeline_mode=batch_<source>` derivation per venue.                                                                                                                                                                                                                                         |
| `migrate_tradfi_to_v9_canonical --dry-run` (OLD-TAIL, T-OLD re-verify) | day=2023-05-01..02             | L-hive **planned=3,360, moved=0, 0 skipped, 0 errors** → the `category=`→`asset_group=` re-derivation (T-OLD-1/2 fix, mtds@51c604a4) holds: **no old-tail orphans**.                                                                                                                                                                                                                    |
| `rebuild_tradfi_manifest --dry-run` (object-scan)                      | day=2026-05-12..18             | **984 shards, 0 unparseable, 0 skipped_hyphen**, source-aware `pipeline_mode` stamped (`batch_databento` for CME/NYSE/NASDAQ/CBOE; VIX→`batch_databento`). CF-11 re-emit path present (no-op under `CLOUD_PROVIDER=local` mock — env artifact; logic proven by unit tests + real-`_index` re-run).                                                                                      |
| Era-B byte-probe                                                       | day=2026-05-18 (+ 05-15/05-01) | chains present only as `instrument_type=futures_chain`/`combo` with `data_type=trades`/`ohlcv_1m`; **`data_type=(options_chain\|futures_chain)` count = 0** (Era-B clean).                                                                                                                                                                                                              |
| `cf_manifest_audit` on `market-data-tick-tradfi-prd/_index`            | 144,062 rows                   | reads data-state honestly (NOT the constant): CF-1 v9=0% / CF-3 pipeline_mode blank / CF-4 source absent / CF-8 available_at absent — the **expected PRE-apply v8 state**; CF-2 asset_group GREEN; CF-5 typed-reasons GREEN (EXPECTED_WEEKEND 35,050 / HOLIDAY 2,427 / OUT_OF_COVERAGE 8 / SOURCE_RETURNED_ZERO 5). The migrator+rebuild convert these to v9/source-aware AT `--apply`. |

**Consolidated ①–⑫ — REGRESSION RISK: NONE** (per-point evidence in the session-2 table above; this session re-confirmed
① recent+old-tail dry-runs clean, ② rebuild object-scan clean + re-emit unit-proven, ⑨ source-aware on disk, ⑩ Era-B
count=0, ⑪ batch=live single derivation path, ⑫ rollback snapshot `pre_migration_2026_06_08.parquet` present + phantom
`prefix_tpls` fixed is@5e8d192d; CF-11 ④/③ CLOSED above). The T-OLD-2c content-aware attribution script
(`attribute_tradfi_needs_attribution.py` + its 5-test suite) is **test-green (5/5) + ruff/basedpyright-clean**, landed
this session as a separate mtds code commit (see the T-OLD-2c todo flip) so the migrator's preserved-but-unattributed
legacy objects have their post-apply resolver. (T-OLD-2c is a POST-apply tool — it runs after `--apply`; it does NOT
gate the dry-run.)

**Remaining gates — ALL OPERATIONAL (no code owed before `--apply`):** the full-corpus `--apply` (with `--also-legacy`
per R1) + the gated delete-after sweep (R2) + `migrate_instruments_store_v9 --asset-group tradfi --apply` run + IS
Massive backfill→catalogue regen + pre-migration drain (already EXECUTED 2026-06-08 per the coordinator). The cross-AG
G1.run-SEED denominator finding (⑥/⑦, T-OLD-2b matrix widening) is slot-7-owned and does **not** gate G4. **STOP before
`--apply`.**
