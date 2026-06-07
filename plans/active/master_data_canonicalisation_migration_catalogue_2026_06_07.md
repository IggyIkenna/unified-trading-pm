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

| Class              | Site                                                                                                                                                                                                                                   | State | Fix / owner                                                                                               |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | --------------------------------------------------------------------------------------------------------- |
| WRITE migrator     | `migrate_tradfi_to_v9_canonical.py` (`_pipeline_mode`→`batch_databento`)                                                                                                                                                               | ✓     | reference impl — copy this pattern                                                                        |
| WRITE rebuild      | `rebuild_{cefi,tradfi,sports,prediction}_manifest*` (`derive_pipeline_mode_for_row`)                                                                                                                                                   | ✓     | reference impl                                                                                            |
| **WRITE migrator** | **`migrate_defi_full_v9_canonical.py:70/700/714`** `DEFAULT_PIPELINE_MODE="batch"` → coarse path+col                                                                                                                                   | **✗** | **vm-defi** — derive `batch_<source>` per shard via SOURCE_PRIORITY, in the C0 walk                       |
| **WRITE rebuild**  | **`rebuild_defi_manifest.py:88/206/230/250`** `_DEFAULT_PIPELINE_MODE="batch"` (+ `:302` blank — C-#1)                                                                                                                                 | **✗** | **vm-defi** — switch to `derive_pipeline_mode_for_row` like the other AGs                                 |
| **READ (defi)**    | **features `mtds_canonical_reader.py:80-81`** probes exact `pipeline_mode=batch/`+`live/`                                                                                                                                              | **✗** | **vm-ml** — prefix-match `pipeline_mode=batch_*/` (+ `live_*`)                                            |
| **READ**           | **mdps `orchestration_scanner.py:213-214`** matches coarse `batch`/`live` segment                                                                                                                                                      | **✗** | **vm-ml** — prefix-match `batch_*`/`live_*`                                                               |
| TEST               | mtds `test_migrate_defi_full_v9_canonical.py:53-54` · `test_rebuild_defi_manifest.py:17/72` · mdps `test_orchestration_scanner.py:182-230` · features `test_mtds_canonical_reader.py:63-132`                                           | ✗     | update with the code (assert `batch_<source>`)                                                            |
| LIVE (all AGs)     | UTL `pipeline_mode_resolver.py:123` live → `LIVE_WEBSOCKET` (not `live_<source>`)                                                                                                                                                      | ~     | the M1 `live_<source>` OBJECT migration = **gated next tranche** (C-#5) — NOT part of the batch migration |
| DOC ✓              | CLAUDE.md:568 · SUB_AGENT_MANDATORY_RULES:276 · most AG plans · deployment-api/data_status                                                                                                                                             | ✓     | already `batch_*/`                                                                                        |
| DOC ✗              | `defi_manifest_canonicalisation_2026_06_01.md` (many coarse `pipeline_mode=batch/`) · codex `pipeline-mode-partition.md` (mixed) · audit `defi_object_path_canonicalisation_2026_06_01.py:87` · `pipeline_mode_partition_migration:63` | ✗     | reconcile to `batch_<source>` (rides M-COORD-1)                                                           |
| BY-DESIGN          | codex `batch-live-architecture.md:466` + `instruments-live-architecture.md:30` — instruments reference data has **NO `pipeline_mode=live` partition** (live writes the identical batch path)                                           | ✓     | keep — a real exception, not a conflict                                                                   |

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
- [ ] [DATA] P0. **G1.dry-run — per-AG catalogue + enumerate dry-run** (read-only; cefi PROVEN 2026-06-05 on real prod
      GCS; defi/sports/prediction/tradfi pending — each AG slot runs its own).
- [ ] [DATA] P0. **G1.run — per-AG `--apply-write` of the could-exist seed against the AG's canonical `_index`** (VM;
      `MANIFEST_PER_VM_SHARDS=true`). **GATED on**: (a) **IS instrument BACKFILL complete** for that AG
      (`instruments_backfill_phase3_2026_05_22` — the catalogue can only roll up instruments IS actually fetched); (b)
      **accurate UAC** (launch/genesis/coverage rules for that AG verified — else the seeded expected set is wrong); (c)
      **`instruments_manifest_canonicalisation` v9** for the AG's instruments-store `_index`. NOTE: G1.run seeds the
      manifest **could-exist** rows but the canonical `_index` itself comes from the AG's G2 walk — so G1.run for
      raw-tick denominators rides AFTER that AG's G4 manifest is canonical (the catalogue-of-record vs the seed are
      sequenced in the per-AG plan; do not double-walk).
- [ ] [INFRA] P1. **G1.schedule — daily catalogue-aggregation scheduler live per-AG** keyed to the IS update cadence
      (`deployment-service/terraform/gcp/catalogue_regen_scheduler.tf` + `instrument_catalogue_scheduler.tf` exist;
      confirm wired for EVERY AG, not just cefi) so the v2 enumerator always reads a fresh catalogue + the could-exist
      denominator self-updates as instruments list/delist. NOT fire-and-forget (heartbeat + T+10min verify).

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
      (2026-06-05) → stale. parent_epic: manifest_master.
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
- [ ] [DEFI] P1. **M-COORD-5 (DeFi slice, slot-2) — fix the verified G0 defi bug**: `rebuild_defi_manifest.py:302`
      `writer.add(...)` stamps blank `pipeline_mode`+`source` (standardisation finding #1, 🔴 VERIFIED, vm-defi).
      Upgrade to source-aware stamping before defi G4. Repo: market-tick-data-service. parent_epic: mtds_mdps_master.

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
