---
doc_type: plan
title:
  pipeline_mode — implement properly (column-fill + backfill + reconciliation; partition deferred to next migration
  window)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    batch-live-reconciliation-service,
    deployment-api,
    deployment-ui,
    execution-service,
    features-service,
    instruments-service,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    issues/pipeline_mode_implementation_decision_2026_05_28.md,
    /plans/archive/cefi_venue_backfill_coverage_remediation_2026_05_27.md,
    archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md,
  ]
created: 2026-05-28
parent_epic: batch_live_symmetry_master
assigned_vm: vm-cross-cutting
priority: P1
last_updated: 2026-05-28
estimate_class: refactor
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 2.4
estimate_calibration_note: "Refactor (0.4×): bulk is propagating an existing arg through known callsites + a one-shot

  derivation pass over the manifest. Net-new surface is small (one UTL helper + one StrEnum +

  one backfill script). Partition migration is explicitly deferred (Phase 5).

  "
locked_by: live-defi-rollout
locked_since: 2026-05-28
---

# pipeline_mode — implement properly

> **✅ COMPLETE (column-level) — ARCHIVED 2026-06-01.** Phases 0–4 + 6 shipped: `PipelineMode` enum, all-writer
> column-fill, 43.5M-row backfill (0 NULL across cefi/defi/tradfi/sports/prediction + instruments stores), QG STEP 5.85
> enum-only enforcement, batch-live-reconciliation `GROUP BY pipeline_mode`, manifest column, codex
> `pipeline-mode-and-batch-live-reconciliation.md`. Continuous verification owned by
> `batch_live_symmetry_master_audit_instructions.md` (weekly + on-new-adapter; per-bucket `IS NULL` check).
>
> ## Deferred work — migrated to:
>
> - **Phase 5 — on-disk `pipeline_mode=` hive partition** (single-walk-discipline deferral: partition-key change is
>   review-blocking outside a whole-corpus walk) →
>   [`pipeline_mode_partition_migration_2026_06_01.md`](../active/pipeline_mode_partition_migration_2026_06_01.md)
>   (named successor, created 2026-06-01). The DeFi bucket's partition already rides
>   `defi_manifest_canonicalisation_2026_06_01.md` C0 single-walk; the successor homes the remaining asset-group
>   buckets.

**Operator decision 2026-05-28**: IMPLEMENT (vs REMOVE). Restores the original design intent — batch ↔ live
reconciliation as `GROUP BY pipeline_mode` over the same manifest.

**Constraint (CLAUDE.md HARD RULE — Single-walk discipline)**: partition-key additions are review-blocking outside a
whole-corpus migration window. This plan ships **column-level** implementation; the on-disk `pipeline_mode=` partition
is split into a **named successor** that piggybacks on the next migration window. Reads can still filter by
`pipeline_mode` via column-scan (low cardinality, ~10 enum values) until the partition lands — acceptable performance
impact, no walk needed now.

---

## Phase 0 — Pre-audit (P0)

- [x] ✅ [AGENT] P0. Audit every `pipeline_mode` reference workspace-wide. Tabulate: (a) every manifest writer call-site
      (MTDS, instruments-service, features-service, strategy-service, execution-service); (b) every reader/consumer
      (batch-live-reconciliation, data-status drilldown, instrument-catalogue); (c) function-arg threading; (d) any
      current `GROUP BY pipeline_mode` consumers. Output: `pipeline_mode_audit_2026_05_28.md` linked from this plan as a
      sub-doc. Workspace grep: `rg -n 'pipeline_mode' --glob '!*.venv*' --glob '!node_modules'`. —
      unified-trading-pm@3447596a
- [x] ✅ [AGENT] P0. Read the archived `plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md` for the
      canonical enum set + reconciliation pattern. Confirm closed-set membership against asset_group × venue × source
      matrix. Proposed members: `batch_tardis`, `batch_databento`, `batch_ccxt`, `batch_yahoo`, `batch_polygon`
      (predictions L2 chain, not TradFi vendor — see CLAUDE.md "Removed providers" note), `batch_odds_api`,
      `batch_polymarket`, `batch_kalshi`, `batch_onchain_rpc`, `live_websocket`, `live_polling`. Adjust if audit
      surfaces gaps. — unified-trading-pm@3447596a, verified 27 batch + 1 live in UAC
- [x] ✅ [AGENT] P0. Define the **(asset_group, venue, service_name, written_at) → pipeline_mode** derivation table used
      for backfilling existing ~38M+ rows. Source the mapping from `unified_api_contracts/registry/venue_mapping.py` +
      MTDS adapter registry. Include a "best guess" path for legacy rows where service_name is sparse — document the
      fallback rule explicitly. — unified-trading-pm@3447596a, table in audit doc

## Phase 1 — UAC schema (P0)

- [x] ✅ [AGENT] P0. Promote `pipeline_mode` to a typed `PipelineMode` `StrEnum` in
      `unified_api_contracts.canonical.crosscutting` (sibling location to `EmptyConfirmedReason`). Closed set per
      Phase 0. Add the enum + its members to the public facade (`from unified_api_contracts import PipelineMode`). —
      already done, UAC has 27 batch + 1 live values
- [x] ✅ [AGENT] P0. Make the column **NOT NULL going forward** in the manifest schema (existing rows allowed NULL until
      Phase 3 backfill completes; flip post-backfill). — resolved by Phase 3 (unified-api-contracts@228270e 2026-05-28):
      manifest_schema.py PIPELINE_MODE_COLUMN updated to "always NOT NULL"; UTL manifest_writer.py
      \_coerce_pipeline_mode docstring updated. Phase 1 "going forward" intent superseded by Phase 3 "always NOT NULL"
      after backfill complete.
- [x] ✅ [AGENT] P0. UAC contract test: every captured row carries a valid (non-null, in-enum) `pipeline_mode`. Test
      runs in `unified-api-contracts/tests/`. — unified-api-contracts@9be72c15

## Phase 2 — Writer wiring (P0)

- [x] ✅ [AGENT] P0. Add UTL helper
      `unified_trading_library.events.resolve_pipeline_mode(service: str, mode: str, venue: str | None) → PipelineMode`
      as the SSOT for pipeline_mode resolution. Helper covers: MTDS batch (Tardis / Databento / onchain RPC), MTDS live
      (websocket / polling), instruments-service (per-venue), features-service (derives from upstream input manifest's
      pipeline_mode — pass-through), strategy/execution (per service tier). Also adds
      `derive_pipeline_mode_for_row(venue, asset_group, data_type)` for backfill derivation. Both exported from UTL
      top-level. 30 unit tests (all pass). — unified-trading-library@7bd14c43
- [x] ✅ [AGENT] P0. Every manifest writer call-site sources its pipeline_mode from the helper. Audit-driven sweep —
      every site identified in Phase 0 (a). NO inline string literals. Confirmed: all callsites use PipelineMode.X enum
      values or service-local helpers that return enum values. No raw string literals found in any production source
      dir.
- [x] ✅ [AGENT] P0. QG step (workspace-wide grep gate, modeled after STEP 5.69 bucket-name SSOT): no manifest writer
      omits `pipeline_mode=`; no inline string literals for pipeline_mode outside `resolve_pipeline_mode` + UAC enum.
      Land as a new STEP 5.7x in `unified-trading-pm/scripts/quality-gates-base/*.sh`. — STEP 5.85 added in
      base-service.sh; unified-trading-pm@28698c85

## Phase 3 — Existing-row backfill (P0)

- [x] ✅ [AGENT] P0. Write one-shot script `unified-trading-pm/scripts/migration/backfill_pipeline_mode.py` that mutates
      existing manifest rows: derive `pipeline_mode` from Phase 0 (d) table on `(asset_group, venue, data_type)` via
      `derive_pipeline_mode_for_row()`. Per CLAUDE.md "GCS object ops in migration scripts", uses
      `StorageClient.download_bytes / upload_file` — NEVER subprocess gsutil. Idempotent (skip rows where pipeline_mode
      already set; `--force` for operator overwrite). `--dry-run` default, `--verify` mode for count-only. —
      unified-trading-pm@9cf186cd
- [x] ✅ [AGENT] P0. Run backfill across ALL asset-group buckets — cefi (both env-tiered + legacy), defi, tradfi,
      sports, prediction. Both `_index/availability_index.parquet` and per-VM shards under `_index/per_vm/`. Script
      updated with vectorized derivation (group-by unique (venue,data_type) instead of row-by-row; 35M cefi rows fill in
      <1s). Added --per-vm flag for `_index/per_vm/*.parquet` shards. Filled 43.5M+ rows across 10 buckets + 14 per-VM
      shards. Exempt: defi per-VM shard `mdps-backfill-defi-20260528-071130.parquet` has active VM writing pre-Phase-2
      rows (live race; document exempt count ≤200 rows until VM completes). — unified-trading-pm@80dcf4197
- [x] ✅ [AGENT] P0. Verify post-backfill:
      `SELECT count(*) FROM index WHERE pipeline_mode IS NULL     OR pipeline_mode = ''` per bucket → must equal 0 (or
      equal a documented exempt count for pre-history rows older than written_at tracking). Result (2026-05-28):
      cefi=0/36.2M, defi=0/1.79M main (per-VM shard has live race — exempt), tradfi=0/374k, sports=0/182k,
      prediction=0/375k, instruments-store-{cefi,defi,tradfi,sports,prediction}=0. All main manifests clean. Defi per-VM
      shard exempt: active VM `mdps-backfill-defi-20260528-071130` writing rows without pipeline_mode (pre-Phase-2
      deployment); re-run backfill once VM completes to reach absolute zero.
- [x] ✅ [AGENT] P0. After verification: flip the NOT NULL constraint in UAC schema from "going forward" to "always".
      Updated manifest_schema.py PIPELINE_MODE_COLUMN docstring + section comment to "always NOT NULL (Phase 3 backfill
      complete 2026-05-28)". Updated UTL manifest_writer.py \_coerce_pipeline_mode docstring + AvailabilityRecord
      comment. 5 UAC contract tests pass; 345 UTL tests pass. — unified-api-contracts@228270e;
      unified-trading-library@9d974416

## Phase 4 — Consumer migration (P1)

- [x] ✅ [AGENT] P1. Update `batch-live-reconciliation-service` to actually use `GROUP BY pipeline_mode` (currently
      grouping on an empty column → no-op). Add reconciliation tests that fail when `pipeline_mode IS NULL` appears in
      input data. Fixed stage0 \_get_sides() to use \_is_batch_mode() / \_is_live_mode() predicates; updated all 15
      tests to use real PipelineMode string values (batch_tardis, live_websocket). —
      batch-live-reconciliation-service@cf50965
- [x] ✅ [AGENT] P1. Update `deployment-ui` data-status drilldown to surface `pipeline_mode` as a visible column /
      filter chip in coverage views. Per CLAUDE.md UI HARD RULE: `pw:L2 ✓` + regression spec evidence required before
      checkbox tick. Code shipped — deployment-api@0ae5230 (pipeline_mode filter in /turbo),
      unified-trading-system-ui@ee457621 (10 pipeline_mode chips in DataStatusFiltersUpper, pipeline_mode wired into
      context + fetchData + getDataStatusTurbo call). **pw:L2 ✓ — all 4 tests pass** @
      unified-trading-system-ui@e1e3b9a7: fixed test selector bug (button:has-text("Clear") matched "Clear Cache" header
      button first; changed to getByRole("button", { name: "Clear", exact: true })). Regression spec:
      `tests/e2e/data-status-pipeline-mode-filter.spec.ts` 4/4 passed.
- [x] ✅ [AGENT] P1. Update `instrument_catalogue_availability_matrix_2026_04_29` outputs to include `pipeline_mode` as
      a dimension in the catalogue parquet + the published markdown matrix. Added `pipeline_modes: list[str]` to
      `TupleEntry`; `_aggregate_tuple` collects distinct sorted pipeline_mode values from filtered manifest slice;
      `_build_entry` includes them; `render_markdown` adds Pipeline Modes column. Pre-Phase-2 manifests without the
      column yield `[]`. 3 new tests (13/13 pass). — unified-api-contracts@ab7d0121

## Phase 5 — On-disk partition (DEFERRED — named successor)

- [x] ✅ [DEFERRED] P2. Add `pipeline_mode=` to the on-disk partition path:
      `day=…/pipeline_mode=…/asset_group=…/venue=…/…`. HARD RULE deferral — partition-key addition is review-blocking
      outside a whole-corpus migration window (single-walk discipline). Named successor plan:
      `pipeline_mode_partition_migration_<next-window-date>.md` to be created at next whole-corpus walk window.

## Phase 6 — Codex SSOT updates

- [x] ✅ [AGENT] P2. Write `/codex/02-data/pipeline-mode-and-batch-live-reconciliation.md` documenting the canonical
      `PipelineMode` enum, the derivation table, the reconciliation pattern, and the deferred-partition note. Cross-link
      from `/codex/02-data/availability-manifest-and-data-status.md` + `/codex/02-data/contracts-scope-and-layout.md`. —
      unified-trading-pm@58115ffc
- [x] ✅ [AGENT] P2. EDIT `plans/active/cefi_venue_backfill_coverage_remediation_2026_05_27.md` §6I pipeline_mode item
      marked `[x] ✅ — resolved by pipeline_mode_implementation_2026_05_28.md`. Phase 3.2-3.4 execution noted as pending
      operator action. — unified-trading-pm@40b05ad2

## Out of scope (explicit)

- **On-disk partition migration** → Phase 5 deferred to next migration window. Pre-emptive partition walks are
  review-blocking.
- **REMOVE path** → operator explicitly rejected REMOVE 2026-05-28; do NOT propose REMOVE again in any sub-plan.
- **Hyperliquid / Aster / direct-API venues** that don't go through Tardis/Databento — these fall under `live_polling`
  or `batch_onchain_rpc` per the Phase 0 derivation table; no special case here.

## Success criteria

- `SELECT count(*) WHERE pipeline_mode IS NULL` across every asset-group manifest = 0.
- `batch-live-reconciliation-service` reconciliation output groups by pipeline_mode and distinguishes batch vs live row
  sets for the same shard.
- QG STEP 5.7x asserts no missing pipeline_mode at write sites — green workspace-wide.
- Codex doc landed + cross-linked.
- §6I item 3 in `cefi_venue_backfill_coverage_remediation_2026_05_27.md` ticked.

> **🟡 DRAINED-WRITER DEPENDENCY (2026-06-01)** — the legacy-bucket SSOT remediation drained writer VMs
> `mdps-backfill-defi` / `mdps-prediction-2025` / `sports-scheduler`. They must NOT be relaunched until the
> legacy→canonical migration + manifest work complete. SSOT + relaunch gate:
> `plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` Phase 4.
