---
title:
  "MASTER COORDINATOR — data + manifest + schema migration + IS catalogue + pipeline_mode standardisation (single-pane
  dependency-gated sequencer for the whole data-layer cutover)"
created: 2026-06-07
parent_epic: epics/manifest_master.md
assigned_vm: vm-cross-cutting
status: active
priority: P0
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
locked_by: live-defi-rollout
locked_since: 2026-06-07
source:
  - operator 2026-06-07 ("coordinated master plan around data/manifest/schema migrations + IS catalogue; attach all plan
    todos; block on upstream readiness; no orphans")
  - pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md (the Phase-0 apply-gate)
  - proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md (the could-exist-universe foundation)
---

# MASTER COORDINATOR — Data-Layer Canonicalisation, Migration, Catalogue & Pipeline-Mode Cutover

> **Role (operator 2026-06-07): a PURE COORDINATOR — it tracks, gates, and links; it executes nothing.** Every line of
> code, every migration `--apply`, every audit lives in the registered sub-plans below. This plan is the single pane of
> glass: the global dependency DAG that blocks each gate on its upstream being GREEN, the sub-plan registry, the audit
> framework, and the orphan sweep. It is **data-layer only** — it cross-links `master_to_live_defi_2026_05_23.md` (the
> live-cutover master) as the **downstream consumer**, it does not own live promotion.
>
> **Coordinator non-duplication (HARD)**: this REPLACES scattered coordination. The DeFi plan's `## MASTER` section is
> demoted to a DeFi executor that points UP here; the `pipeline_mode_source…standardisation` plan keeps its Phase-0
> apply-gate but is registered as G0 here. No third coordinator — if you find cross-plan sequencing anywhere else, fold
> its links into THIS registry.

## The governing sequence — 6 dependency gates (operator's end-to-end order)

```
G0  Foundation MODEL + code + doc/codex/plan coherence   ─┐  (cross-cutting; gates ALL applies)
G1  IS CATALOGUE foundation (could-exist universe SSOT)   ─┤→ both GREEN before any per-AG dry-run is trustworthy
G2  Per-AG migration/manifest/schema scripts updated      ─┘     + 7+2-point AUDIT + DRY-RUN green (per AG)
G3  Manifest consolidation + deployment-API/UI UNION view + pipeline_mode drilldowns
G4  Per-AG --apply (manifest + data/schema migration)   ← GATED on G0,G1,G2,G3 GREEN + pre-migration drain
G5  Resume BACKFILLS → 100% honest coverage (UI drilldowns shrink to minor) + massive/polygon cost-swap vs databento
                                                          ↓
                                  master_to_live_defi_2026_05_23.md  (live promotion — downstream)
```

**Single hardest invariant (from the standardisation plan, restated as the master gate):** **NO `--apply`
data/manifest/schema migration runs until G0 + G1 + G2 + G3 are GREEN.** The walk bakes in whatever model exists at
apply-time; fixing a wrong model needs a banned second whole-corpus walk (single-walk discipline). The current migrators
stamp **coarse `pipeline_mode="batch"`** (or blank — defi rebuild `:302`); the canonical target is **source-aware
`{mode}_{source}[_{transport}]`** — so every migrator/rebuild/enumerator MUST be upgraded in G0/G2 BEFORE its AG's G4
apply.

## 🟢 Dispatch waves (live — who owns what NOW)

Slot map: **2=DeFi · 3=CeFi · 4=Sports · 5=Prediction · 6=TradFi · 7=cross-cutting**.

**WAVE 1 — IN FLIGHT (launched 2026-06-07): close G0 all-AG + launch G1 all-AG.**

| Slot | Gate          | Scope (in flight)                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ---- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 7    | G0 + G1-found | C-PATH READ (features/mdps readers prefix-match) + doc reconcile (#7/M-COORD-1) + G1 FOUNDATION (`build_instrument_catalogue` + `enumerate_expected_universe` v2 all-AG-capable + daily scheduler per AG). **RE-SCOPED 2026-06-07: the v2 producer MUST be instrument-shape-aware — `(instrument_type × data_type)` validity filter + bundle-grain (G1-ENUM, P0) — NOT generic fan-out** (else false `expected_unattempted` pollution; see G1-expanded) |
| 2    | G0 + G1-defi  | C-PATH WRITE (`migrate_defi`/`rebuild_defi` → `derive_pipeline_mode_for_row`; last coarse writer) + DeFi IS-catalogue (dry-run now; run gated on slot-7 code + DeFi IS backfill)                                                                                                                                                                                                                                                                        |
| 3    | G1-cefi       | CeFi instruments-store v9 + catalogue run (dry-run proven 2026-06-05) + scheduler                                                                                                                                                                                                                                                                                                                                                                       |
| 4    | G1-sports     | Sports instruments-store v9 + fixtures/leagues could-exist + catalogue run + scheduler                                                                                                                                                                                                                                                                                                                                                                  |
| 5    | G1-prediction | Prediction instruments-store v9 + polymarket-market could-exist + catalogue run + scheduler                                                                                                                                                                                                                                                                                                                                                             |
| 6    | G1-tradfi     | TradFi instruments-store v9 + listed-contracts-per-session could-exist + catalogue run + scheduler                                                                                                                                                                                                                                                                                                                                                      |

Intra-wave gate: slot-7 G1-foundation code is the prerequisite for slots 2–6 catalogue **runs** (dry-runs are
unblocked); per-AG `--apply-write` seed also gated on that AG's IS backfill complete + accurate UAC. G0 read/docs are
parallel-safe.

**WAVE 2 (after G0+G1 green)** — G2 per-AG dry-run + 7+2-point audit (one slot each) → **WAVE 3** G3 UNION UI (slot 7) →
**WAVE 4** G4 per-AG `--apply` (gated G0∧G1∧G2∧G3 + drain) → **WAVE 5** G5 backfills→100% + cost-swap. Live-side
(M3/M4/M6/M7 · `live_websocket`→`live_<source>` · M8 cadence) = tracked parallel track, after the batch migration.

> **🟢 G3-CONSUMER — deployment-api/UI UNION read path SHIPPED 2026-06-07 (vm-cross-cutting / slot-7)**: the data-status
> CONSUMER is now honest for the post-migration v9 multi-row manifest (reads the v9 contract; fixture-tested — does NOT
> need the data migrated yet). **`deployment-api@4dd2575`**: new `data_status_union.union_reduce_to_cells` collapses
> each cell's multi-(source × pipeline_mode) rows to ONE honest `capture_status` via the **M5 union rule** (≥1
> source/mode `captured` ⇒ cell `captured`; status precedence captured>empty>failed>expected; known-empty > pending),
> wired into the panel rollup (`_compute_capture_status_counts`) + the hierarchical `_aggregate_counts` so the 4-state
> counts are CELL-grain (no double-count across provenance rows; v8 manifests unchanged — guarded on the provenance
> columns). Coverage % = `captured / (captured+empty+failed+expected_unattempted)` over the could-exist denominator
> (READ, never re-derived per CF-14). **DRILLDOWN** (`deployment-api@4dd2575`): per-(pipeline_mode × source) breakdown
> at shard-atom leaves (a cell shows e.g. captured via `batch_databento` + `replay_databento`, missing in
> `live_databento`) + `pipeline_mode`/`source` as filter AND `group_by` axes + a top-level provenance summary.
> **deployment-ui** `HierarchicalShardDrilldown` renders the pipeline_mode/source breakdown + the 4-state
> (**`deployment-ui@0dc40eb`**) — **UI tick stays [BLOCKED-PLAYWRIGHT]** (pw:L2 pending on a UI-capable slot;
> regression: `src/components/HierarchicalShardDrilldown.test.tsx`). **M5 + the M4 data-status portion (mode-agnostic
> UNION; the live `select_for_mode` precedence stays OPEN in batch-live-reconciliation-service — live-side track) are
> DONE on the CONSUMER side** (G0-plan M5 row annotated PARTIAL — the `cadence` dimension + unified-trading-system-ui
> parity remain). Tests: deployment-api `test_data_status_union.py` + `test_data_status_drilldown_provenance.py`
> (QG-green) · UI vitest 766 green. **Landed on LDR via the tab-mirror; the LDR→staging promotion is dep-tier-gated on
> deployment-service reaching STAGING_GREEN — NOT bypassed** (`--skip-dep-tier-gate` is agent-forbidden). Out of scope
> (gated): the live read-path precedence service M4 in batch-live-reconciliation-service; the actual `--apply`;
> M3/M6/M7.

## ⚠️ CONFLICTS SURFACED + RESOLVED (the coordinator's job — track + resolve, do not let them reach `--apply`)

> The whole point of this coordinator is to catch where existing code/docs CONTRADICT the ratified source-aware model
> and resolve them BEFORE the irreversible single-walk apply. **Full repo sweep done 2026-06-07** (grep
> `pipeline_mode=(batch|live)` / `DEFAULT_PIPELINE_MODE` / `derive_pipeline_mode_for_row` across all repos). **The
> headline finding overturned my own framing**: the source-aware `pipeline_mode=batch_<source>/` path key is ALREADY the
> live convention for **cefi / tradfi / sports / prediction** (their `rebuild_*_manifest` + `migrate_tradfi`/sports use
> UTL `derive_pipeline_mode_for_row(venue, ag, data_type)` → `batch_<source>`; UTL `pipeline_mode_resolver` already
> bridges the coarse "batch" input → `batch_<source>` output for batch). **DeFi is the lone coarse outlier**, and a few
> DeFi-scoped readers/tests/docs still assume coarse. So C-PATH is NOT "every AG" — it is concentrated + tractable.

**C-PATH inventory (categorized; ✓ = already source-aware, ✗ = coarse conflict):**

| Class              | Site                                                                                                                                                                                                                                   | State  | Fix / owner                                                                                                                                                                                             |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| WRITE migrator     | `migrate_tradfi_to_v9_canonical.py` (`_pipeline_mode`→`batch_databento`)                                                                                                                                                               | ✓      | reference impl — copy this pattern                                                                                                                                                                      |
| WRITE rebuild      | `rebuild_{cefi,tradfi,sports,prediction}_manifest*` (`derive_pipeline_mode_for_row`)                                                                                                                                                   | ✓      | reference impl                                                                                                                                                                                          |
| **WRITE migrator** | **`migrate_defi_full_v9_canonical.py:70/700/714`** `DEFAULT_PIPELINE_MODE="batch"` → coarse path+col                                                                                                                                   | **✅** | **DONE mtds@f80c50f1** — `batch_<source>` per shard via `derive_pipeline_mode_for_row`; source+transport in path+column; coarse retired                                                                 |
| **WRITE rebuild**  | **`rebuild_defi_manifest.py:88/206/230/250`** `_DEFAULT_PIPELINE_MODE="batch"` (+ `:302` blank — C-#1)                                                                                                                                 | **✅** | **DONE mtds@f80c50f1** — `derive_pipeline_mode_for_row` source-aware (path+col), `pipeline_mode=` day-probe, per-shard isolation; C-#1 `:302` fixed                                                     |
| READ (defi)        | features `mtds_canonical_reader.py` — was exact `pipeline_mode=batch/`+`live/` probe                                                                                                                                                   | ✅     | **DONE features@c487e04b** — day-level mode-agnostic listing, prefix-match `batch_*/live_*/replay_*` + bare + legacy `category=`, canonical-over-legacy ranked                                          |
| READ               | mdps `orchestration_scanner.py` — day-listing already mode-agnostic; FIXED source-aware leak bug                                                                                                                                       | ✅     | **DONE mdps@d59749c (PR#103→staging)** — gated `batch_onchain_rpc` legacy-venue branch on absence of `data_type=` (canonical `dex_pool_state` no longer leaks into `dex_swaps`); +source-aware fixtures |
| TEST               | mtds `test_migrate_defi_full_v9_canonical.py:53-54` · `test_rebuild_defi_manifest.py:17/72` · mdps `test_orchestration_scanner.py:182-230` · features `test_mtds_canonical_reader.py:63-132`                                           | ◑      | **mtds DONE mtds@f80c50f1** (both defi test files assert `batch_<source>` + source/transport, 25/25 green); mdps/features test updates ride their READ change (features@c487e04b / mdps@d59749c)        |
| LIVE (all AGs)     | UTL `pipeline_mode_resolver.py:123` live → `LIVE_WEBSOCKET` (not `live_<source>`)                                                                                                                                                      | ~      | the M1 `live_<source>` OBJECT migration = **gated next tranche** (C-#5) — NOT part of the batch migration                                                                                               |
| DOC ✓              | CLAUDE.md:568 · SUB_AGENT_MANDATORY_RULES:276 · most AG plans · deployment-api/data_status                                                                                                                                             | ✓      | already `batch_*/`                                                                                                                                                                                      |
| DOC ✗              | `defi_manifest_canonicalisation_2026_06_01.md` (many coarse `pipeline_mode=batch/`) · codex `pipeline-mode-partition.md` (mixed) · audit `defi_object_path_canonicalisation_2026_06_01.py:87` · `pipeline_mode_partition_migration:63` | ✗      | reconcile to `batch_<source>` (rides M-COORD-1)                                                                                                                                                         |
| BY-DESIGN          | codex `batch-live-architecture.md:466` + `instruments-live-architecture.md:30` — instruments reference data has **NO `pipeline_mode=live` partition** (live writes the identical batch path)                                           | ✓      | keep — a real exception, not a conflict                                                                                                                                                                 |

**RESOLUTION (HARD, single-walk)**: bring the DeFi migrator + rebuild to the cefi/tradfi pattern
(`derive_pipeline_mode_for_row` → `batch_<source>` in path + column, same C0 walk — a coarse apply + later re-walk = the
banned second whole-corpus walk); flip the 2 DeFi-scoped readers + the 4 tests to prefix-match `batch_*/`; reconcile the
coarse doc stragglers (M-COORD-1). The live→`live_<source>` object migration is the separate gated tranche.

**Other standardisation findings:**

- ✅ **C-#2 (UTL) — RESOLVED 2026-06-07 (utl@d0745bde)**: `ManifestWriter.add()` now AUTO-DERIVES `pipeline_mode` via
  `derive_pipeline_mode_for_row` for a derivable market-data row (venue+data_type, no feature_group) — blank can no
  longer pass silently; features/service rows keep `""`. (The DeFi rebuild `#1` stamp itself is still vm-defi's.)
- ✅ **C-#6 (UTL) — RESOLVED 2026-06-07 (utl@d0745bde)**: `_assert_source_matches_pipeline_mode` raises
  `PipelineModeSourceMismatchError` when an EXPLICIT batch `source` disagrees with `source_string_for(pipeline_mode)`
  (`batch_databento` + `source="massive"`), in record_captured / record_captured_from_counts / add() (gated on an
  explicit caller-provided source — auto-stamped single-source cells are correct-by-construction).
- ✅ **C-TRANSPORT (P0) — RESOLVED 2026-06-07 (operator R4)**: (1) the `hyperliquid_rest` antipattern is retired in the
  enum (uac@cc69b123: `BATCH_HYPERLIQUID` + the unified-vendor `LIVE/REPLAY_HYPERLIQUID`; `Transport` enum +
  `transport_of`
  - `default_transport_for_source`); the `transport` manifest COLUMN landed (utl@d0745bde) + is stamped by IS seeds
    (is@03a93e10) + the consumer sweep renamed `hyperliquid_rest`→`hyperliquid` (mtds@c567962e). (2) codex
    `02-data/pipeline-mode-partition.md` reconciled (pm@9120464fe). (3) R4 ratified by operator. REMAINING: the UI
    reference-data regen (gated on the UI playwright gate — see the standardisation plan) + the other codex docs
    (`pipeline-mode-and-batch-live-reconciliation.md` still has `hyperliquid_rest` refs) ride the #7 doc audit. The
    `live_websocket`→`live_<source>` OBJECT migration stays the separate gated tranche.
- **C-TRANSPORT (original write-up, surfaced by operator 2026-06-07) — the optional `[_{transport}]` suffix is
  under-specified + inconsistently implemented + undocumented in codex.** The M1 form is `{mode}_{source}[_{transport}]`
  with `transport ∈ {rest, websocket, flat_file}`, BUT:
  1. **Antipattern in the SHIPPED enum**: `BATCH_HYPERLIQUID_REST="batch_hyperliquid_rest"` (+ LIVE/REPLAY) glue the
     transport INTO the source name — the standardisation plan (lines 125-126) explicitly names this "the M1
     antipattern; target `hyperliquid` + transport". The new enum (uac@8cafb758/6cd08c89) carried it forward. **Fix**:
     split → source=`hyperliquid`, transport=`rest` as a separate trailing segment/column. Owner: vm-cross-cutting
     (UAC).
  2. **codex `02-data/pipeline-mode-partition.md` is STALE + silent on transport**: documents only
     `{batch_*, live_websocket}`, says "Don't use `pipeline_mode=replay_*`" + "replay writes to `live_websocket`" —
     directly contradicts the M1 source-aware + `replay_<source>` + transport model. Owner: M-COORD-1 (doc reconcile) —
     rewrite to the `{mode}_{source}[_{transport}]` form incl. replay + the transport-suffix rule.
  3. **Suffix policy NOT ratified** (operator residual ○): line 95 leaves "transport as a trailing path/enum segment
     (`live_tardis_websocket`) vs a column" as an "Open fork" with a recommendation only — **carry the transport suffix
     in the path key ONLY where a source genuinely runs >1 transport for the SAME shard (else noise), AND also as a
     `transport` column** (line 216). Needs operator ratification before the migrators encode it.

  **Operator residual R4 — ratify the transport rule**: (a) transport suffix in `pipeline_mode` path key only when a
  source has >1 transport per shard (else omit); (b) always populate a separate `transport` column; (c) split the
  `hyperliquid_rest` source → `hyperliquid` + transport=`rest`. Recommend yes to all three (matches the M1
  recommendation + kills the antipattern). Until ratified, the DeFi/per-AG migrators stamp `{mode}_{source}` WITHOUT a
  transport suffix (safe subset — adding the suffix later for a genuine >1-transport source is additive, not a re-walk).

## Sub-plan registry (every data-layer plan, its gate, owner, blocked-until)

> Status is coarse (`see plan` for detail). The value here is the GATE + the BLOCKED-UNTIL edge. Owner = `assigned_vm`.

| Gate   | Plan / issue                                                                                                                                                                                                | Role                                                                                                                                    | Owner                     | Blocked-until (upstream)                            |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- | --------------------------------------------------- |
| **G0** | `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`                                                                                                                                         | **THE model + apply-gate** (batch/live/replay × source × transport; M2/M3 registries; M4 precedence; cont. contract; 0.8 doc reconcile) | vm-cross-cutting          | — (root; Phase-0 code must go GREEN)                |
| G0     | `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01`                                                                                                                                                 | canonical bucket SSOT (env-tier readers/writers) + L6 decommission                                                                      | vm-cross-cutting          | partly done; L6 ⟶ G4                                |
| G0     | `data_source_provenance_all_asset_groups_2026_06_01`                                                                                                                                                        | `source` column — RIDES each AG's single-walk                                                                                           | per-AG                    | G0 model (source-aware) ratified ✓                  |
| G0     | `pipeline_mode_partition_migration_2026_06_01`                                                                                                                                                              | on-disk `pipeline_mode=` partition — RIDES each AG walk                                                                                 | per-AG                    | G0 model form (M1) locked                           |
| G0     | `manifest_reader_fail_fast_on_stale_fallback_2026_05_28`                                                                                                                                                    | reader fail-fast default + consolidator liveness (no legacy fallback)                                                                   | vm-cross-cutting          | parallel-safe                                       |
| **G1** | `proper_instrument_catalogue_lifecycle_rollup_2026_06_04`                                                                                                                                                   | **could-exist-universe SSOT** — `build_instrument_catalogue` roll-up + daily scheduler + v2-enumerator recurring run                    | vm-cross-cutting          | `instruments_manifest_canon` (IS indices canonical) |
| G1     | `instruments_manifest_canonicalisation_2026_06_01`                                                                                                                                                          | IS reference/instrument `_index` canonical (all AG)                                                                                     | per-AG slice              | G0                                                  |
| G1     | `instruments_backfill_phase3_2026_05_22`                                                                                                                                                                    | IS reference backfill                                                                                                                   | vm-cross-cutting          | G1 catalogue GREEN ⟶ G5                             |
| **G2** | `defi_manifest_canonicalisation_2026_06_01`                                                                                                                                                                 | DeFi MTDS single-walk + §A–H executor                                                                                                   | vm-defi (slot-2)          | G0 + G1                                             |
| G2     | `cefi_manifest_canonicalisation_2026_06_01`                                                                                                                                                                 | CeFi single-walk                                                                                                                        | vm-cefi (slot-3)          | G0 + G1                                             |
| G2     | `sports_manifest_canonicalisation_2026_06_01`                                                                                                                                                               | Sports single-walk (+ fixtures/transfer-window reasons)                                                                                 | vm-sports (slot-4)        | G0 + G1                                             |
| G2     | `prediction_manifest_canonicalisation_2026_06_01`                                                                                                                                                           | Prediction single-walk                                                                                                                  | vm-prediction (slot-5)    | G0 + G1                                             |
| G2     | `tradfi_manifest_canonicalisation_2026_06_01`                                                                                                                                                               | TradFi single-walk (v9 + partition + source re-consol)                                                                                  | vm-tradfi (slot-6)        | G0 + G1                                             |
| G2     | `downstream_services_manifest_canonicalisation_2026_06_01`                                                                                                                                                  | MDPS/features/strategy/execution `_index` canonical                                                                                     | vm-ml                     | G0 + G1 + the AG MTDS walks                         |
| G2     | `solana_defi_legacy_migration_2026_05_27`                                                                                                                                                                   | DeFi Solana legacy→canonical (serialise with defi §C)                                                                                   | vm-defi                   | defi G2 single-walk                                 |
| G2     | `features_input_manifest_migration_2026_05_25`                                                                                                                                                              | features input `_index` migration                                                                                                       | vm-ml                     | G0 + downstream                                     |
| G2     | issue `defi_code_codex_drift_2026_05_27`                                                                                                                                                                    | DeFi code↔codex drift (wrapped by defi plan §A/§F)                                                                                      | vm-defi                   | wrapped → defi G2                                   |
| G2     | issue `features_service_defi_data_loading_blockers_2026_05_29`                                                                                                                                              | features DeFi e2e data-layer (wrapped by defi §C0/§D)                                                                                   | vm-defi/vm-ml             | defi G2 + downstream                                |
| G2     | issue `cefi_processed_candles_manifest_file_disconnect_2026_05_25`                                                                                                                                          | CeFi processed-candles manifest disconnect                                                                                              | vm-cefi                   | cefi G2                                             |
| **G3** | (data-status §B in each per-AG plan) + **M5** in the G0 plan                                                                                                                                                | deployment-api/UI = ONE UNION view across pipeline modes + 4-state + pipeline_mode/source drilldowns                                    | vm-cross-cutting + per-AG | G0 (M5) + G2 readers union-aware                    |
| **G4** | per-AG `*_manifest_canonicalisation` **`--apply`** items + `bucket_name_ssot` L6 delete                                                                                                                     | irreversible manifest + data/schema migration                                                                                           | per-AG                    | **G0 ∧ G1 ∧ G2 ∧ G3 ∧ pre-migration drain**         |
| **G5** | `mtds_backfill_phase3` · `mdps_backfill_phase3` · `features_backfill_phase3` · `instruments_backfill_phase3` · `aws_cloud_toggle_and_backfill_parity_2026_05_22`                                            | resume backfills → 100% honest coverage; massive/polygon-vs-databento cost-swap                                                         | per-AG                    | **G4 GREEN for that AG**                            |
| ∥      | `ci_canonical_v2_migration_2026_05_29` · `mdps_pure_polars_migration_2026_05_28` · `global_ledger_pnl_attribution_migration_2026_06_01` · `planning_vm_canonical_bringup_and_topology_reconcile_2026_06_05` | parallel infra/CI/ledger — tracked, NOT on the migration critical path                                                                  | various                   | parallel-safe                                       |

## G1 expanded — IS catalogue is the ROOT of all missing-data understanding (operator 2026-06-07)

> **IS (instruments-service) + UAC together define the could-exist universe — every downstream honest denominator,
> preflight (⑥/⑦), and `expected_unattempted` seed reads it. If IS or UAC is wrong, EVERY AG's coverage % is wrong.** So
> G1 is gated, and its catalogue has a full code → dry-run → real-run → schedule lifecycle, tracked per-AG.

> **🟢 G1-ENUM — CODE SHIPPED 2026-06-07 (vm-cross-cutting / slot-7)**: the shape-aware producer is live — UAC validity
> matrix `uac@97c26dbe` (`valid_data_types_for_instrument_type` + `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`, defi
> lazily derived from `PROTOCOL_CAPABILITIES`, uncertain rows flagged for AG owners) + instruments-service enumerator
> `is@6ea46565` (`_row_data_types` filters every `_enumerate_v2_*` to valid pairs + preserves prediction grain-binding;
> cefi OPTION/COMBO leaves → zero per-leaf rows; impossible combos excluded; +12 IS / +32 UAC tests, both repos QG
> green). **Unblocks slots 2-6 G1.run** (each AG owner still verifies its matrix slice + re-runs its dry-run against the
> shape-aware producer before `--apply-write`). Original finding ↓ retained for context.
>
> **✅ DECISION (operator 2026-06-07) — ERA-B is canonical for `options_chain`/`futures_chain` (cefi + tradfi).** They
> are **INSTRUMENT_TYPES**, with `data_type=trades`, bundled per-underlying — matching the live writer
> (`tardis_shared.py` Phase 1.6, which explicitly fixed the data_type/instrument_type overload) and the on-disk object
> paths. Era-A (these as data_types) in the UAC validity matrix + `SOURCE_PRIORITY` +
> `capability_declarations/_cefi.py` + the v8 manifest + the `test_cefi_options_chain_bundle` test is **LEGACY/stale** →
> reconcile UP to Era-B in the v9 migration (the data is already Era-B). This RESOLVES the bundle-grain blocker: the
> catalogue/enumerate bundle-grain rollup is built Era-B-shaped (one `options_chain`/`futures_chain` candidate per
> underlying instrument, `data_type=trades`), NOT a per-contract or data_type=options_chain shape. **Coordinated change
> (owner: vm-cross-cutting)**: matrix + SOURCE_PRIORITY
>
> - capability_declarations + catalogue producer + the Era-A test, in lockstep; each AG (cefi slot-3 / tradfi slot-6)
>   flips its matrix slice + re-runs G2. Gates cefi + tradfi apply-readiness.

> **🔴 G1-ENUM (P0, CROSS-AG, surfaced by slot-3 cefi dry-run 2026-06-07) — the v2 enumerator over-fans → false
> `expected_unattempted` pollution.** `_enumerate_v2_*` (`enumerate_expected_universe.py`) fans ALL data*types over
> EVERY instrument with **no `(instrument_type × data_type)` validity filter and no bundle-grain handling**. cefi
> ground-truth: options/futures are captured as per-underlying `options_chain`/`futures_chain` BUNDLES (~0 per-OPTION /
> per-COMBO rows), yet the catalog has 72,156 OPTION + 17,472 COMBO → `OPTION/COMBO × 7 data_types` never match the
> present-set + impossible combos (`PERPETUAL × options_chain`). An `--apply-write` now would seed **millions of false
> `expected_unattempted` rows → distort the exact denominator G1 exists to make honest.** The dry-run caught it
> pre-write. **This is the SAME root as slot-4's sports finding** (generic producer is fixture-grain, sports atom is
> league-grain; prediction already solved it with a per-cqg granularity-aware producer). **Cross-AG**: the
> `for dt in data_types` no-filter pattern is in EVERY
> `\_enumerate_v2*\*`. **FIX (owner: slot-7 G1-foundation in instruments-service)**: the generic producer becomes instrument-shape-aware — `(instrument_type
> ×
> data_type)`validity filter + bundle-grain (mirror the prediction per-cqg producer); **each AG owner (slots 2-6) verifies their slice** before any G1.run apply-write. **Gates every AG's`--apply-write`seed** (a G1 prerequisite). Tracked: P0 in cefi plan + must land in`proper_instrument_catalogue_lifecycle_rollup_2026_06_04`
> (central fix) + a verify-slice todo in each AG plan. **Re-scopes WAVE-1 slot-7**: the "generic foundation" must be
> AG-shape-aware, NOT one-size fan-out.
>
> **✅ G1-V8 (P0, cross-AG, the SECOND G1 long pole): the instruments-store v9 MIGRATOR IS BUILT 2026-06-07
> (`is@febb899e`) + dry-run-green for all 5 AGs — see "Two G1 long poles" item 2 below. The `--apply` RUN stays G4-gated
> per-AG. Historical context (now RESOLVED):** Confirmed v8 across **cefi (100% v8), sports (v8), tradfi (0.8% v9 /
> 20,218 rows v8)** — and slot-6 found the fix is "a gated G4-class single-walk `--apply` with **no migrator built yet**
> (instruments*manifest **E2**, vm-cross-cutting)". So gate-c (v9 `_index`) is UNMET for every AG **because the tool to
> fix it hasn't been written**. This gates EVERY AG's G1.run apply-write alongside G1-ENUM. **Owner: vm-cross-cutting
> must BUILD the `instruments_manifest` E2 v9 single-walk migrator**
> (asset_group=/pipeline_mode=batch*<source>/source/transport/ available_at/typed data_type) for the instruments-store
> buckets — the analogue of the per-AG MTDS migrators, which don't exist for the IS reference surface. Until it lands,
> no AG's instruments-store goes v9 → no honest G1 seed. Tracked: `instruments_manifest_canonicalisation_2026_06_01`
> (must spawn the E2 migrator) + each AG plan's §H.

**Two G1 long poles gate every AG's `--apply-write` seed (both cross-cutting, both must land first):**

1. ✅ **G1-ENUM — CODE DONE 2026-06-07** (`uac@97c26dbe` matrix + `is@6ea46565` shape-aware
   `enumerate_expected_universe` producer; validity filter + bundle-grain; tests green). Per-AG slice verification +
   dry-run re-run still owed by each AG owner before `--apply-write`.
2. ✅ **G1-V8 — MIGRATOR BUILT + DRY-RUN GREEN (all 5 AGs) 2026-06-07** (`is@febb899e`,
   `instruments-service/scripts/migrate_instruments_store_v9.py`). AG-parametric single-walk that rewrites BOTH the
   instruments-store `_index` rows AND object paths to canonical v9 (CF-1 v9 · CF-2 `asset_group=` · CF-3
   `pipeline_mode=batch_instruments_service` · CF-4 `source=instruments_service` · CF-TRANSPORT `transport=rest` · CF-5
   typed reasons · CF-7 `data_type` · CF-8 `available_at` · CF-9 `resolve_bucket_name` · CF-10 honest `capture_status`
   from `instrument_count`). DRY-RUN validated on all 5 real prod `_index` files (cefi/defi/tradfi/sports/prediction →
   100% v9 projection). 14 credential-free unit tests; QG `--no-fix` exit 0. The `--apply` RUN stays G4-gated
   (coordinator G0 + Phase-0 writer-code + pre-migration drain; each AG owner runs its bucket's `--apply`). Sports is
   structural-only (its `capture_status`/reasons are enumerator-authoritative → sports plan owns the relabel). So gate-c
   (v9 `_index`) is now **TOOL-READY** for every AG; what remains is each AG's gated `--apply` run.

**Per-AG G1 status (WAVE-1 dry-runs):**

- **cefi (slot-3)**: **G2 VERIFY RE-RUN DONE on the shape-aware producer (2026-06-07)** — migrator + rebuild +
  instruments-store-v9 dry-runs GREEN (source-aware `batch_tardis` paths, writer-stamped v9 columns, 30,803 IS rows→100%
  v9); `enumerate v2` exit 0 = **3,446 plausible candidates** (OPTION 141K + COMBO 64.8K correctly bundle-skipped via
  `frozenset()` → the G1-ENUM over-fan is FIXED for cefi options/combos; no impossible combos). **2 residual could-exist
  findings gate G1.run apply-write**: 🔴 **F1 RESOLVED via writer SSOT** — `tardis_shared.py` Phase-1.6 makes **Era-B
  canonical** (chain = `instrument_type`; `data_type` is pure market-data → the object PATH `data_type=trades` + the
  rebuild are CORRECT; the v8-manifest + UAC-matrix `data_type=<chain>` are the legacy **Era-A** overload Phase-1.6
  banned; the "12 phantoms" are stale Era-A rows → DROP not demote). It is a **deliberate, TESTED** Era-A↔Era-B conflict
  (UAC matrix + 2 asserting tests vs writer) spanning **cefi+tradfi+slot-7 catalogue** → operator/slot-7 Era decision,
  landed as ONE coherent matrix↔catalogue↔manifest change (recommend Era-B). 🔴 **F2** DERIBIT/OKX `FUTURE` captured at
  `futures_chain` BUNDLE grain but enumerated per-contract (~160/2-day false `expected_unattempted`; venue-specific →
  catalogue rollup, NOT a matrix flip — BYBIT has per-contract `future`). Same class as tradfi/sports. **Matrix SLICE is
  AG-owner's; catalogue producer is slot-7 PART A (NOT shipped — no in-flight PR). cefi is NOT apply-ready: BLOCKED on
  PART A + the Era decision.** Migrators re-confirmed GREEN post `hyperliquid_rest→hyperliquid` rename (mtds@c567962e).
  Full write-up + P0 todos in `cefi_manifest_canonicalisation_2026_06_01.md` § "G2 VERIFY PASS". 🟢 G3 UNION view
  SHIPPED (one operational gate cleared). gate-c (v9) tool-ready via G1-V8.
- **sports (slot-4)**: **WAVE-2 dry-runs GREEN (2026-06-07)** — G1-ENUM league-grain producer DONE (is@99a5fbf5) +
  AG-specific producer present; **fixed a real G1-ENUM bug: the UAC `("sports","league")` validity slice silently
  dropped `ODDS` → now derived from `SPORTS_DATA_TYPE_TO_SOURCE` (uac@aff80339/PR#95)**. G1-V8 instruments-store v9
  dry-run GREEN (2.68M → 100% v9, `asset_group`/`source`/`transport`/`available_at` all stamped,
  `pipeline_mode=batch_<source>`). MTDS migrator object-path dry-run GREEN (source-aware `batch_odds_api`,
  `category`→`asset_group`). `--apply` gated (G0 + IS v9 walk + IS backfill + 2 data-state findings: 6,869 blank
  `capture_status` + mdps consolidated-index-reads-0). Full verdict: `sports_manifest_canonicalisation_2026_06_01.md` §
  "G2 WAVE-2 readiness verdict".
- **tradfi (slot-6)**: catalogue + enumerate dry-run mechanism GREEN (588,798 candidates) — BUT this ran on the OLD
  over-fanning producer (predates G1-ENUM) → **re-validate the candidate set against slot-7's shape-aware producer**
  (tradfi is per-contract so less bundle-affected than cefi, but impossible-combo filtering still applies). gate-b
  (capture FROZEN — catalogue marks ~651K delisted) **remediated**: slot-6 shipped the **Massive IS reference adapter**
  (uac@12974b11/#91 + is@6ea46565/#407, auto-merging to staging) so tradfi reference data is no longer frozen. gate-c
  (v9) still blocked on G1-V8.
- **defi (slot-2)**, **prediction (slot-5)**: prediction's per-cqg producer is the G1-ENUM reference; both still owe
  their v9 walk (G1-V8) + dry-run.

**The could-exist universe = (IS instrument lifecycle catalogue) × (UAC availability rules).** The two halves:

- **IS half — the lifecycle catalogue** (`proper_instrument_catalogue_lifecycle_rollup_2026_06_04`):
  `build_instrument_catalogue.py` rolls up the maintained per-date
  `instrument_availability/by_date/day=…/venue=…/ instruments.parquet` defns into the cumulative
  `available_from`/`available_to` lifecycle catalogue, which `enumerate_expected_universe.py` (v2) cross-joins × dates ×
  data_types − existing manifest rows → seeds `record_expected_unattempted` for IS-listed-but-not-yet-backfilled cells.
- **UAC half — the availability rules**: chain genesis dates, `DEFI_VENUE_LAUNCH_DATES` / per-AG venue launch, listing/
  delist windows, `SOURCE_PRIORITY`, `expected_coverage()` scope — these tell the enumerator WHEN a listed instrument is
  genuinely expected to have data (post-genesis, post-launch, in-coverage). UAC accuracy is a HARD G1 input.

**G1 catalogue lifecycle (tracked stages — each per-AG, on a VM where it touches prod GCS):**

- [ ] [CODE] P0. **G1.code — catalogue producer + enumerator GREEN** (`build_instrument_catalogue.py` +
      `enumerate_expected_universe.py` v2, defi/cefi/tradfi/sports/prediction-capable; `resolve_bucket_name` env-tier
      fix). Owner: `proper_instrument_catalogue_lifecycle_rollup_2026_06_04` (vm-cross-cutting) + per-AG slices of
      `instruments_manifest_canonicalisation_2026_06_01`. **DeFi (slot-2): code-ready + denominator regression shipped
      is@bb8fb203** (⑦-defi). cefi dry-run proven 2026-06-05.
- [ ] [DATA] P0. **G1.dry-run — per-AG catalogue + enumerate dry-run** (read-only; **cefi RE-RUN on shape-aware producer
      DONE slot-3 2026-06-07** — enumerate v2 exit 0, 3,446 plausible candidates, OPTION/COMBO bundle-skip working;
      residual F1 chain-`data_type`-axis + F2 FUTURE bundle-grain gate apply-write, see cefi plan § "G2 VERIFY PASS";
      defi pending — each AG slot runs its own). **sports DRY-RUN DONE (slot-4, 2026-06-07): generic
      `build_instrument_catalogue --asset-group sports` → 0-row catalogue (raw entity cols lack
      `instrument_key`/`instrument_id`; no `sports` branch in `run_rollup`) AND captured atom is per-LEAGUE not
      per-fixture → needs a league-grain `build_sports_catalogue_dataframe` producer before enumerate v2 can run. Full
      finding + spec + gate flags in `sports_manifest_canonicalisation_2026_06_01.md` § ⑦.** **prediction DRY-RUN DONE
      (slot-5, 2026-06-07): found+fixed a crash — `build_instrument_catalogue` resolved the prediction instruments-store
      via the per-AG dict (no PREDICTION entry → `BucketNamingError`) so the cqg roll-up never ran; fix=flat-kind helper
      `is@a7fa55a8` (+regression test). With that, `--asset-group prediction --dry-run` runs exit 0 → 0 cqg rows, GATED
      on the IS prediction backfill (`market_lifecycle/by_canonical_group/`=0 objects;
      `instrument_availability/by_date/` is `market=`-grain, no `canonical_question_group=`). enumerate rides the
      catalogue (same gate). cf_manifest_audit(instruments-store-pred): 493 rows 100% v8, CF-1/3/4/8 RED (§H v9 walk
      gated). G1.schedule WIRED (prediction in both catalogue schedulers). Full finding in
      `prediction_manifest_canonicalisation_2026_06_01.md` § ⑦ G1-2026-06-07.** **tradfi DRY-RUN DONE (slot-6,
      2026-06-07): `build_instrument_catalogue --asset-group tradfi` rolls up 11,579 `by_date` parquets (full local run
      = VM job, timed out ~10min; producer already proven — slot-7 applied `prod/catalog.parquet` = 684,372 instruments,
      95% delisted = capture-freeze signature). `enumerate_expected_universe v2 --catalog-path <prod/catalog.parquet>`
      scan-only (2026-06-04..05) exit 0 → **588,798 candidate `expected_unattempted`** (= 32,711 alive × 9 data_types ×
      2 days; present-set 73,352/144,062), sample-inspected (e.g. `CBOE:INDEX:VIX × {trades,ohlcv_1m,…}`). **RE-RAN on
      the G1-ENUM shape-aware producer (@6ea46565) 2026-06-07 → 587,990 (barely dropped, −808). 🔴 gate-(a) RED —
      ROOT-CAUSE: tradfi options/combos are captured at BUNDLE grain (manifest: 0 per-contract OPTION rows;
      options_chain 3,262 + combo 58,292 + futures_chain 15,600) but the catalogue + enumerate are PER-CONTRACT (622K
      OPTION) → ~563K false candidates (grain mismatch). Needs G1-ENUM BUNDLE-GRAIN rollup for tradfi (catalogue emits
      options_chain/futures_chain bundles + matrix `option/combo→frozenset()`, mirror cefi) — co-owned slot-6+slot-7;
      validity matrix alone insufficient.** cf_manifest_audit(instruments-store-tradfi-prd): 20,388 rows 0.8% v9,
      CF-1/3/4/8 RED + 60 legacy-only (§ Step-1 v9 walk **BLOCKED on the G1-V8 instruments_manifest E2 migrator
      BUILD** + G0). **G1.run apply-write GATED** (a RED bundle-grain; b: capture freeze; c: v9 indices/migrator-build)
      → dry-run only; gate-b remediation Massive IS adapter SHIPPED + **STAGING-GREEN** (UAC@12974b11 PR#91 MERGED +
      IS@c0f2f39c PR#407 MERGED, both quality-gates-v2 PASS). **G1.schedule: tradfi MISSING from both catalogue
      schedulers' instruments-store `for_each` → gated todo filed.** Full finding in
      `tradfi_manifest_canonicalisation_2026_06_01.md` § G1.**
- [ ] [DATA] P0. **G1.run — per-AG `--apply-write` of the could-exist seed against the AG's canonical `_index`** (VM;
      `MANIFEST_PER_VM_SHARDS=true`). **GATED on**: (a) **IS instrument BACKFILL complete** for that AG
      (`instruments_backfill_phase3_2026_05_22` — the catalogue can only roll up instruments IS actually fetched); (b)
      **accurate UAC** (launch/genesis/coverage rules for that AG verified — else the seeded expected set is wrong); (c)
      **`instruments_manifest_canonicalisation` v9** for the AG's instruments-store `_index`. NOTE: G1.run seeds the
      manifest **could-exist** rows but the canonical `_index` itself comes from the AG's G2 walk — so G1.run for
      raw-tick denominators rides AFTER that AG's G4 manifest is canonical (the catalogue-of-record vs the seed are
      sequenced in the per-AG plan; do not double-walk).
- [ ] [INFRA] P1. **G1.schedule — daily catalogue-aggregation scheduler live per-AG** keyed to the IS update cadence.
      **TF AUTHORED deployment@98bee4b** — `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf` (NEW):
      per-AG `for_each` (cefi/defi/tradfi/sports/prediction) Cloud Run Job + Scheduler running
      `build_instrument_catalogue.py` (sports carries `--by-date-prefix`), 01:00 UTC, terraform-fmt clean. **Finding
      (vm-cross-cutting 2026-06-07)**: the two PRE-EXISTING schedulers (`catalogue_regen_scheduler.tf` +
      `instrument_catalogue_scheduler.tf`) run DIFFERENT scripts (UAC envelope/availability +
      `generate_instrument_catalogue.py`) — NEITHER ran the `build_instrument_catalogue.py` lifecycle roll-up, so this
      is a NEW scheduler, not a per-AG extension of cefi. **REMAINING (apply-gated)**: `terraform apply` + T+10min
      per-AG `gcloud run jobs executions` verify (infra apply pipeline) → then GREEN. Bucket-name `pred`-vs-`prediction`
      discrepancy flagged in the .tf header.

**Cross-AG IS references (each AG owns its instruments-store reference surface — sliced, not duplicated):** defi §H
`instruments-store-defi` walk · sports `instruments-store-sports` (2.68M rows + the 316-cell legacy→prd data-loss-gated
migration) · cefi/tradfi/prediction reference surfaces — all sub-items of
`instruments_manifest_canonicalisation_2026_06_01` (the per-service all-AG plan) + each AG's
`*_manifest_canonicalisation` §H slice. **G2 (an AG's MTDS/data walk) must NOT be trusted as denominator-complete until
that AG's G1 (IS catalogue + UAC) is GREEN** — the audit's ⑧ enforces this.

## Audit framework — the per-AG readiness gate (the 7-point + 2 NEW checks)

Every AG's G2→G4 transition runs the operator's readiness audit. SSOT for the checklist:
`plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` (CF-1…CF-12) + each
`*_master_audit_instructions.md`. The audit is **dry-run-green before `--apply`**:

1. ① Migrator dry-run · ② Manifest-rebuild dry-run
2. ③ 4-state pre-flight on every service IS→execution on the buckets used
3. ④ Empty/partial honest (zero-vol/NaN/last-price, data-type-dependent) + downstream handles
4. ⑤ Read/write paths match post-migration everywhere
5. ⑥ IS + UAC guardrail against instruments/fixtures that cannot exist
6. ⑦ deployment-api/UI numerator/denominator = the **could-exist universe** (IS + UAC + upstream availability; manifest
   seeds `expected_unattempted` for IS-listed-but-not-yet-backfilled cells)
7. **⑧ NEW — IS-catalogue completeness (G1 gate)**: the AG's `build_instrument_catalogue` roll-up is GREEN + the daily
   aggregation scheduler is live + the v2-enumerator recurring run seeds the could-exist universe (this is the root that
   makes ⑥/⑦ honest). A cefi daily-scheduler exists (`catalogue_regen_scheduler.tf` /
   `instrument_catalogue_scheduler.tf`) — confirm each AG's is wired, not just cefi.
8. **⑨ NEW — pipeline_mode source-aware upgrade (G0 gate)**: NO coarse `pipeline_mode="batch"`/blank anywhere the AG
   writes; migrators/rebuild/enumerator stamp source-aware `{mode}_{source}[_{transport}]`; readers are union-aware
   across modes; the manifest + data-status carry the pipeline_mode + source + cadence axes. (Catches the verified defi
   `rebuild_defi_manifest.py:302` blank-stamp class for every AG.)

## vm-defi (slot-2) status + findings — 2026-06-07

> Progress on the **G0 C-PATH WRITE** (defi migrator/rebuild source-aware) + **G1-defi IS-catalogue** rows of the gate
> board. Code-ready facts + the gates verified; ship of the code unit is **blocked on a pre-existing MTDS QG-red** (see
> the finding below), not on the change itself.

**G0 C-PATH WRITE — CODE-READY (pending ship):** `migrate_defi_full_v9_canonical.py` + `rebuild_defi_manifest.py` now
derive the SOURCE-AWARE `{batch}_{source}` pipeline_mode PER SHARD via UTL
`derive_pipeline_mode_for_row(venue,"defi", data_type)` (the cefi/tradfi pattern), stamp `source` (=
`source_string_for(pm)`, C-#6-consistent) **+ a `transport` column** (`default_transport_for_source`, no path suffix),
in BOTH the PATH key and the manifest/parquet column. The coarse `DEFAULT_PIPELINE_MODE="batch"` /
`_DEFAULT_PIPELINE_MODE="batch"` / `_PIPELINE_MODES` are RETIRED; the rebuild day-probe lists `pipeline_mode=` (covers
every source-aware mode) + bare legacy; bare/legacy-coarse paths auto-derive source-aware; per-shard isolation added to
the rebuild `add()` loop. Tests rewritten + GREEN (25/25, credential-free). Verified per-shard: DEX
state→`batch_onchain_subgraph`, perp→`batch_hyperliquid`, oracle CHAINLINK→`batch_chainlink` / PYTH→`batch_pyth_hermes`.
**Single-walk safety GREEN**: GCS probe confirmed NO coarse `pipeline_mode=batch/` data was ever applied (dest `*-prd-`
trees are pre-pipeline_mode bare; rebuild bucket 2340 days all bare) — so upgrading the migrator before any G4 apply
does not require a second whole-corpus walk.

**G1-defi IS-catalogue — gates verified, seed apply correctly GATED (dry-run only):**

- A (slot-7 PART C code) GREEN · B (DeFi IS instrument backfill) GREEN · D (UAC chain-genesis / `*_VENUE_LAUNCH_DATES` /
  `PROTOCOL_LAUNCH_DATES`) GREEN.
- **C (defi instruments-store `_index` v9-canonical) 🔴 RED**: the `_index` is **0% v9** — schema_version distribution
  **v4=33,869 / v8=20,686 / v6=14,330** (68,885 rows), missing `source`/`asset_group`/`transport` columns. The defi
  instruments-store §H walk (`defi_manifest_canonicalisation` §H + `instruments_manifest_canonicalisation`) has NOT run.
- Catalogue **dry-run executed** (`build_instrument_catalogue --asset-group defi --dry-run`, read-only, exit 0) but
  rolled up **0 rows** — `instrument_availability/by_date/` in `instruments-store-defi-prd-*` is EMPTY (the 4,339-row IS
  backfill + the 68,885-row `_index` live in the NON-prd bucket; env-tier bucket split per
  `bucket_name_ssot_legacy_dual_write_remediation`). So the G1.run `--apply-write` seed is doubly gated → NOT run.

- [ ] [DATA] P1. **G1.run-defi seed — BLOCKED on GATE C**: do NOT `--apply-write` the defi could-exist seed until (c)
      the `instruments-store-defi` `_index` is v9-canonical (currently 0% v9) AND the defi
      `instrument_availability/     by_date/` is populated in the bucket the catalogue producer reads (`-prd-` is
      empty). Owner: vm-defi, after the defi §H instruments-store walk. Repo: instruments-service. parent_epic:
      manifest_master.
- [ ] [UAC] P2. **DeFi `SOURCE_PRIORITY` registry gaps** (surfaced by the C-PATH WRITE derivation):
      `(defi,     dex_pool_swaps)` is UNREGISTERED → falls back to `batch_onchain_rpc` (vs
      `dex_pool_state`→`onchain_subgraph`); non-Hyperliquid perp venues (LIGHTER→tardis via the venue override) are
      absent from `(defi, perp_funding)=     ["hyperliquid"]`. Both derive cleanly today (fallback + per-shard
      isolation) but should be registered for an explicit per-shard source. Repo: unified-api-contracts
      (`registry/source_priority.py`). parent_epic: manifest_master.
- [ ] [INFRA] P2. **MTDS local `--no-fix` QG is pre-existing-RED** (blocks the `.qg_last_passed_sha` sentinel → no clean
      quickmerge for ANY MTDS change): ~16 `❌` on current LDR — 6 files >900 lines (5 unrelated:
      `migrate_sports_canonical_v9`/`rebuild_sports_manifest_v9`/`rebuild_prediction_manifest`/`solana_lst_archival`/
      `websocket_runner`), deep-UAC-imports / asyncio.run-in-loop / raw-response.json / empty-fallbacks in untouched
      handlers, STEP 5.85 inline-`pipeline_mode=` literals across the migration scripts, + macOS-environmental
      false-positives (574s>300s timing, BSD `grep -P` errors, no systemd cap). The defi C-PATH WRITE change adds ZERO
      net-new failures (its 25 unit tests pass; ruff clean; basedpyright-neutral). Repo: market-tick-data-service.
      parent_epic: mtds_mdps_master.
- [ ] [DATA] P1. **DeFi instruments-store `by_date` has a DOUBLED `day={D}/day={D}/` prefix on the recent tail**
      (~2026-05-05 onward — `day=2026-05-05/07` confirmed doubled; `day=2026-05-03` and ALL earlier days are single,
      canonical `day={D}/venue={V}/instruments.parquet`). Surfaced by the G2 verify dry-run 2026-06-07 (slot-2). **TWO
      defects**: (1) an instruments-service `by_date` WRITER regression that nested a second `day=` for recent snapshots
      (`gs://instruments-store-defi-prd-…/instrument_availability/by_date/day=2026-05-07/day=2026-05-07/venue=AAVEV3-ARBITRUM/instruments.parquet`);
      (2) the slot-7 v9 OBJECT migrator (`migrate_instruments_store_v9.py` `canonical_object_rel`) inserts
      `pipeline_mode=/asset_group=` after the FIRST `day=` but does NOT normalise the second → its projected canonical
      path is MALFORMED
      (`day=2026-05-07/pipeline_mode=batch_instruments_service/asset_group=defi/day=2026-05-07/venue=…`). The
      catalogue/enumerate are UNAFFECTED (`build_instrument_catalogue` uses `_DAY_RE.search` + `_VENUE_RE.search` →
      resolves the correct day+venue), so this is a **G4 object-migration gate**, not a CF-14 blocker. **Fix BOTH before
      the gated defi §H object `--apply`**: dedupe/normalise the writer + add a `day=…/day=…` collapse (or a pre-flight
      reject) to `canonical_object_rel`. Repos: instruments-service (writer + slot-7 migrator). parent_epic:
      manifest_master.
- [ ] [UAC] P3. **NICE-TO-HAVE — defi G1-ENUM matrix `POOL` row is union-coarse**: the derived
      `valid_data_types_for_instrument_type("defi","POOL")` is the UNION across all POOL-declaring protocols →
      `{dex_pool_state, dex_pool_swaps, gas_fees, lending_indices, liquidations, perp_funding}`, so a pure-DEX pool
      (e.g. UNISWAP_V3) would seed `expected_unattempted` for `perp_funding`/`lending_indices`/`liquidations` it never
      produces (a perp-DEX like GMX legitimately needs them). NOT an impossible-combo (gate-(a) still passes — no
      `odds`/`oracle_prices` leak into POOL), but a per-protocol grain would tighten the denominator. Repo:
      unified-api-contracts (`registry/capability_declarations/_defi.py` PROTOCOL_CAPABILITIES). parent_epic:
      manifest_master. Provenance: G2 verify 2026-06-07 (slot-2).
- [ ] [SCRIPT] P3. **NICE-TO-HAVE — defi migrator `_list_objects` L1 find is a full-bucket scan** (re-verify 2026-06-07,
      slot-2): `migrate_defi_full_v9_canonical.py:570` always issues `_safe_find(fs, {base}/{dir_name})` for the L1
      layout, but all 6 dedicated source buckets are `day=`-partitioned today (no top-level `{dir_name}/` or
      `raw_tick_data/` tree) → that L1 prefix matches nothing yet gcsfs enumerates the whole bucket (a 3-day local
      dry-run hit a >280 s timeout on it; the L1 `dex_pools` find alone >120 s isolated). NOT a correctness issue
      (returns the correct empty set; date-scoped runs DO complete — the earlier `day=2024-06-01` dry-run finished
      0-errors) and laptop-variable, but it wastes a whole-bucket enumeration per bucket on the in-region VM `--apply`
      too. Gate the L1 find on a cheap existence probe (or drop it) — **validate against the whole corpus on the VM
      first** so a bucket with a genuine L1 tree is never silently skipped (data-loss risk). Repo:
      market-tick-data-service. parent_epic: mtds_mdps_master. **TRIAGED 2026-06-07 (slot-2) → SPEED-NOTE,
      NON-BLOCKING:** the `--apply` does NOT date-shard `_list_objects` (the `launch-canonical-migration-vm.sh` launcher
      runs ONE VM over the full date range → exactly ONE `_list_objects` per bucket = 6 wasted whole-bucket scans total,
      not N×6), and the in-region VM completes whole-bucket scans (the baked-union `discover_union` run over the whole
      corpus proved it). So the L1 find adds wall-clock to the apply but never blocks it. Per the apply-ready criterion
      (fix only if it blocks at scale) this stays a **deferred optimisation**, not an apply-gate. Kept P3.

### G2-defi readiness verdict (WAVE 2 verify pass — slot-2, 2026-06-07)

**VERDICT: defi migration CODE is DRY-RUN-GREEN on LDR — the manifest+data `--apply` is code-ready, correctly GATED.**
Re-run on the WAVE-1 source-aware code against real prod GCS (read-only). No code changed (verify pass = dry-runs only);
this is a `docs(plans):` flip.

- **①+⑨ MTDS migrator dry-run (CF-3/CF-13) GREEN — mtds@f80c50f1.**
  `migrate_defi_full_v9_canonical --start-date 2024-06-01 --end-date 2024-06-01` (dry, all 6 buckets) → 0 errors, 0
  needs_attr. Projected PATHS + in-process `_conform` COLUMNS both verified source-aware:
  `dex_pool_state→pipeline_mode=batch_onchain_subgraph` (source=`onchain_subgraph`), `dex_pool_swaps→batch_onchain_rpc`
  (source=`onchain_rpc`); both `schema_version=9`, `asset_group=defi`, `transport=rest` (separate COLUMN), per-row
  `available_at` (EOD UTC), canonical underscore `data_type`, `pipeline_mode=…/asset_group=defi/` LEFT of `venue=`;
  legacy source `category=defi` correctly migrated. NOT coarse `batch`/blank.
- **②+③ instruments-store v9 index dry-run (CF-1/CF-2/CF-4) GREEN — is@2971a064.**
  `migrate_instruments_store_v9 --asset-group defi --skip-objects` (dry) → prd `_index` **125,242 rows v8→v9 (100%)**:
  schema_version `{9:125242}`, source=`instruments_service`, transport=`rest`,
  pipeline_mode=`batch_instruments_service`, asset_group=`defi`, available_at filled on all rows, `category` dropped.
  cf_manifest_audit projection → CF-GREEN. (Object-walk side: GREEN for canonical single-`day=` objects; the recent
  doubled-`day=` tail is the P1 finding above — a G4 gate, not an index blocker.)
- **③ catalogue + enumerate (CF-14) — mechanism GREEN, candidate-count GATED.**
  `build_instrument_catalogue --asset-group defi --dry-run` on the now-populated prd `instrument_availability/by_date/`
  → **64,724 by_date snapshots enumerated** for rollup (listing GREEN; the prior "0 rows / -prd- empty" finding is
  RESOLVED — by_date is now populated 2020-01-20…2026-05-08). The full LOCAL rollup EXCEEDED a 580s budget downloading
  64,724 small parquets (exit 124, did NOT finish) → the rollup + enumerate candidate-count run needs a VM / longer
  timeout, deferred with the gated G1.run write below (the count is downstream of the gated catalogue WRITE anyway).
  Validity-matrix slice VERIFIED correct (UAC@97c26dbe, enumerate@6ea46565): **all 6 defi instrument_types present in
  by_date map cleanly** — `POOL`/`LENDING`/`SPOT_PAIR`/ `PERPETUAL`/`STAKING`/`YIELD_BEARING`, zero
  unmapped/over-fan/None-fallthrough; `_enumerate_v2_defi` is G1-ENUM shape-aware (genesis/launch/lifecycle +
  bundle-skip). Full enumerate candidate-count is gated on the **G1.run catalogue WRITE** (a `--apply-write`, correctly
  GATED on GATE C below) — not runnable read-only without a persisted catalogue parquet.
- **④⑤⑥⑦⑧ (CF-5/6/7/8/10/11/12)** ride the WAVE-1 code (rebuild `record_zero_rows`/typed reasons, A7 fetch-failure
  classification, batch=live single path) — unchanged this pass; verified by the 25/25 credential-free unit suite.

**Remaining gates for the defi `--apply` (G4) — all correctly held:**

1. **G0 ∧ G1 ∧ G3** (cross-AG coordinator gates).
2. **GATE C — instruments-store-defi `_index` v9 walk** (currently 0% v9 on disk: 125,242 v8; dry-run proves the
   transform is correct — the WRITE is the gated `--apply`).
3. **DeFi IS backfill + the doubled-`day=` writer/migrator fix** (P1 above) before the §H object `--apply`.
4. **Pre-migration drain** (all VMs stopped + consolidated) before any object `--apply`.

Sampled-not-walked disclosure: MTDS dry-run sampled `day=2024-06-01` across all 6 buckets (path+column verified) +
in-process `_conform` of real dex-pools/dex-swaps objects; instruments-store `_index` transform walked all 125,242 rows;
by_date instrument_type coverage sampled across all venues for `day=2025-12-15`+`2026-05-03` (+ a 6-day spread). The
doubled-`day=` boundary was sampled day-by-day across 2026-05-01…08. The full 64,724-parquet catalogue rollup count +
the enumerate candidate-count are deferred to the gated G1.run write.

### 🟢 DeFi APPLY-READY VERDICT + completed 7+2-point audit (slot-2, 2026-06-07)

> **VERDICT: DeFi is APPLY-READY on LDR.** Every G1+G2 dry-run is green and the 7+2-point audit passes; the migration
> CODE is correct and no code change is owed before `--apply`. **The only things between DeFi and the real `--apply` are
> OPERATIONAL gates** (drain + the gated WRITE runs), not code. No `--apply` run in this pass (gated).

**7+2 audit — per-CF verdict (CF-1…CF-14; data-state reads, not constants):**

| CF         | Invariant                                               | defi verdict    | Evidence (sampled vs walked)                                                                                                                                                                                                                               |
| ---------- | ------------------------------------------------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CF-1       | schema_version=9                                        | 🟢              | migrator `_conform` stamps `9` on real ORCA parquet (sampled); IS `_index` transform → `{9:125242}` (WALKED all rows)                                                                                                                                      |
| CF-2       | `asset_group=` not `category=` (path+row)               | 🟢              | real source `category=defi`→canonical `asset_group=defi/` path key + column; `category` dropped from `_index` (walked)                                                                                                                                     |
| CF-3/CF-13 | source-aware `pipeline_mode={mode}_{source}` (path+col) | 🟢              | `batch_onchain_subgraph`/`batch_onchain_rpc` per-shard on real paths+cols; coarse `batch`/blank retired; 14-case derivation incl. antipattern-retired `batch_hyperliquid` (sampled)                                                                        |
| CF-4       | `source` COLUMN every external cell                     | 🟢              | `source=onchain_subgraph` on real rows; IS rows `source=instruments_service` (walked). P2 `SOURCE_PRIORITY` registry-gap todo open (derives cleanly via fallback today)                                                                                    |
| CF-5       | typed `EmptyConfirmedReason`                            | 🟢              | defi writers use `DefiManifestRecorder.record_zero_rows` + `EXPECTED_PRE_VENUE_LAUNCH`/`EXPECTED_PRE_GENESIS_CHAIN` (code grep)                                                                                                                            |
| CF-6       | `expected_unattempted` materialised                     | 🟢 (code)       | shape-aware `_enumerate_v2_defi` + `build_instrument_catalogue` produce the could-exist seed; the apply-write RUN is the gated G1.run                                                                                                                      |
| CF-7       | canonical data_type / flat venue+chain / `{VENUE}_V{N}` | 🟢              | input `dex_pools`→typed `dex_pool_state`; `SUSHISWAP`→`SUSHISWAP_V3` on real paths (sampled)                                                                                                                                                               |
| CF-8       | per-row `available_at`, no lookahead                    | 🟢              | real ORCA `available_at=2026-05-28T21:21:46` write-time; IS `available_at` filled on all 125,242 rows (walked)                                                                                                                                             |
| CF-9       | env-split bucket via `resolve_bucket_name`              | 🟢              | migrator/rebuild build buckets via `resolve_bucket_name`; the `gs://` occurrences are docstring/log strings, not f-string bucket construction (grep)                                                                                                       |
| CF-10      | no phantom/date-impossible captured                     | 🟢 (projection) | IS `_index`: 57,466 null→`captured` from `instrument_count>0`, 0 dishonest captured-but-empty (walked); object-presence phantom sweep is `reconcile_phantom_manifest_rows_all` post-apply                                                                  |
| CF-11      | fetch-failure → `attempted_failed`                      | 🟢              | defi handlers (mev/evm_defi/perp_funding) call `record_failed(...)`; no `except: return []` swallow (grep)                                                                                                                                                 |
| CF-12      | batch=live symmetry                                     | 🟢              | one code path (no defi live-only data_types); verified by the 25/25 credential-free unit suite                                                                                                                                                             |
| CF-14/⑧    | IS-catalogue could-exist ROOT green                     | 🟢 (mechanism)  | `-prd-` by_date POPULATED (64,724 parquets); shape-aware producer runs; validity-matrix slice correct (IS adapters emit `POOL`/`STAKING`/`LENDING`/`SPOT_PAIR`/`YIELD_BEARING`, all matrix-covered). Full rollup candidate-count = gated G1.run (VM-scale) |

**Sampled-vs-walked (audit-level)**: WALKED — the full 125,242-row instruments-store `_index` transform (deterministic,
no object probe). SAMPLED — MTDS migrator conform on the latest populated day per bucket + a real 14,093-row ORCA
parquet (the whole-corpus migrator walk runs on the in-region VM); the 64,724-parquet catalogue rollup LISTED but not
fully rolled up locally (VM-scale). Adapter/handler CF-5/9/11/12 verified by code grep, not a corpus walk. **Remaining
gaps**: the full catalogue rollup + enumerate candidate-count (gated G1.run VM run) and the object-presence phantom
sweep (post-apply) — both downstream of the gated WRITE, not code.

**Remaining gates to the real `--apply` — ALL OPERATIONAL (no code owed):**

1. **G0** GREEN ✓ (Phase-0 source-aware writer code landed) · **G3 UNION view SHIPPED ✓** (deployment-api@4dd2575 +
   deployment-ui@0dc40eb, pm@822393880).
2. **GATE C — instruments-store-defi `_index` v9 WRITE**: run `migrate_instruments_store_v9 --asset-group defi --apply`
   (the dry-run proved the 125,242-row transform projects 100% v9; this is the gated WRITE, not a code fix).
3. **DeFi IS backfill complete** + the gated `build_instrument_catalogue`+`enumerate_expected_universe --apply-write`
   G1.run VM run (catalogue/enumerate UNAFFECTED by the doubled-`day=` bug; that bug is a §H **object**-migration gate,
   fixed before the §H object `--apply` only).
4. **Pre-migration drain** (all GCP+AWS VMs stopped + manifest consolidated + snapshot) before any object `--apply`.

No code-correctness blocker remains for the DeFi migrator/rebuild/enumerator. The 3 open todos are: P1 doubled-`day=` (a
§H object-migration gate, instruments-service) · P2 `SOURCE_PRIORITY` registry tidy · P3 POOL union-coarse + P3 L1-find
speed-note (both deferred optimisations, non-blocking).

## Orphan sweep (2026-06-07) — every active data-layer plan/issue is registered above

- Swept `plans/active/*.md` + `plans/active/issues/*.md` for manifest/migration/catalogue/pipeline_mode/backfill/
  coverage/schema themes. **All registered above** — 0 orphans in-theme at sweep time.
- **Superseded epics flagged** (already banner-marked in `plans/epics/`): `manifest_evolution_SUPERSEDED_2026_05_21` +
  `manifest_migration_SUPERSEDED_2026_05_21` — do NOT reference; the live epic is `epics/manifest_master.md`.
- Re-run the sweep at every gate promotion (a new active plan touching the data layer with no registry row here is
  review-blocking).

## Master coordination todos (this plan's OWN work — pure coordination, no execution)

- [ ] [DOCS] P0. **M-COORD-1 — drive the G0 doc-coherence reconcile (the standardisation plan's item 0.8) to GREEN**:
      CLAUDE.md + the codex layer (`pipeline-mode-partition.md`, `availability-manifest-and-data-status.md`) +
      `SUB_AGENT_MANDATORY_RULES.md` + **all 5 per-AG plans + downstream + instruments** acknowledge the source-aware
      `{mode}_{source}[_{transport}]` model + the apply-gate. Today the per-AG plans (2026-06-01) PREDATE the standard
      (2026-06-05) → stale. parent_epic: manifest_master. **SSOT layer DONE (vm-cross-cutting 2026-06-07)**: the codex
      reconciliation doc, the workspace `CLAUDE.md`, and the sub-agent rules were rewritten to the source-aware
      mode/source/transport model (replay tier + hyperliquid vendor, retiring the glued-transport antipattern).
      **REMAINING**: the 5 per-AG plans carry stale tokens left to each AG owner (they intermix factual on-disk object
      counts that must not be falsified), plus `availability-manifest-and-data-status.md` and the downstream/instruments
      plans on next touch.
- [x] ✅ [DOCS] P0. **M-COORD-2 — DONE (2026-06-07): gate banners added** to the DeFi §MASTER (demoted) + all 6
      cross-AG/ downstream/instruments plans (cefi/sports/prediction/tradfi `--apply` apply-gate; instruments = G1-root;
      downstream = G2). Additive banners only (slot precedence respected). **Residual (folds into M-COORD-1)**: repoint
      the `master:` FRONTMATTER field of the plans that point at `defi_manifest…§MASTER` → the coordinator, and the full
      CLAUDE.md + codex source-aware-model reconcile. parent_epic: manifest_master.
- [x] ✅ [AUDIT] P1. **M-COORD-3 — DONE (2026-06-07): CF-13 (pipeline_mode source-aware, extends CF-3) + CF-14
      (IS-catalogue could-exist ROOT, foundation of CF-6) added to `canonical_form_cross_service_audit_checklist.md`** —
      the ⑨ + ⑧ readiness checks; an AG's audit now fails RED until they hold; cross-AG ownership stays in this
      coordinator's registry (not duplicated). Residual: cite CF-13/14 in each `*_master_audit_instructions.md`
      ownership matrix on next touch. parent_epic: manifest_master.
- [ ] [CHORE] P1. **M-COORD-4 — wire the gate-state board**: a small status block here (G0…G5 = RED/AMBER/GREEN per AG)
      refreshed at each gate promotion, so the orchestrator sees the critical path. Recompute from the registered plans'
      checkboxes (never hand-maintain divergent state). parent_epic: manifest_master.
- [x] ✅ [DEFI] P1. **M-COORD-5 (DeFi slice, slot-2) — DONE mtds@f80c50f1**: `rebuild_defi_manifest.py`
      `writer.add(...)` now passes `asset_group=defi` + the source-aware `pipeline_mode` + `source` + `transport` (no
      more blank `pipeline_mode`/`source` — standardisation finding #1 resolved); migrator likewise stamps source-aware
      in path+column. Tests green 25/25. Repo: market-tick-data-service. parent_epic: mtds_mdps_master.

## Demotion + linkage record

- `defi_manifest_canonicalisation_2026_06_01.md` `## MASTER` section → demoted to **DeFi executor**; a banner points UP
  to this coordinator (its cross-plan registry is superseded by the table above).
- `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` → registered as **G0** (keeps its Phase-0
  apply-gate; this master references it, does not duplicate it).
- `master_to_live_defi_2026_05_23.md` → **downstream consumer** (G5 → live promotion); cross-linked, not subsumed.

## Verification (full-execution criterion)

This coordinator is COMPLETE-as-a-coordinator when: (1) every active data-layer plan/issue has a registry row + a
blocked-until edge; (2) the G0 doc-reconcile (M-COORD-1) is GREEN so no per-AG plan/codex doc contradicts the
source-aware model; (3) the audit SSOT carries ⑧+⑨; (4) the gate-state board reflects the registered plans' real state;
(5) 0 orphans. The migration itself is done by the registered sub-plans — this plan just proves they are correctly
sequenced and nothing is unblocked-out-of-order or orphaned.
