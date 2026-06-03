---
title: Data-source provenance enforced across all asset groups (source column + SOURCE_PRIORITY)
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
priority: P0
status: active
estimate_class: infra
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 8
created: 2026-06-01
locked_by: live-defi-rollout
locked_since: 2026-06-01
completion_gates:
  code: C5
  deployment: D3
  business: B4
repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: features-service
    code: C0
    deployment: none
    business: none
related_plans:
  - plans/epics/mtds_mdps_master.md
  - plans/active/tradfi_massive_dual_source_2026_05_28.md
  - plans/epics/defi_master.md
  - plans/epics/sports_master.md
---

# Data-source provenance enforced across all asset groups

> **🟡 SEQUENCING DEPENDENCY — `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` is RUNNING (2026-06-01).**
> That plan drained the tick-data writers and is migrating legacy→canonical tick buckets via **server-side copy**
> (`migrate_legacy_tick_buckets_to_canonical.py` — moves objects, does NOT add columns). It touches the **same tick-data
> objects** + owns the drain/relaunch cadence. **Do NOT launch the `source`-column backfill now — it would race the
> in-flight copy** (and it needs the Phase 1/2 write-path fix first anyway). Sequence: (1) let the remediation finish;
> (2) **bundle this plan's source-stamping write-path fix (Phase 1+2) into the remediation's code-fix → tarball →
> relaunch** so relaunched writers stamp `source`; (3) run the source-column **data backfill after, on the CANONICAL
> buckets** (the server-side copy doesn't add `source`, so backfill is still required — not redundant). Net: each object
> is content-rewritten once. See § Migration scope.

## Overview

TradFi shipped a dual-source provenance model (`tradfi_massive_dual_source_2026_05_28.md`): a shard
(`data_type × venue × time`) may be populated by more than one vendor over time, **co-mingled on the same hive drop**
and disambiguated by a **row-level `source` column** + a per-source manifest row, resolved downstream via UAC
`SOURCE_PRIORITY`. Operator decision 2026-06-01: **`source` stays a column, not a hive path key** — better for
batch/live symmetry and single-walk discipline.

**This concern is crosscutting, not TradFi-only.** Every asset group except prediction realistically gets the same
logical metric from >1 source over time. The crosscutting audit (2026-06-01, see § Audit findings) found the root cause:
**`SOURCE_PRIORITY` already declares multi-source lists for cefi / defi / sports, but the `source` field is only
_enforced_ and only _wired downstream_ for `category=="tradfi"`.** Everyone else writes `source=""` with no gate and no
read-time reconciliation — so two sources for one cell silently collapse (last-write-wins) or double-count.

## Design decision (SSOT for this plan)

**Source is stamped on EVERY cell, ALL asset groups — even when only one source is currently declared.** (Operator
2026-06-01: "I don't care if there are two data sources yet — I may find an alternative for Tardis, so it's the same
issue.") The source a cell uses can change over time — a Tardis replacement, a second vendor added, a provider swapped.
If you only start stamping `source` at the moment a 2nd source appears, the entire pre-existing single-source corpus is
left unlabelled and cannot be distinguished from the new source after the swap. So stamping is **universal**, not gated
on cardinality.

Generalize the existing TradFi gate (`manifest_writer.py` `if category == "tradfi" and not source`) to:

> **Raise `MissingSourceError` when `source` is blank OR not a member of `SOURCE_PRIORITY[(asset_group, data_type)]`,
> for every captured cell.**

`SOURCE_PRIORITY` validates _which_ source is allowed (closed set) and drives _resolution_ when >1 exists — it does NOT
decide _whether_ to stamp. Cardinality (>1) governs resolution only. No asset_group is exempt; no hardcoded list; the
registry is the SSOT for the allowed source strings (it already enumerates the current source for every cell, e.g.
`("cefi", …)=["tardis"]`, `("prediction", "trades")=["polymarket_clob"]`).

## Decisions taken (Q1 + Q2) — 2026-06-01 (operator-delegated; SHIPPED this form)

> These record the operator answers to the two open design questions + the **as-implemented** contract. The shipped UTL
> gate (UTL@0f7198f2) implements the **auto-stamp** variant below — which **refines the "raise when blank for every
> cell" rule stated in § Design decision / Phase 1**. Flagged here for explicit confirm/override.

**Q1 — computed/service sources are EXEMPT (operator pick).** A cell whose only `SOURCE_PRIORITY` source(s) are internal
emitters (`execution_service` / `strategy_service` / `features_onchain_service` / `cross_instrument`) does NOT stamp
`source` — its lineage is the upstream cell, not a vendor. Implemented as `COMPUTED_SOURCES` in UAC
`source_priority.py`; `external_sources_for()` filters them out. This **resolves the plan's internal contradiction**:
Phase 1 text said "only an unregistered cell is exempt", but `execution_fills` / `hedge_ratio_snapshot` /
`cross_instrument_signal` ARE registered (for the PipelineMode round-trip) yet must not gate. Computed-source membership
is the principled exemption.

**Q2 — AUTO-STAMP single-source; require explicit only for multi-source (my call under operator delegation).** The
shipped gate (`ManifestWriter._resolve_and_validate_source`, applied in `record_captured` **and** legacy `add`):

| cell                                                                                                      | blank `source` behaviour                                      |
| --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| 1 external source (cefi `tardis`, prediction `polymarket_clob`, single-source defi `onchain_subgraph`, …) | **auto-stamp** the sole registered external source (NO raise) |
| >1 external source (tradfi trades, defi `oracle_prices`/`native_staking_rates`, sports `FIXTURES`)        | **raise `MissingSourceError`** — writer must pass `source=`   |
| computed/service-only, or unregistered                                                                    | exempt → `source=""`                                          |
| any passed `source` not in the cell's `SOURCE_PRIORITY` list                                              | **raise** (membership validation)                             |

**Why auto-stamp (not the literal "raise on blank for every cell")**: both reach the operator's end state — _every
external cell carries `source`_, swap-resilient. Auto-stamp gets there **without threading `source=` through the
hundreds of single-source callsites** (all of MDPS cefi, every sports/prediction/single-source-defi writer) and without
breaking them at runtime. Trade-off: a single-source writer no longer _declares_ its source (the registry fills it), so
a future registry-drift could auto-stamp a wrong default — mitigated by the membership-validation raise + the QG STEP
5.64 generalisation. Helpers shipped: `source_required()` (>1 external) / `default_source()` (sole external) /
`external_sources_for()` / `COMPUTED_SOURCES` — **not** the `validate_source()` named in the Phase 1 item.

> **OPERATOR: confirm auto-stamp, or override → raise-on-blank-everywhere.** Override means: thread `source=` through
> EVERY single-source writer (MDPS canonical_writer, all sports/prediction/single-source-defi callsites) + flip the gate
> to raise on any blank. Larger rollout; breaks each writer until threaded. Auto-stamp avoids that. Until overridden,
> auto-stamp stands and the Phase 1 items below are flipped against it.

## Scope boundary — what stamps `source` (so "all asset groups in full" is unambiguous)

- **IN SCOPE — every ingested raw market-data cell** that has a `SOURCE_PRIORITY` entry: all five asset groups, every
  venue × data_type. These carry an external vendor/source and MUST stamp it (write-path + backfill).
- **MDPS processed candles inherit/propagate the upstream source.** A candle is derived from a raw cell with a known
  `source`; the candle pipeline must carry that `source` through so a tardis-derived vs venue-derived candle stays
  distinguishable (Phase 4-MDPS todo). Same swap-resilience rationale.
- **EXEMPT (computed, no external vendor)** — features-service outputs, `strategy_output`, `execution_record`, `pnl`,
  and any data_type with **no** `SOURCE_PRIORITY` entry. The gate does not fire for these; their lineage is the upstream
  cell, not a vendor. (If such a cell unexpectedly has a `SOURCE_PRIORITY` entry, that's a registry bug to fix.)

## Audit findings (2026-06-01 crosscutting sweep — the exposed gaps)

Verdict basis: **every cell must stamp `source` now** (swap-resilience) — so a single-source cell with a blank `source`
column is RED, not exempt.

| Asset group | Current source(s)                                                                                                     | `source` stamped today                                                                    | Status                                                                                                                                                                         |
| ----------- | --------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| TradFi      | databento (+massive / yahoo / barchart)                                                                               | ✅ v9 column + gate (`manifest_writer.py:2430`)                                           | 🟡 code GREEN; **backfill now RUNNABLE** — `MASSIVE_API_KEY` provided (use S3 flat-files for bulk history; stamp `source=databento` on legacy rows)                            |
| DeFi        | `onchain_subgraph`/`onchain_rpc` (most), `oracle_prices`=pyth+chainlink, `native_staking_rates`=solana_rpc+helius_rpc | ❌ writers route via `add()`, never pass source (`_defi_manifest.py:174`, docstring L144) | **🔴 RED** — no cell stamps source; the 2 multi-source cells additionally collapse last-write-wins **today**                                                                   |
| CeFi        | `tardis` (single, but **operator may swap for an alternative** → stamp now)                                           | ❌ source `""`                                                                            | **🔴 RED** — stamp `source=tardis` on every cefi cell NOW so a future Tardis-swap/2nd-source is distinguishable                                                                |
| Sports      | `api_football`/`footystats`/`odds_api`/… (`FIXTURES` already 2-source)                                                | ❌ source in PATH not column                                                              | **🔴 RED** — path→column migration + stamp every cell                                                                                                                          |
| Prediction  | `polymarket_clob`/`polymarket_gamma_api`/… (single per venue)                                                         | ❌ source `""`                                                                            | **🔴 RED** — stamp source now (swap-resilience). _Venue ≠ source still holds_: cross-venue dispersion (Polymarket vs Kalshi) stays a feature-layer concern, NOT a source merge |

> **Audit run 2026-06-01 (code write-path).** Full result + per-item evidence:
> [`plans/audit/results/data_source_provenance_audit_2026_06_01.md`](../audit/results/data_source_provenance_audit_2026_06_01.md).
> Correction (operator 2026-06-01): **provenance is universal** — every cell stamps `source` now, even single-source,
> because any source may later be swapped/supplemented. So **all five asset groups are RED/owed** for stamping (defi is
> additionally the one LIVE multi-source collapse). TradFi backfill is **unblocked** (`MASSIVE_API_KEY` provided).

## Phased execution

### Phase 1 — UAC + UTL: universal source gate (P0, foundation)

- [x] ✅ [UAC] P0. Registry-driven source helpers in `source_priority.py` — uac@aab101ad. Shipped `source_required()`
      (>1 external), `default_source()` (sole external → auto-stamp), `external_sources_for()`, `COMPUTED_SOURCES`,
      exposed at the UAC + crosscutting facades. **NOTE (auto-stamp variant per § Decisions Q2):** shipped these instead
      of `validate_source(...)-raises-for-every-cell`; single-source cells auto-stamp rather than raise. Membership
      validation (passed source ∈ list) is enforced in UTL.
- [x] ✅ [UTL] P0. Universal source gate `_resolve_and_validate_source()` in `manifest_writer.py`, applied in
      `record_captured` AND legacy `add` — utl@0f7198f2. **Auto-stamp form (per § Decisions Q2):** auto-stamp sole
      external source / raise on multi-source-blank / raise on invalid source / computed+unregistered exempt — NOT
      raise-on-every-blank. `MissingSourceError` gained `invalid_source`/`allowed_sources`.
- [x] ✅ [TEST] P0. `tests/unit/test_manifest_writer_source.py` extended — utl@0f7198f2 (+ UAC
      `tests/unit/test_source_priority.py` uac@aab101ad): tradfi/defi/sports multi-source raise without `source`;
      cefi/prediction/defi-swap **auto-stamp**; invalid source raises; two sources on one cell → two manifest rows;
      computed + unregistered exempt; `add()` path covered.

### Phase 2 — DeFi writer rewiring (P0, biggest gap)

- [x] ✅ [UTL] P0. `DefiManifestRecorder.record_captured()` accepts `source=` + passes `category="defi"` to
      `ManifestWriter.add()` so the registry gate resolves (single-source defi auto-stamps; multi-source requires
      source) — mtds@2ef636a6. (Routes through `add()` not `record_captured()` — `add()` gained the same gate, the
      F6-precedent path; avoids the df-flow refactor. Equivalent enforcement.)
- [x] ✅ [MTDS] P0. DeFi handler callsites: single-source handlers (dex_pools, lending_indices, swap, …) **auto-stamp**
      their registered source (no per-callsite change needed); the multi-source cells are threaded explicitly —
      mtds@2ef636a6.
- [x] ✅ [MTDS] P0. oracle_prices stamps `source=chainlink`/`pyth_hermes` (+ fixed pyth rows mislabelled
      `pipeline_mode=BATCH_CHAINLINK` → `BATCH_PYTH_HERMES` on captured/empty/failed); native_staking stamps
      `helius_rpc`/`solana_rpc` + matching pipeline_mode by `helius_key` presence — mtds@2ef636a6.
- [x] ✅ [AUDIT] P1. Features-service DeFi onchain calculators audited (2026-06-01) — **no change needed**: they call
      `.add()` WITHOUT `category`, so cells are unregistered→exempt; their DeFi outputs (`feature_observation_snapshot`,
      `cross_instrument_signal`) are computed-exempt by design.
- [ ] [SCRIPT] P1. Write `backfill_defi_source_column.py` (copy tradfi template) — stamps the known historical source
      **per data_type** (most defi → `onchain_subgraph`; `oracle_prices` → resolve pyth vs chainlink from the existing
      `pipeline_mode`/path; `native_staking_rates` → solana_rpc vs helius_rpc). Idempotent.
- [ ] [DATA] P1. Backfill the existing DeFi corpus — run now, parallel in-region VMs sharded by `day=` (see § Migration
      scope); fold into the defi canonicalisation migration (`defi_manifest_canonicalisation_2026_06_01.md`) if open,
      else run direct; manifest re-consolidation after.

### Phase 3 — CeFi writer source (P1 — stamp `source=tardis` NOW for swap-resilience)

> Operator 2026-06-01: "I may find an alternative for Tardis, so it's the same issue." cefi has one source today
> (`tardis`) but it MUST be stamped on every cefi cell **now** — so that when Tardis is replaced or a 2nd source is
> added, the existing corpus is already labelled `source=tardis` and downstream can distinguish/resolve. This is NOT
> latent; a blank `source` on cefi today is a real gap (the universal Phase 1 gate requires it).

- [ ] [MTDS] P1. Thread `source="tardis"` through every CeFi adapter write + extend
      `record_empty_for_shard`/`record_failed_for_shard` to accept + forward `source`.
      `market-data-processing-service/.../core/canonical_writer.py`. (No `SOURCE_PRIORITY` change needed yet — `tardis`
      is already the declared source; expand the list only when the alternative actually lands.)
- [ ] [TEST] P1. CeFi unit test: a cefi cell without `source=` raises; `source="tardis"` persists; a future
      `["<alt>", "tardis"]` registry expansion resolves two sources by priority.
- [ ] [DATA] P1. Backfill `source="tardis"` onto the existing cefi corpus — **fold into
      `cefi_manifest_canonicalisation_2026_06_01.md` C-source rider** (its single bundled walk owns the cefi `_index`;
      do NOT open a separate cefi source walk — single-walk discipline). If that walk has not launched, run direct (see
      § Migration scope, two steps): (1) data-parquet column backfill — **write `backfill_cefi_source_column.py`** (copy
      tradfi template) then fan across same-region VMs, sharded by `day=` (no egress, idempotent); (2) manifest
      re-consolidation after. Labels the corpus before any Tardis swap.

### Phase 4 — Sports writer source (P1)

- [x] ✅ [MTDS] P1. Sports multi-source `FIXTURES` threaded `source="api_football"` at both writers —
      instruments-service@6bbd6919. **NOTE:** the `FIXTURES` (multi-source) manifest writers are in
      **instruments-service** (`engine/orchestrator.py` `run_batch_instruments` +
      `triggers/sports_fixtures_daily_repoll.py`), not MTDS adapters as the item assumed. Single-source sports cells
      (FIXTURE_EVENTS, INJURIES, …) auto-stamp; `record_empty` paths are exempt (no category).
- [x] ✅ [TEST] P1. Sports `FIXTURES` multi-source covered in UTL `test_manifest_writer_source.py` — utl@0f7198f2
      (raise-without-source + stamp-with-`api_football`); + UAC generic resolution for sports uac@559dc81b.
- [x] ✅ [SCRIPT] P1. ~~Write `backfill_sports_source_column.py` (copy tradfi template)~~ — **CLOSED WON'T-DO 2026-06-03
      (redundant + would violate single-walk discipline).** The path→column source lift is ALREADY implemented in
      `market-tick-data-service/.../scripts/rebuild_sports_manifest_v9.py` `_source_from_row()` (reads source from the
      `source`/`data_source`/`venue` columns + the `pipeline_mode` path token `batch_X→X`, closed-set), and the
      rebuilder re-emits every captured row via `writer.add(source=…)` on the canonical column layout as part of the
      single C-walk. A separate script would be a second sports source walk — banned by the next todo + single-walk
      discipline. Verified via the 2026-06-03 dry-run (MDPS PLAN lines drop `data_source=ODDS_API/` from the path →
      source goes to column).
- [ ] [DATA] P1. Backfill the existing sports corpus — **fold into `sports_manifest_canonicalisation_2026_06_01.md`
      C-source rider** (its single bundled walk owns the sports `_index`; do NOT open a separate sports source walk —
      single-walk discipline). If that walk has not launched, run direct (parallel in-region VMs sharded by `day=`, see
      § Migration scope) + manifest re-consolidation after. Confirms sports source moves path→column for the whole
      corpus.

### Phase 5 — Downstream reconciliation wired for all multi-source asset groups (P0 correctness)

- [ ] [TEST] P0. Prove the consumer read path resolves source priority for **cefi/defi/tradfi** (not just tradfi):
      2-source cell (same instrument+ts from two providers, co-mingled in one folder) → consumer emits exactly ONE
      resolved row via `select_primary_available_source()`. No silent double-count. Cover features-service consumers.
      **PARTIAL — resolution PRIMITIVES proven generic (uac@559dc81b: select_primary picks index-0 primary per cell;
      detect_dual_source_conflicts surfaces overlaps). REMAINING: wire the resolver into the cefi/tradfi consumer read
      paths — currently dead code (see finding below).** **⚠️ SPORTS DESCOPED 2026-06-03 (slot-4 read-path audit):
      sports multi-source is `FIELD_UNION`, NOT same-field source-pick — different providers contribute DIFFERENT fields
      per fixture (API-Football base + FootyStats predictions + Understat xG), merged by
      `features_service/sports/exporters/derived_features_exporter.py::_merge_provider_columns` ("left-merge
      non-overlapping provider columns" — the resolver docstring's rule-4, explicitly "handled at the consumer/writer
      layer, NOT by select_primary"); odds are per-bookmaker (each `venue=` is a DISTINCT instrument, not the same
      metric twice). So `select_primary_available_source` does not apply to sports — sports reads are already correct.
      Remaining scope is **cefi/tradfi** same-field dual-source ONLY (e.g. tradfi databento/massive), owned by this
      cross-AG plan, not slot-4 sports.**
- [x] ✅ [UAC] P1. Confirmed (2026-06-01 read-path audit): `detect_dual_source_conflicts()` /
      `select_primary_available_source()` are generic (not tradfi-gated) but **invoked by NO non-test consumer** —
      result filed as the finding below. The conflict-detection primitive itself is tested (uac@559dc81b).
- [ ] [UAC] P1. **FINDING (2026-06-01 read-path audit; SHARPENED 2026-06-03 slot-4)**:
      `select_primary_available_source()` / `detect_dual_source_conflicts()` are generic + unit-tested (uac@559dc81b)
      but **called by NO non-test consumer** — dead code at the read layer. **Read-layer reality (slot-4 audit):** there
      is NO single generic features-service reader — each family has its own loader
      (`delta_one/app/core/data_loader.py`, `volatility/core/data_loader.py`,
      `onchain/adapters/mtds_canonical_reader.py` [DeFi-only], sports `data/gcs_reader.py`), so this is a **per-loader**
      wire, not one insertion point. **Sports is OUT** (FIELD_UNION, see Phase-5 TEST todo). Practical same-field cases
      needing the resolver: **tradfi** (databento/massive co-mingled — the only live 2-source pair today) + **cefi**
      when its 2nd source lands. Recipe per loader: after reading a cell's parquet, take the distinct `source` column
      values → `select_primary_available_source(ag, data_type, available)` → filter rows to the winning source
      (dedup-to-primary), with a 2-source→1-row regression test. Owned by this cross-AG plan (tradfi/cefi), not slot-4
      sports.
- [ ] [UTL] P1. **FINDING (2026-06-01 read-path audit)**: `manifest_consolidator.py` dedup key (`_BASE_DEDUP_COLS` +
      `_OPTIONAL_DEDUP_COLS`) **omits `source`** — two source rows for one `(date, venue, data_type, …)` cell collapse
      to ONE row by last-write-wins on `(attempted_at, written_at)`, NOT by `SOURCE_PRIORITY`. Matches the shipped
      tradfi **union** model (per-source provenance lives in the parquet `source` column), so not a data-loss bug today.
      **Decision (sequence with the data-side backfill)**: if per-source _manifest_ rows must be preserved, add `source`
      to `_OPTIONAL_DEDUP_COLS` — but that changes consolidation cardinality for all asset groups (naive consumers would
      then see N rows/cell), so it must land WITH the read-path resolver wiring above. Do NOT change unilaterally.
- [ ] [TEST] P1. **`available_at` parity across sources (batch = live)**: rows from any source for a cell are
      timestamped with the live-mode `available_at` of the `SOURCE_PRIORITY` top entry — NOT each vendor's slower
      archive time. A 2-source fixture asserts identical `available_at` derivation per cell, so swapping/adding a source
      never shifts the lookahead. (Covers the tradfi audit item (n) generalised to all asset groups.)

### Phase 6 — QG + audit instructions + codex (P1)

- [ ] [QG] P1. **(checker DONE, wiring REMAINING)** Checker generalised —
      `check_tradfi_source_explicit_at_record_captured.py` now flags only when a callsite's resolved
      `(category, data_type)` (literal or module-constant) is multi-source per `source_required()` AND `source=` is
      absent; covers `record_captured` + `add`; degrades to no-op if UAC absent (PM@5bba69651, slot ref). Verified
      catches defi/tradfi multi-source-blank, skips single-source (auto-stamp). **REMAINING: wire into MTDS + MDPS
      `quality-gates.sh` — blocked until the checker reaches LDR (can't wire a clean repo to a PM script not yet
      promoted).**
- [x] ✅ [AUDIT] P1. Add a **Dual-source provenance** section to ALL per-epic audit instruction files: `tradfi_master`
      (items h–o), `cefi_master` (i–l), `sports_master` (h–j, incl. path→column migration finding), `predictions_master`
      (h–j, N/A-by-design invariant), `defi_master` (n1–n4, strongest multi-source case), `mtds_mdps_master` (Mode 1
      item j, write-time stamping), `manifest_master` (item i, the `source`-column schema home + registry-driven gate).
      The defi/mtds_mdps/manifest edits were layered on top of an in-flight "zero-rows = silent lie" sweep
      (operator-acked 2026-06-01 as ready-to-ship → bundled).
- [x] ✅ [CODEX] P1. Generalised `codex/02-data/contracts-scope-and-layout.md` (new § "Generalised beyond TradFi —
      `source` is universal across ALL asset groups") + `honest-absence-downstream-handling.md` (§ "Multi-source cell
      consumer policy" banner generalised to all groups + read-path-finding note) — PM slot ref. Documents auto-stamp +
      computed-exempt + the generic resolver/read-path status.
- [ ] [MTDS] P1. **Prediction — stamp `source` on every cell NOW** (`polymarket_clob` / `polymarket_gamma_api` /
      `kalshi_*`): single-source today but stamp for swap-resilience (a future Polymarket data-provider change).
      Required by the universal Phase 1 gate. `market-tick-data-service/.../engine/orchestrator.py`
      (`record_captured_from_counts`). **Historical backfill/re-consolidation folds into
      `prediction_manifest_canonicalisation_2026_06_01.md` C-source rider** (its single bundled walk owns the prediction
      `_index` — do NOT open a separate prediction source walk).
- [ ] [CODEX] P2. Document the prediction invariant precisely: stamping `source` ≠ treating venues as sources —
      Polymarket/Kalshi stay separate **venues**, cross-venue dispersion is a feature-layer concern, and when Kalshi
      lands it is a venue addition; AND each venue's cell still stamps its own source. Both are true.

### Phase 7 — Prod data-state verification (P1, post-enforcement)

- [ ] [DATA] P1. **TradFi backfill UNBLOCKED** (`MASSIVE_API_KEY` provided by operator 2026-06-01) — run the dual-source
      backfill per `tradfi_massive_dual_source_2026_05_28.md` Phase 5: stamp `source=databento` on legacy tradfi rows +
      ingest MASSIVE via **S3 flat-files** for bulk history (flat-files are independent of the REST tier — the bulk
      path; REST for incremental/live). Unblock the dual-source plan's deferred table accordingly.
- [ ] [AUDIT] P1. After enforcement lands, read ACTUAL `source` column distribution per (asset_group, venue, data_type)
      in prod manifests/parquets — confirm **zero blank source on EVERY cell, all asset groups** (not just
      multi-source). Data-state, NOT constant (manifest-v8 lesson: constant said 8 while 0% of rows were v8). Report
      per-cell histogram. **TOOL BUILT (read-only)**:
      `scripts/quality_gates/audit_source_column_distribution.py --manifest-path <gs-uri> [--strict]` — per-cell
      `source` histogram, classifies GREEN/RED(external-blank)/EXEMPT(computed/unregistered) via
      `external_sources_for()`; `--strict` exits 1 on any external-vendor blank. PM slot ref. **PROD RUN still
      sequenced** AFTER the bucket remediation + enforcement deploy + backfill (running pre-backfill correctly reports
      ~100% blank = the baseline). Re-run post-backfill to confirm zero-blank.

## Migration scope — `source` lives in TWO places (do not conflate)

`source` is recorded **both** as a per-row column inside the GCS **data parquets** AND as a field on the **manifest**
row (confirmed: UTL writegate v9 adds the column; `backfill_tradfi_source_column.py` "single-walk pass over every TradFi
parquet … stamps `source` on every row … rewrites the file in-place"; manifest `source` is populated by
re-consolidation). Backfilling the existing corpus is therefore **two distinct steps, per asset group**:

1. **Data-parquet column backfill (the data itself)** — walk every parquet under that asset group's canonical prefix,
   stamp the known historical `source` on every row, rewrite in place. Template:
   `market-tick-data-service/.../scripts/backfill_tradfi_source_column.py` (one per asset group: cefi→`tardis`,
   defi→`onchain_subgraph`/per-handler, sports→its source, prediction→`polymarket_clob`). Idempotent (skip files already
   carrying a non-blank `source`).
2. **Manifest re-consolidation** — runs **after** step 1; the consolidator re-derives the manifest `source` from the
   rewritten parquets. Index-level, cheap. (TradFi precedent: drain → consolidate → snapshot → backfill → re-consolidate
   → resume.)

> **EXECUTE — parallel in-region VMs (operator decision 2026-06-01), but SEQUENCE behind the running tick-bucket
> remediation.** This is just read+write; on VMs in the same region there is **no egress cost** and it fans across many
> VMs, so it is **fast — do not defer to a future window.** Single-walk discipline's real constraint is _"touch each
> object once,"_ NOT _"wait."_ Decide per bucket:
>
> - **A tick-bucket migration is RUNNING right now** — `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`
>   (legacy→canonical **server-side copy**, writers already drained). Its copy does NOT add `source`. **Do not run a
>   concurrent `source` walk on those objects** (race). Sequence behind it: run the `source` backfill on the
>   **canonical** buckets **after** the copy completes. The copy is metadata-cheap (server-side), so the only content
>   rewrite is this backfill → still "touch once" for the expensive op.
> - **If a CONTENT-rewriting whole-corpus pass is pending** for a bucket (e.g. the defi canonicalisation migration
>   `defi_manifest_canonicalisation_2026_06_01.md`, or a v9 schema migration), **fold the `source`-column add into that
>   pass** — read+written once with both changes.
> - **If nothing is pending/running** for a bucket, the `source` backfill **is** that bucket's walk — run it directly.
>
> Check the MTDS migration registry to pick run-direct / fold-in / sequence-behind per bucket (never to defer). **New
> writes stamp both places at write time → no migration for new data.**

### Execution sequencing (per asset group, parallelised across VMs)

1. **Write-path fix first (Phase 1 + 2)** — land the universal source gate + writer stamping so new writes carry
   `source`; otherwise the backfill races fresh blank rows.
2. **Pre-migration drain (HARD RULE)** — stop that bucket's writer VMs (GCP Cloud Run + AWS batch), consolidate the
   manifest, snapshot `_index` to `_index/snapshots/pre_source_backfill_<date>.parquet`.
3. **Parallel data-parquet backfill** — fan the per-asset-group `backfill_<ag>_source_column.py` (template = the tradfi
   one) across many same-region VMs, sharded by `day=`/partition (idempotent; skip non-blank). No egress (in-region).
4. **Manifest re-consolidation** → verify zero blank `source` (data-state read) → **resume writers**.

## Out of scope (deferred — named successors required)

- (none for the source backfill — operator authorised running it now, parallelised; see § Migration scope.) Per-bucket
  execution is tracked by the Phase-3/4/7 backfill todos + a `<asset_group>_source_backfill_<date>.md` runbook if a
  bucket's fold-in/run-direct needs its own ledger.

## Completion criteria — "closed in full" across all asset groups

This plan is closeable only when ALL of the following are GREEN (no asset_group, no step skipped):

- [ ] [DATA] P0. **Write-path** — universal gate live (`source` blank OR not-in-`SOURCE_PRIORITY` → raise) for every
      asset group; every MTDS/MDPS writer (cefi/defi/sports/prediction/tradfi) stamps `source`; QG STEP 5.64
      generalised + green.
- [ ] [DATA] P0. **Data parquets** — `source` column populated on every ingested cell across all five asset groups, read
      from ACTUAL prod rows (data-state, not the constant): **zero blank `source`**. Sports migrated path→column. MDPS
      candles carry the inherited upstream source.
- [ ] [DATA] P0. **Manifest** — re-consolidated; manifest `source` populated for every cell; multi-source cells = two
      rows.
- [ ] [DATA] P0. **Downstream** — consumer read path resolves source priority for every multi-source asset group (one
      row per instrument+ts, no double-count); `detect_dual_source_conflicts()` surfaces divergence; `available_at`
      parity holds.
- [ ] [DATA] P0. **Sequencing honoured** — source backfill ran behind / folded into the running tick-bucket remediation,
      on canonical buckets, no race.
- [ ] [CODEX] P1. **Codex + audit instructions** updated to the universal rule; audit result archived when every todo
      above is `[x]`.

Scope exemptions (by design, not gaps): features-service / strategy / execution outputs (computed — no vendor source).

## Codex SSOTs

- `codex/02-data/contracts-scope-and-layout.md` — generalise dual-source `source` column section beyond tradfi
- `codex/02-data/honest-absence-downstream-handling.md` — generalise multi-source consumer policy
- `codex/02-data/availability-manifest-and-data-status.md` — `source` field semantics across asset groups

## Provenance

Crosscutting data-source provenance audit run 2026-06-01 (slot 1, operator-directed). Four parallel read-only audits
(cefi/defi/sports/prediction) + the prior tradfi exploration. Operator directive: provenance must be auditable across
**all** asset groups, gaps exposed, PM active todos created.
