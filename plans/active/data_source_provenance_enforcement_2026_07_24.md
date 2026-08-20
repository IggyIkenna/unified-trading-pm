---
doc_type: plan
title: Data-source provenance enforcement — all asset groups (split from M-1)
summary: >-
  Extracted 2026-07-24 from data_completion_to_100_all_ag_2026_06_21.md (M-1) per the plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, bucket-(d) split, operator-approved). This is the
  still-inline residual of the already-archived `data_source_provenance_all_asset_groups_2026_06_01.md` (source column +
  SOURCE_PRIORITY enforcement across cefi/defi/tradfi/sports/prediction), migrated VERBATIM — no scope added, dropped,
  or reworded. M-1 remains the coordinator hub for cross-cutting work and owns the shared Progress Log.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui]
scope: [engineer, admin]
tags: [backfill, manifest, source-provenance, data-completion, data-correctness]
related:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
last_updated: 2026-08-17
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  data_completion_to_100_all_ag_2026_06_21 (M-1) -- extracted 2026-07-24, plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md) bucket-(d) split, operator-approved.
drift_direction: advance-code
context_scope:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/source_priority.py,
    /codex/02-data/pipeline-mode-partition.md,
    /plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md,
    /codex/04-architecture/instruments-preflight-chain.md,
  ]
---

# Data-source provenance enforcement — all asset groups

> **Split from M-1 on 2026-07-24** (`data_completion_to_100_all_ag_2026_06_21.md`, plan line-cap remediation,
> `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` bucket-(d) split, operator-approved). This plan carries
> M-1's still-inline `data_source_provenance_all_asset_groups_2026_06_01.md` fold-in residual **verbatim**; M-1 stays
> the coordinator hub (measured snapshot, per-AG launch matrix, cross-cutting scope, shared Progress Log).
>
> **Read M-1 first** for the program-level snapshot + launch matrix. This plan is the `source` column /
> `SOURCE_PRIORITY` enforcement tail specifically (write-path gate, historical backfill, read-path resolver, per all
> five asset groups).

### From `data_source_provenance_all_asset_groups_2026_06_01.md` (archived 2026-07-13 -- Data-source provenance enforced across all asset groups (source column + SOURCE_PRIORITY))

- [x] ✅ [SCRIPT] P1. **SHIPPED via `cross_cutting_satellite_ao_dispatch_batch3_2026_08_09.md` todo 1** (this finalize
      plan's own todo 2 archives that batch doc). Wrote `backfill_defi_source_column.py` —
      `market-tick-data-service@63776a43`, verified ancestor of `origin/live-defi-rollout`.

- [ ] [DATA] P1. Backfill the existing DeFi corpus — run now, parallel in-region VMs sharded by `day=` (see § Migration
      scope); fold into the defi canonicalisation migration (`defi_manifest_canonicalisation_2026_06_01.md`) if open,
      else run direct; manifest re-consolidation after. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [MTDS] P1. **SHIPPED via `cross_cutting_satellite_ao_dispatch_batch3_2026_08_09.md` todo 2** — the narrow
      remaining slice (the captured write-path already shipped `source="tardis"` for cefi; this fixed
      `record_empty_for_shard`/`record_failed_for_shard` in `market-data-processing-service`'s `canonical_writer.py` to
      likewise forward `source`). `market-data-processing-service@c8bece4e8`, verified ancestor of
      `origin/live-defi-rollout`. The historical-corpus backfill sub-item stays here (rides the cefi C-source RIDER, see
      below) — NOT covered by batch3.

- [x] ✅ [TEST] P1. **SHIPPED via `cross_cutting_satellite_ao_dispatch_batch3_2026_08_09.md` todo 3.** CeFi unit test
      confirmed live for `("cefi", "trades")`: blank `source=` raises, `source="tardis"` persists, a synthetic
      `SOURCE_PRIORITY` expansion resolves by priority order — `market-tick-data-service@78a8c93b`, verified ancestor of
      `origin/live-defi-rollout`.

- [ ] [DATA] P1. Backfill `source="tardis"` onto the existing cefi corpus — **fold into
      `cefi_manifest_canonicalisation_2026_06_01.md` C-source rider** (its single bundled walk owns the cefi `_index`;
      do NOT open a separate cefi source walk — single-walk discipline). If that walk has not launched, run direct (see
      § Migration scope, two steps): (1) data-parquet column backfill — **write `backfill_cefi_source_column.py`** (copy
      tradfi template) then fan across same-region VMs, sharded by `day=` (no egress, idempotent); (2) manifest
      re-consolidation after. Labels the corpus before any Tardis swap. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. Backfill the existing sports corpus — **fold into `sports_manifest_canonicalisation_2026_06_01.md`
      C-source rider** (its single bundled walk owns the sports `_index`; do NOT open a separate sports source walk —
      single-walk discipline). If that walk has not launched, run direct (parallel in-region VMs sharded by `day=`, see
      § Migration scope) + manifest re-consolidation after. Confirms sports source moves path→column for the whole
      corpus. **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

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
      cross-AG plan, not slot-4 sports.** **TRADFI SLICE DONE + LAYER CORRECTED (slot-6 2026-06-05, UAC@637288d4 +
      mtds@0579438):** the read-path resolution is wired at the **MDPS raw read** (the actual co-mingle surface — two
      `pipeline_mode=`-partitioned objects per cell, NOT row-level co-mingle in one parquet; see the resolved FINDING
      below). `_resolve_multi_source_blobs` collapses a 2-source cell to exactly ONE primary-source object → no
      double-aggregate; regression `tests/unit/test_orchestration_scanner_multi_source.py` asserts 2-source→1 primary
      (databento>massive; massive>yahoo for ohlcv_15m) + the no-op guards. This covers tradfi (the only live 2-source
      pair). **REMAINING for full P0:** cefi when its 2nd source lands (same MDPS path, no new wiring — just a cefi
      regression case) → so this P0 is tradfi-complete; leave open for the cefi-2nd-source case. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [UTL] P1. **FINDING (2026-06-01 read-path audit)**: `manifest_consolidator.py` dedup key (`_BASE_DEDUP_COLS` +
      `_OPTIONAL_DEDUP_COLS`) **omits `source`** — two source rows for one `(date, venue, data_type, …)` cell collapse
      to ONE row by last-write-wins on `(attempted_at, written_at)`, NOT by `SOURCE_PRIORITY`. Matches the shipped
      tradfi **union** model (per-source provenance lives in the parquet `source` column), so not a data-loss bug today.
      **Decision (sequence with the data-side backfill)**: if per-source _manifest_ rows must be preserved, add `source`
      to `_OPTIONAL_DEDUP_COLS` — but that changes consolidation cardinality for all asset groups (naive consumers would
      then see N rows/cell), so it must land WITH the read-path resolver wiring above. Do NOT change unilaterally.
      **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation
      ruling.)**

- [x] ✅ [TEST] P1. **SHIPPED via `cross_cutting_satellite_ao_dispatch_batch3_2026_08_09.md` todo 4.** `available_at`
      parity fixture added for the registered 2-source cell (`tradfi/ohlcv_15m`, databento/yahoo) — proves derivation is
      source-blind by construction. `market-tick-data-service@63ce1e05`, verified ancestor of
      `origin/live-defi-rollout`.

- [x] ✅ [QG] P1. Checker generalised — `check_tradfi_source_explicit_at_record_captured.py` now flags only when a
      callsite's resolved `(category, data_type)` (literal or module-constant) is multi-source per `source_required()`
      AND `source=` is absent; covers `record_captured` + `add`; degrades to no-op if UAC absent (PM@5bba69651, slot
      ref). Verified catches defi/tradfi multi-source-blank, skips single-source (auto-stamp). **Wiring complete
      2026-08-15**: MDPS already wired (STEP 5.109); MTDS closed the remaining gap —
      `market-tick-data-service@bbd54fc6b8` (STEP 5.97, slot-19·infra), verified clean run (0 baselined, 0 new
      occurrences). **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [x] ✅ [MTDS] P1. **RESOLVED-MOOT via `cross_cutting_satellite_ao_dispatch_batch3_2026_08_09.md` todo 5.** A12a — all
      8 named DeFi collect handlers were ALREADY wired to `assert_defi_catalog_fresh(...)` (7 since `fca15304`
      2026-06-05, the 8th since `b77fba7a` 2026-06-21) — this item's "8 still-unwired" framing was stale by ~2 months.
      The one genuine gap (a missing DeFi row in `/codex/04-architecture/instruments-preflight-chain.md`) was added, no
      MTDS code change needed.

- [x] ❌ [DATA] P1. OBSOLETE/WONTFIX — closed 2026-08-09 (cross_cutting_satellite_ao_dispatch_batch3 finalize
      reconciliation): superseded, folded into the P0 "Data parquets"/"Manifest" rollup items below, no separate
      carve-out. ~~TradFi backfill UNBLOCKED (`MASSIVE_API_KEY` provided by operator 2026-06-01) — run the dual-source
      backfill per `tradfi_massive_dual_source_2026_05_28.md` Phase 5: stamp `source=databento` on legacy tradfi rows +
      ingest MASSIVE via **S3 flat-files** for bulk history (flat-files are independent of the REST tier — the bulk
      path; REST for incremental/live). Unblock the dual-source plan's deferred table accordingly.~~ **Massive was
      REMOVED as a TradFi source 2026-07-19** (operator ruling: Databento = batch SoT, Yahoo = daily; routing DELETED
      `uac@a2beed46`/`mtds@362a487e`) and its GCS corpus **PURGED 2026-07-21** (accepted permanent loss);
      `tradfi_massive_dual_source_2026_05_28.md` itself now carries a `status: superseded` banner ("OBSOLETE — do not
      build"). No MASSIVE ingestion remains possible or wanted. The still-valid half (zero-blank `source` on every
      tradfi cell, including legacy rows) is already covered generically by the P0 "Data parquets" / "Manifest" todos
      below in this same doc — no separate carve-out needed. SSOT: `/codex/02-data/tradfi-databento-sourcing-ssot.md`,
      `plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md`. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [AUDIT] P1. After enforcement lands, read ACTUAL `source` column distribution per (asset_group, venue, data_type)
      in prod manifests/parquets — confirm **zero blank source on EVERY cell, all asset groups** (not just
      multi-source). Data-state, NOT constant (manifest-v8 lesson: constant said 8 while 0% of rows were v8). Report
      per-cell histogram. **TOOL BUILT (read-only)**:
      `scripts/quality_gates/audit_source_column_distribution.py --manifest-path <gs-uri> [--strict]` — per-cell
      `source` histogram, classifies GREEN/RED(external-blank)/EXEMPT(computed/unregistered) via
      `external_sources_for()`; `--strict` exits 1 on any external-vendor blank. PM slot ref. **PROD RUN still
      sequenced** AFTER the bucket remediation + enforcement deploy + backfill (running pre-backfill correctly reports
      ~100% blank = the baseline). Re-run post-backfill to confirm zero-blank. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. **Write-path** — universal gate live (`source` blank OR not-in-`SOURCE_PRIORITY` → raise) for every
      asset group; every MTDS/MDPS writer (cefi/defi/sports/prediction/tradfi) stamps `source`; QG STEP 5.64
      generalised + green. **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per
      MTDS consolidation ruling.)** **Note (2026-08-15, slot-11): fold in a 1-row manual manifest patch** —
      `cefi/HYPERLIQUID/trades`, `date=2026-06-29`, `instrument_id=HYPERLIQUID:PERPETUAL:IP-USD@LIN`, both `source` and
      `pipeline_mode` blank, `capture_status=empty_confirmed`. Confirmed purely historical (no live write path today can
      reproduce it — both `onchain_perp_batch_handler.py` and `live/manifest_recorder.py` require `pipeline_mode`
      unconditionally on every write, verified since the batch handler's first commit). Not worth a standalone script;
      patch this one row whenever this todo is next worked. See
      `/plans/archive/issues/hyperliquid_trades_blank_pipeline_mode_write_path_gap_2026_08_15.md`.

- [ ] [DATA] P0. **Data parquets** — `source` column populated on every ingested cell across all five asset groups, read
      from ACTUAL prod rows (data-state, not the constant): **zero blank `source`**. Sports migrated path→column. MDPS
      candles carry the inherited upstream source. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. **Manifest** — re-consolidated; manifest `source` populated for every cell; multi-source cells = two
      rows. **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation
      ruling.)**

- [ ] [DATA] P0. **Downstream** — consumer read path resolves source priority for every multi-source asset group (one
      row per instrument+ts, no double-count); `detect_dual_source_conflicts()` surfaces divergence; `available_at`
      parity holds. **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [ ] [DATA] P0. **Sequencing honoured** — source backfill ran behind / folded into the running tick-bucket remediation,
      on canonical buckets, no race. **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

- [ ] [CODEX] P1. **Codex + audit instructions** updated to the universal rule; audit result archived when every todo
      above is `[x]`.

Scope exemptions (by design, not gaps): features-service / strategy / execution outputs (computed — no vendor source).
**(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — P0 provenance enforcement whose [DATA] todos are prod corpus
  backfills explicitly folded into other plans' single-walk windows (cefi/sports C-source riders) — cross-plan
  single-walk sequencing is coordination judgment. Genuinely AO-eligible slices exist ([SCRIPT]
  backfill_defi_source_column, [TEST] unit tests, [QG] checker wiring) but splitting them out is a plan-authoring call.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03 (full re-scout pass)**: re-verified context_scope (6 entries, corrects the prior marker's
  stale count) -- unchanged; already covers the enforcement SSOT source + the preflight-chain codex doc the A12a todo
  needs.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- reaffirms 2026-07-30 (unchanged): P0
  provenance enforcement whose `[DATA]` todos are prod corpus backfills explicitly folded into other plans' single-walk
  windows (cross-plan sequencing is coordination judgment); genuinely AO-eligible slices exist (`[SCRIPT]`
  backfill_defi_source_column, `[TEST]` unit tests, the A12a remaining-8-handler wiring) but splitting them out of this
  coordination doc into a fresh batch is plan-authoring work this audit does not do.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **cross_cutting_satellite_ao_dispatch_batch3 finalize reconciliation, 2026-08-09 (slot 15)**: reconciled all 5
  `EXTRACTED 2026-08-09 -> batch3` pointers against batch3's now-done todos, converting each to a checked `[x]` with the
  verified shipping commit citation (all 4 distinct commits confirmed ancestors of `origin/live-defi-rollout`:
  `market-tick-data-service@63776a43`, `market-data-processing-service@c8bece4e8`, `market-tick-data-service@78a8c93b`,
  `market-tick-data-service@63ce1e05` — the A12a item resolved-moot, no code commit). Also flipped the stale
  obsolete-Massive checkbox (`[ ]` -> `[x]`, item's own text already explained it's superseded/folded into the P0 rollup
  -- the checkbox itself was the only stale part). Doc keeps 13 open `- [ ]` items (DeFi/cefi/sports corpus backfills,
  the tradfi read-path resolver PARTIAL, the manifest dedup-key FINDING, the QG checker wiring, the 6 big P0 rollups,
  the CODEX item) -- `status` stays `active`, nowhere near zero open work.
**context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:623b4887e36857be]: KEEP-NA, valid -- Cross-AG (cefi/defi/tradfi/sports/prediction) source-provenance enforcement coordinator. All 12 open items are either (a) prod-corpus backfills explicitly required to fold into OTHER plans' single-walk windows (cefi/sports C-source riders, defi canonicalisation) -- cross-plan sequencing judgment, not a worker-alone bounded call, or (b) P0 rollup items (write-path gate verification, data-parquet zero-blank confirmation, manifest re-consolidation, downstream resolver wiring, sequencing) spanning all 5 asset groups, or (c) explicitly dependency-gated on the resolver-wiring item landing first ('must land WITH the read-path resolver wiring... Do NOT change unilaterally') or on cefi's still-nonexistent 2nd data source. Two independent prior na-eligibility-audit passes (2026-07-30, 2026-08-08 round7) reached the identical KEEP-NA verdict with matching reasoning; my own fresh read of all 12 items agrees -- none is a small, worker-determinable outcome free of cross-plan coordination judgment.
